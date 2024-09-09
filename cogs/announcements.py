from asyncio import sleep
from datetime import datetime
from disnake import Forbidden, TextChannel, ButtonStyle
from disnake.ext import commands, tasks
from disnake.ui import Button
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.embeds import DispatchesEmbed, MajorOrderEmbed, SteamEmbed
from utils.db import DispatchesDB, GuildRecord, MajorOrderDB, GuildsDB, SteamDB
from utils.api import API, Data


class AnnouncementsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.major_order_check.start()
        self.dispatch_check.start()
        self.steam_check.start()

    def cog_unload(self):
        self.major_order_check.stop()
        self.dispatch_check.stop()
        self.steam_check.stop()

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
                GuildsDB.update_patch_notes(channel.guild.id, False)
            else:
                self.bot.announcement_channels.remove(channel)
                GuildsDB.update_announcement_channel(channel.guild.id, 0)
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
            else:
                await channel.send(embed=embeds[guild.language])
        except Forbidden as e:
            try:
                self.bot.announcement_channels.remove(channel)
            except:
                pass
            GuildsDB.update_announcement_channel(channel.guild.id, 0)
            return self.bot.logger.error(
                f"{self.qualified_name} | send_embed | {e} | {channel.id = }"
            )
        except Exception as e:
            return self.bot.logger.error(
                f"{self.qualified_name} | send_embed | {e} | {channel.id = }"
            )

    @wait_for_startup()
    @tasks.loop(minutes=1)
    async def major_order_check(self):
        if self.bot.announcement_channels == []:
            return
        announcement_start = datetime.now()
        api = API()
        await api.pull_from_api(get_assignments=True, get_planets=True)
        if api.error:
            return await self.bot.moderator_channel.send(
                f"<@164862382185644032>\n{api.error[0]}\n{api.error[1]}\n:warning:"
            )
        data = Data(data_from_api=api)
        if not data.assignment:
            return
        self._newest_id = data.assignment.id
        last_MO = MajorOrderDB.get_last()
        if not last_MO:
            last_MO = MajorOrderDB.setup()
        if last_MO.id != self._newest_id:
            languages = GuildsDB.get_used_languages()
            embeds = {
                lang: MajorOrderEmbed(data.assignment, data.planets, lang)
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
                await sleep(1.025)
            self.bot.logger.info(
                f"{major_orders_sent} MO announcements sent out in {(datetime.now() - announcement_start).total_seconds():.2f} seconds"
            )

    @major_order_check.before_loop
    async def before_mo_check(self):
        await self.bot.wait_until_ready()

    @wait_for_startup()
    @tasks.loop(minutes=1)
    async def dispatch_check(self):
        if self.bot.announcement_channels == []:
            return
        dispatch_start = datetime.now()
        api = API()
        await api.pull_from_api(get_dispatches=True)
        if api.error:
            return await self.bot.moderator_channel.send(
                f"<@164862382185644032>\n{api.error[0]}\n{api.error[1]}\n:warning:"
            )
        if api.dispatches in (None, []):
            return self.bot.logger.error(
                f"{self.qualified_name} | dispatch_check | {api.dispatches = }"
            )
        if api.dispatches[0]["message"] == None:
            return self.bot.logger.error(
                f'{self.qualified_name} | dispatch_check | {api.dispatches[0]["message"] = }'
            )
        data = Data(data_from_api=api)
        self._newest_id = data.dispatch.id
        last_dispatch = DispatchesDB.get_last()
        if not last_dispatch:
            last_dispatch = DispatchesDB.setup()
        if last_dispatch.id != self._newest_id:
            languages = GuildsDB.get_used_languages()
            embeds = {lang: DispatchesEmbed(data.dispatch) for lang in languages}
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
                await sleep(1.025)
            self.bot.logger.info(
                f"{dispatches_sent} dispatch announcements sent out in {(datetime.now() - dispatch_start).total_seconds():.2f} seconds"
            )

    @dispatch_check.before_loop
    async def before_dispatch_check(self):
        await self.bot.wait_until_ready()

    @wait_for_startup()
    @tasks.loop(minutes=1)
    async def steam_check(self):
        if self.bot.patch_channels == []:
            return
        patch_notes_start = datetime.now()
        api = API()
        await api.pull_from_api(get_steam=True)
        if api.error:
            return await self.bot.moderator_channel.send(
                f"<@164862382185644032>\n{api.error[0]}\n{api.error[1]}\n:warning:"
            )
        data = Data(data_from_api=api)
        self._newest_id = int(data.steam.id)
        last_patch_notes = SteamDB.get_last()
        if not last_patch_notes:
            last_patch_notes = SteamDB.setup()
        if last_patch_notes.id != self._newest_id:
            languages = GuildsDB.get_used_languages()
            embeds = {lang: SteamEmbed(data.steam) for lang in languages}
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
                await sleep(1.025)
            self.bot.logger.info(
                f"{patch_notes_sent} patch notes sent out in {(datetime.now() - patch_notes_start).total_seconds():.2f} seconds"
            )

    @steam_check.before_loop
    async def before_steam_check(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(AnnouncementsCog(bot))
