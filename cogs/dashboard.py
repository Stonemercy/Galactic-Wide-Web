from asyncio import sleep
from os import getenv
from disnake import AppCmdInter, PartialMessage
from disnake.ext import commands, tasks
from helpers.embeds import Dashboard
from helpers.db import Guilds
from datetime import datetime
from helpers.functions import pull_from_api


class DashboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.messages = []
        self.dashboard.start()
        self.db_cleanup.start()
        self.cache_messages.start()
        print("Dashboard cog has finished loading")

    def cog_unload(self):
        self.dashboard.stop()
        self.db_cleanup.stop()
        self.cache_messages.stop()

    async def message_list_gen(self, i):
        try:
            channel = self.bot.get_channel(int(i[1])) or await self.bot.fetch_channel(
                int(i[1])
            )
            try:
                message = channel.get_partial_message(int(i[2]))
                self.messages.append(message)
            except Exception as e:
                guild = self.bot.get_guild(int(i[0]))
                print("message_list_gen message", guild.id, e)
        except Exception as e:
            return print("message_list_gen channel", i[1], e)

    async def update_message(self, i: PartialMessage, data):
        guild = Guilds.get_info(i.guild.id)
        if guild == None:
            return print("Update message - Guild not in DB")
        dashboard = Dashboard(data)
        try:
            await i.edit(embeds=dashboard.embeds)
        except Exception as e:
            print("Update message", e, i)
            pass

    @tasks.loop(count=1)
    async def cache_messages(self):
        guilds = Guilds.get_all_guilds()
        if not guilds:
            return
        self.messages = []
        for i in guilds:
            if i[1] == 0:
                continue
            self.bot.loop.create_task(self.message_list_gen(i))

    @cache_messages.before_loop
    async def before_caching(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def dashboard(self):
        now = datetime.now()
        if now.minute not in [0, 15, 30, 45] or self.messages == []:
            return
        data = await pull_from_api(
            get_campaigns=True,
            get_assignments=True,
            get_planet_events=True,
            get_planets=True,
        )
        chunked_messages = [
            self.messages[i : i + 50] for i in range(0, len(self.messages), 50)
        ]
        for chunk in chunked_messages:
            for message in chunk:
                self.bot.loop.create_task(self.update_message(message, data))
            await sleep(2.0)  # keep at 2.0

    @dashboard.before_loop
    async def before_dashboard(self):
        await self.bot.wait_until_ready()

    @commands.slash_command(guild_ids=[int(getenv("SUPPORT_SERVER"))])
    async def force_update_dashboard(self, inter: AppCmdInter):
        if inter.author.id != self.bot.owner_id:
            return await inter.send(
                "You can't use this", ephemeral=True, delete_after=3.0
            )
        await inter.response.defer(ephemeral=True)
        dashboards_updated = 0
        data = await pull_from_api(
            get_campaigns=True,
            get_assignments=True,
            get_planet_events=True,
            get_planets=True,
        )
        chunked_messages = [
            self.messages[i : i + 50] for i in range(0, len(self.messages), 50)
        ]
        for chunk in chunked_messages:
            for message in chunk:
                self.bot.loop.create_task(self.update_message(message, data))
                dashboards_updated += 1
            await sleep(2.0)  # keep at 2.0
        await inter.send(
            f"Attempted to update {dashboards_updated} dashboards",
            ephemeral=True,
            delete_after=5,
        )

    @tasks.loop(minutes=5)
    async def db_cleanup(self):
        messages: list[PartialMessage] = self.messages
        guilds_in_db = Guilds.get_all_guilds()
        if not guilds_in_db:
            return
        guild_ids = []
        for i in self.bot.guilds:
            guild_ids.append(i.id)
        for guild in guilds_in_db:
            if guild[0] not in guild_ids:
                print(f"Anomoly found, removing")
                Guilds.remove_from_db(guild[0])
                for j in messages:
                    if j.guild.id == guild[0]:
                        messages.remove(j)
            continue

    @db_cleanup.before_loop
    async def before_dashboard(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(DashboardCog(bot))
