from asyncio import sleep
from datetime import datetime, time
from disnake import Embed, TextChannel
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.db import Steam, GWWGuild, MajorOrder, Dispatch
from utils.embeds import Dashboard, DispatchesEmbed, SteamEmbed
from utils.interactables import WikiButton
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

    async def send_embed(
        self, channel: TextChannel, embeds: dict[str, Embed], type: str
    ):
        guild = GWWGuild.get_by_id(channel.guild.id)
        if not guild:
            self.bot.logger.error(
                f"{self.qualified_name} | send_embed | {guild = } | {channel.id = } | {type = }"
            )
            if type == "Patch" and channel in self.bot.patch_channels:
                return self.bot.patch_channels.remove(channel)
            elif type == "Dispatch" and channel in self.bot.announcement_channels:
                return self.bot.announcement_channels.remove(channel)
            elif type == "MO" and channel in self.bot.major_order_channels:
                return self.bot.major_order_channels.remove(channel)
        try:
            components = None
            if type == "MO":
                components = [
                    WikiButton(link=f"https://helldivers.wiki.gg/wiki/Major_Orders")
                ]
            await channel.send(embed=embeds[guild.language], components=components)
        except Exception as e:
            for channels_list in (
                self.bot.announcement_channels,
                self.bot.patch_channels,
                self.bot.major_order_channels,
            ):
                if channel in channels_list:
                    channels_list.remove(channel)
            return self.bot.logger.error(
                f"{self.qualified_name} | send_embed | {e} | {channel.id = } | {guild = }"
            )

    @tasks.loop(minutes=1)
    async def major_order_check(self):
        announcement_start = datetime.now()
        if (
            not self.bot.announcement_channels
            or announcement_start < self.bot.ready_time
            or not self.bot.data.loaded
            or not self.bot.c_n_m_loaded
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
                    player_requirements=self.bot.data.planets_with_player_reqs,
                    language_json=self.bot.json_dict["languages"][lang],
                    json_dict=self.bot.json_dict,
                )
                for lang in list({guild.language for guild in GWWGuild.get_all()})
            }
            major_orders_sent = 0
            last_MO.id = self.bot.data.assignment.id
            last_MO.save_changes()
            for chunk in [
                self.bot.announcement_channels[i : i + 50]
                for i in range(0, len(self.bot.announcement_channels), 50)
            ]:
                for channel in chunk:
                    self.bot.loop.create_task(self.send_embed(channel, embeds, "MO"))
                    major_orders_sent += 1
                await sleep(1.5)
            self.bot.logger.info(
                f"{major_orders_sent} MO announcements sent out in {(datetime.now() - announcement_start).total_seconds():.2f} seconds"
            )

    @major_order_check.before_loop
    async def before_mo_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def dispatch_check(self):
        dispatch_start = datetime.now()
        if (
            not self.bot.announcement_channels
            or dispatch_start < self.bot.ready_time
            or not self.bot.data.loaded
            or not self.bot.c_n_m_loaded
        ):
            return
        last_dispatch = Dispatch()
        if last_dispatch.id != self.bot.data.dispatch.id:
            embeds = {
                lang: DispatchesEmbed(
                    self.bot.json_dict["languages"][lang], self.bot.data.dispatch
                )
                for lang in list({guild.language for guild in GWWGuild.get_all()})
            }
            chunked_channels = [
                self.bot.announcement_channels[i : i + 50]
                for i in range(0, len(self.bot.announcement_channels), 50)
            ]
            dispatches_sent = 0
            last_dispatch.id = self.bot.data.dispatch.id
            last_dispatch.save_changes()
            for chunk in chunked_channels:
                for channel in chunk:
                    self.bot.loop.create_task(
                        self.send_embed(channel, embeds, "Dispatch")
                    )
                    dispatches_sent += 1
                await sleep(1.5)
            self.bot.logger.info(
                f"{dispatches_sent} dispatch announcements sent out in {(datetime.now() - dispatch_start).total_seconds():.2f} seconds"
            )

    @dispatch_check.before_loop
    async def before_dispatch_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def steam_check(self):
        patch_notes_start = datetime.now()
        if (
            not self.bot.patch_channels
            or patch_notes_start < self.bot.ready_time
            or not self.bot.data.loaded
            or not self.bot.c_n_m_loaded
        ):
            return
        last_patch_notes = Steam()
        if last_patch_notes.id != self.bot.data.steam[0].id:
            languages = list({guild.language for guild in GWWGuild.get_all()})
            embeds = {
                lang: SteamEmbed(
                    self.bot.data.steam[0], self.bot.json_dict["languages"][lang]
                )
                for lang in languages
            }
            chunked_patch_channels = [
                self.bot.patch_channels[i : i + 50]
                for i in range(0, len(self.bot.patch_channels), 50)
            ]
            patch_notes_sent = 0
            last_patch_notes.id = self.bot.data.steam[0].id
            last_patch_notes.save_changes()
            for chunk in chunked_patch_channels:
                for channel in chunk:
                    self.bot.loop.create_task(self.send_embed(channel, embeds, "Patch"))
                    patch_notes_sent += 1
                await sleep(1.1)
            self.bot.logger.info(
                f"{patch_notes_sent} patch notes sent out in {(datetime.now() - patch_notes_start).total_seconds():.2f} seconds"
            )

    @steam_check.before_loop
    async def before_steam_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(
        time=[time(hour=6, minute=20, second=0), time(hour=18, minute=20, second=0)]
    )
    async def major_order_updates(self, force: bool = False, test: bool = False):
        mo_updates_start = datetime.now()
        if (
            not self.bot.major_order_channels
            or mo_updates_start < self.bot.ready_time
            or not self.bot.data.loaded
            or not self.bot.c_n_m_loaded
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
        chunked_mo_channels = [
            self.bot.major_order_channels[i : i + 50]
            for i in range(0, len(self.bot.major_order_channels), 50)
        ]
        mo_updates_sent = 0
        for chunk in chunked_mo_channels:
            for channel in chunk:
                self.bot.loop.create_task(self.send_embed(channel, embeds, "MO"))
                mo_updates_sent += 1
            await sleep(1.5)
        if not force:
            self.bot.logger.info(
                f"{mo_updates_sent} MO announcements sent out in {(datetime.now() - mo_updates_start).total_seconds():.2f} seconds"
            )
        return mo_updates_sent

    @major_order_updates.before_loop
    async def before_major_order_updates(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(AnnouncementsCog(bot))
