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
            or not self.bot.data.assignments
        ):
            return
        active_mo_ids = MajorOrder()
        for major_order in self.bot.data.assignments:
            if major_order.id not in active_mo_ids.ids:
                embeds = {
                    lang: [
                        Dashboard.MajorOrderEmbed(
                            assignment=major_order,
                            planets=self.bot.data.planets,
                            liberation_changes_tracker=self.bot.data.liberation_changes,
                            mo_task_tracker=self.bot.data.major_order_changes,
                            language_json=self.bot.json_dict["languages"][lang],
                            json_dict=self.bot.json_dict,
                            with_health_bars=True,
                        )
                    ]
                    for lang in list({guild.language for guild in GWWGuild.get_all()})
                }
                mo_briefing = [
                    ge
                    for ge in self.bot.data.global_events
                    if ge.assignment_id == major_order.id
                    and ge.title != ""
                    and ge.message != ""
                ]
                if mo_briefing:
                    mo_briefing = mo_briefing[0]
                    for embed_list in embeds.values():
                        for embed in embed_list:
                            embed.insert_field_at(
                                0,
                                mo_briefing.title,
                                mo_briefing.split_message[0],
                                inline=False,
                            )
                            for index, chunk in enumerate(
                                mo_briefing.split_message[1:], 1
                            ):
                                embed.insert_field_at(index, "", chunk, inline=False)
                else:
                    self.bot.logger.info(
                        f"MO briefing not available for assignment {major_order.id}"
                    )
                active_mo_ids.ids.append(major_order.id)
                active_mo_ids.save_changes()
                await self.bot.interface_handler.send_news("Generic", embeds)
                self.bot.logger.info(
                    f"Sent MO announcements out to {len(self.bot.interface_handler.news_feeds.channels_dict['Generic'])} channels"
                )
        current_mo_ids = [mo.id for mo in self.bot.data.assignments]
        for active_id in active_mo_ids.ids.copy():
            if active_id not in current_mo_ids:
                active_mo_ids.ids.remove(active_id)
                active_mo_ids.save_changes()

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
        for dispatch in self.bot.data.dispatches:
            if last_dispatch.id < dispatch.id:
                if len(dispatch.message) < 25:
                    continue
                embeds = {
                    lang: [
                        DispatchesLoopEmbed(
                            self.bot.json_dict["languages"][lang], dispatch
                        )
                    ]
                    for lang in list({guild.language for guild in GWWGuild.get_all()})
                }
                await self.bot.interface_handler.send_news("Generic", embeds)
                last_dispatch.id = dispatch.id
                last_dispatch.save_changes()
                self.bot.logger.info(
                    f"Sent generic announcements out to {len(self.bot.interface_handler.news_feeds.channels_dict['Generic'])} channels"
                )
                return

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
                lang: [
                    SteamLoopEmbed(
                        self.bot.data.steam[0], self.bot.json_dict["languages"][lang]
                    )
                ]
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
        time=[time(hour=5, minute=20, second=0), time(hour=17, minute=20, second=0)]
    )
    async def major_order_updates(self):
        mo_updates_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or mo_updates_start < self.bot.ready_time
            or not self.bot.data.loaded
            or not self.bot.data.assignments
        ):
            return
        embeds = {
            lang: [
                Dashboard.MajorOrderEmbed(
                    assignment=major_order,
                    planets=self.bot.data.planets,
                    liberation_changes_tracker=self.bot.data.liberation_changes,
                    mo_task_tracker=self.bot.data.major_order_changes,
                    language_json=self.bot.json_dict["languages"][lang],
                    json_dict=self.bot.json_dict,
                    with_health_bars=True,
                )
                for major_order in self.bot.data.assignments
            ]
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
                if (
                    global_event.assignment_id != 0
                    or all(
                        [
                            not global_event.title,
                            not global_event.message,
                            not global_event.effect_ids,
                        ]
                    )
                    or global_event.title.upper() == "BRIEFING"
                ):
                    last_GE.id = global_event.id
                    last_GE.save_changes()
                    continue
                embeds = {
                    lang: [
                        GlobalEventsLoopEmbed(
                            self.bot.data.planets,
                            self.bot.json_dict["languages"][lang],
                            self.bot.json_dict["planet_effects"],
                            global_event,
                        )
                    ]
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
