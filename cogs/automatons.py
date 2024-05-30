from json import load
from logging import getLogger
from disnake import AppCmdInter
from disnake.ext import commands
from helpers.db import Guilds
from helpers.embeds import Automaton
from data.lists import enemies

logger = getLogger("disnake")


class AutomatonsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.automatons_dict = enemies["automatons"]
        self.variations_dict: dict = {}
        for i in enemies["automatons"].values():
            if i["variations"] != None:
                for n, j in i["variations"].items():
                    self.variations_dict[n] = j

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
        description="Returns information on an Automaton or variation.",
    )
    async def automaton(
        self,
        inter: AppCmdInter,
        species: str = commands.Param(
            autocomplete=automatons_autocomp,
            default=None,
            description="A specific 'main' automaton",
        ),
        variation: str = commands.Param(
            autocomplete=variations_autocomp,
            default=None,
            description="A specific variant of an automaton",
        ),
    ):
        logger.info("AutomatonsCog, automaton command used")
        if not species and not variation:
            return await inter.send(":robot:", delete_after=10.0, ephemeral=True)
        await inter.response.defer(ephemeral=True)
        guild_in_db = Guilds.get_info(inter.guild_id)
        guild_language = load(
            open(f"data/languages/{guild_in_db[5]}.json", encoding="UTF-8")
        )
        if species and variation:
            return await inter.send(
                guild_language["enemy.species_or_variation"],
                ephemeral=True,
                delete_after=5.0,
            )
        elif (species != None and species not in self.automatons_dict) or (
            variation != None and variation not in self.variations_dict
        ):
            return await inter.send(
                guild_language["enemy.missing"],
                ephemeral=True,
            )
        if species != None:
            species_info = self.automatons_dict[species]
            embed = Automaton(species, species_info, guild_language)
        elif variation != None:
            variation_info = self.variations_dict[variation]
            embed = Automaton(variation, variation_info, guild_language, variation=True)
        return await inter.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(AutomatonsCog(bot))
