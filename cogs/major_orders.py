from disnake import Embed, TextChannel
from disnake.ext import commands, tasks
from helpers.embeds import DispatchesEmbed, MajorOrderEmbed, SteamEmbed
from helpers.db import Dispatches, MajorOrders, Guilds, Steam
from helpers.functions import pull_from_api


class MOAnnouncementsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channels = []
        self.major_order_check.start()
        self.cache_channels.start()
        self.dispatch_check.start()
        self.steam_check.start()
        print("Major Orders cog has finished loading")

    def cog_unload(self):
        self.major_order_check.stop()
        self.cache_channels.stop()
        self.dispatch_check.stop()
        self.steam_check.stop()

    async def channel_list_gen(self, channel_id: int):
        try:
            channel = self.bot.get_channel(
                int(channel_id)
            ) or await self.bot.fetch_channel(int(channel_id))
            self.channels.append(channel)
        except Exception as e:
            return print("MO channel list gen", channel_id, e)

    async def send_embed(self, channel: TextChannel, embed: Embed):
        guild = Guilds.get_info(channel.guild.id)
        if guild == None:
            return print("send_embed - Guild not in DB")
        try:
            await channel.send(embed=embed)
        except Exception as e:
            return print("Send embed", e, channel.id)

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

    @tasks.loop(minutes=1)
    async def major_order_check(self):
        last_id = MajorOrders.get_last_id()
        data = await pull_from_api(get_assignments=True, get_planets=True)
        self.newest_id = data["assignments"][0]["id"]
        if last_id == None:
            MajorOrders.setup()
            last_id = MajorOrders.get_last_id()
        if last_id == 0 or last_id != self.newest_id:
            MajorOrders.set_new_id(self.newest_id)
            embed = MajorOrderEmbed(data["assignments"][0], data["planets"])
            for i in self.channels:
                self.bot.loop.create_task(self.send_embed(i, embed))

    @major_order_check.before_loop
    async def before_mo_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def dispatch_check(self):
        last_id = Dispatches.get_last_id()
        data = await pull_from_api(get_dispatches=True)
        self.newest_id = data["dispatches"][0]["id"]
        if last_id == None:
            Dispatches.setup()
        if last_id == 0 or last_id != self.newest_id:
            Dispatches.set_new_id(self.newest_id)
            embed = DispatchesEmbed(data["dispatches"][0])
            for i in self.channels:
                self.bot.loop.create_task(self.send_embed(i, embed))

    @dispatch_check.before_loop
    async def before_dispatch_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def steam_check(self):
        last_id = Steam.get_last_id()
        data = await pull_from_api(get_steam=True)
        self.newest_id = int(data["steam"][0]["id"])
        if last_id == None:
            Steam.setup()
        if last_id == 0 or last_id != self.newest_id:
            Steam.set_new_id(self.newest_id)
            embed = SteamEmbed(data["steam"][0])
            for i in self.channels:
                self.bot.loop.create_task(self.send_embed(i, embed))

    @steam_check.before_loop
    async def before_steam_check(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(MOAnnouncementsCog(bot))
