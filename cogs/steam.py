from disnake import AppCmdInter, MessageInteraction
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GuildRecord, GuildsDB
from utils.embeds import SteamEmbed
from utils.selectmenus import SteamStringSelect


class SteamCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(description="Get previous Steam posts", dm_permission=False)
    async def steam(
        self,
        inter: AppCmdInter,
    ):
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name}"
        )
        await inter.response.defer(ephemeral=True)
        guild_in_db: GuildRecord = GuildsDB.get_info(inter.guild_id)
        if not guild_in_db:
            guild_in_db = GuildsDB.insert_new_guild(inter.guild.id)
        embed = SteamEmbed(
            steam=self.bot.data.steam[0],
            language=self.bot.json_dict["languages"][guild_in_db.language],
        )
        components = [SteamStringSelect(self.bot)]
        await inter.send(embed=embed, components=components)

    @commands.Cog.listener("on_dropdown")
    async def steam_notes_listener(self, inter: MessageInteraction):
        if inter.component.custom_id != "steam":
            return
        guild_in_db: GuildRecord = GuildsDB.get_info(inter.guild_id)
        steam_data = [
            steam for steam in self.bot.data.steam if steam.title == inter.values[0]
        ][0]
        embed = SteamEmbed(
            steam_data, self.bot.json_dict["languages"][guild_in_db.language]
        )
        await inter.response.edit_message(embed=embed)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(SteamCog(bot))
