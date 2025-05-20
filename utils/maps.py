from asyncio import to_thread
from data.lists import faction_colours
from dataclasses import dataclass
from datetime import datetime
from math import cos, radians, sin
from PIL import Image, ImageDraw, ImageFont
from random import randint
from utils.data import DSS, Assignment, Campaign, Planet, Planets
from utils.mixins import ReprMixin

faction_mapping: dict[int, str] = {
    1: "Humans",
    2: "Terminids",
    3: "Automaton",
    4: "Illuminate",
}
dim_faction_colours: dict[str, tuple[float, float, float]] = {
    faction: tuple(int(colour / 2.5) for colour in colours)
    for faction, colours in faction_colours.items()
}


class Maps:
    def __init__(self):
        self.latest_maps: dict[str, Maps.LatestMap] | dict = {}

    @dataclass
    class LatestMap(ReprMixin):
        updated_at: datetime
        map_link: str

    @dataclass
    class FileLocations:
        empty_map: str = "resources/maps/empty_map.webp"
        sector_map: str = "resources/maps/sector_map.webp"
        waypoints_map: str = "resources/maps/waypoints_map.webp"
        assignment_map: str = "resources/maps/assignment_map.webp"
        dss_map: str = "resources/maps/dss_map.webp"
        planets_map: str = "resources/maps/planets_map.webp"
        arrow_map: str = "resources/maps/arrow_map.webp"

        def localized_map_path(language_code: str) -> str:
            return f"resources/maps/{language_code}.webp"

    async def update_base_map(
        self,
        planets: Planets,
        assignment: Assignment,
        campaigns: list[Campaign],
        dss: DSS,
    ) -> None:
        await to_thread(self.update_sectors, planets=planets)
        self.update_waypoint_lines(planets=planets)
        self.update_assignment_tasks(
            assignment=assignment,
            planets=planets,
            campaigns=campaigns,
        )
        self.update_planets(
            planets=planets,
            active_planets=[campaign.planet.index for campaign in campaigns],
        )
        self.update_dss(dss=dss)

    def update_sectors(self, planets: Planets) -> None:
        valid_planets: list[Planet] = [
            planet
            for planet in planets.values()
            if not (planet.current_owner == "Humans" and not planet.event)
        ]
        sector_info: dict[str, dict[str, tuple | list]] = {
            planet.sector: {
                "coords": planet.map_waypoints,
                "faction": [],
            }
            for planet in valid_planets
        }
        for planet in valid_planets:
            sector_info[planet.sector]["faction"].append(
                planet.current_owner if not planet.event else planet.event.faction
            )
        with Image.open(fp=Maps.FileLocations.empty_map) as background:
            alpha = background.getchannel(channel="A")
            background = background.convert(mode="RGB")
            for info in sector_info.values():
                info["faction"] = max(set(info["faction"]), key=info["faction"].count)
                ImageDraw.floodfill(
                    image=background,
                    xy=info["coords"],
                    value=dim_faction_colours[info["faction"]],
                    thresh=25,
                )
            background.putalpha(alpha=alpha)
            background.save(fp=Maps.FileLocations.sector_map)

    def update_waypoint_lines(self, planets: Planets) -> None:
        with Image.open(fp=Maps.FileLocations.sector_map) as background:
            draw_on_background_with_sectors = ImageDraw.Draw(im=background)
            for index, planet in planets.items():
                for waypoint in planet.waypoints:
                    try:
                        waypoint_coords = planets[waypoint].map_waypoints
                        draw_on_background_with_sectors.line(
                            xy=(
                                waypoint_coords[0],
                                waypoint_coords[1],
                                planet.map_waypoints[0],
                                planet.map_waypoints[1],
                            ),
                            width=2,
                        )
                    except KeyError:
                        continue
            background.save(fp=Maps.FileLocations.waypoints_map)

    def update_assignment_tasks(
        self,
        assignment: Assignment,
        planets: Planets,
        campaigns: list[Campaign] | list,
    ) -> None:
        with Image.open(fp=Maps.FileLocations.waypoints_map) as background:
            if assignment:
                background_draw = ImageDraw.Draw(im=background)
                for task in assignment.tasks:
                    if task.type in (11, 13):
                        self._draw_ellipse(
                            draw=background_draw,
                            coords=planets[task.values[2]].map_waypoints,
                            fill_colour=faction_colours["MO"],
                        )
                    elif task.type == 12 and (
                        planet_events := [
                            planet for planet in planets.values() if planet.event
                        ]
                    ):
                        for planet in planet_events:
                            if planet.event.faction == faction_mapping[task.values[1]]:
                                self._draw_ellipse(
                                    draw=background_draw,
                                    coords=planet.map_waypoints,
                                    fill_colour=faction_colours["MO"],
                                )
                    elif task.type == 2:
                        self._draw_ellipse(
                            draw=background_draw,
                            coords=planets[task.values[8]].map_waypoints,
                            fill_colour=faction_colours["MO"],
                        )
                    elif task.type == 3 and task.progress != 1:
                        for campaign in campaigns:
                            if campaign.faction == faction_mapping[task.values[0]]:
                                self._draw_ellipse(
                                    draw=background_draw,
                                    coords=campaign.planet.map_waypoints,
                                    fill_colour=faction_colours["MO"],
                                )
        background.save(fp=Maps.FileLocations.assignment_map)

    def update_planets(self, planets: Planets, active_planets: list[int]) -> None:
        with Image.open(fp=Maps.FileLocations.assignment_map) as background:
            background_draw = ImageDraw.Draw(im=background)
            for index, planet in planets.items():
                if planet.dss_in_orbit:
                    self._draw_ellipse(
                        draw=background_draw,
                        coords=planet.map_waypoints,
                        fill_colour=faction_colours["DSS"],
                        radius=17,
                    )
                if index == 64:
                    for i in range(12, 6, -1):
                        background_draw.ellipse(
                            xy=[
                                (
                                    planet.map_waypoints[0] - i,
                                    planet.map_waypoints[1] - i,
                                ),
                                (
                                    planet.map_waypoints[0] + i,
                                    planet.map_waypoints[1] + i,
                                ),
                            ],
                            fill=(i * 20, i * 5, i * 20),
                        )
                    background_draw.ellipse(
                        xy=[
                            (planet.map_waypoints[0] - 7, planet.map_waypoints[1] - 7),
                            (planet.map_waypoints[0] + 7, planet.map_waypoints[1] + 7),
                        ],
                        fill=(0, 0, 0),
                        outline=(200, 100, 255),
                    )
                elif planet.index == 0:
                    with Image.open("resources/super_earth.png") as se_icon:
                        background.paste(
                            se_icon,
                            (
                                planet.map_waypoints[0] - 25,
                                planet.map_waypoints[1] - 25,
                            ),
                            se_icon,
                        )
                elif 1240 in planet.active_effects:
                    background_draw.ellipse(
                        xy=[
                            (
                                planet.map_waypoints[0] - 10,
                                planet.map_waypoints[1] - 10,
                            ),
                            (
                                planet.map_waypoints[0] + 10,
                                planet.map_waypoints[1] + 10,
                            ),
                        ],
                        fill="red",
                    )
                elif set([1241, 1252]) & planet.active_effects:
                    planet_image = Image.new("RGBA", (2000, 2000), (0, 0, 0, 0))
                    planet_draw = ImageDraw.Draw(planet_image)
                    planet_draw.ellipse(
                        xy=[
                            (
                                planet.map_waypoints[0] - 10,
                                planet.map_waypoints[1] - 10,
                            ),
                            (
                                planet.map_waypoints[0] + 10,
                                planet.map_waypoints[1] + 10,
                            ),
                        ],
                        fill=(102, 99, 100),
                    )
                    cx, cy = planet.map_waypoints
                    angles = []
                    while len(angles) < 7:
                        candidate = randint(0, 360)
                        if all(abs(candidate - a) >= 30 for a in angles):
                            angles.append(candidate)
                    for start_angle in angles:
                        step_size = 11 * 1.2
                        new_x = cx + int(step_size * cos(radians(start_angle)))
                        new_y = cy + int(step_size * sin(radians(start_angle)))
                        planet_draw.line(
                            [(cx, cy), (new_x, new_y)],
                            fill=(0, 0, 0, 0),
                            width=randint(2, 4),
                        )
                    background.paste(im=planet_image, mask=planet_image)
                    planet_image.close()
                else:
                    background_draw.ellipse(
                        xy=[
                            (
                                planet.map_waypoints[0] - 10,
                                planet.map_waypoints[1] - 10,
                            ),
                            (
                                planet.map_waypoints[0] + 10,
                                planet.map_waypoints[1] + 10,
                            ),
                        ],
                        fill=(
                            faction_colours[planet.current_owner]
                            if index in active_planets
                            else tuple(
                                int(colour / 1.5)
                                for colour in faction_colours[planet.current_owner]
                            )
                        ),
                    )
                if planet.event and planet.event.siege_fleet:
                    with Image.open(
                        f"resources/siege_fleets/{planet.event.siege_fleet.name.replace(' ', '_').lower()}.png"
                    ) as fleet_icon:
                        background.paste(
                            fleet_icon,
                            (
                                int(planet.map_waypoints[0] - 25),
                                int(planet.map_waypoints[1] - 50),
                            ),
                            fleet_icon,
                        )
                elif 1269 in planet.active_effects:
                    with Image.open(
                        f"resources/siege_fleets/the_great_host.png"
                    ) as fleet_icon:
                        background.paste(
                            fleet_icon,
                            (
                                int(planet.map_waypoints[0] - 25),
                                int(planet.map_waypoints[1] - 50),
                            ),
                            fleet_icon,
                        )
            background.save(fp=Maps.FileLocations.planets_map)

    def update_dss(self, dss: DSS) -> None:
        if dss and dss.flags == 1:
            with Image.open(
                fp=Maps.FileLocations.planets_map
            ) as background, Image.open("resources/DSS.png") as dss_icon:
                dss_coords = (
                    int(dss.planet.map_waypoints[0]) - 17,
                    int(dss.planet.map_waypoints[1]) - 130,
                )
                background.paste(dss_icon, dss_coords, dss_icon)
                background.save(fp=Maps.FileLocations.dss_map)
        else:
            with Image.open(fp=Maps.FileLocations.planets_map) as background:
                background.save(fp=Maps.FileLocations.dss_map)

    def draw_arrow(self, language_code: str, planet: Planet) -> None:
        with Image.open(
            fp=Maps.FileLocations.localized_map_path(language_code=language_code)
        ) as background:
            background_draw = ImageDraw.Draw(im=background)
            target_coords = planet.map_waypoints
            background_draw.line(
                (
                    target_coords[0] - 7,
                    target_coords[1] + 25,
                    target_coords[0] + 75,
                    target_coords[1] + 100,
                ),
                width=20,
            )
            background_draw.line(
                (
                    target_coords[0] + 7,
                    target_coords[1] + 25,
                    target_coords[0] - 75,
                    target_coords[1] + 100,
                ),
                width=20,
            )
            background_draw.line(
                (
                    target_coords[0],
                    target_coords[1] + 25,
                    target_coords[0],
                    target_coords[1] + 250,
                ),
                width=20,
            )
            background.save(fp=Maps.FileLocations.arrow_map)

    def localize_map(
        self,
        language_code_short: str,
        language_code_long: str,
        planets: Planets,
        active_planets: list[int],
        type_3_campaigns: list[Campaign],
        planet_names_json: dict,
    ) -> None:
        with Image.open(fp=Maps.FileLocations.dss_map) as background:
            self._write_names(
                background=background,
                language_code=language_code_long,
                planets=planets,
                active_planets=active_planets,
                type_3_campaigns=type_3_campaigns,
                planet_names_json=planet_names_json,
            )
            background.save(fp=f"resources/maps/{language_code_short}.webp")

    def _draw_ellipse(
        self,
        draw: ImageDraw.ImageDraw,
        coords: tuple,
        fill_colour: tuple,
        radius: int = 15,
    ) -> None:
        draw.ellipse(
            [
                (coords[0] - radius, coords[1] - radius),
                (coords[0] + radius, coords[1] + radius),
            ],
            fill=fill_colour,
        )

    def _write_names(
        self,
        background: Image.Image,
        language_code: str,
        planets: Planets,
        active_planets: list[int],
        type_3_campaigns: list[Campaign],
        planet_names_json: dict,
    ) -> None:
        font = ImageFont.truetype("resources/gww-font.ttf", 35)
        background_draw = ImageDraw.Draw(im=background)
        for index, planet in planets.items():
            if index in active_planets:
                if planet.dss_in_orbit:
                    border_colour = "deepskyblue"
                elif planet.event and planet.event.siege_fleet:
                    border_colour = faction_colours[planet.event.faction]
                elif planet.index in [c.planet.index for c in type_3_campaigns]:
                    border_colour = faction_colours[
                        [c for c in type_3_campaigns if c.planet.index == planet.index][
                            0
                        ].faction
                    ]
                else:
                    border_colour = "black"
                name_text = planet_names_json[str(index)]["names"][
                    language_code
                ].replace(" ", "\n")
                if (
                    (planet.event and planet.event.siege_fleet)
                    or planet.dss_in_orbit
                    or planet.index in [c.planet.index for c in type_3_campaigns]
                ):
                    xy = (planet.map_waypoints[0], planet.map_waypoints[1] - 50)
                else:
                    xy = planet.map_waypoints
                background_draw.multiline_text(
                    xy=xy,
                    text=name_text,
                    anchor="md",
                    font=font,
                    stroke_width=3,
                    stroke_fill=border_colour,
                    align="center",
                    spacing=-10,
                )
