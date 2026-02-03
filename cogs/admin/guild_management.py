from datetime import time
from typing import TYPE_CHECKING
from disnake import ButtonStyle, Colour, Embed, Guild, MessageInteraction, ui
from disnake.ext import commands, tasks
from utils.bot import GalacticWideWebBot
from utils.containers import GuildContainer
from utils.dataclasses import Languages
from utils.dbv2 import GWWGuilds

if TYPE_CHECKING:
    from utils.dbv2 import GWWGuild


class GuildManagementCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot
        self.guilds_to_remove = []
        self.user_installs = 0

    def cog_load(self) -> None:
        if not self.guild_checking.is_running():
            self.guild_checking.start()
            self.bot.loops.append(self.guild_checking)

    def cog_unload(self) -> None:
        if self.guild_checking.is_running():
            self.guild_checking.cancel()
        if self.guild_checking in self.bot.loops:
            self.bot.loops.remove(self.guild_checking)

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

    @guild_checking.error
    async def guild_checking_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "guild_checking loop")

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
