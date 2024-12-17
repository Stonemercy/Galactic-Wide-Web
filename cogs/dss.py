from disnake import AppCmdInter
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.interactables import WikiButton
from utils.checks import wait_for_startup
from utils.db import GWWGuild
from utils.embeds import DSSEmbed


class DSSCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Returns information on the Democracy Space Station",
        dm_permission=False,
    )
    async def dss(
        self,
        inter: AppCmdInter,
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="If you want the response to be seen by others in the server.",
        ),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{public = }>"
        )
        if self.bot.data.dss == "Error":
            return await inter.send(
                "The DSS is currently unavailable. Please try again later.",
                ephemeral=public != "Yes",
            )
        await inter.send(
            embed=DSSEmbed(
                self.bot.data.dss,
                self.bot.json_dict["languages"][
                    GWWGuild.get_by_id(inter.guild_id).language
                ],
            ),
            components=[
                WikiButton(
                    link=f"https://helldivers.wiki.gg/wiki/Democracy_Space_Station"
                )
            ],
            ephemeral=public != "Yes",
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(DSSCog(bot))
