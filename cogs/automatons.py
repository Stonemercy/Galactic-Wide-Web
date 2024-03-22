from disnake import AppCmdInter
from disnake.ext import commands
from helpers.embeds import Automaton
from data.lists import enemies


class AutomatonsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.automatons_dict = enemies["automatons"]
        self.variations_dict: dict = {}
        for i in enemies["automatons"].values():
            if i["variations"] != None:
                for n, j in i["variations"].items():
                    self.variations_dict[n] = j
        print("Automatons cog has finished loading")

    async def automatons_autocomp(inter: AppCmdInter, user_input: str):
        return [
            command
            for command in enemies["automatons"]
            if user_input in command.lower()
        ]

    async def variations_autocomp(inter: AppCmdInter, user_input: str):
        variations_list: list[str] = []
        for i in enemies["automatons"].values():
            if i["variations"] != None:
                for n in i["variations"]:
                    variations_list.append(n)
        return [command for command in variations_list if user_input in command.lower()]

    @commands.slash_command(
        description="Get information on a bot",
    )
    async def automaton(
        self,
        inter: AppCmdInter,
        species: str = commands.Param(
            autocomplete=automatons_autocomp,
            default=None,
            description="A specific 'main' bot",
        ),
        variation: str = commands.Param(
            autocomplete=variations_autocomp,
            default=None,
            description="A specific variant of a bot",
        ),
    ):
        if not species and not variation:
            return await inter.send(":robot:", delete_after=10.0)
        if species and variation:
            return await inter.send(
                "Please choose species **or** variation",
                ephemeral=True,
                delete_after=5.0,
            )
        elif species != None and species not in self.automatons_dict:
            return await inter.send(
                (
                    "That bot isn't in my list, please try again.\n"
                    "||If you believe this is a mistake, please contact my Support Server||"
                ),
                ephemeral=True,
            )
        elif variation != None and variation not in self.variations_dict:
            return await inter.send(
                (
                    "That variation isn't in my list, please try again.\n"
                    "||If you believe this is a mistake, please contact my Support Server||"
                ),
                ephemeral=True,
            )
        if species != None:
            species_info = self.automatons_dict[species]
            embed = Automaton(species, species_info)
        elif variation != None:
            variation_info = self.variations_dict[variation]
            embed = Automaton(variation, variation_info, variation=True)
        return await inter.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(AutomatonsCog(bot))
