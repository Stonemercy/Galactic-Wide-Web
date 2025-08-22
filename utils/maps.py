from cv2 import (
    FLOODFILL_FIXED_RANGE,
    FLOODFILL_MASK_ONLY,
    IMREAD_UNCHANGED,
    LINE_AA,
    circle,
    floodFill,
    imread,
    imwrite,
    line,
    merge,
    resize,
    split,
)
from numpy import uint8, zeros
from data.lists import SpecialUnits, faction_colours
from dataclasses import dataclass
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from utils.data import DSS, Assignment, Campaign, Planet, Planets
from utils.mixins import ReprMixin

DIM_FACTION_COLOURS: dict[str, tuple[int, int, int]] = {
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

    def update_base_map(
        self,
        planets: Planets,
        assignments: list[Assignment],
        campaigns: list[Campaign],
        dss: DSS,
        sector_names: dict,
    ) -> None:
        self.update_sectors(planets=planets)
        self.update_waypoint_lines(planets=planets)
        self.update_assignment_tasks(
            assignments=assignments,
            planets=planets,
            campaigns=campaigns,
            sector_names=sector_names,
        )
        self.update_planets(
            planets=planets,
            active_planets=[campaign.planet.index for campaign in campaigns],
        )
        self.update_dss(dss=dss, type_3_campaigns=[c for c in campaigns if c.type == 3])

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
        background = imread(Maps.FileLocations.empty_map, IMREAD_UNCHANGED)
        if background.shape[2] == 4:
            alpha_channel = background[:, :, 3].copy()
            background_rgb = background[:, :, :3].copy()
        else:
            background_rgb = background.copy()
            alpha_channel = None

        for info in sector_info.values():
            info["faction"] = max(set(info["faction"]), key=info["faction"].count)
            color = DIM_FACTION_COLOURS[info["faction"]]
            bgr_color = (color[2], color[1], color[0])
            h, w = background.shape[:2]
            mask = zeros((h + 2, w + 2), uint8)
            floodFill(
                image=background_rgb,
                mask=mask,
                seedPoint=info["coords"],
                newVal=bgr_color,
                loDiff=(50, 50, 50),
                upDiff=(50, 50, 50),
                flags=FLOODFILL_FIXED_RANGE | FLOODFILL_MASK_ONLY ^ FLOODFILL_MASK_ONLY,
            )
        if alpha_channel is not None:
            background = merge(
                [
                    background_rgb[:, :, 0],
                    background_rgb[:, :, 1],
                    background_rgb[:, :, 2],
                    alpha_channel,
                ]
            )
        else:
            background = background_rgb
        imwrite(Maps.FileLocations.sector_map, background)

    def update_waypoint_lines(self, planets: Planets) -> None:
        background = imread(Maps.FileLocations.sector_map, IMREAD_UNCHANGED)
        for planet in planets.values():
            for waypoint in planet.waypoints:
                try:
                    line(
                        img=background,
                        pt1=planet.map_waypoints,
                        pt2=planets[waypoint].map_waypoints,
                        color=(255, 255, 255, 255),
                        thickness=2,
                    )
                except KeyError:
                    continue

        imwrite(Maps.FileLocations.waypoints_map, background)

    def update_assignment_tasks(
        self,
        assignments: list[Assignment],
        planets: Planets,
        campaigns: list[Campaign] | list,
        sector_names: dict,
    ) -> None:
        background = imread(Maps.FileLocations.waypoints_map, IMREAD_UNCHANGED)
        if assignments:
            for assignment in assignments:
                for task in assignment.tasks:
                    if task.progress_perc == 1:
                        continue
                    if task.type in (11, 13):
                        self._draw_ellipse(
                            image=background,
                            coords=planets[task.planet_index].map_waypoints,
                            fill_colour=faction_colours["MO"],
                            radius=12,
                        )
                    elif task.type == 12 and (
                        planet_events := [
                            planet for planet in planets.values() if planet.event
                        ]
                    ):
                        for planet in planet_events:
                            if planet.event.faction == task.faction:
                                self._draw_ellipse(
                                    image=background,
                                    coords=planet.map_waypoints,
                                    fill_colour=faction_colours["MO"],
                                    radius=12,
                                )
                    elif task.type == 2:
                        if task.sector_index:
                            sector_name: str = sector_names[task.sector_index]
                            planets_in_sector = [
                                p
                                for p in planets.values()
                                if p.sector.lower() == sector_name.lower()
                            ]
                            for planet in planets_in_sector:
                                self._draw_ellipse(
                                    image=background,
                                    coords=planet.map_waypoints,
                                    fill_colour=faction_colours["MO"],
                                    radius=12,
                                )
                        elif task.planet_index:
                            self._draw_ellipse(
                                image=background,
                                coords=planets[task.planet_index].map_waypoints,
                                fill_colour=faction_colours["MO"],
                                radius=12,
                            )
                        elif task.faction:
                            for planet in [
                                c.planet
                                for c in campaigns
                                if c.planet.current_owner == task.faction
                            ]:
                                self._draw_ellipse(
                                    image=background,
                                    coords=planet.map_waypoints,
                                    fill_colour=faction_colours["MO"],
                                    radius=12,
                                )
                    elif task.type == 3 and task.progress != 1:
                        for campaign in campaigns:
                            if campaign.faction == task.faction:
                                self._draw_ellipse(
                                    image=background,
                                    coords=campaign.planet.map_waypoints,
                                    fill_colour=faction_colours["MO"],
                                    radius=12,
                                )
        imwrite(Maps.FileLocations.assignment_map, background)

    def update_planets(self, planets: Planets, active_planets: list[int]) -> None:
        background = imread(Maps.FileLocations.assignment_map, IMREAD_UNCHANGED)
        PLANET_RADIUS = 8
        for index, planet in planets.items():
            if planet.dss_in_orbit:
                self._draw_ellipse(
                    image=background,
                    coords=planet.map_waypoints,
                    fill_colour=faction_colours["DSS"],
                    radius=12,
                )
            if index == 64:
                for i in range(PLANET_RADIUS, PLANET_RADIUS - 6, -1):
                    circle(
                        background,
                        planet.map_waypoints,
                        i,
                        (i * 20, i * 5, i * 20, 255),
                        -1,
                    )
                circle(
                    background,
                    planet.map_waypoints,
                    int(PLANET_RADIUS / 2),
                    (0, 0, 0, 255),
                    -1,
                )
            elif planet.index == 0:
                se_icon = imread("resources/super_earth.png", IMREAD_UNCHANGED)
                self.paste_image(background, se_icon, planet.map_waypoints)
            elif 1240 in [ae.id for ae in planet.active_effects]:
                circle(
                    background,
                    planet.map_waypoints,
                    PLANET_RADIUS,
                    (0, 0, 255, 255),
                    -1,
                )
            elif 1241 in [ae.id for ae in planet.active_effects] or 1252 in [
                ae.id for ae in planet.active_effects
            ]:
                frac_planet_icon = imread(
                    "resources/fractured_planet.png", IMREAD_UNCHANGED
                )
                self.paste_image(
                    background,
                    frac_planet_icon,
                    planet.map_waypoints,
                    x_offset=-20,
                    y_offset=10,
                )
            else:
                colour = (
                    faction_colours[planet.current_owner]
                    if index in active_planets
                    else tuple(
                        int(colour / 1.5)
                        for colour in faction_colours[planet.current_owner]
                    )
                )
                colour = (*colour[::-1], 255)
                circle(
                    background,
                    planet.map_waypoints,
                    8,
                    colour,
                    -1,
                )
            offset = 0
            if index in active_planets:
                for su in SpecialUnits.get_from_effects_list(planet.active_effects):
                    su_icon = imread(
                        f"resources/Emojis/Planet Effects/{su[0].title()}.png",
                        IMREAD_UNCHANGED,
                    )
                    su_icon = resize(su_icon, (32, 32))
                    self.paste_image(
                        background,
                        su_icon,
                        planet.map_waypoints,
                        x_offset=20 + offset,
                        y_offset=-20,
                    )
                    offset += 32
        imwrite(Maps.FileLocations.planets_map, background)

    def update_dss(self, dss: DSS, type_3_campaigns: list[Campaign]) -> None:
        background = imread(Maps.FileLocations.planets_map, IMREAD_UNCHANGED)
        if dss and dss.flags == 1:
            dss_icon = imread("resources/DSS.png", IMREAD_UNCHANGED)
            verti_diff = 70
            if dss.planet.index in [c.planet.index for c in type_3_campaigns]:
                verti_diff += 50
            dss_coords = (
                int(dss.planet.map_waypoints[0]) - 17,
                int(dss.planet.map_waypoints[1]) - verti_diff,
            )
            self.paste_image(background, dss_icon, dss_coords)
        imwrite(Maps.FileLocations.dss_map, background)

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

    def _draw_ellipse(self, image, coords, fill_colour, radius=15):
        bgr_color = (*fill_colour[::-1], 255)
        circle(image, coords, radius, bgr_color, -1, LINE_AA)

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

    def _write_names(
        self,
        background: Image.Image,
        language_code: str,
        planets: Planets,
        active_planets: list[int],
        type_3_campaigns: list[Campaign],
        planet_names_json: dict,
    ) -> None:
        font = ImageFont.truetype("resources/gww-font.ttf", 25)
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
                if (planet.event and planet.event.siege_fleet) or planet.index in [
                    c.planet.index for c in type_3_campaigns
                ]:
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

    def paste_image(self, background, overlay, coords, x_offset=0, y_offset=0) -> None:
        x, y = (
            (coords[0] - int(overlay.shape[0] / 2)) + x_offset,
            (coords[1] - int(overlay.shape[1] / 2)) + y_offset,
        )
        b, g, r, a = split(overlay)
        overlay_rgb = merge((b, g, r))
        mask = a.astype(float) / 255.0
        mask = merge((mask, mask, mask))
        h, w = overlay.shape[:2]
        roi = background[y : y + h, x : x + w, :3].astype(float)
        blended = (overlay_rgb.astype(float) * mask + roi * (1 - mask)).astype(uint8)
        background[y : y + h, x : x + w, :3] = blended
