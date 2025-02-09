from asyncio import sleep
from datetime import datetime, timedelta, time
from disnake import (
    ButtonStyle,
    Colour,
    Embed,
    Guild,
    MessageInteraction,
)
from disnake.ext import commands, tasks
from disnake.ui import Button
from main import GalacticWideWebBot
from utils.db import BotDashboard, GWWGuild
from utils.embeds.loop_embeds import BotDashboardLoopEmbed
from utils.interactables import AppDirectoryButton, GitHubButton, KoFiButton


class GuildManagementCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.bot_dashboard.start()
        self.dashboard_checking.start()
        self.guild_checking.start()
        self.guilds_to_remove = []
        self.user_installs = 0

    def cog_unload(self):
        self.bot_dashboard.stop()
        self.dashboard_checking.stop()
        self.guild_checking.stop()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        GWWGuild.new(guild.id)
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

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        GWWGuild.delete(guild.id)
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
        bot_dashboard = BotDashboard()
        channel = self.bot.get_channel(
            bot_dashboard.channel_id
        ) or await self.bot.fetch_channel(bot_dashboard.channel_id)
        if bot_dashboard.message_id == 0:
            message = await channel.send("Placeholder message, please ignore.")
            bot_dashboard.message_id = message.id
            bot_dashboard.save_changes()
        else:
            if datetime.now().minute == 0:
                app_info = await self.bot.application_info()
                self.user_installs = app_info.approximate_user_install_count
            dashboard_embed = BotDashboardLoopEmbed(
                bot=self.bot, user_installs=self.user_installs
            )
            try:
                message = channel.get_partial_message(bot_dashboard.message_id)
            except Exception as e:
                self.bot.logger.error(
                    f"{self.qualified_name} | bot_dashboard | {e} | {channel.id}"
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

    @tasks.loop(
        time=[
            time(hour=i, minute=j, second=0)
            for i in range(24)
            for j in range(2, 62, 15)
        ]
    )
    async def dashboard_checking(self):
        now = datetime.now()
        guild = GWWGuild.get_by_id(1212722266392109088)
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
        guilds: list[GWWGuild] = GWWGuild.get_all()
        if guilds:
            for guild in guilds:
                if guild.id not in [
                    discord_guild.id for discord_guild in self.bot.guilds
                ]:
                    self.guilds_to_remove.append(guild.id)
            if self.guilds_to_remove:
                embed = Embed(
                    title="Servers in DB that don't have the bot installed",
                    colour=Colour.brand_red(),
                    description="These servers are in the PostgreSQL database but not in the `self.bot.guilds` list.",
                ).add_field(
                    "Guilds:",
                    "\n".join([str(id) for id in self.guilds_to_remove]),
                    inline=False,
                )
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
            for guild_id in self.guilds_to_remove:
                GWWGuild.delete(guild_id)
                self.bot.logger.info(
                    f"{self.qualified_name} | ban_listener | removed {guild_id} from the DB"
                )
                await inter.send(f"Deleted guilds `{guild_id}` from the DB")
            embed: Embed = inter.message.embeds[0].add_field(
                "", "# GUILDS DELETED", inline=False
            )
            await inter.message.edit(components=[], embed=embed)
            self.guilds_to_remove.clear()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(GuildManagementCog(bot))
