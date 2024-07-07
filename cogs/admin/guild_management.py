from asyncio import sleep
from datetime import datetime, timedelta
from disnake import (
    Activity,
    ActivityType,
    ButtonStyle,
    Colour,
    Embed,
    Guild,
    MessageInteraction,
    NotFound,
    OptionType,
)
from disnake.ext import commands, tasks
from disnake.ui import Button
from helpers.db import Guilds, BotDashboard
from helpers.embeds import BotDashboardEmbed, ReactRoleDashboard
from helpers.functions import health_bar
from logging import getLogger
from math import inf
from os import getenv, getpid
from psutil import Process, cpu_percent

logger = getLogger("disnake")


class GuildManagementCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot_dashboard.start()
        self.react_role_dashboard.start()
        self.dashboard_checking.start()
        self.startup_time = datetime.now()

    def cog_unload(self):
        self.bot_dashboard.stop()
        self.react_role_dashboard.stop()
        self.dashboard_checking.stop()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        channel_id = int(getenv("MODERATION_CHANNEL"))
        channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
            channel_id
        )
        Guilds.insert_new_guild(guild.id)
        embed = Embed(title="New guild joined!", colour=Colour.brand_green())
        embed.add_field("Name", guild.name, inline=False).add_field(
            "Users", guild.member_count, inline=False
        ).add_field(
            "Big guild?", {True: "Yes", False: "No"}[guild.large], inline=False
        ).add_field(
            "Created", f"<t:{int(guild.created_at.timestamp())}:R>", inline=False
        ).add_field(
            "Owner", f"<@{guild.owner_id}>", inline=False
        )
        embed.set_thumbnail(guild.icon.url if guild.icon != None else None).set_image(
            guild.banner.url if guild.banner != None else None
        )
        await channel.send(embed=embed)
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
        embed = Embed(title="Guild left...", colour=Colour.brand_red())
        embed.add_field("Name", guild.name, inline=False).add_field(
            "Users", guild.member_count, inline=False
        ).add_field(
            "Big guild?", {True: "Yes", False: "No"}[guild.large], inline=False
        ).add_field(
            "Created", f"<t:{int(guild.created_at.timestamp())}:R>", inline=False
        ).add_field(
            "Owner", f"<@{guild.owner_id}>", inline=False
        )
        embed.set_thumbnail(guild.icon.url if guild.icon != None else None).set_image(
            guild.banner.url if guild.banner != None else None
        )
        await channel.send(embed=embed)

    @tasks.loop(minutes=1)
    async def bot_dashboard(self):
        now = datetime.now()
        data = BotDashboard.get_info()
        if data[1] == 0:
            channel = self.bot.get_channel(data[0]) or await self.bot.fetch_channel(
                data[0]
            )
            message = await channel.send("Placeholder message, please ignore.")
            BotDashboard.set_message(message.id)
        else:
            dashboard_embed = BotDashboardEmbed(now)
            commands = ""
            for global_command in self.bot.global_slash_commands:
                for option in global_command.options:
                    if option.type == OptionType.sub_command:
                        commands += f"</{global_command.name} {option.name}:{global_command.id}>\n"
                if global_command.name != "weapons":
                    commands += f"</{global_command.name}:{global_command.id}>\n"
            dashboard_embed.add_field(
                "The GWW has",
                f"{len(self.bot.global_slash_commands)} commands available:\n{commands}",
            ).add_field("Currently in", f"{len(self.bot.guilds)} discord servers")
            member_count = 0
            for i in self.bot.guilds:
                member_count += i.member_count
            dashboard_embed.add_field("Members of Democracy", f"{member_count:,}")

            pid = getpid()
            process = Process(pid)
            memory_used = process.memory_info().rss / 1024**2
            latency = 9999.999 if self.bot.latency == float(inf) else self.bot.latency
            dashboard_embed.add_field(
                "------------------\nHardware Info",
                (
                    f"**CPU**: {cpu_percent()}%\n"
                    f"**RAM**: {memory_used:.2f}MB\n"
                    f"**Last restart**: <t:{int(self.startup_time.timestamp())}:R>\n"
                    f"**Latency**: {int(latency * 1000)}ms"
                ),
                inline=False,
            )
            dashboard_not_setup = len(Guilds.dashboard_not_setup())
            healthbar = health_bar(
                (len(self.bot.guilds) - dashboard_not_setup),
                len(self.bot.guilds),
                "Humans",
            )
            dashboard_embed.add_field(
                "------------------\nDashboards Setup",
                (
                    f"**Setup**: {len(self.bot.guilds) - dashboard_not_setup}\n"
                    f"**Not Setup**: {dashboard_not_setup}\n"
                    f"{healthbar}"
                ),
            )
            feed_not_setup = len(Guilds.feed_not_setup())
            healthbar = health_bar(
                (len(self.bot.guilds) - feed_not_setup),
                len(self.bot.guilds),
                "Humans",
            )
            dashboard_embed.add_field(
                "------------------\nAnnouncements Setup",
                (
                    f"**Setup**: {len(self.bot.guilds) - feed_not_setup}\n"
                    f"**Not Setup**: {feed_not_setup}\n"
                    f"{healthbar}"
                ),
            )
            dashboard_embed.add_field("", "", inline=False)
            maps_not_setup = len(Guilds.maps_not_setup())
            healthbar = health_bar(
                (len(self.bot.guilds) - maps_not_setup),
                len(self.bot.guilds),
                "Humans",
            )
            dashboard_embed.add_field(
                "------------------\nMaps Setup",
                (
                    f"**Setup**: {len(self.bot.guilds) - maps_not_setup}\n"
                    f"**Not Setup**: {maps_not_setup}\n"
                    f"{healthbar}"
                ),
            )
            patch_notes_not_setup = len(Guilds.patch_notes_not_setup())
            healthbar = health_bar(
                (len(self.bot.guilds) - patch_notes_not_setup),
                len(self.bot.guilds),
                "Humans",
            )
            dashboard_embed.add_field(
                "------------------\nPatch Notes Enabled",
                (
                    f"**Setup**: {len(self.bot.guilds) - patch_notes_not_setup}\n"
                    f"**Not Setup**: {patch_notes_not_setup}\n"
                    f"{healthbar}"
                ),
            )
            dashboard_embed.add_field(
                "Credits",
                (
                    "https://helldivers.fandom.com/wiki/Helldivers_Wiki - Most of my enemy information is from them, as well as a lot of the enemy images.\n\n"
                    "https://helldivers.news/ - Planet images are from them, their website is also amazing.\n\n"
                    "https://github.com/helldivers-2/ - The people over here are kind and helpful, great work too!\n\n"
                    "and **You**\n"
                ),
                inline=False,
            )

            channel = self.bot.get_channel(data[0]) or await self.bot.fetch_channel(
                data[0]
            )
            try:
                message = channel.get_partial_message(data[1])
            except Exception as e:
                logger.error(f"GuildManagementCog, bot_dashboard, {e}, {channel.id}")
            try:
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
                        Button(
                            label="Ko-Fi",
                            style=ButtonStyle.link,
                            url="https://ko-fi.com/galacticwideweb",
                        ),
                        Button(
                            label="GitHub",
                            style=ButtonStyle.link,
                            url="https://github.com/Stonemercy/Galactic-Wide-Web",
                        ),
                    ],
                ),
            except Exception as e:
                logger.error(f"GuildManagementCog, bot_dashboard, {e}, {message.id}")
                pass

    @bot_dashboard.before_loop
    async def before_bot_dashboard(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=1)
    async def react_role_dashboard(self):
        embed = ReactRoleDashboard()
        data = BotDashboard.get_info()
        channel_id = data[0]
        message_id = data[2]
        components = [
            Button(label="Subscribe to Bot Updates", custom_id="BotUpdatesButton")
        ]
        channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
            channel_id
        )
        if channel == None:
            logger.error("GuildManagementCog, react_role_dashboard, channel == None")
            return
        if message_id == None:
            message = await channel.send(embed=embed, components=components)
            BotDashboard.set_react_role(message.id)
        else:
            message = channel.get_partial_message(message_id)
            try:
                await message.edit(embed=embed, components=components)
            except NotFound:
                message = await channel.send(embed=embed, components=components)
                BotDashboard.set_react_role(message.id)
            except:
                pass

    @react_role_dashboard.before_loop
    async def before_react_role(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener("on_button_click")
    async def react_role(self, inter: MessageInteraction):
        if inter.component.custom_id == "BotUpdatesButton":
            role = inter.guild.get_role(1228077919952437268)
            if role in inter.author.roles:
                await inter.author.remove_roles(role)
                return await inter.send(
                    "Removed the Bot Update role from you",
                    ephemeral=True,
                    delete_after=10,
                )
            else:
                await inter.author.add_roles(role)
                return await inter.send(
                    "Gave you the Bot Update role",
                    ephemeral=True,
                    delete_after=10,
                )

    @tasks.loop(minutes=1)
    async def dashboard_checking(self):
        guild = Guilds.get_info(1212722266392109088)
        if guild != None:
            channel = self.bot.get_channel(guild[1]) or await self.bot.fetch_channel(
                guild[1]
            )
            message = await channel.fetch_message(guild[2])
            if message.edited_at.replace(
                tzinfo=None, hour=message.edited_at.hour + 1
            ) < (datetime.now() - timedelta(minutes=16)):
                error_channel = self.bot.get_channel(
                    1212735927223590974
                ) or await self.bot.fetch_channel(1212735927223590974)
                await error_channel.send(
                    f"<@164862382185644032> {message.jump_url} was last edited <t:{int(message.edited_at.timestamp())}:R> :warning:"
                )
                await sleep(15 * 60)

    @dashboard_checking.before_loop
    async def before_dashboard_check(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(GuildManagementCog(bot))
