from data.lists import enemies
from disnake import AppCmdInter
from disnake.ext import commands
from json import load
from main import GalacticWideWebBot
from utils.db import GuildRecord, GuildsDB
from utils.embeds import Illuminate


class IlluminateCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.illuminate_dict = enemies["illuminate"]
        self.variations_dict = {}
        for i in enemies["illuminate"].values():
            if i["variations"]:
                self.variations_dict.update(i["variations"])

    async def illuminate_autocomp(inter: AppCmdInter, user_input: str):
        return [cmd for cmd in enemies["illuminate"] if user_input in cmd.lower()]

    async def variations_autocomp(inter: AppCmdInter, user_input: str):
        variations_list: list[str] = []
        for i in enemies["illuminate"].values():
            if i["variations"]:
                variations_list.extend([variation for variation in i["variations"]])
        return [cmd for cmd in variations_list if user_input in cmd.lower()]

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
            f"{self.qualified_name} | /{inter.application_command.name} <{species = }> <{variation = }>"
        )
        if not species and not variation:
            return await inter.send(":alien:", delete_after=10.0, ephemeral=True)
        guild_in_db: GuildRecord = GuildsDB.get_info(inter.guild_id)
        if not guild_in_db:
            guild_in_db = GuildsDB.insert_new_guild(inter.guild.id)
        guild_language = load(
            open(f"data/languages/{guild_in_db.language}.json", encoding="UTF-8")
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
        # if not embed.image_set: # ADD THIS WHEN I HAVE SPECIES INFO
        #     await self.bot.moderator_channel.send(
        #         f"Image missing for **illuminage __{species = } {variation = }__** <@{self.bot.owner_id}> :warning:"
        #     )

        return await inter.send(embed=embed, ephemeral=True)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(IlluminateCog(bot))
