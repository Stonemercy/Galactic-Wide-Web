from disnake import AppCmdInter, InteractionContextTypes, ApplicationInstallTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GWWGuild
from utils.embeds import WarfrontEmbed


class WarfrontCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Returns information on a specific War front",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
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
        if inter.guild:
            guild = GWWGuild.get_by_id(inter.guild_id)
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        embed = WarfrontEmbed(
            faction, self.bot.data, guild_language, self.bot.json_dict["planets"]
        )
        await inter.send(embed=embed)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(WarfrontCog(bot))
