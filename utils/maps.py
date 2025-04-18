from asyncio import to_thread
from data.lists import faction_colours
from dataclasses import dataclass
from datetime import datetime
from math import cos, radians, sin
from PIL import Image, ImageDraw, ImageFont
from random import randint
from utils.data import DSS, Assignment, Campaign, Planet, Planets


class Maps:
    def __init__(self):
        self.dim_faction_colours = {
            faction: tuple(int(colour / 2.5) for colour in colours)
            for faction, colours in faction_colours.items()
        }
        self.faction_mapping = {
            1: "Humans",
            2: "Terminids",
            3: "Automaton",
            4: "Illuminate",
        }
        self.latest_maps: dict[str, Maps.LatestMap] = {}

    @dataclass
    class LatestMap:
        updated_at: datetime
        map_link: str

    @dataclass
    class FileLocations:
        empty_map = "resources/maps/empty_map.webp"
        sector_map = "resources/maps/sector_map.webp"
        waypoints_map = "resources/maps/waypoints_map.webp"
        assignment_map = "resources/maps/assignment_map.webp"
        dss_map = "resources/maps/dss_map.webp"
        planets_map = "resources/maps/planets_map.webp"
        arrow_map = "resources/maps/arrow_map.webp"

        def localized_map_path(language_code: str) -> str:
            return f"resources/maps/{language_code}.webp"

    async def update_base_map(
        self,
        planets: Planets,
        assignment: Assignment,
        campaigns: list[Campaign],
        dss: DSS,
    ):
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

    def update_sectors(self, planets: Planets):
        valid_planets = [
            planet
            for planet in planets.values()
            if not (planet.current_owner == "Humans" and not planet.event)
        ]
        sector_info = {
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
                    value=self.dim_faction_colours[info["faction"]],
                    thresh=25,
                )
            background.putalpha(alpha=alpha)
            background.save(fp=Maps.FileLocations.sector_map)

    def update_waypoint_lines(self, planets: Planets):
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
                    except:
                        continue
            background.save(fp=Maps.FileLocations.waypoints_map)

    def update_assignment_tasks(
        self,
        assignment: Assignment,
        planets: Planets,
        campaigns: list[Campaign] | list,
    ):
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
                            if (
                                planet.current_owner == "Humans"
                                and planet.event.faction
                                == self.faction_mapping[task.values[1]]
                            ):
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
                            if campaign.faction == self.faction_mapping[task.values[0]]:
                                self._draw_ellipse(
                                    draw=background_draw,
                                    coords=campaign.planet.map_waypoints,
                                    fill_colour=faction_colours["MO"],
                                )
        background.save(fp=Maps.FileLocations.assignment_map)

    def update_planets(self, planets: Planets, active_planets: list[int]):
        with Image.open(fp=Maps.FileLocations.assignment_map) as background:
            background_draw = ImageDraw.Draw(im=background)
            for index, planet in planets.items():
                coords = planet.map_waypoints
                if planet.dss_in_orbit:
                    self._draw_ellipse(
                        draw=background_draw,
                        coords=coords,
                        fill_colour=faction_colours["DSS"],
                        radius=17,
                    )
                if index == 64:
                    for i in range(12, 6, -1):
                        background_draw.ellipse(
                            xy=[
                                (coords[0] - i, coords[1] - i),
                                (coords[0] + i, coords[1] + i),
                            ],
                            fill=(i * 20, i * 5, i * 20),
                        )
                    background_draw.ellipse(
                        xy=[
                            (coords[0] - 7, coords[1] - 7),
                            (coords[0] + 7, coords[1] + 7),
                        ],
                        fill=(0, 0, 0),
                        outline=(200, 100, 255),
                    )
                elif 1240 in planet.active_effects:
                    background_draw.ellipse(
                        xy=[
                            (coords[0] - 10, coords[1] - 10),
                            (coords[0] + 10, coords[1] + 10),
                        ],
                        fill="red",
                    )
                elif set([1241, 1252]) & planet.active_effects:
                    planet_image = Image.new("RGBA", (2000, 2000), (0, 0, 0, 0))
                    planet_draw = ImageDraw.Draw(planet_image)
                    planet_draw.ellipse(
                        xy=[
                            (coords[0] - 10, coords[1] - 10),
                            (coords[0] + 10, coords[1] + 10),
                        ],
                        fill="red",
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
                            width=randint(3, 4),
                        )
                    background.paste(im=planet_image, mask=planet_image)
                    planet_image.close()
                else:
                    current_owner = planet.current_owner
                    background_draw.ellipse(
                        xy=[
                            (coords[0] - 10, coords[1] - 10),
                            (coords[0] + 10, coords[1] + 10),
                        ],
                        fill=(
                            faction_colours[current_owner]
                            if index in active_planets
                            else tuple(
                                int(colour / 1.5)
                                for colour in faction_colours[current_owner]
                            )
                        ),
                    )
            background.save(fp=Maps.FileLocations.planets_map)

    def update_dss(self, dss: DSS):
        if dss and dss != "Error":
            with Image.open(
                fp=Maps.FileLocations.planets_map
            ) as background, Image.open("resources/DSS.png") as dss_icon:
                dss_icon = dss_icon.convert("RGBA")
                dss_coords = (
                    int(dss.planet.map_waypoints[0]) - 17,
                    int(dss.planet.map_waypoints[1]) - 130,
                )
                dss_icon = background.paste(dss_icon, dss_coords, dss_icon)
                background.save(fp=Maps.FileLocations.dss_map)

    def draw_arrow(self, language_code: str, planet: Planet):
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
        dss: DSS,
        planet_names_json: dict,
    ):
        with Image.open(fp=Maps.FileLocations.dss_map) as background:
            self._write_names(
                background=background,
                language_code=language_code_long,
                planets=planets,
                active_planets=active_planets,
                dss=dss,
                planet_names_json=planet_names_json,
            )
            background.save(fp=f"resources/maps/{language_code_short}.webp")

    def _draw_ellipse(
        self,
        draw: ImageDraw.ImageDraw,
        coords: tuple,
        fill_colour: tuple,
        radius: int = 15,
    ):
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
        dss: DSS,
        planet_names_json: dict,
    ):
        font = ImageFont.truetype("gww-font.ttf", 35)
        background_draw = ImageDraw.Draw(im=background)
        for index, planet in planets.items():
            if index in active_planets:
                border_colour = "black"
                if dss and dss != "Error":
                    if index == dss.planet.index:
                        border_colour = "deepskyblue"
                name_text = planet_names_json[str(index)]["names"][
                    language_code
                ].replace(" ", "\n")
                background_draw.multiline_text(
                    xy=planet.map_waypoints,
                    text=name_text,
                    anchor="md",
                    font=font,
                    stroke_width=3,
                    stroke_fill=border_colour,
                    align="center",
                    spacing=-10,
                )
