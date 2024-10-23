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
)
from disnake.ext import commands, tasks
from disnake.ui import Button
from main import GalacticWideWebBot
from utils.buttons import AppDirectoryButton, GitHubButton, KoFiButton
from utils.checks import wait_for_startup
from utils.db import BotDashboardRecord, GuildRecord, GuildsDB, BotDashboardDB
from utils.embeds import BotDashboardEmbed, ReactRoleDashboard


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

    @wait_for_startup()
    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        GuildsDB.insert_new_guild(guild.id)
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

    @wait_for_startup()
    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        GuildsDB.remove_from_db(guild.id)
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
        dashboard: BotDashboardRecord = BotDashboardDB.get_info()
        channel = self.bot.get_channel(
            dashboard.channel_id
        ) or await self.bot.fetch_channel(dashboard.channel_id)
        if dashboard.message_id == 0:
            message = await channel.send("Placeholder message, please ignore.")
            BotDashboardDB.set_message(message.id)
        else:
            dashboard_embed = BotDashboardEmbed(bot=self.bot)
            try:
                message = channel.get_partial_message(dashboard.message_id)
            except Exception as e:
                self.bot.logger.error(
                    f"GuildManagementCog, bot_dashboard, {e}, {channel.id}"
                )
            try:
                await message.edit(
                    embed=dashboard_embed,
                    components=[
                        AppDirectoryButton(),
                        KoFiButton(),
                        GitHubButton(),
                    ],
                ),
            except Exception as e:
                await self.bot.moderator_channel.send(
                    f"<@{self.bot.owner_id}>\n```py\n{e}\n```\n`bot_dashboard function in guild_management.py`"
                )
                self.bot.logger.error(
                    f"{self.qualified_name} | bot_dashboard | {e} | {message}"
                )

    @bot_dashboard.before_loop
    async def before_bot_dashboard(self):
        await self.bot.wait_until_ready()

    @tasks.loop(count=1)
    async def react_role_dashboard(self):
        dashboard = BotDashboardDB.get_info()
        components = [
            Button(label="Subscribe to Bot Updates", custom_id="BotUpdatesButton")
        ]
        channel = self.bot.get_channel(
            dashboard.channel_id
        ) or await self.bot.fetch_channel(dashboard.channel_id)
        if not channel:
            return self.bot.logger.error(
                f"{self.qualified_name} | react_role_dashboard | {channel = }"
            )
        embed = ReactRoleDashboard()
        if not dashboard.react_role_message_id:
            message = await channel.send(embed=embed, components=components)
            BotDashboardDB.set_react_role(message.id)
        else:
            message = channel.get_partial_message(dashboard.react_role_message_id)
            try:
                await message.edit(embed=embed, components=components)
            except NotFound:
                message = await channel.send(embed=embed, components=components)
                BotDashboardDB.set_react_role(message.id)
            except Exception as e:
                await self.bot.moderator_channel.send(f"Bot Dashboard\n```py\n{e}\n```")
                pass

    @react_role_dashboard.before_loop
    async def before_react_role(self):
        await self.bot.wait_until_ready()

    @wait_for_startup()
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

    @tasks.loop(
        time=[
            time(hour=i, minute=j, second=0)
            for i in range(24)
            for j in range(2, 62, 15)
        ]
    )
    async def dashboard_checking(self):
        now = datetime.now()
        guild: GuildRecord = GuildsDB.get_info(1212722266392109088)
        if guild:
            try:
                channel = self.bot.get_channel(
                    guild.dashboard_channel_id
                ) or await self.bot.fetch_channel(guild.dashboard_channel_id)
                message = await channel.fetch_message(guild.dashboard_message_id)
                updated_time = message.edited_at.replace(tzinfo=None) + timedelta(
                    hours=1
                )
                if updated_time < (
                    now - timedelta(minutes=16)
                ) and self.bot.startup_time < (now - timedelta(minutes=16)):
                    await self.bot.moderator_channel.send(
                        f"<@{self.bot.owner_id}> {message.jump_url} was last edited <t:{int(message.edited_at.timestamp())}:R> :warning:"
                    )
                    await sleep(15 * 60)
            except Exception as e:
                self.bot.logger.error(
                    f"{self.qualified_name} | dashboard_checking | {e}"
                )

    @dashboard_checking.before_loop
    async def before_dashboard_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(time=[time(hour=0, minute=0, second=0, microsecond=0)])
    async def guild_checking(self):
        guilds_in_db = GuildsDB.get_all_guilds()
        if guilds_in_db:
            for guild in guilds_in_db:
                if guild.guild_id not in [
                    discord_guild.id for discord_guild in self.bot.guilds
                ]:
                    self.guilds_to_remove.append(str(guild.guild_id))
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

    @wait_for_startup()
    @commands.Cog.listener("on_button_click")
    async def ban_listener(self, inter: MessageInteraction):
        if inter.component.custom_id == "guild_remove":
            for guild in self.guilds_to_remove:
                GuildsDB.remove_from_db(int(guild))
                self.bot.logger.error(
                    f"{self.qualified_name} | ban_listener | removed {guild} from the DB"
                )
                await inter.send(f"Deleted guilds `{guild}` from the DB")
            embed: Embed = inter.message.embeds[0].add_field(
                "", "# GUILDS DELETED", inline=False
            )
            await inter.message.edit(components=[], embed=embed)
            self.guilds_to_remove.clear()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(GuildManagementCog(bot))
