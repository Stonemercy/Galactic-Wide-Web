from datetime import datetime, timedelta
from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    Colour,
    File,
    InteractionContextTypes,
    MediaGalleryItem,
    ui,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.containers import PlanetContainers
from utils.checks import wait_for_startup
from utils.dbv2 import GWWGuild, GWWGuilds
from utils.maps import Maps


class PlanetCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    async def planet_autocomp(inter: AppCmdInter, user_input: str) -> list[str]:
        if not inter.bot.data.loaded:
            return []
        return [
            f"{p.index}-{p.names.get('en-GB', str(p.index))}"
            for p in sorted(
                inter.bot.data.formatted_data.planets.values(),
                key=lambda x: x.stats.player_count,
                reverse=True,
            )
            if user_input.lower() in p.names.get("en-GB", str(p.index)).lower()
            or user_input in str(p.index)
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
    ) -> None:
        await inter.response.defer(ephemeral=public != "Yes")
        planet_data = None
        if "-" not in planet:
            planet_data_list = [
                p
                for p in self.bot.data.formatted_data.planets.values()
                if p.names.get("en-GB", str(p.index)).lower() == planet
            ]
            if planet_data_list:
                planet_data = planet_data_list[0]
        else:
            try:
                index = int(planet.split("-")[0])
            except ValueError:
                await inter.send(
                    f"The planet you supplied (`{planet}`) is in the incorrect format. Please choose a planet from the list."
                )
                return
            planet_data = self.bot.data.formatted_data.planets.get(index)
        if not planet_data:
            return await inter.send(
                "That planet is unavailable. Please select another planet from the list.",
                ephemeral=public != "Yes",
            )
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild_id, "en", [])
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        components = PlanetContainers(
            planet=planet_data,
            lang_code=guild_language["code_long"],
            containers_json=guild_language["containers"]["PlanetContainers"],
            faction_json=guild_language["factions"],
            gambit_planets=self.bot.data.formatted_data.gambit_planets,
        )

        if with_map == "Yes":
            fifteen_minutes_ago = datetime.now() - timedelta(minutes=15)
            latest_map = self.bot.maps.latest_maps.get(guild.language)
            if not latest_map or (
                latest_map and latest_map.updated_at < fifteen_minutes_ago
            ):
                self.bot.maps.update_base_map(
                    planets=self.bot.data.formatted_data.planets,
                    assignments=self.bot.data.formatted_data.assignments.get("en", []),
                    campaigns=self.bot.data.formatted_data.campaigns,
                )
                language_json = self.bot.json_dict["languages"][guild.language]
                self.bot.maps.localize_map(
                    language_code_short=language_json["code"],
                    language_code_long=language_json["code_long"],
                    planets=self.bot.data.formatted_data.planets,
                    planet_names_json=self.bot.json_dict["planets"],
                )
                self.bot.maps.add_icons(
                    lang=guild.language,
                    long_code=language_json["code_long"],
                    planets=self.bot.data.formatted_data.planets,
                    dss=self.bot.data.formatted_data.dss,
                    planet_names_json=self.bot.json_dict["planets"],
                )
                message = await self.bot.channels.waste_bin_channel.send(
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
            arrow_map_message = await self.bot.channels.waste_bin_channel.send(
                file=File(fp=self.bot.maps.FileLocations.arrow_map)
            )
            components.append(
                ui.Container(
                    ui.MediaGallery(
                        MediaGalleryItem(arrow_map_message.attachments[0].url)
                    ),
                    accent_colour=Colour.dark_embed(),
                ),
            )
        await inter.send(
            components=components,
            ephemeral=public != "Yes",
        )


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(PlanetCog(bot))
