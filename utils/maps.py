from cv2 import (
    circle,
    floodFill,
    FLOODFILL_FIXED_RANGE,
    FLOODFILL_MASK_ONLY,
    imread,
    imwrite,
    IMREAD_UNCHANGED,
    line,
    LINE_AA,
    merge,
    resize,
    split,
)
from data.lists import CUSTOM_COLOURS
from dataclasses import dataclass
from datetime import datetime, timedelta
from numpy import uint8, zeros
from PIL import Image, ImageDraw, ImageFont
from utils.api_wrapper.models import Assignment, Campaign, DSS, Planet
from utils.dataclasses import Factions, SpecialUnits
from utils.mixins import ReprMixin

DIM_FACTION_COLOURS: dict[str, tuple[int, int, int]] = {
    faction.full_name: tuple(int(colour / 2.5) for colour in faction.colour)
    for faction in Factions.all
}


class Maps:
    def __init__(self):
        self.latest_maps: dict[str, Maps.LatestMap] = {}
        self.TEXT_SIZE = 25

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
        planets_map: str = "resources/maps/planets_map.webp"
        icons_map: str = "resources/maps/icons_map.webp"
        arrow_map: str = "resources/maps/arrow_map.webp"

        def localized_map_path(language_code: str) -> str:
            return f"resources/maps/localized/{language_code}.webp"

    def update_base_map(
        self, planets: list[Planet], assignments: list[Assignment]
    ) -> None:
        self.update_sectors(planets=planets)
        self.update_waypoint_lines(planets=planets)
        self.update_assignment_tasks(assignments=assignments, planets=planets)
        self.update_planets(planets=planets)

    def update_sectors(self, planets: list[Planet]) -> None:
        sectors: dict[str, list[str]] = {}
        for planet in planets.values():
            faction_name = (
                planet.faction.full_name
                if not planet.event
                else planet.event.faction.full_name
            )
            if planet.sector not in sectors:
                sectors[planet.sector] = [faction_name]
            else:
                sectors[planet.sector].append(faction_name)
        enemy_sectors = {s: l for s, l in sectors.items() if set(l) != set(["Humans"])}
        sector_percentages = {
            sector: 1.5
            - (factions.count(max(factions, key=factions.count)) / len(factions))
            for sector, factions in enemy_sectors.items()
        }
        sector_factions = {
            s: max([i for i in f if i != "Humans"], key=f.count)
            for s, f in enemy_sectors.items()
        }
        sector_coords = {}
        for sector in enemy_sectors:
            sector_coords[sector] = [p for p in planets.values() if p.sector == sector][
                0
            ].map_waypoints
        background = imread(Maps.FileLocations.empty_map, IMREAD_UNCHANGED)
        if background.shape[2] == 4:
            alpha_channel = background[:, :, 3].copy()
            background_rgb = background[:, :, :3].copy()
        else:
            background_rgb = background.copy()
            alpha_channel = None

        for sector, coords in sector_coords.items():
            color = DIM_FACTION_COLOURS[sector_factions[sector]]
            percentage = sector_percentages[sector]
            bgr_color = (
                int(color[2] * percentage),
                int(color[1] * percentage),
                int(color[0] * percentage),
            )
            h, w = background.shape[:2]
            mask = zeros((h + 2, w + 2), uint8)
            floodFill(
                image=background_rgb,
                mask=mask,
                seedPoint=coords,
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

    def update_waypoint_lines(self, planets: dict[int, Planet]) -> None:
        background = imread(Maps.FileLocations.sector_map, IMREAD_UNCHANGED)
        for planet in planets.values():
            for waypoint in planet.waypoints:
                try:
                    way_planet = planets.get(waypoint)
                    if way_planet:
                        line(
                            img=background,
                            pt1=planet.map_waypoints,
                            pt2=way_planet.map_waypoints,
                            color=(255, 255, 255, 255),
                            thickness=2,
                        )
                except KeyError:
                    continue

        imwrite(Maps.FileLocations.waypoints_map, background)

    def update_assignment_tasks(
        self, assignments: list[Assignment], planets: dict[int, Planet]
    ) -> None:
        background = imread(Maps.FileLocations.waypoints_map, IMREAD_UNCHANGED)
        if assignments:
            for planet in (p for p in planets.values() if p.in_assignment):
                self._draw_ellipse(
                    image=background,
                    coords=planet.map_waypoints,
                    fill_colour=CUSTOM_COLOURS["MO"],
                    radius=12 if not planet.dss_in_orbit else 15,
                )

        imwrite(Maps.FileLocations.assignment_map, background)

    def update_planets(self, planets: dict[int, Planet]) -> None:
        background = imread(Maps.FileLocations.assignment_map, IMREAD_UNCHANGED)
        PLANET_RADIUS = 8
        for index, planet in planets.items():
            if planet.dss_in_orbit:
                self._draw_ellipse(
                    image=background,
                    coords=planet.map_waypoints,
                    fill_colour=CUSTOM_COLOURS["DSS"],
                    radius=12,
                )
            if index == 64:
                for i in range(PLANET_RADIUS, PLANET_RADIUS - 4, -1):
                    circle(
                        background,
                        planet.map_waypoints,
                        i,
                        (i * 25, i * 10, i * 25, 255),
                        -1,
                    )
                circle(
                    background,
                    planet.map_waypoints,
                    int(PLANET_RADIUS / 2),
                    (0, 0, 0, 255),
                    -1,
                )
            elif 1352 in (ae.id for ae in planet.active_effects):
                for i in range(PLANET_RADIUS, PLANET_RADIUS - 4, -1):
                    circle(
                        background,
                        planet.map_waypoints,
                        i,
                        (i * 10, i * 25, i * 25, 255),
                        -1,
                    )
                circle(
                    background,
                    planet.map_waypoints,
                    int(PLANET_RADIUS / 2),
                    (0, 0, 0, 255),
                    -1,
                )
            elif 1240 in (ae.id for ae in planet.active_effects):
                circle(
                    background,
                    planet.map_waypoints,
                    PLANET_RADIUS,
                    (0, 0, 255, 255),
                    -1,
                )
            elif [ae for ae in planet.active_effects if ae.id in (1241, 1252)] != []:
                continue
            else:
                colour = (
                    planet.faction.colour
                    if planet.active_campaign
                    else tuple(int(colour / 1.5) for colour in planet.faction.colour)
                )
                colour = (*colour[::-1], 255)
                circle(
                    background,
                    planet.map_waypoints,
                    8,
                    colour,
                    -1,
                )

        imwrite(Maps.FileLocations.planets_map, background)

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
        planets: dict[int, Planet],
        planet_names_json: dict,
    ) -> None:
        with Image.open(fp=Maps.FileLocations.planets_map) as background:
            self._write_names(
                background=background,
                language_code=language_code_long,
                planets=planets,
                planet_names_json=planet_names_json,
            )
            background.save(fp=f"resources/maps/localized/{language_code_short}.webp")

    def _write_names(
        self,
        background: Image.Image,
        language_code: str,
        planets: dict[int, Planet],
        planet_names_json: dict,
    ) -> None:
        font = ImageFont.truetype("resources/gww-font.ttf", self.TEXT_SIZE)
        background_draw = ImageDraw.Draw(im=background)
        for index, planet in planets.items():
            if planet.active_campaign:
                if planet.dss_in_orbit:
                    border_colour = "deepskyblue"
                else:
                    border_colour = "black"
                name_text = planet_names_json[str(index)]["names"][
                    language_code
                ].replace(" ", "\n")
                background_draw.multiline_text(
                    xy=planet.map_waypoints,
                    text=name_text,
                    anchor="md",
                    font=font,
                    stroke_width=2,
                    stroke_fill=border_colour,
                    align="center",
                    spacing=-10,
                )

    def paste_image(self, background, overlay, coords, x_offset=0, y_offset=0) -> None:
        x, y = (
            (coords[0] - int(overlay.shape[0] / 2)) + x_offset,
            (coords[1] - int(overlay.shape[1] / 2)) + y_offset,
        )
        x = max(x, 57)
        y = max(y, 57)
        b, g, r, a = split(overlay)
        overlay_rgb = merge((b, g, r))
        mask = a.astype(float) / 255.0
        mask = merge((mask, mask, mask))
        h, w = overlay.shape[:2]
        roi = background[y : y + h, x : x + w, :3].astype(float)
        blended = (overlay_rgb.astype(float) * mask + roi * (1 - mask)).astype(uint8)
        background[y : y + h, x : x + w, :3] = blended

    def add_icons(
        self,
        lang: str,
        long_code: str,
        planets: dict[int, Planet],
        dss: DSS,
    ):
        frac_planet_icon = imread(
            "resources/map_icons/fractured_planet.png", IMREAD_UNCHANGED
        )
        path = Maps.FileLocations.localized_map_path(language_code=lang)
        background = imread(path, IMREAD_UNCHANGED)
        for planet in planets.values():
            if planet.index == 0:
                se_icon = imread(
                    "resources/map_icons/super_earth.png", IMREAD_UNCHANGED
                )
                self.paste_image(background, se_icon, planet.map_waypoints)
            elif [ae for ae in planet.active_effects if ae.id in (1241, 1252)] != []:
                self.paste_image(
                    background,
                    frac_planet_icon,
                    planet.map_waypoints,
                    x_offset=-20,
                    y_offset=10,
                )
            loc_name = planet.names.get(long_code, str(planet.index))
            if planet.active_campaign or planet.homeworld:
                x_offset = 0
                for su in SpecialUnits.get_from_effects_list(planet.active_effects):
                    su_icon = imread(
                        f"resources/map_icons/{su[0].lower().replace(' ', '_')}_bordered.png",
                        IMREAD_UNCHANGED,
                    )
                    su_icon = resize(
                        su_icon,
                        (int(32 * (su_icon.shape[1] / su_icon.shape[0])), 32),
                    )
                    self.paste_image(
                        background,
                        su_icon,
                        planet.map_waypoints,
                        x_offset=35 + x_offset,
                        y_offset=-(20 + ((loc_name.count(" ") + 1) * self.TEXT_SIZE)),
                    )
                    x_offset += su_icon.shape[0]
            if dss and planet.dss_in_orbit:
                dss_icon = (
                    imread("resources/map_icons/dss_glow.png", IMREAD_UNCHANGED)
                    if dss.flags == 1
                    and not (
                        all([ta.status == 0 for ta in dss.tactical_actions])
                        and dss.move_timer_datetime
                        > datetime.now() + timedelta(days=30)
                    )
                    else imread(
                        "resources/map_icons/dss_glow_inactive.png", IMREAD_UNCHANGED
                    )
                )
                verti_diff = 20
                if planet.active_campaign:
                    verti_diff += 45
                    if loc_name.count(" ") > 0:
                        verti_diff += loc_name.count(" ") * (self.TEXT_SIZE - 5)
                dss_coords = (
                    int(dss.planet.map_waypoints[0]) - 17,
                    int(dss.planet.map_waypoints[1]) - verti_diff,
                )
                self.paste_image(background, dss_icon, dss_coords)
        imwrite(path, background)
