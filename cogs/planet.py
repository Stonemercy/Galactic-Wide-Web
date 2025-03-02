from disnake import AppCmdInter, InteractionContextTypes, ApplicationInstallTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GWWGuild
from utils.embeds.command_embeds import PlanetCommandEmbed
from utils.interactables import HDCButton, WikiButton
from utils.maps import Maps


class PlanetCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    async def planet_autocomp(inter: AppCmdInter, user_input: str):
        return [
            planet["name"]
            for planet in inter.bot.json_dict["planets"].values()
            if user_input.lower() in planet["name"].lower()
        ][:25]

    @wait_for_startup()
    @commands.slash_command(
        description="Returns the war details on a specific planet.",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
    )
    async def planet(
        self,
        inter: AppCmdInter,
        planet: str = commands.Param(
            autocomplete=planet_autocomp, description="The planet you want to lookup"
        ),
        with_map: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want a map showing where this planet is?",
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{planet = }> <{with_map = }> <{public = }>"
        )
        planet_data = self.bot.data.planets.get_by_name(planet)
        if not planet_data:
            return await inter.send(
                "That planet is unavailable. Please select another planet from the list.",
                ephemeral=public != "Yes",
            )
        if inter.guild:
            guild = GWWGuild.get_by_id(inter.guild_id)
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        embed = PlanetCommandEmbed(
            planet_names=[
                planet_names
                for planet_names in self.bot.json_dict["planets"].values()
                if planet_names["name"].lower() == planet.lower()
            ][0],
            planet=planet_data,
            language_json=guild_language,
            planet_effects=[
                self.bot.json_dict["planet_effects"].get(str(effect), None)
                for effect in planet_data.active_effects
            ],
        )
        embeds = [embed]
        if not embed.image_set:
            await self.bot.moderator_channel.send(
                f"Image missing for biome of **planet __{planet}__** {planet_data.biome} <@{self.bot.owner_id}> :warning:"
            )
        if with_map == "Yes":
            map = Maps(
                data=self.bot.data,
                waste_bin_channel=self.bot.waste_bin_channel,
                planet_names_json=self.bot.json_dict["planets"],
                languages_json_list=[guild_language],
                target_planet=planet_data.index,
            )
            await map.localize()
            embeds.append(map.embeds[guild.language])
        await inter.send(
            embeds=embeds,
            ephemeral=public != "Yes",
            components=[
                WikiButton(
                    link=f"https://helldivers.wiki.gg/wiki/{planet.replace(' ', '_')}"
                ),
                HDCButton(
                    link=f"https://helldiverscompanion.com/#hellpad/planets/{planet_data.index}"
                ),
            ],
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(PlanetCog(bot))
