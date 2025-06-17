from asyncio import sleep
from data.lists import locales_dict
from datetime import datetime, timedelta, time
from disnake import (
    ButtonStyle,
    Embed,
    Guild,
    MessageInteraction,
)
from disnake.ext import commands, tasks
from disnake.ui import Button
from main import GalacticWideWebBot
from utils.dbv2 import BotDashboard, Feature, GWWGuilds, GWWGuild
from utils.embeds.loop_embeds import (
    BotDashboardLoopEmbed,
    GuildJoinListenerEmbed,
    GuildLeaveListenerEmbed,
    GuildsNotInDBLoopEmbed,
)
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

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        guild_in_db = GWWGuilds.get_specific_guild(id=guild.id)
        if guild_in_db:
            await self.bot.moderator_channel.send(
                f"Guild **{guild.name}** just added the bot but was already in the DB"
            )
        else:
            language = locales_dict.get(guild.preferred_locale, "en")
            GWWGuilds.add(guild_id=guild.id, language=language, feature_keys=[])
        embed = GuildJoinListenerEmbed(guild=guild)
        await self.bot.moderator_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        guild_in_db: GWWGuild | None = GWWGuilds.get_specific_guild(id=guild.id)
        if not guild_in_db:
            await self.bot.moderator_channel.send(
                f"Guild **{guild.name}** just removed the bot but was not in the DB"
            )
        else:
            guild_in_db.delete()
            embed = GuildLeaveListenerEmbed(guild=guild)
            await self.bot.moderator_channel.send(embed=embed)

    @tasks.loop(minutes=1)
    async def bot_dashboard(self):
        bot_dashboard = self.bot_dashboard_db
        channel = self.bot.get_channel(
            bot_dashboard.channel_id
        ) or await self.bot.fetch_channel(bot_dashboard.channel_id)
        if not channel:
            await self.bot.moderator_channel.send(
                f"@stonemercy\nbot_dashboard channel returned {channel}"
            )
        else:
            now = datetime.now()
            if now.minute == 0 or now - timedelta(minutes=2) < self.bot.startup_time:
                app_info = await self.bot.application_info()
                self.user_installs = app_info.approximate_user_install_count
            dashboard_embed = BotDashboardLoopEmbed(
                bot=self.bot, user_installs=self.user_installs
            )
            try:
                message = channel.get_partial_message(bot_dashboard.message_id)
            except Exception as e:
                self.bot.logger.error(
                    msg=f"{self.qualified_name} | bot_dashboard | {e} | {channel.id}"
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
                    content=f"<@{self.bot.owner.id}>\n```py\n{e}\n```\n`bot_dashboard function in guild_management.py`"
                )
                self.bot.logger.error(
                    msg=f"{self.qualified_name} | bot_dashboard | {e} | {message}"
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
                embed = GuildsNotInDBLoopEmbed(guilds_to_remove=self.guilds_to_remove)
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
