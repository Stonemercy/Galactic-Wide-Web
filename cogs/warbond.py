from os import listdir
from disnake import AppCmdInter
from disnake.ext import commands
from helpers.embeds import Items
from json import load


class WarbondCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.warbond_names = []
        for i in listdir("data/json/warbonds"):
            self.warbond_names.append(i.replace("_", " ").replace(".json", "").title())
        self.item_names = load(open("data/json/items/item_names.json"))
        print("Warbonds cog has finished loading")

    async def warbond_autocomp(inter: AppCmdInter, user_input: str):
        warbond_names = []
        for i in listdir("data/json/warbonds"):
            warbond_names.append(i.replace("_", " ").replace(".json", "").title())
        return [warbond for warbond in warbond_names if user_input in warbond.lower()]

    @commands.slash_command(description="Get info on some armour.")
    async def warbond(
        self,
        inter: AppCmdInter,
        warbond: str = commands.Param(autocomplete=warbond_autocomp),
    ):

        if warbond not in self.warbond_names:
            return await inter.send(
                (
                    "That warbond isn't in my list, please try again.\n"
                    "||If you believe this is a mistake, please contact my Support Server||"
                ),
                ephemeral=True,
                delete_after=10,
            )
        chosen_warbond = load(
            open(f"data/json/warbonds/{warbond.replace(' ', '_').lower()}.json")
        )
        embeds = Items.Warbond(chosen_warbond, warbond, self.item_names)
        return await inter.send(embeds=embeds)


def setup(bot: commands.Bot):
    bot.add_cog(WarbondCog(bot))
