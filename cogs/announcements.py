from asyncio import sleep
from datetime import datetime
from logging import getLogger
from disnake import Forbidden, TextChannel, ButtonStyle
from disnake.ext import commands, tasks
from helpers.embeds import DispatchesEmbed, MajorOrderEmbed, SteamEmbed
from helpers.db import Dispatches, MajorOrders, Guilds, Steam
from helpers.functions import pull_from_api
from disnake.ui import Button

logger = getLogger("disnake")


class AnnouncementsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channels = []
        self.patch_channels = []
        self.major_order_check.start()
        self.dispatch_check.start()
        self.steam_check.start()

    def cog_unload(self):
        self.major_order_check.stop()
        self.dispatch_check.stop()
        self.steam_check.stop()

    async def send_embed(self, channel: TextChannel, embeds, type: str):
        guild = Guilds.get_info(channel.guild.id)
        if guild == None:
            logger.error(
                f"AnnouncementsCog, send_embed, guild == None for {channel.id}, {type}"
            )
            if type == "Patch":
                self.patch_channels.remove(channel)
                Guilds.update_patch_notes(channel.guild.id, False)
            else:
                self.channels.remove(channel)
                Guilds.update_announcement_channel(channel.guild.id, 0)
        try:
            if type == "Announcement":
                await channel.send(
                    embed=embeds[guild[5]],
                    components=[
                        Button(
                            style=ButtonStyle.link,
                            label="Support Server",
                            url="https://discord.gg/Z8Ae5H5DjZ",
                        )
                    ],
                )
            else:
                await channel.send(embed=embeds[guild[5]])
        except Forbidden:
            self.channels.remove(channel)
            Guilds.update_announcement_channel(channel.guild.id, 0)
            return logger.error(
                f"AnnouncementsCog, send_embed, Forbidden, {channel.id}"
            )
        except Exception as e:
            return logger.error(f"AnnouncementsCog, send_embed, {e}, {channel.id}")

    @tasks.loop(minutes=1)
    async def major_order_check(self):
        announcement_start = datetime.now()
        if len(self.channels) == 0:
            return logger.error("AnnouncementsCog, len(self.channels) == 0")
        last_id = MajorOrders.get_last_id()
        data = await pull_from_api(get_assignments=True, get_planets=True)
        for data_key, data_value in data.items():
            if data_value == None:
                return logger.error(
                    f"AnnouncementsCog, major_order_check, {data_key} returned {data_value}"
                )
        if len(data["assignments"]) < 1:
            return  # return nothing because this happens when there's no MO
        self.newest_id = data["assignments"][0]["id"]
        if last_id == None:
            MajorOrders.setup()
            last_id = MajorOrders.get_last_id()
        if last_id == 0 or last_id != self.newest_id:
            MajorOrders.set_new_id(self.newest_id)
            languages = Guilds.get_used_languages()
            embeds = {}
            for lang in languages:
                embed = MajorOrderEmbed(data["assignments"][0], data["planets"], lang)
                embeds[lang] = embed
            chunked_channels = [
                self.channels[i : i + 50] for i in range(0, len(self.channels), 50)
            ]
            major_orders_sent = 0
            for chunk in chunked_channels:
                for channel in chunk:
                    self.bot.loop.create_task(self.send_embed(channel, embeds, "MO"))
                    major_orders_sent += 1
                await sleep(1.025)
            logger.info(
                f"{major_orders_sent} MO announcements sent out in {(datetime.now() - announcement_start).total_seconds():.2f} seconds"
            )

    @major_order_check.before_loop
    async def before_mo_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def dispatch_check(self):
        announcement_start = datetime.now()
        last_id = Dispatches.get_last_id()
        data = await pull_from_api(get_dispatches=True)
        if data["dispatches"] == None:
            return logger.error(
                f'AnnouncementsCog, dispatch_check, data["dispatches"] == None'
            )
        if data["dispatches"][0]["message"] == None:
            return logger.error(
                f'AnnouncementsCog, dispatch_check, data["dispatches"][0]["message"] == None'
            )
        self.newest_id = data["dispatches"][0]["id"]
        if last_id == None:
            Dispatches.setup()
            last_id = Dispatches.get_last_id()
        if last_id == 0 or last_id != self.newest_id:
            Dispatches.set_new_id(self.newest_id)
            languages = Guilds.get_used_languages()
            embeds = {}
            for lang in languages:
                embed = DispatchesEmbed(data["dispatches"][0])
                embeds[lang] = embed
            chunked_channels = [
                self.channels[i : i + 50] for i in range(0, len(self.channels), 50)
            ]
            announcements_sent = 0
            for chunk in chunked_channels:
                for channel in chunk:
                    self.bot.loop.create_task(
                        self.send_embed(channel, embeds, "Dispatch")
                    )
                    announcements_sent += 1
                await sleep(1.025)
            logger.info(
                f"{announcements_sent} dispatch announcements sent out in {(datetime.now() - announcement_start).total_seconds():.2f} seconds"
            )

    @dispatch_check.before_loop
    async def before_dispatch_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def steam_check(self):
        patch_notes_start = datetime.now()
        last_id = Steam.get_last_id()
        data = await pull_from_api(get_steam=True)
        if data["steam"] == None:
            return logger.info(f'AnnouncementsCog, steam_check, data["steam"] == None')
        self.newest_id = int(data["steam"][0]["id"])
        if last_id == None:
            Steam.setup()
            last_id = Steam.get_last_id()
        if last_id == 0 or last_id != self.newest_id:
            Steam.set_new_id(self.newest_id)
            languages = Guilds.get_used_languages()
            embeds = {}
            for lang in languages:
                embed = SteamEmbed(data["steam"][0])
                embeds[lang] = embed
            chunked_patch_channels = [
                self.patch_channels[i : i + 50]
                for i in range(0, len(self.patch_channels), 50)
            ]
            patch_notes_sent = 0
            for chunk in chunked_patch_channels:
                for channel in chunk:
                    self.bot.loop.create_task(self.send_embed(channel, embeds, "Patch"))
                    patch_notes_sent += 1
                await sleep(1.025)
            logger.info(
                f"{patch_notes_sent} patch notes sent out in {(datetime.now() - patch_notes_start).total_seconds():.2f} seconds"
            )

    @steam_check.before_loop
    async def before_steam_check(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(AnnouncementsCog(bot))
