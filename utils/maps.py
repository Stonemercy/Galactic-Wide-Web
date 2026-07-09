from math import hypot
from cv2 import (
    INTER_NEAREST,
    addWeighted,
    arrowedLine,
    circle,
    fillPoly,
    floodFill,
    FLOODFILL_FIXED_RANGE,
    FLOODFILL_MASK_ONLY,
    imread,
    imwrite,
    IMREAD_UNCHANGED,
    line,
    LINE_AA,
    merge,
    polylines,
    resize,
    split,
)
from data.lists import CUSTOM_COLOURS
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from numpy import (
    arctan2,
    array,
    clip,
    cos,
    dot,
    float32,
    linalg,
    full_like,
    newaxis,
    pi,
    sin,
    sqrt,
    uint8,
    where,
    zeros,
)
from numpy.random import randint, random_sample
from PIL import Image, ImageDraw, ImageFont
from utils.api_wrapper.models import Assignment, DSS, Planet
from utils.dataclasses import Factions, Faction
from utils.mixins import ReprMixin

DIM_FACTION_COLOURS: dict[str, tuple[int, int, int]] = {
    faction.full_name: tuple(int(colour / 2.5) for colour in faction.colour)
    for faction in Factions.all
}

VONOROI_COLOURS: dict[Faction, dict[str, tuple]] = {
    Factions.automaton: {"tint": (0, 0, 100), "lines": (0, 0, 175)},
    Factions.illuminate: {"tint": (40, 0, 15), "lines": (175, 60, 110)},
    Factions.terminids: {"tint": (20, 75, 95), "lines": (0, 150, 200)},
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
        _prefix: str = "resources/maps/"
        empty_map: str = _prefix + "empty_map.webp"
        sector_map: str = _prefix + "sector_map.webp"
        waypoints_map: str = _prefix + "waypoints_map.webp"
        assignment_map: str = _prefix + "assignment_map.webp"
        planets_map: str = _prefix + "planets_map.webp"
        icons_map: str = _prefix + "icons_map.webp"
        arrow_map: str = _prefix + "arrow_map.webp"

        def localized_map_path(language_code: str) -> str:
            return f"resources/maps/localized/{language_code}.webp"

    def update_base_map(
        self, planets: list[Planet], assignments: list[Assignment]
    ) -> None:
        self.update_sectors(planets=planets)
        self.update_waypoint_lines(planets=planets)
        self.update_assignment_tasks(assignments=assignments, planets=planets)
        self.update_planets(planets=planets)

    def update_sectors(self, planets: dict[int, Planet]) -> None:
        sectors: dict[str, list[Faction]] = {}
        for planet in planets.values():
            faction = planet.faction if not planet.event else planet.event.faction
            if planet.sector not in sectors:
                sectors[planet.sector] = [faction]
            else:
                sectors[planet.sector].append(faction)
        enemy_sectors = {
            s: set(l) for s, l in sectors.items() if set(l) != set(["Humans"])
        }
        sector_coords: dict[str, tuple[int, int]] = {}
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
            sector_faction = list(enemy_sectors[sector])
            if len(sector_faction) == 1:
                if sector_faction[0] == Factions.humans:
                    continue
                elif [
                    p
                    for p in planets.values()
                    if p.sector == sector and p.active_campaign
                ]:
                    bgr_color = DIM_FACTION_COLOURS[sector_faction[0].full_name]
                else:
                    bgr_color = tuple(
                        int(i / 2)
                        for i in DIM_FACTION_COLOURS[sector_faction[0].full_name]
                    )
            else:
                bgr_color = DIM_FACTION_COLOURS[sector_faction[1].full_name]
            bgr_color = tuple(int(i) for i in bgr_color[::-1])
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
            for n_index in planet.nearby:
                colour = planet.faction.colour
                if planet.event:
                    colour = planet.event.faction.colour
                near_planet = planets.get(n_index)
                if not near_planet or (near_planet.is_hidden and planet.is_hidden):
                    continue
                x1, y1 = planet.map_waypoints
                x2, y2 = near_planet.map_waypoints
                distance_div = 0.5
                with_attack_arrows = False
                if near_planet.is_hidden:
                    distance_div = 0.25
                elif planet.is_hidden:
                    distance_div = 0.75
                else:
                    if planet.event:
                        if near_planet.index in planet.defending_from:
                            distance_div = 0.01
                        else:
                            colour = planet.faction.colour
                    elif near_planet.event:
                        if planet.index in near_planet.defending_from:
                            distance_div = 0.99
                            with_attack_arrows = True
                        elif planet.faction == near_planet.faction:
                            colour = near_planet.faction.colour
                end_point = (
                    int(x1 + (x2 - x1) * distance_div),
                    int(y1 + (y2 - y1) * distance_div),
                )
                if with_attack_arrows:
                    self.draw_flow_arrows(
                        background=background,
                        pt1=planet.map_waypoints,
                        pt2=end_point,
                    )
                line(
                    img=background,
                    pt1=planet.map_waypoints,
                    pt2=end_point,
                    color=(*list(colour)[::-1], 255),
                    thickness=2,
                    lineType=LINE_AA,
                )

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
            planet_effect_ids = [ae.id for ae in planet.active_effects]
            if 1190 in planet_effect_ids or 1376 in planet_effect_ids:
                continue
            if any(aeid in (1373, 1374, 1375) for aeid in planet_effect_ids):
                # exostorm
                exostorm_icon = imread(
                    "resources/map_icons/exostorm_swirl.png", IMREAD_UNCHANGED
                )
                self.paste_image(background, exostorm_icon, planet.map_waypoints)
            if planet.dss_in_orbit:
                self._draw_ellipse(
                    image=background,
                    coords=planet.map_waypoints,
                    fill_colour=CUSTOM_COLOURS["DSS"],
                    radius=12,
                )
            if index == 64:
                # meridia
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
            elif 1352 in planet_effect_ids:
                # black hole
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
            elif 1240 in planet_effect_ids:
                # going to be destroyed
                circle(
                    background,
                    planet.map_waypoints,
                    PLANET_RADIUS,
                    (0, 0, 255, 255),
                    -1,
                )
            elif any([aeid in (1241, 1252) for aeid in planet_effect_ids]):
                # fractured planets
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
                    PLANET_RADIUS,
                    colour,
                    -1,
                )

        for planet in [
            p for p in planets.values() if 1376 in (e.id for e in p.active_effects)
        ]:
            self.draw_void(background, planet, planets)

        for planet in [
            p
            for p in planets.values()
            if 73 in (e.effect_type for e in p.active_effects)
        ]:
            self.draw_gloom(background, planet, planets)

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

    def draw_flow_arrows(self, background, pt1, pt2, spacing=15, size=10):
        x1, y1 = pt1
        x2, y2 = pt2
        length = hypot(x2 - x1, y2 - y1)
        if length < spacing:
            return
        dx, dy = (x2 - x1) / length, (y2 - y1) / length
        steps = int(length // spacing)
        for i in range(1, steps):
            cx = x1 + dx * spacing * i
            cy = y1 + dy * spacing * i
            tail = (round(cx - dx * size / 2), round(cy - dy * size / 2))
            tip = (round(cx + dx * size / 2), round(cy + dy * size / 2))
            arrowedLine(
                img=background,
                pt1=tail,
                pt2=tip,
                color=(255, 255, 255, 175),
                thickness=1,
                line_type=LINE_AA,
                tipLength=1,
            )

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
                background=background, language_code=language_code_long, planets=planets
            )
            background.save(fp=f"resources/maps/localized/{language_code_short}.webp")

    def _write_names(
        self, background: Image.Image, language_code: str, planets: dict[int, Planet]
    ) -> None:
        if language_code == "zh-Hant":
            font = ImageFont.truetype("resources/gww-font-zh-hant.ttf", self.TEXT_SIZE)
            font.set_variation_by_name("Medium")
        else:
            font = ImageFont.truetype("resources/gww-font.ttf", self.TEXT_SIZE)
        background_draw = ImageDraw.Draw(im=background)
        for planet in planets.values():
            if planet.active_campaign and not planet.is_hidden:
                if planet.dss_in_orbit:
                    border_colour = "deepskyblue"
                else:
                    border_colour = "black"
                background_draw.multiline_text(
                    xy=planet.map_waypoints,
                    text=planet.names.get(language_code, planet.name).replace(
                        " ", "\n"
                    ),
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
            planet_effect_ids = [ae.id for ae in planet.active_effects]
            if 1376 in planet_effect_ids:
                continue
            if planet.index == 0:
                se_icon = imread(
                    "resources/map_icons/super_earth.png", IMREAD_UNCHANGED
                )
                self.paste_image(background, se_icon, planet.map_waypoints)
            elif any([aeid in (1241, 1252) for aeid in planet_effect_ids]):
                self.paste_image(
                    background,
                    frac_planet_icon,
                    planet.map_waypoints,
                    x_offset=-20,
                    y_offset=10,
                )
            loc_name = planet.names.get(long_code, planet.name)
            if (
                planet.faction != Factions.humans or planet.active_campaign
            ) and not planet.is_hidden:
                x_offset = 0
                for sf in planet.subfactions:
                    sf_icon = imread(
                        f"resources/map_icons/{sf.eng_name.lower().replace(' ', '_')}_bordered.png",
                        IMREAD_UNCHANGED,
                    )
                    if sf_icon is not None:
                        self.paste_image(
                            background,
                            sf_icon,
                            planet.map_waypoints,
                            x_offset=(35 if planet.active_campaign else 10) + x_offset,
                            y_offset=-(
                                20
                                + (
                                    (loc_name.count(" ") + 1)
                                    * (self.TEXT_SIZE if planet.active_campaign else 0)
                                )
                            ),
                        )
                        x_offset += sf_icon.shape[0]
            if dss and planet.dss_in_orbit:
                dss_icon = (
                    imread("resources/map_icons/dss_glow.png", IMREAD_UNCHANGED)
                    if dss.flags == 1
                    and not (
                        all([ta.status == 0 for ta in dss.tactical_actions])
                        and dss.move_timer_datetime
                        > datetime.now(tz=timezone.utc) + timedelta(days=30)
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

    def get_voronoi_cell_polygon(
        self, focal, others, bounds=(-2000, 2000, -2000, 2000)
    ):
        xmin, xmax, ymin, ymax = bounds
        polygon = array(
            [
                [xmin, ymin],
                [xmax, ymin],
                [xmax, ymax],
                [xmin, ymax],
            ],
            dtype=float,
        )

        for other in others:
            mid = (focal + other) / 2.0
            normal = focal - other
            polygon = self.clip_polygon_by_halfplane(polygon, mid, normal)
            if len(polygon) == 0:
                break

        return polygon

    def clip_polygon_by_halfplane(self, polygon, point_on_plane, normal):
        if len(polygon) == 0:
            return polygon

        result = []
        n = len(polygon)

        def inside(p):
            return dot(p - point_on_plane, normal) >= 0

        def intersect(a, b):
            da = dot(a - point_on_plane, normal)
            db = dot(b - point_on_plane, normal)
            t = da / (da - db)
            return a + t * (b - a)

        for i in range(n):
            a = polygon[i]
            b = polygon[(i + 1) % n]
            a_in = inside(a)
            b_in = inside(b)

            if a_in:
                result.append(a)
                if not b_in:
                    result.append(intersect(a, b))
            elif b_in:
                result.append(intersect(a, b))

        return array(result)

    def clip_polygon_by_circle(self, polygon, center, radius):
        if len(polygon) == 0:
            return polygon

        result = []
        n = len(polygon)
        tol = 1.0

        def inside(p):
            return linalg.norm(p - center) <= radius

        def on_circle(p):
            return abs(linalg.norm(p - center) - radius) <= tol

        def intersect(a, b):
            d = b - a
            f = a - center
            qa = dot(d, d)
            qb = 2 * dot(f, d)
            qc = dot(f, f) - radius**2
            disc = qb**2 - 4 * qa * qc
            if disc < 0:
                return a
            disc = sqrt(disc)
            t1 = (-qb - disc) / (2 * qa)
            t2 = (-qb + disc) / (2 * qa)
            for t in (t1, t2):
                if 0 <= t <= 1:
                    return a + t * d
            return a

        for i in range(n):
            a = polygon[i]
            b = polygon[(i + 1) % n]
            a_in = inside(a)
            b_in = inside(b)

            if a_in:
                result.append(a)
                if not b_in:
                    result.append(intersect(a, b))
            elif b_in:
                result.append(intersect(a, b))

        if len(result) == 0:
            return array([])

        final = []
        for i in range(len(result)):
            a = result[i]
            b = result[(i + 1) % len(result)]
            final.append(a)
            if on_circle(a) and on_circle(b):
                angle_a = arctan2(a[1] - center[1], a[0] - center[0])
                angle_b = arctan2(b[1] - center[1], b[0] - center[0])
                diff = (angle_b - angle_a + pi) % (2 * pi) - pi
                for step in range(1, 20):
                    t = step / 20
                    angle = angle_a + diff * t
                    final.append(center + radius * array([cos(angle), sin(angle)]))

        return array(final)

    def draw_voronoi_tint(
        self,
        background,
        focal_planet,
        nearby_planets,
        background_weight: float,
        tint_colour: tuple[int, int, int],
        tint_weight: float,
        with_lines: bool = True,
        line_colour: tuple[int, int, int] = None,
        with_static: bool = False,
        with_stars: bool = False,
    ):
        cell_polygon = self.get_voronoi_cell_polygon(focal_planet, nearby_planets)
        cell_polygon = self.clip_polygon_by_circle(
            cell_polygon, array((1000, 1000), dtype=float), 1000
        )
        if len(cell_polygon) == 0:
            return

        cell_px = cell_polygon.astype(int)
        cell_px = clip(cell_px, 0, 2000 - 1)

        mask = zeros((2000, 2000), dtype=uint8)
        fillPoly(mask, [cell_px], 255)

        tint_colour = (*tint_colour, 255)
        tint = full_like(background, tint_colour)
        tinted = addWeighted(background, background_weight, tint, tint_weight, 0)

        background[:] = where(mask[:, :, newaxis] == 255, tinted, background)
        if with_lines:
            polylines(
                background,
                [cell_px],
                isClosed=True,
                color=(*line_colour, 150),
                thickness=2,
            )

        if with_static:
            cell_pixels = where(mask == 255)
            if len(cell_pixels[0]) > 0:
                intensity = int(30 * tint_weight)
                if intensity > 0:
                    grain_size = 2
                    small_noise = randint(
                        -intensity,
                        intensity + 1,
                        size=(2000 // grain_size, 2000 // grain_size),
                    )
                    noise_full = resize(
                        small_noise.astype(float32),
                        (2000, 2000),
                        interpolation=INTER_NEAREST,
                    ).astype(int)
                    noise = noise_full[cell_pixels]
                    if with_stars:
                        star_chance = 0.0015
                        star_mask = random_sample(len(cell_pixels[0])) < star_chance
                    for c in range(3):
                        ch = background[:, :, c]
                        vals = ch[cell_pixels].astype(int)
                        reflected = where(
                            vals + noise < 0,
                            -noise,
                            where(vals + noise > 255, -noise, noise),
                        )
                        new_vals = clip(vals + reflected, 0, 255).astype(uint8)
                        if with_stars:
                            new_vals[star_mask] = 255
                        ch[cell_pixels] = new_vals
                        background[:, :, c] = ch

    def draw_void(self, background, planet: Planet, planets: dict[int, Planet]):
        focal_planet = array(planet.map_waypoints)
        nearby_planets = array(
            [p.map_waypoints for p in planets.values() if p != planet], dtype=float
        )

        self.draw_voronoi_tint(
            background,
            focal_planet,
            nearby_planets,
            0.05,
            VONOROI_COLOURS[Factions.illuminate]["tint"],
            0.7,
            line_colour=VONOROI_COLOURS[Factions.illuminate]["lines"],
            with_static=True,
            with_stars=True,
        )

    def draw_gloom(self, background, planet: Planet, planets: dict[int, Planet]):
        focal_planet = array(planet.map_waypoints)
        nearby_planets = array(
            [p.map_waypoints for p in planets.values() if p != planet], dtype=float
        )
        gloom_effect = next(
            (gwe for gwe in planet.active_effects if gwe.effect_type == 73), None
        )

        effect_percent = gloom_effect.percent / 100
        if planet.active_campaign:
            effect_percent -= 0.1
        self.draw_voronoi_tint(
            background,
            focal_planet,
            nearby_planets,
            clip(0.25 + (1 - effect_percent) / 0.25 * 0.6, 0.25, 0.75),
            VONOROI_COLOURS[Factions.terminids]["tint"],
            effect_percent,
            with_lines=False,
            with_static=True,
        )
