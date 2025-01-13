from datetime import datetime, time
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.db import Steam, GWWGuild, MajorOrder, Dispatch
from utils.embeds import Dashboard, DispatchesEmbed, SteamEmbed
from utils.testing.assignment import TestAssignment


class AnnouncementsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.major_order_check.start()
        self.dispatch_check.start()
        self.steam_check.start()
        self.major_order_updates.start()

    def cog_unload(self):
        self.major_order_check.stop()
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
            or not self.bot.data.assignment
        ):
            return
        if self.bot.interface_handler.busy:
            return self.bot.logger.info(
                "Major order check tried to run but interface handler was busy"
            )
        last_MO = MajorOrder()
        if last_MO.id != self.bot.data.assignment.id:
            embeds = {
                lang: Dashboard.MajorOrderEmbed(
                    assignment=self.bot.data.assignment,
                    planets=self.bot.data.planets,
                    liberation_changes=self.bot.data.liberation_changes,
                    player_requirements=self.bot.data.planets_with_player_reqs,
                    language_json=self.bot.json_dict["languages"][lang],
                    json_dict=self.bot.json_dict,
                )
                for lang in list({guild.language for guild in GWWGuild.get_all()})
            }
            last_MO.id = self.bot.data.assignment.id
            last_MO.save_changes()
            await self.bot.interface_handler.send_news("MO", embeds)
            self.bot.logger.info(
                f"Sent MO announcements out to {len(self.bot.interface_handler.news_feeds.channels_dict['MO'])} channels"
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
        ):
            return
        if self.bot.interface_handler.busy:
            return self.bot.logger.info(
                "Dispatch check tried to run but interface handler was busy"
            )
        last_dispatch = Dispatch()
        if last_dispatch.id != self.bot.data.dispatch.id:
            embeds = {
                lang: DispatchesEmbed(
                    self.bot.json_dict["languages"][lang], self.bot.data.dispatch
                )
                for lang in list({guild.language for guild in GWWGuild.get_all()})
            }
            await self.bot.interface_handler.send_news("Generic", embeds)
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
        ):
            return
        if self.bot.interface_handler.busy:
            return self.bot.logger.info(
                "Steam check tried to run but interface handler was busy"
            )
        last_patch_notes = Steam()
        if last_patch_notes.id != self.bot.data.steam[0].id:
            languages = list({guild.language for guild in GWWGuild.get_all()})
            embeds = {
                lang: SteamEmbed(
                    self.bot.data.steam[0], self.bot.json_dict["languages"][lang]
                )
                for lang in languages
            }
            await self.bot.interface_handler.send_news("Patch", embeds)
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
                player_requirements=self.bot.data.planets_with_player_reqs,
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


def setup(bot: GalacticWideWebBot):
    bot.add_cog(AnnouncementsCog(bot))
