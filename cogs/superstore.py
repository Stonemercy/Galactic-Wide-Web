from disnake import AppCmdInter, InteractionContextTypes, ApplicationInstallTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.embeds.command_embeds import SuperstoreCommandEmbed


class SuperstoreCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    ###### DISABLED UNTIL SOURCE IS UPDATED ######
    # @wait_for_startup()
    # @commands.slash_command(
    #     description="Get the current Superstore rotation",
    #     install_types=ApplicationInstallTypes.all(),
    #     contexts=InteractionContextTypes.all(),
    # )
    # async def superstore(
    #     self,
    #     inter: AppCmdInter,
    #     public: str = commands.Param(
    #         choices=["Yes", "No"],
    #         default="No",
    #         description="Do you want other people to see the response to this command?",
    #     ),
    # ):
    #     await inter.response.defer(ephemeral=public != "Yes")
    #     self.bot.logger.info(
    #         f"{self.qualified_name} | /{inter.application_command.name} <{public = }>"
    #     )
    #     await inter.send(
    #         embed=SuperstoreCommandEmbed(self.bot.data.superstore),
    #         ephemeral=public != "Yes",
    #     )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(SuperstoreCog(bot))
