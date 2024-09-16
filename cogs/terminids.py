from data.lists import enemies
from disnake import AppCmdInter
from disnake.ext import commands
from json import load
from main import GalacticWideWebBot
from utils.db import GuildRecord, GuildsDB
from utils.embeds import Terminid


class TerminidsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.terminids_dict = enemies["terminids"]
        self.variations_dict = {}
        for i in enemies["terminids"].values():
            if i["variations"] != None:
                for n, j in i["variations"].items():
                    self.variations_dict[n] = j

    async def terminids_autocomp(inter: AppCmdInter, user_input: str):
        return [
            command for command in enemies["terminids"] if user_input in command.lower()
        ][:25]

    async def variations_autocomp(inter: AppCmdInter, user_input: str):
        variations_list: list[str] = []
        for i in enemies["terminids"].values():
            if i["variations"] != None:
                for n in i["variations"]:
                    variations_list.append(n)
        return [command for command in variations_list if user_input in command.lower()]

    @commands.slash_command(
        description="Returns information on a Terminid or variation.",
    )
    async def terminid(
        self,
        inter: AppCmdInter,
        species: str = commands.Param(
            autocomplete=terminids_autocomp,
            default=None,
            description="A specific 'main' species",
        ),
        variation: str = commands.Param(
            autocomplete=variations_autocomp,
            default=None,
            description="A specific variant of a species",
        ),
    ):
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{species = }> <{variation = }>"
        )
        if not species and not variation:
            return await inter.send(
                "<a:explodeybug:1219248670482890752>", delete_after=10.0, ephemeral=True
            )
        await inter.response.defer(ephemeral=True)
        guild_in_db: GuildRecord = GuildsDB.get_info(inter.guild_id)
        if guild_in_db == None:
            guild_in_db = GuildsDB.insert_new_guild(inter.guild.id)
        guild_language = load(
            open(f"data/languages/{guild_in_db.language}.json", encoding="UTF-8")
        )
        if species and variation:
            return await inter.send(
                guild_language["enemy.species_or_variation"],
                ephemeral=True,
            )
        elif (species and species not in self.terminids_dict) or (
            variation and variation not in self.variations_dict
        ):
            return await inter.send(
                guild_language["enemy.missing"],
                ephemeral=True,
            )
        if species:
            species_info = self.terminids_dict[species]
            embed = Terminid(species, species_info, guild_language)
        elif variation:
            variation_info = self.variations_dict[variation]
            embed = Terminid(variation, variation_info, guild_language, variation=True)
        if not embed.image_set:
            await self.bot.moderator_channel.send(
                f"Image missing for **terminids __{species = } {variation = }__** <@{self.bot.owner_id}> :warning:"
            )

        return await inter.send(embed=embed, ephemeral=True)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(TerminidsCog(bot))
