from asyncio import sleep
from datetime import datetime, time
from disnake import Forbidden, TextChannel, ButtonStyle
from disnake.ext import commands, tasks
from disnake.ui import Button
from main import GalacticWideWebBot
from utils.embeds import DispatchesEmbed, MajorOrderEmbed, SteamEmbed
from utils.db import DispatchesDB, GuildRecord, MajorOrderDB, GuildsDB, SteamDB
from utils.interactables import WikiButton


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

    async def send_embed(self, channel: TextChannel, embeds, type: str):
        """embeds must be a dict in the following format:\n
        `{ language: embed }`\n
        and needs to have all languages used by the userbase"""
        guild: GuildRecord = GuildsDB.get_info(channel.guild.id)
        if not guild:
            self.bot.logger.error(
                f"{self.qualified_name} | send_embed | {guild = } | {channel.id = } | {type = }"
            )
            if type == "Patch":
                self.bot.patch_channels.remove(channel)
                guild = GuildsDB.update_patch_notes(channel.guild.id, False)
            else:
                self.bot.announcement_channels.remove(channel)
                guild = GuildsDB.update_announcement_channel(channel.guild.id, 0)
            return
        try:
            if type == "Announcement":
                await channel.send(
                    embed=embeds[guild.language],
                    components=[
                        Button(
                            style=ButtonStyle.link,
                            label="Support Server",
                            url="https://discord.gg/Z8Ae5H5DjZ",
                        )
                    ],
                )
            elif type == "MO":
                await channel.send(
                    embed=embeds[guild.language],
                    components=[
                        WikiButton(link=f"https://helldivers.wiki.gg/wiki/Major_Orders")
                    ],
                )
            else:
                await channel.send(embed=embeds[guild.language])
        except Forbidden as e:
            try:
                self.bot.announcement_channels.remove(channel)
            except:
                pass
            guild = GuildsDB.update_announcement_channel(channel.guild.id, 0)
            return self.bot.logger.error(
                f"{self.qualified_name} | send_embed | {e} | {channel.id = }"
            )
        except Exception as e:
            return self.bot.logger.error(
                f"{self.qualified_name} | send_embed | {e} | {channel.id = }"
            )

    @tasks.loop(minutes=1)
    async def major_order_check(self):
        announcement_start = datetime.now()
        if (
            self.bot.announcement_channels == []
            or announcement_start < self.bot.ready_time
            or not self.bot.data.loaded
            or not self.bot.c_n_m_loaded
        ):
            return
        if not self.bot.data.assignment:
            return
        self._newest_id = self.bot.data.assignment.id
        last_MO = MajorOrderDB.get_last()
        if not last_MO:
            last_MO = MajorOrderDB.setup()
        if last_MO.id != self._newest_id:
            languages = GuildsDB.get_used_languages()
            embeds = {
                lang: MajorOrderEmbed(
                    data=self.bot.data,
                    language=self.bot.json_dict["languages"][lang],
                    planet_names=self.bot.json_dict["planets"],
                    reward_types=self.bot.json_dict["items"]["reward_types"],
                )
                for lang in languages
            }
            chunked_channels = [
                self.bot.announcement_channels[i : i + 50]
                for i in range(0, len(self.bot.announcement_channels), 50)
            ]
            major_orders_sent = 0
            MajorOrderDB.set_new_id(self._newest_id)
            for chunk in chunked_channels:
                for channel in chunk:
                    self.bot.loop.create_task(self.send_embed(channel, embeds, "MO"))
                    major_orders_sent += 1
                await sleep(1.1)
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
            self.bot.announcement_channels == []
            or dispatch_start < self.bot.ready_time
            or not self.bot.data.loaded
            or not self.bot.c_n_m_loaded
        ):
            return
        self._newest_id = self.bot.data.dispatch.id
        last_dispatch = DispatchesDB.get_last()
        if not last_dispatch:
            last_dispatch = DispatchesDB.setup()
        if last_dispatch.id != self._newest_id:
            languages = GuildsDB.get_used_languages()
            embeds = {
                lang: DispatchesEmbed(
                    self.bot.json_dict["languages"][lang], self.bot.data.dispatch
                )
                for lang in languages
            }
            chunked_channels = [
                self.bot.announcement_channels[i : i + 50]
                for i in range(0, len(self.bot.announcement_channels), 50)
            ]
            dispatches_sent = 0
            DispatchesDB.set_new_id(self._newest_id)
            for chunk in chunked_channels:
                for channel in chunk:
                    self.bot.loop.create_task(
                        self.send_embed(channel, embeds, "Dispatch")
                    )
                    dispatches_sent += 1
                await sleep(1.1)
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
            self.bot.patch_channels == []
            or patch_notes_start < self.bot.ready_time
            or not self.bot.data.loaded
            or not self.bot.c_n_m_loaded
        ):
            return

        self._newest_id = int(self.bot.data.steam[0].id)
        last_patch_notes = SteamDB.get_last()
        if not last_patch_notes:
            last_patch_notes = SteamDB.setup()
        if last_patch_notes.id != self._newest_id:
            languages = GuildsDB.get_used_languages()
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
            SteamDB.set_new_id(self._newest_id)
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

    @tasks.loop(time=[time(hour=hour, minute=20, second=0) for hour in range(0, 24, 6)])
    async def major_order_updates(self, force: bool = False):
        mo_updates_start = datetime.now()
        if (
            self.bot.major_order_channels == []
            or mo_updates_start < self.bot.ready_time
            or not self.bot.data.loaded
            or not self.bot.c_n_m_loaded
        ):
            return
        if self.bot.data.assignment == None:
            return
        languages = GuildsDB.get_used_languages()
        embeds = {
            lang: MajorOrderEmbed(
                data=self.bot.data,
                language=self.bot.json_dict["languages"][lang],
                planet_names=self.bot.json_dict["planets"],
                reward_types=self.bot.json_dict["items"]["reward_types"],
                with_health_bars=True,
            )
            for lang in languages
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
            await sleep(1.1)
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
