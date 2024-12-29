from disnake import AppCmdInter, ApplicationInstallTypes, InteractionContextTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GWWGuild
from utils.embeds import EnemyEmbed
from utils.interactables import WikiButton


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
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
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
                ":robot:", delete_after=10.0, ephemeral=public != "Yes"
            )
        if inter.guild:
            guild = GWWGuild.get_by_id(inter.guild_id)
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        if species and variation:
            return await inter.send(
                guild_language["enemy"]["species_or_variation"],
                ephemeral=public != "Yes",
            )
        elif (species and species not in self.automaton_dict) or (
            variation and variation not in self.variations_dict
        ):
            return await inter.send(
                guild_language["enemy"]["missing"],
                ephemeral=public != "Yes",
            )
        if species:
            embed = EnemyEmbed(
                "Automaton",
                {"name": species, "info": self.automaton_dict[species]},
                guild_language,
            )
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
            embed = EnemyEmbed(
                "Automaton", variation_info, guild_language, variation=True
            )
            components = [WikiButton(link=variation_info["info"]["url"])]
        if not embed.image_set:
            await self.bot.moderator_channel.send(
                f"Image missing for **automaton __{species = } {variation = }__** <@{self.bot.owner_id}> :warning:\n```{embed.error}```"
            )
        return await inter.send(
            embed=embed, ephemeral=public != "Yes", components=components
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(AutomatonCog(bot))
