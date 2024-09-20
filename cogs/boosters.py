from disnake import AppCmdInter
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.embeds import Items


class BoostersCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    async def booster_autocomp(inter: AppCmdInter, user_input: str):
        boosters_json: dict = inter.bot.json_dict["items"]["boosters"]
        return [
            i["name"] for i in boosters_json.values() if user_input in i["name"].lower()
        ][:25]

    @commands.slash_command(
        description="Returns the description of a specific booster."
    )
    async def booster(
        self,
        inter: AppCmdInter,
        booster: str = commands.Param(
            autocomplete=booster_autocomp, description="The booster you want to lookup"
        ),
    ):
        boosters = {
            j["name"]: j for j in self.bot.json_dict["items"]["boosters"].values()
        }
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{booster = }>"
        )
        if booster not in boosters:
            return await inter.send(
                (
                    "That booster isn't in my list, please try again.\n"
                    "||If you believe this is a mistake, please contact my Support Server||"
                ),
                ephemeral=True,
            )
        chosen_booster = boosters[booster]
        embed = Items.Booster(chosen_booster)
        if not embed.image_set:
            await self.bot.moderator_channel.send(
                f"Image missing for **booster __{booster}__** <@{self.bot.owner_id}> :warning:"
            )
        return await inter.send(embed=embed, ephemeral=True)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(BoostersCog(bot))
