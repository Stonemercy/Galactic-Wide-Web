from asyncio import sleep
from disnake import TextChannel
from disnake.ext import commands, tasks
from helpers.embeds import DispatchesEmbed, MajorOrderEmbed, SteamEmbed
from helpers.db import Dispatches, MajorOrders, Guilds, Steam
from helpers.functions import pull_from_api


class AnnouncementsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channels = []
        self.patch_channels = []
        self.cache_channels.start()
        self.cache_patch_channels.start()
        self.major_order_check.start()
        self.dispatch_check.start()
        self.steam_check.start()
        print("Announcements cog has finished loading")

    def cog_unload(self):
        self.major_order_check.stop()
        self.cache_channels.stop()
        self.cache_patch_channels.stop()
        self.dispatch_check.stop()
        self.steam_check.stop()

    async def channel_list_gen(self, channel_id: int):
        try:
            channel = self.bot.get_channel(
                int(channel_id)
            ) or await self.bot.fetch_channel(int(channel_id))
            self.channels.append(channel)
        except Exception as e:
            return print("announcement channel list gen", channel_id, e)

    async def patch_channel_list_gen(self, channel_id: int):
        try:
            channel = self.bot.get_channel(
                int(channel_id)
            ) or await self.bot.fetch_channel(int(channel_id))
            self.patch_channels.append(channel)
        except Exception as e:
            return print("patch channel list gen", channel_id, e)

    async def send_embed(self, channel: TextChannel, embeds):
        guild = Guilds.get_info(channel.guild.id)
        if guild == None:
            return print("send_embed - Guild not in DB")
        try:
            await channel.send(embed=embeds[guild[5]])
        except Exception as e:
            return print("Send embed announcements", e, channel.id)

    @tasks.loop(count=1)
    async def cache_channels(self):
        guilds = Guilds.get_all_guilds()
        if not guilds:
            return
        self.channels = []
        for i in guilds:
            if i[3] == 0:
                continue
            self.bot.loop.create_task(self.channel_list_gen(i[3]))

    @cache_channels.before_loop
    async def before_caching(self):
        await self.bot.wait_until_ready()

    @tasks.loop(count=1)
    async def cache_patch_channels(self):
        guilds = Guilds.get_all_guilds()
        if not guilds:
            return
        self.patch_channels = []
        for i in guilds:
            if i[4] == False:
                continue
            self.bot.loop.create_task(self.patch_channel_list_gen(i[3]))

    @cache_patch_channels.before_loop
    async def before_patch_caching(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def major_order_check(self):
        last_id = MajorOrders.get_last_id()
        data = await pull_from_api(get_assignments=True, get_planets=True)
        if (
            len(data) < 2
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
                    self.bot.loop.create_task(self.send_embed(channel, embeds))
                await sleep(2)

    @major_order_check.before_loop
    async def before_mo_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def dispatch_check(self):
        last_id = Dispatches.get_last_id()
        data = await pull_from_api(get_dispatches=True)
        if len(data) == 0:
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
                    self.bot.loop.create_task(self.send_embed(channel, embeds))
                await sleep(2)

    @dispatch_check.before_loop
    async def before_dispatch_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def steam_check(self):
        last_id = Steam.get_last_id()
        data = await pull_from_api(get_steam=True)
        if len(data) == 0:
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
                    self.bot.loop.create_task(self.send_embed(channel, embeds))
                await sleep(2)

    @steam_check.before_loop
    async def before_steam_check(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(AnnouncementsCog(bot))
