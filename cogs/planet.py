from datetime import datetime, timedelta
from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    Colour,
    Embed,
    File,
    InteractionContextTypes,
    InteractionTimedOut,
    NotFound,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.dbv2 import GWWGuild, GWWGuilds
from utils.embeds import PlanetEmbeds
from utils.interactables import HDCButton, WikiButton
from utils.maps import Maps


class PlanetCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    async def planet_autocomp(inter: AppCmdInter, user_input: str):
        return [
            p.name
            for p in inter.bot.data.planets.values()
            if user_input.lower() in p.name.lower()
        ][:25]

    @wait_for_startup()
    @commands.slash_command(
        description="Returns the war details on a specific planet.",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns the war details on a specific planet. This includes a lot of stats that arent available in the dashboard.",
            "example_usage": "**`/planet planet:Heeth with_map:Yes public:Yes`** returns a large embed with all of the stats the planet has. It also includes a map with an arrow pointing to the planet. It can also be seen by others in discord.",
        },
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
        try:
            await inter.response.defer(ephemeral=public != "Yes")
        except (NotFound, InteractionTimedOut):
            await inter.channel.send(
                "There was an error with that command, please try again.",
                delete_after=5,
            )
            return
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
            guild = GWWGuilds.get_specific_guild(id=inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    msg=f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild_id, "en", [])
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        planet_name = [
            planet_names
            for planet_names in self.bot.json_dict["planets"].values()
            if planet_names["name"].lower() == planet.lower()
        ][0]["names"][guild_language["code_long"]]
        planet_changes = self.bot.data.liberation_changes.get_entry(planet_data.index)
        embeds = PlanetEmbeds(
            planet_name=planet_name,
            planet=planet_data,
            language_json=guild_language,
            liberation_change=planet_changes,
            region_changes=self.bot.data.region_changes,
            total_players=self.bot.data.total_players,
        )

        if not embeds[0].image_set:
            await self.bot.moderator_channel.send(
                f"# <@{self.bot.owner.id}> :warning:\nImage missing for biome of **planet __{planet}__** {planet_data.biome} {planet_data.biome['name'].lower().replace(' ', '_')}.png"
            )
        if with_map == "Yes":
            fifteen_minutes_ago = datetime.now() - timedelta(minutes=15)
            latest_map = self.bot.maps.latest_maps.get(guild.language)
            if not latest_map or (
                latest_map and latest_map.updated_at < fifteen_minutes_ago
            ):
                self.bot.maps.update_base_map(
                    planets=self.bot.data.planets,
                    assignments=self.bot.data.assignments,
                    campaigns=self.bot.data.campaigns,
                    dss=self.bot.data.dss,
                    sector_names=self.bot.json_dict["sectors"],
                )
                language_json = self.bot.json_dict["languages"][guild.language]
                self.bot.maps.localize_map(
                    language_code_short=language_json["code"],
                    language_code_long=language_json["code_long"],
                    planets=self.bot.data.planets,
                    active_planets=[
                        campaign.planet.index for campaign in self.bot.data.campaigns
                    ],
                    type_3_campaigns=[
                        c for c in self.bot.data.campaigns if c.type == 3
                    ],
                    planet_names_json=self.bot.json_dict["planets"],
                )
                message = await self.bot.waste_bin_channel.send(
                    file=File(
                        fp=self.bot.maps.FileLocations.localized_map_path(
                            language_json["code"]
                        )
                    )
                )
                self.bot.maps.latest_maps[language_json["code"]] = Maps.LatestMap(
                    datetime.now(), message.attachments[0].url
                )
                latest_map = self.bot.maps.latest_maps[language_json["code"]]
            self.bot.maps.draw_arrow(language_code=guild.language, planet=planet_data)
            embed = Embed(colour=Colour.dark_embed())
            embed.set_image(file=File(self.bot.maps.FileLocations.arrow_map))
            embeds.append(embed)
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
