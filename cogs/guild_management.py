from asyncio import sleep
from datetime import datetime
from disnake import (
    Activity,
    ActivityType,
    ButtonStyle,
    Guild,
)
from disnake.ext import commands, tasks
from helpers.db import Guilds, BotDashboard
from helpers.embeds import BotDashboardEmbed
from os import getenv, getpid
from psutil import Process, cpu_percent
from helpers.functions import health_bar
from disnake.ui import Button


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
        Guilds.insert_new_guild(guild.id)
        await channel.send(
            f"Just joined server #{len(self.bot.guilds)} `{guild.name}` with {guild.member_count} members"
        )
        await self.bot.change_presence(
            activity=Activity(name="for alien sympathisers", type=ActivityType.watching)
        )
        await sleep(10.0)
        await self.bot.change_presence(
            activity=Activity(name="for Socialism", type=ActivityType.watching)
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

            dashboard_not_setup = len(Guilds.dashboard_not_setup())
            healthbar = health_bar(
                (len(self.bot.guilds) - dashboard_not_setup), len(self.bot.guilds)
            )
            dashboard_embed.add_field(
                "------------------\nDashboards Info",
                (
                    f"**Setup**: {len(self.bot.guilds) - dashboard_not_setup}\n"
                    f"**Not Setup**: {dashboard_not_setup}\n"
                    f"{healthbar}"
                ),
            )

            feed_not_setup = len(Guilds.feed_not_setup())
            healthbar = health_bar(
                (len(self.bot.guilds) - feed_not_setup), len(self.bot.guilds)
            )
            dashboard_embed.add_field(
                "------------------\nWar Feeds Info",
                (
                    f"**Setup**: {len(self.bot.guilds) - feed_not_setup}\n"
                    f"**Not Setup**: {feed_not_setup}\n"
                    f"{healthbar}"
                ),
            )

            channel = self.bot.get_channel(data[0]) or await self.bot.fetch_channel(
                data[0]
            )
            try:
                message = channel.get_partial_message(data[1])
            except Exception as e:
                print(f"bot_dashboard ", e)
            await message.edit(
                embed=dashboard_embed,
                components=[
                    Button(
                        label="Top.GG",
                        style=ButtonStyle.link,
                        url="https://top.gg/bot/1212535586972369008",
                    ),
                    Button(
                        label="App Directory",
                        style=ButtonStyle.link,
                        url="https://discord.com/application-directory/1212535586972369008",
                    ),
                ],
            ),

    @bot_dashboard.before_loop
    async def before_bot_dashboard(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(GuildManagementCog(bot))
