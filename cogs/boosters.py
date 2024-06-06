from logging import getLogger
from disnake import AppCmdInter
from disnake.ext import commands
from helpers.embeds import Items
from json import load

logger = getLogger("disnake")


class BoostersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.boosters: dict = load(open("data/json/items/boosters.json"))
        self.boosters["item_list"] = {}
        for i, j in self.boosters.items():
            if i == "item_list":
                continue
            self.boosters["item_list"][j["name"]] = j
        self.boosters = self.boosters["item_list"]

    async def booster_autocomp(inter: AppCmdInter, user_input: str):
        boosters_json: dict = load(open("data/json/items/boosters.json"))
        boosters = [i["name"] for i in boosters_json.values()]
        return [booster for booster in boosters if user_input in booster.lower()]

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
        logger.info(f"BoostersCog, booster booster:{booster} command used")
        if booster not in self.boosters:
            return await inter.send(
                (
                    "That booster isn't in my list, please try again.\n"
                    "||If you believe this is a mistake, please contact my Support Server||"
                ),
                ephemeral=True,
            )
        chosen_booster = self.boosters[booster]
        embed = Items.Booster(chosen_booster)
        return await inter.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(BoostersCog(bot))
