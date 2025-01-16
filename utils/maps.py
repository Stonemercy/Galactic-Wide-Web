from data.lists import faction_colours
from datetime import datetime
from disnake import Colour, Embed, File, TextChannel
from PIL import Image, ImageDraw, ImageFont
from utils.data import Data, Tasks


class Maps:
    def __init__(
        self,
        data: Data,
        waste_bin_channel: TextChannel,
        planet_names_json: dict,
        languages_json_list: list[dict],
        target_planet: int = None,
    ):
        self.data = data
        self.waste_bin_channel = waste_bin_channel
        self.planet_names_json = planet_names_json
        self.languages_json_list = languages_json_list
        self.arrow_needed = target_planet != None
        self.target_planet = target_planet
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
        self._generate_base_map()

    def _generate_base_map(self):
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
                    radius=22,
                )
            self._draw_planets(background=background)
            if self.data.dss and self.data.dss != "Error":
                self._add_dss_icon(background=background)
            if self.arrow_needed:
                self._draw_arrow(background=background)
            background.save(fp="resources/base_map.webp")

    def _fill_sectors(self, background: Image.Image):
        sector_info = {}
        dim_faction_colour = {
            faction: tuple(int(colour / 3) for colour in colours)
            for faction, colours in faction_colours.items()
        }
        for planet in self.data.planets.values():
            if planet.current_owner == "Humans" and not planet.event:
                continue
            faction = planet.current_owner if not planet.event else planet.event.faction
            if planet.sector not in sector_info:
                sector_info[planet.sector] = {
                    "coords": self.planet_coordinates[planet.index],
                    "faction": [faction],
                }
            else:
                sector_info[planet.sector]["faction"].append(faction)
        alpha = background.getchannel(channel="A")
        background = background.convert(mode="RGB")
        for info in sector_info.values():
            self._fill_sector(background, info, dim_faction_colour)
        background.putalpha(alpha=alpha)
        return background

    def _fill_sector(self, background, sector_info, colours):
        sector_info["faction"] = max(
            set(sector_info["faction"]), key=sector_info["faction"].count
        )
        ImageDraw.floodfill(
            image=background,
            xy=sector_info["coords"],
            value=colours[sector_info["faction"]],
            thresh=25,
        )

    def _draw_waypoint_lines(self, background: Image.Image):
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
        faction_mapping = {
            1: "Humans",
            2: "Terminids",
            3: "Automaton",
            4: "Illuminate",
        }
        background_draw = ImageDraw.Draw(im=background)
        for task in self.data.assignment.tasks:
            task: Tasks.Task
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

    def _draw_planets(self, background: Image.Image):
        background_draw = ImageDraw.Draw(im=background)
        for index, coords in self.planet_coordinates.items():
            if index == 64:
                inside = (28, 22, 48)
                outside = (106, 76, 180)
                background_draw.ellipse(
                    xy=[
                        (coords[0] - 15, coords[1] - 15),
                        (coords[0] + 15, coords[1] + 15),
                    ],
                    fill=outside,
                )
                background_draw.ellipse(
                    xy=[
                        (coords[0] - 12, coords[1] - 12),
                        (coords[0] + 12, coords[1] + 12),
                    ],
                    fill=inside,
                )
            else:
                current_owner = self.data.planets[index].current_owner
                background_draw.ellipse(
                    xy=[
                        (coords[0] - 15, coords[1] - 15),
                        (coords[0] + 15, coords[1] + 15),
                    ],
                    fill=(
                        faction_colours[current_owner]
                        if index in self.available_planets
                        else faction_colours[current_owner.lower()]
                    ),
                )

    def _add_dss_icon(self, background: Image.Image):
        dss_icon = Image.open("resources/DSS.png")
        dss_icon = dss_icon.convert("RGBA")
        dss_coords = (
            int(self.planet_coordinates[self.data.dss.planet.index][0]) - 17,
            int(self.planet_coordinates[self.data.dss.planet.index][1]) - 130,
        )
        dss_icon = background.paste(dss_icon, dss_coords, dss_icon)

    def _draw_arrow(self, background: Image.Image, width: int = 20):
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

    def _write_names(self, background: Image.Image, language_code: str):
        font = ImageFont.truetype("gww-font.ttf", 25)
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

    def _draw_ellipse(
        self,
        draw: ImageDraw.ImageDraw,
        coords: tuple,
        fill_colour: tuple,
        radius: int = 20,
    ):
        draw.ellipse(
            [
                (coords[0] - radius, coords[1] - radius),
                (coords[0] + radius, coords[1] + radius),
            ],
            fill=fill_colour,
        )

    def _draw_planet_name(
        self,
        background_draw: ImageDraw.ImageDraw,
        planet_name: str,
        coords: tuple,
        font: ImageFont.FreeTypeFont,
        border_colour: str = "deepskyblue",
    ):
        name_text = planet_name.replace(" ", "\n")
        background_draw.multiline_text(
            xy=coords,
            text=name_text,
            anchor="md",
            font=font,
            stroke_width=2,
            stroke_fill=border_colour,
            align="center",
            spacing=-10,
        )

    async def localize(self):
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
