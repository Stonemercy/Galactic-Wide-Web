from datetime import datetime, time, timedelta
from typing import TYPE_CHECKING
from disnake import ButtonStyle, Colour, Embed, Guild, MessageInteraction, ui
from disnake.ext import commands, tasks
from utils.bot import GalacticWideWebBot
from utils.containers import GuildContainer
from utils.dataclasses import Config, Languages
from utils.dbv2 import GWWGuilds

if TYPE_CHECKING:
    from utils.dbv2 import Feature, GWWGuild


class GuildManagementCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot
        self.loops = (self.dashboard_checking, self.guild_checking)
        self.guilds_to_remove = []
        self.user_installs = 0

    def cog_load(self) -> None:
        for loop in self.loops:
            if not loop.is_running():
                loop.start()
                self.bot.loops.append(loop)

    def cog_unload(self) -> None:
        for loop in self.loops:
            if loop.is_running():
                loop.stop()
            if loop in self.bot.loops:
                self.bot.loops.remove(loop)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild) -> None:
        guild_in_db: GWWGuild | None = GWWGuilds.get_specific_guild(id=guild.id)
        if guild_in_db:
            await self.bot.channels.moderator_channel.send(
                f"Guild **{guild.name}** just added the bot but was already in the DB"
            )
        else:
            language = Languages.get_from_locale(guild.preferred_locale)
            guild_in_db = GWWGuilds.add(
                guild_id=guild.id, language=language.short_code, feature_keys=[]
            )
        container = GuildContainer(guild=guild, db_guild=guild_in_db, joined=True)
        await self.bot.channels.moderator_channel.send(components=container)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild) -> None:
        guild_in_db: GWWGuild | None = GWWGuilds.get_specific_guild(id=guild.id)
        if not guild_in_db:
            await self.bot.channels.moderator_channel.send(
                f"Guild **{guild.name}** just removed the bot but was not in the DB"
            )
        else:
            container = GuildContainer(guild=guild, db_guild=guild_in_db, removed=True)
            guild_in_db.delete()
            await self.bot.channels.moderator_channel.send(components=container)
        for lst in self.bot.interface_handler.lists.values():
            for c in (c for c in lst.copy() if c.guild.id == guild.id):
                lst.remove(c)

    @tasks.loop(
        time=[
            time(hour=i, minute=j, second=0)
            for i in range(24)
            for j in range(2, 62, 15)
        ]
    )
    async def dashboard_checking(self) -> None:
        now = datetime.now()
        guild: GWWGuild | None = GWWGuilds.get_specific_guild(
            id=Config.SUPPORT_SERVER_ID
        )
        if guild:
            try:
                dashboard_list: list[Feature] = [
                    f for f in guild.features if f.name == "dashboards"
                ]
                if dashboard_list == []:
                    self.bot.logger.info(
                        f"{self.qualified_name} | dashboard_checking | No dashboard feature found for {guild.guild_id} (support server)"
                    )
                    return
                else:
                    dashboard: Feature = dashboard_list[0]
                    channel = self.bot.get_channel(
                        dashboard.channel_id
                    ) or await self.bot.fetch_channel(dashboard.channel_id)
                    message = await channel.fetch_message(dashboard.message_id)
                    cutoff = now - timedelta(minutes=17)
                    if (
                        message.edited_at.replace(tzinfo=None) < cutoff
                        and self.bot.startup_time < cutoff
                    ):
                        await self.bot.channels.moderator_channel.send(
                            content=f"<@{self.bot.owner.id}> {message.jump_url} was last edited <t:{int(message.edited_at.timestamp())}:R> :warning:"
                        )
            except Exception as e:
                self.bot.logger.error(
                    f"{self.qualified_name} | dashboard_checking | {e}"
                )

    @dashboard_checking.before_loop
    async def before_dashboard_check(self) -> None:
        await self.bot.wait_until_ready()

    @tasks.loop(time=[time(hour=23, minute=0)])
    async def guild_checking(self) -> None:
        dbguilds = GWWGuilds(fetch_all=True)
        if dbguilds:
            disc_guild_ids = [dguild.id for dguild in self.bot.guilds]
            for dbguild in dbguilds:
                if dbguild.guild_id not in disc_guild_ids:
                    self.guilds_to_remove.append(dbguild.guild_id)
            if self.guilds_to_remove != []:
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
                await self.bot.channels.moderator_channel.send(
                    embed=embed,
                    components=[
                        ui.Button(
                            label="Remove",
                            style=ButtonStyle.danger,
                            custom_id="guild_remove",
                        )
                    ],
                )
        else:
            await self.bot.channels.moderator_channel.send(
                f":alert: {self.bot.owner.mention} :alert:\nDB_GUILDS in `guild_checking` was empty"
            )

    @guild_checking.before_loop
    async def before_guild_check(self) -> None:
        await self.bot.wait_until_ready()

    @commands.Cog.listener("on_button_click")
    async def ban_listener(self, inter: MessageInteraction) -> None:
        if inter.component.custom_id == "guild_remove":
            gww_guilds_to_remove: list[GWWGuild] = [
                GWWGuilds.get_specific_guild(id=guild_id)
                for guild_id in self.guilds_to_remove
            ]
            for guild in gww_guilds_to_remove:
                guild.delete()
                self.bot.logger.info(
                    f"{self.qualified_name} | ban_listener | removed {guild.guild_id} from the DB"
                )
                await inter.send(
                    content=f"Deleted guild `{guild.guild_id}` from the DB"
                )
            embed: Embed = inter.message.embeds[0].add_field(
                name="", value="# GUILDS DELETED FROM DB", inline=False
            )
            await inter.message.edit(components=None, embed=embed)
            self.guilds_to_remove.clear()


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(GuildManagementCog(bot))
