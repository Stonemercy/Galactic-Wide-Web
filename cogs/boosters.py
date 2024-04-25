from disnake import AppCmdInter
from disnake.ext import commands
from helpers.embeds import Items
from json import load


class BoostersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.boosters = load(open("data/json/items/boosters.json"))
        self.boosters["item_list"] = {}
        for i, j in self.boosters.items():
            if i == "item_list":
                continue
            self.boosters["item_list"][j["name"]] = j
        self.boosters = self.boosters["item_list"]
        print("Armours cog has finished loading")

    async def booster_autocomp(inter: AppCmdInter, user_input: str):
        boosters_json = load(open("data/json/items/boosters.json"))
        boosters = []
        for i in boosters_json.values():
            boosters.append(i["name"])
        return [booster for booster in boosters if user_input in booster.lower()]

    @commands.slash_command(
        description="Returns the description of a specific booster."
    )
    async def booster(
        self,
        inter: AppCmdInter,
        booster: str = commands.Param(autocomplete=booster_autocomp),
    ):
        if booster not in self.boosters:
            return await inter.send(
                (
                    "That booster isn't in my list, please try again.\n"
                    "||If you believe this is a mistake, please contact my Support Server||"
                ),
                ephemeral=True,
                delete_after=10,
            )
        chosen_booster = self.boosters[booster]
        embed = Items.Booster(chosen_booster)
        return await inter.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(BoostersCog(bot))
