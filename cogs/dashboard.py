from os import getenv
from disnake import AppCmdInter, File
from disnake.ext import commands, tasks
from helpers.embeds import Dashboard
from helpers.db import Guilds
from datetime import datetime


class DashboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.dashboard.start()
        self.db_cleanup.start()
        print("Dashboard cog has finished loading")

    def cog_unload(self):
        self.dashboard.stop()
        self.db_cleanup.stop()

    @tasks.loop(minutes=1)
    async def dashboard(self):
        now = datetime.now()
        if now.minute not in [0, 15, 30, 45]:
            return
        guilds = Guilds.get_all_info()
        if not guilds:
            return
        dashboard = Dashboard()
        await dashboard.get_data()
        dashboard.set_data()
        for i in guilds:
            if i[1] != 0:
                try:
                    channel = self.bot.get_channel(
                        int(i[1])
                    ) or await self.bot.fetch_channel(int(i[1]))
                except:
                    continue
                try:
                    message = await channel.fetch_message(int(i[2]))
                except:
                    log_channel = self.bot.get_channel(
                        int(getenv("MODERATION_CHANNEL"))
                    ) or await self.bot.fetch_channel(int(getenv("MODERATION_CHANNEL")))
                    guild = self.bot.get_guild(int(i[0]))
                    await log_channel.send(
                        f"I had an issue updating dashboard in `{guild.name}`, owner is `{guild.owner.name}`."
                    )
                    print(f"Guild and channel of error: {guild.id, channel.id}")
                else:
                    if len(message.attachments) > 0:
                        await message.edit(embeds=dashboard.embeds)
                    else:
                        await message.edit(
                            embeds=dashboard.embeds, file=File("resources/banner.jpg")
                        )

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
        guilds = Guilds.get_all_info()
        if not guilds:
            return await inter.send("No dashboards found")
        dashboards_updated = 0
        dashboard = Dashboard()
        await dashboard.get_data()
        dashboard.set_data()
        for i in guilds:
            if i[1] != 0:
                try:
                    channel = self.bot.get_channel(
                        int(i[1])
                    ) or await self.bot.fetch_channel(int(i[1]))
                except:
                    continue
                try:
                    message = await channel.fetch_message(int(i[2]))
                except:
                    log_channel = channel = self.bot.get_channel(
                        int(getenv("MODERATION_CHANNEL"))
                    ) or await self.bot.fetch_channel(int(getenv("MODERATION_CHANNEL")))
                    guild = self.bot.get_guild(int(i[0]))
                    await log_channel.send(
                        f"I had an issue updating dashboard in `{guild.name}`, owner is `{guild.owner.name}`."
                    )
                else:
                    if len(message.attachments) > 0:
                        await message.edit(embeds=dashboard.embeds)
                    else:
                        await message.edit(
                            embeds=dashboard.embeds, file=File("resources/banner.jpg")
                        )
                    dashboards_updated += 1
        await inter.send(f"Updated {dashboards_updated} dashboards", ephemeral=True)

    @tasks.loop(hours=1)
    async def db_cleanup(self):
        guilds_in_db = Guilds.get_all_info()
        if not guilds_in_db:
            return
        guild_ids = []
        for i in self.bot.guilds:
            guild_ids.append(i.id)
        for guild in guilds_in_db:
            if guild[0] not in guild_ids:
                print("Anomoly found, removing")
                Guilds.remove_from_db(guild[0])
            continue

    @db_cleanup.before_loop
    async def before_dashboard(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(DashboardCog(bot))
