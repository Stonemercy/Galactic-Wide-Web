from math import cos, radians, sin
from random import randint
from data.lists import faction_colours
from datetime import datetime
from disnake import Colour, Embed, File, TextChannel
from PIL import Image, ImageDraw, ImageFont
from utils.data import Data


class Maps:
    """A class for creating Maps"""

    def __init__(
        self,
        data: Data,
        waste_bin_channel: TextChannel,
        planet_names_json: dict,
        languages_json_list: list[dict],
        target_planet: int = None,
    ):
        """Creates a base map

        Args:
            data (Data): The Data to use for the Maps
            waste_bin_channel (TextChannel): The channel where maps are uploaded to
            planet_names_json (dict): The JSON for planet name translation
            languages_json_list (list[dict]): A list of JSON for each language the Maps are requested in
            target_planet (int, optional): The planet index if the map is being used in the `/planet` command. Defaults to None.
        """
        self.data = data
        self.waste_bin_channel = waste_bin_channel
        self.planet_names_json = planet_names_json
        self.languages_json_list = languages_json_list
        self.arrow_needed = target_planet != None
        self.target_planet = target_planet
        self.dim_faction_colours = {
            faction: tuple(int(colour / 2.5) for colour in colours)
            for faction, colours in faction_colours.items()
        }
        self.embeds = {
            language["code"]: Embed(colour=Colour.dark_embed())
            for language in languages_json_list
        }
        self.planet_coordinates = {
            planet.index: (
                (planet.position["x"] * 1000) + 1000,
                ((planet.position["y"] * -1) * 1000) + 1000,
            )
            for planet in data.planets.values()
        }
        self.available_planets = {campaign.planet.index for campaign in data.campaigns}
        self.sector_info = {
            planet.sector: {
                "coords": self.planet_coordinates[planet.index],
                "faction": [],
            }
            for planet in self.data.planets.values()
            if not (planet.current_owner == "Humans" and not planet.event)
        }
        self._generate_base_map()

    def _generate_base_map(self):
        """Generates the base map"""
        with Image.open(fp="resources/map.webp") as background:
            background = self._fill_sectors(background=background)
            self._draw_waypoint_lines(background=background)
            if self.data.assignment:
                self._draw_tasks(background=background)
            if self.data.dss and self.data.dss != "Error":
                background_draw = ImageDraw.Draw(im=background)
                self._draw_ellipse(
                    draw=background_draw,
                    coords=self.planet_coordinates[self.data.dss.planet.index],
                    fill_colour=faction_colours["DSS"],
                    radius=17,
                )
            self._draw_planets(background=background)
            self._draw_cracks(background=background)
            if self.data.dss and self.data.dss != "Error":
                self._add_dss_icon(background=background)
            if self.arrow_needed:
                self._draw_arrow(background=background)
            background.save(fp="resources/base_map.webp")

    def _fill_sectors(self, background: Image.Image):
        """Fills in sectors based on faction presence

        Args:
            background (Image.Image): The map to edit
        """
        for planet in self.data.planets.values():
            if planet.current_owner == "Humans" and not planet.event:
                continue
            faction = planet.event.faction if planet.event else planet.current_owner
            self.sector_info[planet.sector]["faction"].append(faction)
        alpha = background.getchannel(channel="A")
        background = background.convert(mode="RGB")
        for info in self.sector_info.values():
            info["faction"] = max(set(info["faction"]), key=info["faction"].count)
            ImageDraw.floodfill(
                image=background,
                xy=info["coords"],
                value=self.dim_faction_colours[info["faction"]],
                thresh=25,
            )
        background.putalpha(alpha=alpha)
        return background

    def _draw_waypoint_lines(self, background: Image.Image):
        """Draws the waypoints for each active planet

        Args:
            background (Image.Image): The map to edit
        """
        draw_on_background_with_sectors = ImageDraw.Draw(im=background)
        for index, coords in self.planet_coordinates.items():
            for waypoint in self.data.planets[index].waypoints:
                try:
                    waypoint_coords = self.planet_coordinates[waypoint]
                    draw_on_background_with_sectors.line(
                        xy=(
                            waypoint_coords[0],
                            waypoint_coords[1],
                            coords[0],
                            coords[1],
                        ),
                        width=2,
                    )
                except:
                    continue

    def _draw_tasks(self, background: Image.Image):
        """Draws tasks on the map by circling planets

        Args:
            background (Image.Image): The map to edit
        """
        faction_mapping = {
            1: "Humans",
            2: "Terminids",
            3: "Automaton",
            4: "Illuminate",
        }
        background_draw = ImageDraw.Draw(im=background)
        for task in self.data.assignment.tasks:
            if task.type in (11, 13):
                self._draw_ellipse(
                    draw=background_draw,
                    coords=self.planet_coordinates[task.values[2]],
                    fill_colour=faction_colours["MO"],
                )
            elif task.type == 12 and self.data.planet_events:
                for planet in self.data.planet_events:
                    if (
                        planet.current_owner == "Humans"
                        and planet.event.faction == faction_mapping[task.values[1]]
                    ):
                        self._draw_ellipse(
                            draw=background_draw,
                            coords=self.planet_coordinates[planet.index],
                            fill_colour=faction_colours["MO"],
                        )
            elif task.type == 2:
                self._draw_ellipse(
                    draw=background_draw,
                    coords=self.planet_coordinates[task.values[8]],
                    fill_colour=faction_colours["MO"],
                )
            elif task.type == 3 and task.progress != 1:
                for campaign in self.data.campaigns:
                    if campaign.faction == faction_mapping[task.values[0]]:
                        self._draw_ellipse(
                            draw=background_draw,
                            coords=self.planet_coordinates[campaign.planet.index],
                            fill_colour=faction_colours["MO"],
                        )

    def _draw_ellipse(
        self,
        draw: ImageDraw.ImageDraw,
        coords: tuple,
        fill_colour: tuple,
        radius: int = 15,
    ):
        """Draw an ellipse at a coordinate

        Args:
            draw (ImageDraw.ImageDraw): The ImageDraw object to use
            coords (tuple): Where to draw the ellipse
            fill_colour (tuple): What colour to use
            radius (int, optional): The radius of the ellipse. Defaults to 15.
        """
        draw.ellipse(
            [
                (coords[0] - radius, coords[1] - radius),
                (coords[0] + radius, coords[1] + radius),
            ],
            fill=fill_colour,
        )

    def _draw_planets(self, background: Image.Image):
        """Draws circles where planets should be based on the current owner

        Modifications:
            Meridia - Made to look like the wormhole
            Planets with 1240 active effect - Coloured red
            Planets with 1241 or 1252 active effect - Coloured red and cracked

        Args:
            background (Image.Image): The map to edit
        """
        background_draw = ImageDraw.Draw(im=background)
        for index, coords in self.planet_coordinates.items():
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
            elif set([1240, 1241, 1252]) & set(self.data.planets[index].active_effects):
                background_draw.ellipse(
                    xy=[
                        (coords[0] - 10, coords[1] - 10),
                        (coords[0] + 10, coords[1] + 10),
                    ],
                    fill="red",
                )
            else:
                current_owner = self.data.planets[index].current_owner
                background_draw.ellipse(
                    xy=[
                        (coords[0] - 10, coords[1] - 10),
                        (coords[0] + 10, coords[1] + 10),
                    ],
                    fill=(
                        faction_colours[current_owner]
                        if index in self.available_planets
                        else tuple(
                            int(colour / 1.5)
                            for colour in faction_colours[current_owner]
                        )
                    ),
                )

    def _draw_cracks(self, background: Image.Image):
        """Draws cracks on planets affected with effect 1241 or 1252

        Args:
            background (Image.Image): The map to edit
        """
        draw = ImageDraw.Draw(background)
        affected_planets = [
            planet
            for planet in self.data.planets.values()
            if set([1241, 1252]) & set(planet.active_effects)
        ]
        radius = 11
        for planet in affected_planets:
            cx, cy = self.planet_coordinates[planet.index]
            angles = []
            while len(angles) < 7:
                candidate = randint(0, 360)
                if all(abs(candidate - a) >= 30 for a in angles):
                    angles.append(candidate)
            crack_colour = (
                self.dim_faction_colours[self.sector_info[planet.sector]["faction"]]
                if self.sector_info.get(planet.sector, {"faction": "Humans"})["faction"]
                != "Humans"
                else "black"
            )
            for start_angle in angles:
                step_size = radius * 1.2
                new_x = cx + int(step_size * cos(radians(start_angle)))
                new_y = cy + int(step_size * sin(radians(start_angle)))
                draw.line(
                    [(cx, cy), (new_x, new_y)], fill=crack_colour, width=randint(3, 4)
                )

    def _add_dss_icon(self, background: Image.Image):
        """Adds the DSS icon above the planet it's orbiting

        Args:
            background (Image.Image): The map to edit
        """
        dss_icon = Image.open("resources/DSS.png")
        dss_icon = dss_icon.convert("RGBA")
        dss_coords = (
            int(self.planet_coordinates[self.data.dss.planet.index][0]) - 17,
            int(self.planet_coordinates[self.data.dss.planet.index][1]) - 130,
        )
        dss_icon = background.paste(dss_icon, dss_coords, dss_icon)

    def _draw_arrow(self, background: Image.Image, width: int = 20):
        """Draw an arrow below a planet

        Args:
            background (Image.Image): The map to edit
            width (int, optional): Scales the size of the arrow. Defaults to 20.
        """
        background_draw = ImageDraw.Draw(im=background)
        target_coords = self.planet_coordinates[self.target_planet]
        background_draw.line(
            (
                target_coords[0] - 7,
                target_coords[1] + 25,
                target_coords[0] + 75,
                target_coords[1] + 100,
            ),
            width=width,
        )
        background_draw.line(
            (
                target_coords[0] + 7,
                target_coords[1] + 25,
                target_coords[0] - 75,
                target_coords[1] + 100,
            ),
            width=width,
        )
        background_draw.line(
            (
                target_coords[0],
                target_coords[1] + 25,
                target_coords[0],
                target_coords[1] + 250,
            ),
            width=width,
        )

    async def localize(self):
        """Localizes the base map for each language in `self.languages_json_list`, sends it to `self.waste_bin_channel` and adds it to the related embed"""
        for language_json in self.languages_json_list:
            language_code = language_json["code"]
            with Image.open(fp="resources/base_map.webp") as map:
                self._write_names(
                    background=map,
                    language_code=language_json["code_long"],
                )
                map.save(fp=f"resources/{language_code}.webp")
                message = await self.waste_bin_channel.send(
                    file=File(fp=f"resources/{language_code}.webp")
                )
                self.embeds[language_code].set_image(url=message.attachments[0].url)
                self.embeds[language_code].add_field(
                    name=f"Updated",
                    value=f"<t:{int(datetime.now().timestamp())}:R>",
                )

    def _write_names(self, background: Image.Image, language_code: str):
        """Writes the names of active planets in a specific language

        Args:
            background (Image.Image): The map to edit
            language_code (str): The language to use
        """
        font = ImageFont.truetype("gww-font.ttf", 35)
        background_draw = ImageDraw.Draw(im=background)
        for index, coords in self.planet_coordinates.items():
            if index in self.available_planets:
                border_colour = "black"
                if self.data.dss and self.data.dss != "Error":
                    if index == self.data.dss.planet.index:
                        border_colour = "deepskyblue"
                self._draw_planet_name(
                    background_draw=background_draw,
                    planet_name=self.planet_names_json[str(index)]["names"][
                        language_code
                    ],
                    coords=coords,
                    font=font,
                    border_colour=border_colour,
                )

    def _draw_planet_name(
        self,
        background_draw: ImageDraw.ImageDraw,
        planet_name: str,
        coords: tuple,
        font: ImageFont.FreeTypeFont,
        border_colour: str,
    ):
        """Draws a planet name at the given coordinates

        Args:
            background_draw (ImageDraw.ImageDraw): The map to edit
            planet_name (str): The planet name
            coords (tuple): The coords to write at
            font (ImageFont.FreeTypeFont): The font to use
            border_colour (str): The colour the font's border should be.
        """
        name_text = planet_name.replace(" ", "\n")
        background_draw.multiline_text(
            xy=coords,
            text=name_text,
            anchor="md",
            font=font,
            stroke_width=3,
            stroke_fill=border_colour,
            align="center",
            spacing=-10,
        )
