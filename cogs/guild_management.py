from asyncio import sleep
from datetime import datetime
from disnake import Activity, ActivityType, AppCmdInter, Guild
from disnake.ext import commands, tasks
from helpers.db import Guilds, BotDashboard
from helpers.embeds import BotDashboardEmbed
from os import getenv, getpid
from psutil import Process, cpu_percent
from helpers.functions import health_bar


class GuildManagementCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot_dashboard.start()
        print("Guild Management cog has finished loading")
        self.startup_time = datetime.now()

    def cog_unload(self):
        self.bot_dashboard.stop()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        channel_id = int(getenv("MODERATION_CHANNEL"))
        channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
            channel_id
        )
        Guilds.set_info(guild_id=guild.id)
        await channel.send(
            f"Just joined server #{len(self.bot.guilds)} `{guild.name}` with {guild.member_count} members"
        )
        await self.bot.change_presence(
            activity=Activity(name="for alien sympathisers", type=ActivityType.watching)
        )
        await sleep(10.0)
        await self.bot.change_presence(
            activity=Activity(name="for socialism", type=ActivityType.watching)
        )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        channel_id = int(getenv("MODERATION_CHANNEL"))
        channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
            channel_id
        )
        Guilds.remove_from_db(guild.id)
        await channel.send(
            f"Just left `{guild.name}`, down to {len(self.bot.guilds)} servers"
        )

    @commands.slash_command(guild_ids=[int(getenv("SUPPORT_SERVER"))])
    async def info(self, inter: AppCmdInter):
        await inter.send(
            (f"Guilds: {len(inter.bot.guilds)}\n", f"Users: {len(inter.bot.users)}")
        )

    @commands.slash_command(guild_ids=[int(getenv("SUPPORT_SERVER"))])
    async def delete_message(self, inter: AppCmdInter, channel_id, message_id):
        try:
            channel = self.bot.get_channel(
                int(channel_id)
            ) or await self.bot.fetch_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))
            if message.author != self.bot.user:
                await inter.send(
                    "I won't delete messages that arent my own", ephemeral=True
                )
            await message.delete()
        except Exception as e:
            await inter.send(f"Couldn't do it:\n{e}", ephemeral=True)
        else:
            await inter.send("That worked", ephemeral=True)

    @tasks.loop(minutes=1)
    async def bot_dashboard(self):
        data = BotDashboard.get_info()
        if data[1] == 0:
            channel = self.bot.get_channel(data[0]) or await self.bot.fetch_channel(
                data[0]
            )
            message = await channel.send("Placeholder message, please ignore.")
            BotDashboard.set_info(channel.id, message.id)
        else:
            now = datetime.now()
            dashboard_embed = BotDashboardEmbed(now)
            dashboard_embed.add_field(
                "The GWW has",
                f"{len(self.bot.global_slash_commands)} commands available",
            ).add_field("Currently in", f"{len(self.bot.guilds)} discord servers")
            pid = getpid()
            process = Process(pid)
            memory_used = process.memory_info().rss / 1024**2
            dashboard_embed.add_field(
                "------------------\nHardware Info",
                (
                    f"**CPU**: {cpu_percent()}%\n"
                    f"**RAM**: {memory_used:.2f}MB\n"
                    f"**Last restart**: <t:{int(self.startup_time.timestamp())}:R>"
                ),
                inline=False,
            )
            not_setup = len(Guilds.not_setup())
            healthbar = health_bar(
                (len(self.bot.guilds) - not_setup), len(self.bot.guilds)
            )
            dashboard_embed.add_field(
                "------------------\nDashboards Info",
                (
                    f"**Setup**: {len(self.bot.guilds) - not_setup}\n"
                    f"**Not Setup**: {not_setup}\n"
                    f"{healthbar}"
                ),
            )

            channel = self.bot.get_channel(data[0]) or await self.bot.fetch_channel(
                data[0]
            )
            try:
                message = await channel.fetch_message(data[1])
            except Exception as e:
                print(f"bot_dashboard ", e)
            await message.edit(embed=dashboard_embed, content="")

    @bot_dashboard.before_loop
    async def before_bot_dashboard(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(GuildManagementCog(bot))
