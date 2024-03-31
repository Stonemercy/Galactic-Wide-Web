from json import dumps, loads
from os import getenv
from aiohttp import ClientSession
from disnake import TextChannel
from disnake.ext import commands, tasks
from helpers.embeds import MajorOrderEmbed
from helpers.db import MajorOrders, Guilds
from data.lists import language_dict


class MOAnnouncementsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channels = []
        self.major_order_check.start()
        self.cache_channels.start()
        print("Major Orders cog has finished loading")

    def cog_unload(self):
        self.major_order_check.stop()
        self.cache_channels.stop()

    async def channel_list_gen(self, channel_id: int):
        try:
            channel = self.bot.get_channel(
                int(channel_id)
            ) or await self.bot.fetch_channel(int(channel_id))
            self.channels.append(channel)
        except:
            print(channel_id, "channel not found")
            pass

    async def send_major_order(self, channel: TextChannel, event):
        language = Guilds.get_info(channel.guild.id)[4]
        for a, j in language_dict.items():
            if a == language:
                language = j
        embed = MajorOrderEmbed(language, event)
        try:
            await channel.send(embed=embed)
        except Exception as e:
            print("Send major order", e, channel.id)
            pass

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
        self.newest_mo = None
        last_id = MajorOrders.get_last_id()
        api = getenv("API")
        async with ClientSession() as session:
            try:
                async with session.get(f"{api}/events/latest") as r:
                    if r.status == 200:
                        js = await r.json()
                        self.newest_mo = loads(dumps(js))
                        await session.close()
                    else:
                        pass
            except Exception as e:
                print(("Announcement Embed", e))
        if self.newest_mo == None:
            return
        if last_id == 0:
            MajorOrders.setup()
        if last_id == self.newest_mo["id"]:
            return
        else:
            MajorOrders.set_new_id(self.newest_mo["id"])
            for i in self.channels:
                self.bot.loop.create_task(self.send_major_order(i, self.newest_mo))

    @major_order_check.before_loop
    async def before_dashboard(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(MOAnnouncementsCog(bot))
