from json import load
from disnake import AppCmdInter
from disnake.ext import commands
from helpers.db import Guilds
from helpers.embeds import Automaton
from data.lists import enemies
from main import GalacticWideWebBot


class AutomatonCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.automaton_dict = enemies["automaton"]
        self.variations_dict = {}
        for i in enemies["automaton"].values():
            if i["variations"]:
                self.variations_dict.update(i["variations"])

    async def automaton_autocomp(inter: AppCmdInter, user_input: str):
        return [
            command for command in enemies["automaton"] if user_input in command.lower()
        ]

    async def variations_autocomp(inter: AppCmdInter, user_input: str):
        variations_list: list[str] = []
        for i in enemies["automaton"].values():
            if i["variations"]:
                variations_list.extend([variation for variation in i["variations"]])
        return [command for command in variations_list if user_input in command.lower()]

    @commands.slash_command(
        description="Returns information on an Automaton or variation.",
    )
    async def automaton(
        self,
        inter: AppCmdInter,
        species: str = commands.Param(
            autocomplete=automaton_autocomp,
            default=None,
            description="A specific 'main' automaton",
        ),
        variation: str = commands.Param(
            autocomplete=variations_autocomp,
            default=None,
            description="A specific variant of an automaton",
        ),
    ):
        self.bot.logger.info(
            f"automatonCog, automaton species:{species} variation:{variation} command used"
        )
        if not species and not variation:
            return await inter.send(":robot:", delete_after=10.0, ephemeral=True)
        await inter.response.defer(ephemeral=True)
        guild_in_db = Guilds.get_info(inter.guild_id)
        if not guild_in_db:
            guild_in_db = Guilds.insert_new_guild(inter.guild.id)
        guild_language = load(
            open(f"data/languages/{guild_in_db[5]}.json", encoding="UTF-8")
        )
        if species and variation:
            return await inter.send(
                guild_language["enemy.species_or_variation"],
                ephemeral=True,
            )
        elif (species and species not in self.automaton_dict) or (
            variation and variation not in self.variations_dict
        ):
            return await inter.send(
                guild_language["enemy.missing"],
                ephemeral=True,
            )
        if species:
            species_info = self.automaton_dict[species]
            embed = Automaton(species, species_info, guild_language)
        elif variation:
            variation_info = self.variations_dict[variation]
            embed = Automaton(variation, variation_info, guild_language, variation=True)
        return await inter.send(embed=embed, ephemeral=True)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(AutomatonCog(bot))
