from json import load
from disnake import AppCmdInter
from disnake.ext import commands
from helpers.db import Guilds
from helpers.embeds import Illuminate
from data.lists import enemies
from main import GalacticWideWebBot


class IlluminateCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.illuminate_dict = enemies["illuminate"]
        self.variations_dict: dict = {}
        for i in enemies["illuminate"].values():
            if i["variations"] != None:
                for n, j in i["variations"].items():
                    self.variations_dict[n] = j

    async def illuminate_autocomp(inter: AppCmdInter, user_input: str):
        return [
            command
            for command in enemies["illuminate"]
            if user_input in command.lower()
        ]

    async def variations_autocomp(inter: AppCmdInter, user_input: str):
        variations_list: list[str] = []
        for i in enemies["illuminate"].values():
            if i["variations"] != None:
                for n in i["variations"]:
                    variations_list.append(n)
        return [command for command in variations_list if user_input in command.lower()]

    @commands.slash_command(
        description="Returns information on an Illuminate or variation.",
    )
    async def illuminate(
        self,
        inter: AppCmdInter,
        species: str = commands.Param(
            autocomplete=illuminate_autocomp,
            default=None,
            description="A specific 'main' illuminate",
        ),
        variation: str = commands.Param(
            autocomplete=variations_autocomp,
            default=None,
            description="A specific variant of an illuminate",
        ),
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.info(
            f"IlluminateCog, illuminate species:{species} variation:{variation} command used"
        )
        if not species and not variation:
            return await inter.send(":alien:", delete_after=10.0, ephemeral=True)
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
                delete_after=5.0,
            )
        elif (species and species not in self.illuminate_dict) or (
            variation and variation not in self.variations_dict
        ):
            return await inter.send(
                guild_language["enemy.missing"],
                ephemeral=True,
            )
        if species:
            species_info = self.illuminate_dict[species]
            embed = Illuminate(species, species_info, guild_language)
        elif variation:
            variation_info = self.variations_dict[variation]
            embed = Illuminate(
                variation, variation_info, guild_language, variation=True
            )
        return await inter.send(embed=embed, ephemeral=True)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(IlluminateCog(bot))
