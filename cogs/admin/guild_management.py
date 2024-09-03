from asyncio import sleep
from datetime import datetime, timedelta, time
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
from main import GalacticWideWebBot
from math import inf
from os import getpid
from psutil import Process, cpu_percent
from utils.checks import wait_for_startup
from utils.db import Guilds, BotDashboard
from utils.embeds import BotDashboardEmbed, ReactRoleDashboard
from utils.functions import health_bar


class GuildManagementCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.bot_dashboard.start()
        self.react_role_dashboard.start()
        self.dashboard_checking.start()
        self.guild_checking.start()
        self.guilds_to_remove = []

    def cog_unload(self):
        self.bot_dashboard.stop()
        self.react_role_dashboard.stop()
        self.dashboard_checking.stop()
        self.guild_checking.stop()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        Guilds.insert_new_guild(guild.id)
        embed = (
            Embed(title="New guild joined!", colour=Colour.brand_green())
            .add_field("Name", guild.name, inline=False)
            .add_field("Users", guild.member_count, inline=False)
            .add_field(
                "Big guild?", {True: "Yes", False: "No"}[guild.large], inline=False
            )
            .add_field(
                "Created",
                f"<t:{int(guild.created_at.timestamp())}:R>",
                inline=False,
            )
            .add_field("Owner", f"<@{guild.owner_id}>", inline=False)
            .set_thumbnail(guild.icon.url if guild.icon else None)
            .set_image(guild.banner.url if guild.banner else None)
        )
        await self.bot.moderator_channel.send(embed=embed)
        old_activity = self.bot.activity
        await self.bot.change_presence(
            activity=Activity(name="for alien sympathisers", type=ActivityType.watching)
        )
        await sleep(10.0)
        await self.bot.change_presence(activity=old_activity)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        Guilds.remove_from_db(guild.id)
        embed = (
            Embed(title="Guild left", colour=Colour.brand_red())
            .add_field("Name", guild.name, inline=False)
            .add_field("Users", guild.member_count, inline=False)
            .add_field(
                "Big guild?", {True: "Yes", False: "No"}[guild.large], inline=False
            )
            .add_field(
                "Created", f"<t:{int(guild.created_at.timestamp())}:R>", inline=False
            )
            .add_field("Owner", f"<@{guild.owner_id}>", inline=False)
            .set_thumbnail(guild.icon.url if guild.icon else None)
            .set_image(guild.banner.url if guild.banner else None)
        )
        await self.bot.moderator_channel.send(embed=embed)

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
                        commands += f"</{global_command.name} {option.name}:{global_command.id}> "
                if global_command.name != "weapons":
                    commands += f"</{global_command.name}:{global_command.id}> "
            member_count = sum([guild.member_count for guild in self.bot.guilds])
            dashboard_embed.add_field(
                "The GWW has",
                f"{len(self.bot.global_slash_commands)} commands available:\n{commands}",
            ).add_field(
                "Currently in", f"{len(self.bot.guilds)} discord servers"
            ).add_field(
                "Members of Democracy", f"{member_count:,}"
            )
            memory_used = Process(getpid()).memory_info().rss / 1024**2
            latency = 9999.999 if self.bot.latency == float(inf) else self.bot.latency
            dashboard_embed.add_field(
                "Hardware Info",
                (
                    f"**CPU**: {cpu_percent()}%\n"
                    f"**RAM**: {memory_used:.2f}MB\n"
                    f"**Last restart**: <t:{int(self.bot.startup_time.timestamp())}:R>\n"
                    f"**Latency**: {int(latency * 1000)}ms"
                ),
                inline=True,
            )
            dashboard_embed.add_field(
                "Update Timers",
                (
                    f"This Dashboard: <t:{int(self.bot_dashboard.next_iteration.timestamp())}:R>\n"
                    f"All Dashboards: <t:{int(self.bot.get_cog('DashboardCog').dashboard.next_iteration.timestamp())}:R>\n"
                    f"All Maps: <t:{int(self.bot.get_cog('MapCog').map_poster.next_iteration.timestamp())}:R>\n"
                ),
            )
            dashboard_embed.add_field("", "", inline=False)
            stats_dict = {
                "Dashboard Setup": len(Guilds.dashboard_not_setup()),
                "Announcements Setup": len(Guilds.feed_not_setup()),
                None: None,
                "Maps Setup": len(Guilds.maps_not_setup()),
                "Patch Notes Enabled": len(Guilds.patch_notes_not_setup()),
            }
            for title, amount in stats_dict.items():
                if not title:
                    dashboard_embed.add_field("", "", inline=False)
                    continue
                healthbar = health_bar(
                    (len(self.bot.guilds) - amount) / len(self.bot.guilds),
                    "Humans",
                )
                dashboard_embed.add_field(
                    title,
                    (
                        f"**Setup**: {len(self.bot.guilds) - amount}\n"
                        f"**Not Setup**: {amount}\n"
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
                self.bot.logger.error(
                    f"GuildManagementCog, bot_dashboard, {e}, {channel.id}"
                )
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
                await self.bot.moderator_channel.send(
                    f"<@{self.bot.owner_id}>\n```py\n{e}\n```bot_dashboard function in guild_management.py"
                )
                self.bot.logger.error(
                    f"GuildManagementCog, bot_dashboard, {e}, {message.id}"
                )

    @bot_dashboard.before_loop
    async def before_bot_dashboard(self):
        await self.bot.wait_until_ready()

    @tasks.loop(count=1)
    async def react_role_dashboard(self):
        data = BotDashboard.get_info()
        components = [
            Button(label="Subscribe to Bot Updates", custom_id="BotUpdatesButton")
        ]
        channel = self.bot.get_channel(data[0]) or await self.bot.fetch_channel(data[0])
        if not channel:
            self.bot.logger.error(
                "GuildManagementCog, react_role_dashboard, channel == None"
            )
            return
        if data[2] == None:
            embed = ReactRoleDashboard()
            message = await channel.send(embed=embed, components=components)
            BotDashboard.set_react_role(message.id)
        else:
            message = channel.get_partial_message(data[2])
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

    times = []
    for i in range(24):
        times.append(time(hour=i, minute=2, second=0))
        times.append(time(hour=i, minute=17, second=0))
        times.append(time(hour=i, minute=32, second=0))
        times.append(time(hour=i, minute=47, second=0))

    @wait_for_startup()
    @tasks.loop(time=times)
    async def dashboard_checking(self):
        now = datetime.now()
        guild = Guilds.get_info(1212722266392109088)
        if guild:
            try:
                channel = self.bot.get_channel(
                    guild[1]
                ) or await self.bot.fetch_channel(guild[1])
                message = await channel.fetch_message(guild[2])
                updated_time = message.edited_at.replace(tzinfo=None) + timedelta(
                    hours=1
                )
                if updated_time < (
                    now - timedelta(minutes=16)
                ) and self.bot.startup_time < (now - timedelta(minutes=16)):
                    await self.bot.moderator_channel.send(
                        f"<@164862382185644032> {message.jump_url} was last edited <t:{int(message.edited_at.timestamp())}:R> :warning:"
                    )
                    await sleep(15 * 60)
            except Exception as e:
                self.bot.logger.error(f"GuildManagementCog, dashboard_checking, {e}")

    @dashboard_checking.before_loop
    async def before_dashboard_check(self):
        await self.bot.wait_until_ready()

    @wait_for_startup()
    @tasks.loop(time=[time(hour=0, minute=0, second=0, microsecond=0)])
    async def guild_checking(self):
        guilds_in_db = Guilds.get_all_guilds()
        if guilds_in_db:
            for guild_in_db in guilds_in_db:
                if guild_in_db[0] not in [guild.id for guild in self.bot.guilds]:
                    self.guilds_to_remove.append(str(guild_in_db[0]))
            if self.guilds_to_remove != []:
                embed = Embed(
                    title="Servers in DB that don't have the bot installed",
                    colour=Colour.brand_red(),
                    description="These servers are in the PostgreSQL database but not in the `self.bot.guilds` list.",
                ).add_field("Guilds:", "\n".join(self.guilds_to_remove), inline=False)
                await self.bot.moderator_channel.send(
                    embed=embed,
                    components=[
                        Button(
                            label="Remove",
                            style=ButtonStyle.danger,
                            custom_id="guild_remove",
                        )
                    ],
                )

    @guild_checking.before_loop
    async def before_guild_check(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener("on_button_click")
    async def ban_listener(self, inter: MessageInteraction):
        if inter.component.custom_id == "guild_remove":
            for guild in self.guilds_to_remove:
                Guilds.remove_from_db(guild)
                self.bot.logger.error(
                    f"GuildManagementCog, ban_listener, removed {guild} from the DB"
                )
                await inter.send(f"Deleted guilds `{guild}` from the DB")
            embed: Embed = inter.message.embeds[0].add_field(
                "GUILDS DELETED", "You did this", inline=False
            )
            await inter.message.edit(components=[], embed=embed)
            self.guilds_to_remove.clear()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(GuildManagementCog(bot))
