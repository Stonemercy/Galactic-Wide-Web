from disnake import AppCmdInter, InteractionContextTypes, ApplicationInstallTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GWWGuild
from utils.embeds.command_embeds import FactionCommandEmbed
from utils.interactables import WikiButton


class TerminidsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.terminids_dict = self.bot.json_dict["enemies"]["terminids"]
        self.variations_dict = {
            k: v
            for i in self.terminids_dict.values()
            if i["variations"]
            for k, v in i["variations"].items()
        }

    async def terminids_autocomp(inter: AppCmdInter, user_input: str):
        return [
            species
            for species in inter.bot.json_dict["enemies"]["terminids"]
            if user_input.lower() in species.lower()
        ][:25]

    async def variations_autocomp(inter: AppCmdInter, user_input: str):
        variations_list = [
            variation
            for i in inter.bot.json_dict["enemies"]["terminids"].values()
            if i["variations"]
            for variation in i["variations"]
        ]
        return [
            variation
            for variation in variations_list
            if user_input.lower() in variation.lower()
        ][:25]

    @wait_for_startup()
    @commands.slash_command(
        description="Returns information on a Terminid or variation.",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
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
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{species = }> <{variation = }>"
        )
        if not species and not variation:
            return await inter.send(
                "<a:explodeybug:1219248670482890752>",
                delete_after=10.0,
                ephemeral=public != "Yes",
            )
        if inter.guild:
            guild = GWWGuild.get_by_id(inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    msg=f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuild.new(inter.guild_id)
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        if species and variation:
            return await inter.send(
                guild_language["enemies"]["species_or_variation"],
                ephemeral=public != "Yes",
            )
        elif (species and species not in self.terminids_dict) or (
            variation and variation not in self.variations_dict
        ):
            return await inter.send(
                guild_language["enemies"]["missing"],
                ephemeral=public != "Yes",
            )
        if species:
            species_info = {"name": species, "info": self.terminids_dict[species]}
            embed = FactionCommandEmbed("Terminids", species_info, guild_language)
            components = [
                WikiButton(
                    link=f"https://helldivers.wiki.gg/wiki/{species.replace(' ', '_')}"
                )
            ]
        elif variation:
            variation_info = {
                "name": variation,
                "info": self.variations_dict[variation],
            }
            embed = FactionCommandEmbed(
                "Terminids", variation_info, guild_language, variation=True
            )
            components = [WikiButton(link=variation_info["info"]["url"])]
        if not embed.image_set:
            await self.bot.moderator_channel.send(
                f"Image missing for **terminids __{species = } {variation = }__** <@{self.bot.owner_id}> :warning:\n```{embed.error}```"
            )
        return await inter.send(
            embed=embed, ephemeral=public != "Yes", components=components
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(TerminidsCog(bot))
