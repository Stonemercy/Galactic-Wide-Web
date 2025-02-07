from disnake import AppCmdInter, InteractionContextTypes, ApplicationInstallTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import Meridia
from utils.embeds import MeridiaEmbed


class MeridiaCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Get up-to-date information on Meridia",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
    )
    async def meridia(
        self,
        inter: AppCmdInter,
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{public = }>"
        )
        await inter.send(
            embed=MeridiaEmbed(
                Meridia(),
                self.bot.data.global_resources.dark_energy,
                sum(
                    [
                        planet.event.potential_buildup
                        for planet in self.bot.data.planet_events
                    ]
                ),
                len(
                    [
                        planet
                        for planet in self.bot.data.planet_events
                        if planet.event.potential_buildup != 0
                    ]
                ),
                self.bot.data.dark_energy_changes,
            )
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(MeridiaCog(bot))
