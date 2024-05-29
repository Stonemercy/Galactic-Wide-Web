from asyncio import sleep
from logging import getLogger
from disnake import Forbidden, TextChannel
from disnake.ext import commands, tasks
from helpers.embeds import DispatchesEmbed, MajorOrderEmbed, SteamEmbed
from helpers.db import Dispatches, MajorOrders, Guilds, Steam
from helpers.functions import pull_from_api

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
            if type == "Patch":
                self.patch_channels.remove(channel)
                Guilds.update_patch_notes(channel.guild.id, False)
            else:
                self.channels.remove(channel)
                Guilds.update_announcement_channel(channel.guild.id, 0)
            return logger.error("AnnouncementsCog send_embed - Guild not in DB")
        try:
            await channel.send(embed=embeds[guild[5]])
        except Forbidden:
            self.channels.remove(channel)
            Guilds.update_announcement_channel(channel.guild.id, 0)
            return logger.error(f"AnnouncementsCog send_embed forbidden {channel.id}")
        except Exception as e:
            return logger.error(f"AnnouncementsCog send_embed, {e}, {channel.id}")

    @tasks.loop(minutes=1)
    async def major_order_check(self):
        if len(self.channels) == 0:
            return
        last_id = MajorOrders.get_last_id()
        data = await pull_from_api(get_assignments=True, get_planets=True)
        if (
            data["assignments"] in (None, [])
            or data["planets"] in (None, [])
            or data["assignments"][0]["briefing"] == None
            or data["assignments"][0]["description"] == 0
        ):
            return
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
            for chunk in chunked_channels:
                for channel in chunk:
                    self.bot.loop.create_task(self.send_embed(channel, embeds, "MO"))
                await sleep(2)

    @major_order_check.before_loop
    async def before_mo_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def dispatch_check(self):
        last_id = Dispatches.get_last_id()
        data = await pull_from_api(get_dispatches=True)
        if data["dispatches"] in (None, []):
            return
        if data["dispatches"][0]["message"] == None:
            return
        self.newest_id = data["dispatches"][0]["id"]
        if last_id == None:
            Dispatches.setup()
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
            for chunk in chunked_channels:
                for channel in chunk:
                    self.bot.loop.create_task(
                        self.send_embed(channel, embeds, "Dispatch")
                    )
                await sleep(2)

    @dispatch_check.before_loop
    async def before_dispatch_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def steam_check(self):
        last_id = Steam.get_last_id()
        data = await pull_from_api(get_steam=True)
        if data["steam"] in (None, []):
            return
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
            for chunk in chunked_patch_channels:
                for channel in chunk:
                    self.bot.loop.create_task(self.send_embed(channel, embeds, "Patch"))
                await sleep(2)

    @steam_check.before_loop
    async def before_steam_check(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(AnnouncementsCog(bot))
