from disnake import AppCmdInter, ApplicationInstallTypes, InteractionContextTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.embeds.command_embeds import BoosterCommandEmbed
from utils.interactables import HDCButton, WikiButton


class BoostersCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    async def booster_autocomp(inter: AppCmdInter, user_input: str):
        boosters_json: dict = inter.bot.json_dict["items"]["boosters"]
        return [
            i["name"] for i in boosters_json.values() if user_input in i["name"].lower()
        ][:25]

    @wait_for_startup()
    @commands.slash_command(
        description="Returns the description of a specific booster.",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
    )
    async def booster(
        self,
        inter: AppCmdInter,
        booster: str = commands.Param(
            autocomplete=booster_autocomp, description="The booster you want to lookup"
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{booster = }>"
        )
        boosters = {
            j["name"]: j for j in self.bot.json_dict["items"]["boosters"].values()
        }
        if booster not in boosters:
            return await inter.send(
                (
                    "That booster isn't in my list, please try again.\n"
                    "||If you believe this is a mistake, please contact my Support Server||"
                ),
                ephemeral=True,
            )
        embed = BoosterCommandEmbed(boosters[booster])
        if not embed.image_set:
            await self.bot.moderator_channel.send(
                f"Image missing for **booster __{booster}__** <@{self.bot.owner_id}> :warning:"
            )
        return await inter.send(
            embed=embed,
            ephemeral=public != "Yes",
            components=[
                WikiButton(
                    link=f"https://helldivers.wiki.gg/wiki/{booster.replace(' ', '_')}"
                ),
                HDCButton(link="https://helldiverscompanion.com/#hellpad/boosters"),
            ],
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(BoostersCog(bot))
