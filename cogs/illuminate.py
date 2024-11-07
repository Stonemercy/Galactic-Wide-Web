from disnake import AppCmdInter
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.interactables import WikiButton
from utils.checks import wait_for_startup
from utils.db import GuildRecord, GuildsDB
from utils.embeds import EnemyEmbed


class IlluminateCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.illuminate_dict = self.bot.json_dict["enemies"]["illuminate"]
        self.variations_dict = {
            k: v
            for i in self.illuminate_dict.values()
            if i["variations"]
            for k, v in i["variations"].items()
        }

    async def illuminate_autocomp(inter: AppCmdInter, user_input: str):
        return [
            species
            for species in inter.bot.json_dict["enemies"]["illuminate"]
            if user_input in species.lower()
        ][:25]

    async def variations_autocomp(inter: AppCmdInter, user_input: str):
        variations_list = [
            variation
            for i in inter.bot.json_dict["enemies"]["illuminate"].values()
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
        guild_language = self.bot.json_dict["languages"][guild_in_db.language]
        if species and variation:
            return await inter.send(
                guild_language["enemy"]["species_or_variation"],
                ephemeral=True,
            )
        elif (species and species not in self.illuminate_dict) or (
            variation and variation not in self.variations_dict
        ):
            return await inter.send(
                guild_language["enemy"]["missing"],
                ephemeral=True,
            )
        if species:
            species_info = {"name": species, "info": self.illuminate_dict[species]}
            embed = EnemyEmbed("Illuminate", species_info, guild_language)
            components = [
                WikiButton(
                    link=f"https://helldivers.wiki.gg/wiki/Helldivers_1:The_Illuminate"
                )
            ]  # [
            #     WikiButton(
            #         link=f"https://helldivers.wiki.gg/wiki/{species.replace(' ', '_')}"
            #     )
            # ]
        elif variation:
            variation_info = {
                "name": variation,
                "info": self.variations_dict[variation],
            }
            embed = EnemyEmbed(
                "Illuminate", variation_info, guild_language, variation=True
            )
            components = None
        # if not embed.image_set: # ADD THIS WHEN I HAVE SPECIES INFO
        #     await self.bot.moderator_channel.send(
        #         f"Image missing for **illuminage __{species = } {variation = }__** <@{self.bot.owner_id}> :warning:\n```{embed.error}```"
        #     )

        return await inter.send(embed=embed, ephemeral=True, components=components)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(IlluminateCog(bot))
