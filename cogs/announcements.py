from datetime import datetime, time
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.db import GlobalEvent, Steam, GWWGuild, MajorOrder, Dispatch
from utils.embeds.dashboard import Dashboard
from utils.embeds.loop_embeds import (
    DispatchesLoopEmbed,
    GlobalEventsLoopEmbed,
    SteamLoopEmbed,
)
from utils.testing.assignment import TestAssignment


class AnnouncementsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.major_order_check.start()
        self.global_event_check.start()
        self.dispatch_check.start()
        self.steam_check.start()
        self.major_order_updates.start()

    def cog_unload(self):
        self.major_order_check.stop()
        self.global_event_check.stop()
        self.dispatch_check.stop()
        self.steam_check.stop()
        self.major_order_updates.stop()

    @tasks.loop(minutes=1)
    async def major_order_check(self):
        announcement_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or announcement_start < self.bot.ready_time
            or not self.bot.data.loaded
            or self.bot.interface_handler.busy
            or not self.bot.data.assignment
        ):
            return
        last_MO = MajorOrder()
        if last_MO.id != self.bot.data.assignment.id:
            embeds = {
                lang: Dashboard.MajorOrderEmbed(
                    assignment=self.bot.data.assignment,
                    planets=self.bot.data.planets,
                    liberation_changes=self.bot.data.liberation_changes,
                    language_json=self.bot.json_dict["languages"][lang],
                    json_dict=self.bot.json_dict,
                )
                for lang in list({guild.language for guild in GWWGuild.get_all()})
            }
            mo_briefing_list = [
                ge
                for ge in self.bot.data.global_events
                if ge.assignment_id == self.bot.data.assignment.id
            ]
            if mo_briefing_list:
                mo_briefing = mo_briefing_list[0]
                for embed in embeds.values():
                    embed.insert_field_at(
                        0, mo_briefing.title, mo_briefing.split_message[0], inline=False
                    )
                    for index, chunk in enumerate(mo_briefing.split_message[1:], 1):
                        embed.insert_field_at(index, "", chunk, inline=False)
            else:
                self.bot.logger.info(f"MO briefing not available")
                return
            last_MO.id = self.bot.data.assignment.id
            last_MO.save_changes()
            await self.bot.interface_handler.send_news("Generic", embeds)
            self.bot.logger.info(
                f"Sent MO announcements out to {len(self.bot.interface_handler.news_feeds.channels_dict['Generic'])} channels"
            )

    @major_order_check.before_loop
    async def before_mo_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def dispatch_check(self):
        dispatch_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or dispatch_start < self.bot.ready_time
            or not self.bot.data.loaded
            or self.bot.interface_handler.busy
        ):
            return
        last_dispatch = Dispatch()
        if last_dispatch.id != self.bot.data.dispatch.id:
            embeds = {
                lang: DispatchesLoopEmbed(
                    self.bot.json_dict["languages"][lang], self.bot.data.dispatch
                )
                for lang in list({guild.language for guild in GWWGuild.get_all()})
            }
            await self.bot.interface_handler.send_news("Generic", embeds)
            last_dispatch.id = self.bot.data.dispatch.id
            last_dispatch.save_changes()
            self.bot.logger.info(
                f"Sent generic announcements out to {len(self.bot.interface_handler.news_feeds.channels_dict['Generic'])} channels"
            )

    @dispatch_check.before_loop
    async def before_dispatch_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def steam_check(self):
        patch_notes_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or patch_notes_start < self.bot.ready_time
            or not self.bot.data.loaded
            or self.bot.interface_handler.busy
        ):
            return
        last_patch_notes = Steam()
        if last_patch_notes.id != self.bot.data.steam[0].id:
            languages = list({guild.language for guild in GWWGuild.get_all()})
            embeds = {
                lang: SteamLoopEmbed(
                    self.bot.data.steam[0], self.bot.json_dict["languages"][lang]
                )
                for lang in languages
            }
            await self.bot.interface_handler.send_news("Patch", embeds)
            last_patch_notes.id = self.bot.data.steam[0].id
            last_patch_notes.save_changes()
            self.bot.logger.info(
                f"Sent patch announcements out to {len(self.bot.interface_handler.news_feeds.channels_dict['Patch'])} channels"
            )

    @steam_check.before_loop
    async def before_steam_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(
        time=[time(hour=6, minute=20, second=0), time(hour=18, minute=20, second=0)]
    )
    async def major_order_updates(self, test: bool = False):
        mo_updates_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or mo_updates_start < self.bot.ready_time
            or not self.bot.data.loaded
            or (not self.bot.data.assignment and not test)
        ):
            return
        embeds = {
            lang: Dashboard.MajorOrderEmbed(
                assignment=self.bot.data.assignment if not test else TestAssignment(),
                planets=self.bot.data.planets,
                liberation_changes=self.bot.data.liberation_changes,
                language_json=self.bot.json_dict["languages"][lang],
                json_dict=self.bot.json_dict,
            )
            for lang in list(set([guild.language for guild in GWWGuild.get_all()]))
        }
        await self.bot.interface_handler.send_news("MO", embeds)
        self.bot.logger.info(
            f"Sent MO announcements out to {len(self.bot.interface_handler.news_feeds.channels_dict['MO'])} channels"
        )

    @major_order_updates.before_loop
    async def before_major_order_updates(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def global_event_check(self):
        ge_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or ge_start < self.bot.ready_time
            or not self.bot.data.loaded
            or self.bot.interface_handler.busy
            or not self.bot.data.global_events
        ):
            return
        last_GE = GlobalEvent()
        for global_event in self.bot.data.global_events:
            if global_event.id > last_GE.id:
                if global_event.title == "BRIEFING":
                    last_GE.id = global_event.id
                    last_GE.save_changes()
                    continue
                embeds = {
                    lang: GlobalEventsLoopEmbed(
                        self.bot.data.planets,
                        self.bot.json_dict["languages"][lang],
                        self.bot.json_dict["planet_effects"],
                        global_event,
                    )
                    for lang in list({guild.language for guild in GWWGuild.get_all()})
                }
                last_GE.id = global_event.id
                last_GE.save_changes()
                await self.bot.interface_handler.send_news("DetailedDispatches", embeds)
                self.bot.logger.info(
                    f"Sent Global Event out to {len(self.bot.interface_handler.news_feeds.channels_dict['DetailedDispatches'])} channels"
                )
                break

    @global_event_check.before_loop
    async def before_ge_check(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(AnnouncementsCog(bot))
