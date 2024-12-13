from disnake import AppCmdInter
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GuildRecord, GuildsDB
from utils.embeds import WarfrontEmbed


class WarfrontCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Returns information on a specific War front",
        dm_permission=False,
    )
    async def warfront(
        self,
        inter: AppCmdInter,
        faction=commands.Param(
            choices=["Automaton", "Terminids", "Illuminate"],
            description="The faction to focus on",
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="If you want the response to be seen by others in the server.",
        ),
    ):
        ephemeral = public != "Yes"
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{faction = }> <{public = }>"
        )
        await inter.response.defer(ephemeral=ephemeral)
        guild_in_db: GuildRecord = GuildsDB.get_info(inter.guild_id)
        if not guild_in_db:
            guild_in_db = GuildsDB.insert_new_guild(inter.guild.id)
        guild_language = self.bot.json_dict["languages"][guild_in_db.language]
        embed = WarfrontEmbed(
            faction, self.bot.data, guild_language, self.bot.json_dict["planets"]
        )
        await inter.send(embed=embed)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(WarfrontCog(bot))
