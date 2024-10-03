from disnake import AppCmdInter
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GuildRecord, GuildsDB
from utils.embeds import Automaton


class AutomatonCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.automaton_dict = self.bot.json_dict["enemies"]["automaton"]
        self.variations_dict = {
            k: v
            for i in self.automaton_dict.values()
            if i["variations"]
            for k, v in i["variations"].items()
        }

    async def automaton_autocomp(inter: AppCmdInter, user_input: str):
        return [
            species
            for species in inter.bot.json_dict["enemies"]["automaton"]
            if user_input in species.lower()
        ][:25]

    async def variations_autocomp(inter: AppCmdInter, user_input: str):
        variations_list = [
            variation
            for i in inter.bot.json_dict["enemies"]["automaton"].values()
            if i["variations"]
            for variation in i["variations"]
        ]
        return [
            variation
            for variation in variations_list
            if user_input in variation.lower()
        ][:25]

    @wait_for_startup()
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
        await inter.response.defer(ephemeral=True)
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{species = }> <{variation = }>"
        )
        if not species and not variation:
            return await inter.send(":robot:", delete_after=10.0, ephemeral=True)
        guild_in_db: GuildRecord = GuildsDB.get_info(inter.guild_id)
        if not guild_in_db:
            guild_in_db = GuildsDB.insert_new_guild(inter.guild.id)
        guild_language = self.bot.json_dict["languages"][guild_in_db.language]
        if species and variation:
            return await inter.send(
                guild_language["enemy"]["species_or_variation"],
                ephemeral=True,
            )
        elif (species and species not in self.automaton_dict) or (
            variation and variation not in self.variations_dict
        ):
            return await inter.send(
                guild_language["enemy"]["missing"],
                ephemeral=True,
            )
        if species:
            species_info = self.automaton_dict[species]
            embed = Automaton(species, species_info, guild_language)
        elif variation:
            variation_info = self.variations_dict[variation]
            embed = Automaton(variation, variation_info, guild_language, variation=True)
        if not embed.image_set:
            await self.bot.moderator_channel.send(
                f"Image missing for **automaton __{species = } {variation = }__** <@{self.bot.owner_id}> :warning:"
            )

        return await inter.send(embed=embed, ephemeral=True)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(AutomatonCog(bot))
