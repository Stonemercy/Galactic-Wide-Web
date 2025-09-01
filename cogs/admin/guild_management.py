from asyncio import sleep
from datetime import datetime, time, timedelta
from disnake import (
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
from utils.dataclasses import Languages
from utils.dbv2 import BotDashboard, Feature, GWWGuilds, GWWGuild
from utils.embeds import BotDashboardEmbed, GuildEmbed
from utils.interactables import AppDirectoryButton, GitHubButton, KoFiButton


class GuildManagementCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.loops = (self.bot_dashboard, self.dashboard_checking, self.guild_checking)
        for loop in self.loops:
            if not loop.is_running():
                loop.start()
                self.bot.loops.append(loop)
        self.guilds_to_remove = []
        self.user_installs = 0
        self.bot_dashboard_db = BotDashboard()

    def cog_unload(self):
        for loop in self.loops:
            if loop.is_running():
                loop.stop()
                self.bot.loops.remove(loop)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        guild_in_db = GWWGuilds.get_specific_guild(id=guild.id)
        if guild_in_db:
            await self.bot.moderator_channel.send(
                f"Guild **{guild.name}** just added the bot but was already in the DB"
            )
        else:
            language = Languages.get_from_locale(guild.preferred_locale)
            guild_in_db = GWWGuilds.add(
                guild_id=guild.id, language=language.short_code, feature_keys=[]
            )
        embed = GuildEmbed(guild=guild, db_guild=guild_in_db, joined=True)
        await self.bot.moderator_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        guild_in_db: GWWGuild | None = GWWGuilds.get_specific_guild(id=guild.id)
        if not guild_in_db:
            await self.bot.moderator_channel.send(
                f"Guild **{guild.name}** just removed the bot but was not in the DB"
            )
        else:
            embed = GuildEmbed(guild=guild, db_guild=guild_in_db, removed=True)
            guild_in_db.delete()
            await self.bot.moderator_channel.send(embed=embed)

    @tasks.loop(minutes=1)
    async def bot_dashboard(self):
        bot_dashboard = self.bot_dashboard_db
        if not self.bot.bot_dashboard_channel:
            self.bot.bot_dashboard_channel = self.bot.get_channel(
                bot_dashboard.channel_id
            ) or await self.bot.fetch_channel(bot_dashboard.channel_id)
        if not self.bot.bot_dashboard_message:
            try:
                self.bot.bot_dashboard_message = (
                    await self.bot.bot_dashboard_channel.fetch_message(
                        bot_dashboard.message_id
                    )
                )
            except NotFound:
                self.bot.bot_dashboard_message = (
                    await self.bot.bot_dashboard_channel.send(
                        "Placeholder, please ignore."
                    )
                )
                bot_dashboard.message_id = self.bot.bot_dashboard_message.id
                bot_dashboard.save_changes()
        now = datetime.now()
        if now.minute == 0 or now - timedelta(minutes=2) < self.bot.startup_time:
            app_info = await self.bot.application_info()
            self.user_installs = app_info.approximate_user_install_count
        dashboard_embed = BotDashboardEmbed(
            bot=self.bot, user_installs=self.user_installs
        )
        try:
            await self.bot.bot_dashboard_message.edit(
                content="",
                embed=dashboard_embed,
                components=[
                    AppDirectoryButton(),
                    KoFiButton(),
                    GitHubButton(),
                ],
            ),
        except Exception as e:
            await self.bot.moderator_channel.send(
                content=f"<@{self.bot.owner.id}>\n```py\n{e}\n```\n`bot_dashboard function in guild_management.py`"
            )
            self.bot.logger.error(
                msg=f"{self.qualified_name} | bot_dashboard | {e} | {self.bot.bot_dashboard_message}"
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
        guild: GWWGuild | None = GWWGuilds.get_specific_guild(id=1212722266392109088)
        if guild:
            try:
                dashboard: list[Feature] = [
                    f for f in guild.features if f.name == "dashboards"
                ]
                if not dashboard:
                    self.bot.logger.info(
                        msg=f"{self.qualified_name} | dashboard_checking | No dashboard feature found for {guild.guild_id}"
                    )
                    return
                else:
                    dashboard: Feature = dashboard[0]
                    channel = self.bot.get_channel(
                        dashboard.channel_id
                    ) or await self.bot.fetch_channel(dashboard.channel_id)
                    message = await channel.fetch_message(dashboard.message_id)
                    updated_time = message.edited_at.replace(tzinfo=None) + timedelta(
                        hours=1
                    )
                    if updated_time < (
                        now - timedelta(minutes=16)
                    ) and self.bot.startup_time < (now - timedelta(minutes=16)):
                        await self.bot.moderator_channel.send(
                            content=f"<@{self.bot.owner.id}> {message.jump_url} was last edited <t:{int(message.edited_at.timestamp())}:R> :warning:"
                        )
                        await sleep(delay=15 * 60)
            except Exception as e:
                self.bot.logger.error(
                    msg=f"{self.qualified_name} | dashboard_checking | {e}"
                )

    @dashboard_checking.before_loop
    async def before_dashboard_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(time=[time(hour=23, minute=0, second=0, microsecond=0)])
    async def guild_checking(self):
        guilds = GWWGuilds(fetch_all=True)
        if guilds:
            dguild_ids = [dguild.id for dguild in self.bot.guilds]
            for guild in guilds:
                if guild.guild_id not in dguild_ids:
                    self.guilds_to_remove.append(guild.guild_id)
            if self.guilds_to_remove:
                embed = Embed(
                    title="Guilds in DB that don't have the bot installed",
                    colour=Colour.brand_red(),
                    description="These servers are in the database but not in the `self.bot.guilds` list.",
                ).add_field(
                    name="Guilds:",
                    value="\n".join(
                        [str(guild_id) for guild_id in self.guilds_to_remove]
                    ),
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
            gww_guilds_to_remove: list[GWWGuild] = [
                GWWGuilds.get_specific_guild(id=guild_id)
                for guild_id in self.guilds_to_remove
            ]
            for guild in gww_guilds_to_remove:
                guild.delete()
                self.bot.logger.info(
                    msg=f"{self.qualified_name} | ban_listener | removed {guild.guild_id} from the DB"
                )
                await inter.send(
                    content=f"Deleted guild `{guild.guild_id}` from the DB"
                )
            embed: Embed = inter.message.embeds[0].add_field(
                name="", value="# GUILDS DELETED", inline=False
            )
            await inter.message.edit(components=None, embed=embed)
            self.guilds_to_remove.clear()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(cog=GuildManagementCog(bot))
