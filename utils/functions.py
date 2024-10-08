from datetime import datetime
from json import load
from re import sub
from PIL import Image
from disnake import Colour, Embed, File, TextChannel
from utils.db import GuildsDB
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from data.lists import supported_languages
from data.lists import json_dict


def load_json():
    status = "load_json status:\n"
    for key, values in json_dict.copy().items():
        if "path" not in values:
            for second_key, second_values in values.items():
                if "path" in second_values:
                    with open(second_values["path"], encoding="UTF-8") as json_file:
                        json_dict[key][second_key] = load(json_file)
                        status += f"{key} - {second_key} - {'LOADED' if second_values else 'FAILED'}\n"
                        continue
            continue
        else:
            with open(values["path"], encoding="UTF-8") as json_file:
                json_dict[key] = load(json_file)
                status += f"{key} - {'LOADED' if values else 'FAILED'}\n"
    if "FAILED" in status:
        return None
    else:
        return json_dict


def health_bar(perc: float, race: str, reverse: bool = False):
    if race not in ("Terminids", "Automaton", "Illuminate", "Humans", "MO"):
        print(f"health_bar function, {race}, race not in race set")
        return ""
    perc = perc * 10
    if reverse:
        perc = 10 - perc
    perc = int(perc)
    health_icon = {
        "Terminids": "<:tc:1229360523217342475>",
        "Automaton": "<:ac:1229360519689801738>",
        "Illuminate": "<:ic:1246938273734197340>",
        "Humans": "<:hc:1229362077974401024>",
        "MO": "<:moc:1229360522181476403>",
    }[race]
    progress_bar = health_icon * perc
    while perc < 10:
        progress_bar += "<:nc:1229450109901606994>"
        perc += 1
    return progress_bar


def short_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num = round(num / 1000.0, 2)
    return "{:.{}f}{}".format(num, 2, ["", "K", "M", "B", "T", "Q"][magnitude])


def steam_format(content: str):  # thanks Chats
    content = sub(r"\[h1\](.*?)\[/h1\]", r"# \1", content)
    content = sub(r"\[h2\](.*?)\[/h2\]", r"## \1", content)
    content = sub(r"\[h3\](.*?)\[/h3\]", r"### \1", content)
    content = sub(r"\[h4\](.*?)\[/h4\]", r"### \1", content)
    content = sub(r"\[h5\](.*?)\[/h5\]", r"### \1", content)
    content = sub(r"\[h6\](.*?)\[/h6\]", r"### \1", content)
    content = sub(r"\[url=(.+?)](.+?)\[/url\]", r"[\2]\(\1\)", content)
    content = sub(r"<i=1>(.*?)</i>", r"**\1**", content)
    content = sub(r"<i=3>(.*?)</i>", r"**\1**", content)
    content = sub(r"<i=3>(.*?)<i=3>", r"**\1**", content)
    content = sub(r"\[quote\]", r"> ", content)
    content = sub(r"\[quote\]", r"> ", content)
    content = sub(r"\[/quote\]", r"", content)
    content = sub(r"\[b\]", r"**", content)
    content = sub(r"\[/b\]", r"**", content)
    content = sub(r"\[i\]", r"*", content)
    content = sub(r"\[/i\]", r"*", content)
    content = sub(r"\[u\]", r"\n# __", content)
    content = sub(r"\[/u\]", r"__", content)
    content = sub(r"\[list\]", r"", content)
    content = sub(r"\[/list\]", r"", content)
    content = sub(r"\[\*\]", r" - ", content)
    content = sub(r"/\[img\](.*?)\[\/img\]/", r"", content)
    content = sub(
        r"\[previewyoutube=(.+);full\]\[/previewyoutube\]",
        "[YouTube](https://www.youtube.com/watch?v=" + r"\1)",
        content,
    )
    content = sub(r"\[img\](.*?\..{3,4})\[/img\]\n\n", "", content)
    return content


async def dashboard_maps(data, channel: TextChannel, planets_json: dict):
    faction_colors = {
        "Automaton": (252, 76, 79),
        "automaton": (126, 38, 22),
        "Terminids": (253, 165, 58),
        "terminids": (126, 82, 29),
        "Illuminate": (103, 43, 166),
        "illuminate": (51, 21, 83),
        "Humans": (36, 205, 76),
        "humans": (18, 102, 38),
        "MO": (254, 226, 76),
    }
    languages = GuildsDB.get_used_languages()
    planets_coords = {
        planet.index: (
            (planet.position["x"] * 2000) + 2000,
            ((planet.position["y"] * -1) * 2000) + 2000,
        )
        for planet in data.planets.values()
    }
    available_planets = {campaign.planet.index for campaign in data.campaigns}
    map_dict = {}

    for lang in languages:
        embed = Embed(colour=Colour.dark_purple())
        embed.add_field(
            name="Updated", value=f"<t:{int(datetime.now().timestamp())}:R>"
        )
        with Image.open("resources/map.webp") as background:
            background_draw = Draw(background)
            for index, coords in planets_coords.items():
                for waypoint in data.planets[index].waypoints:
                    try:
                        waypoint_coords = planets_coords[waypoint]
                        background_draw.line(
                            (
                                waypoint_coords[0],
                                waypoint_coords[1],
                                coords[0],
                                coords[1],
                            ),
                            width=5,
                        )
                    except KeyError:
                        continue
            if data.assignment:
                for task in data.assignment.tasks:
                    draw_task_on_map(
                        background_draw, task, planets_coords, faction_colors, data
                    )
            for index, coords in planets_coords.items():
                draw_planet_on_map(
                    background_draw,
                    index,
                    coords,
                    available_planets,
                    data,
                    faction_colors,
                )
            for index, coords in planets_coords.items():
                if index in available_planets:
                    draw_planet_names(
                        background_draw, coords, planets_json, index, lang
                    )
            map_image_path = f"resources/map_{lang}.webp"
            background.save(map_image_path)
        message_for_url = await channel.send(file=File(map_image_path))
        embed.set_image(url=message_for_url.attachments[0].url)
        map_dict[lang] = embed

    return map_dict


def draw_task_on_map(background_draw, task, planets_coords, faction_colors, data):
    faction_mapping = {
        1: "Humans",
        2: "Terminids",
        3: "Automaton",
        4: "Illuminate",
    }
    if task.type in (11, 13):
        draw_ellipse(
            background_draw, planets_coords[task.values[2]], faction_colors["MO"]
        )
    elif task.type == 12 and data.planet_events:
        for planet in data.planet_events:
            if (
                planet.current_owner == "Humans"
                and planet.event.faction == faction_mapping[task.values[1]]
            ):
                draw_ellipse(
                    background_draw, planets_coords[planet.index], faction_colors["MO"]
                )
    elif task.type == 2:
        draw_ellipse(
            background_draw, planets_coords[task.values[8]], faction_colors["MO"]
        )
    elif task.type == 3:
        for campaign in data.campaigns:
            if campaign.faction == faction_mapping[task.values[0]]:
                draw_ellipse(
                    background_draw,
                    planets_coords[campaign.planet.index],
                    faction_colors["MO"],
                )


def draw_planet_on_map(
    background_draw, index, coords, available_planets, data, faction_colors
):
    if index == 64:
        fill_color = (95, 61, 181)
    else:
        current_owner = data.planets[index].current_owner
        fill_color = (
            faction_colors[current_owner]
            if index in available_planets
            else faction_colors[current_owner.lower()]
        )
    background_draw.ellipse(
        [(coords[0] - 35, coords[1] - 35), (coords[0] + 35, coords[1] + 35)],
        fill=fill_color,
    )


def draw_ellipse(draw, coords, fill_color, radius=50):
    draw.ellipse(
        [
            (coords[0] - radius, coords[1] - radius),
            (coords[0] + radius, coords[1] + radius),
        ],
        fill=fill_color,
    )


def draw_planet_names(draw, coords, planet_names_loc, index, lang):
    font = truetype("gww-font.ttf", 50)
    name_text = planet_names_loc[str(index)]["names"][
        supported_languages[lang]
    ].replace(" ", "\n")

    draw.multiline_text(
        xy=coords,
        text=name_text,
        anchor="md",
        font=font,
        stroke_width=3,
        stroke_fill="black",
        align="center",
        spacing=-15,
    )


def planet_map(data, planet_index, language):
    embed = Embed(colour=Colour.dark_purple())
    faction_colour = {
        "Automaton": (252, 76, 79),
        "automaton": (126, 38, 22),
        "Terminids": (253, 165, 58),
        "terminids": (126, 82, 29),
        "Illuminate": (103, 43, 166),
        "illuminate": (51, 21, 83),
        "Humans": (36, 205, 76),
        "humans": (18, 102, 38),
    }
    planets_coords = {}
    available_planets = [campaign.planet.name for campaign in data.campaigns]
    for planet in data.planets.values():
        planets_coords[planet.index] = (
            (planet.position["x"] * 2000) + 2000,
            ((planet.position["y"] - (planet.position["y"] * 2)) * 2000) + 2000,
        )
    with Image.open("resources/map.webp") as background:
        background_draw = Draw(background)
        for index, coords in planets_coords.items():
            for i in data.planets[index].waypoints:
                try:
                    background_draw.line(
                        (
                            planets_coords[i][0],
                            planets_coords[i][1],
                            coords[0],
                            coords[1],
                        ),
                        width=5,
                    )
                except:
                    continue
        for index, coords in planets_coords.items():
            if index == 64:
                background_draw.ellipse(
                    [
                        (coords[0] - 35, coords[1] - 35),
                        (coords[0] + 35, coords[1] + 35),
                    ],
                    fill=(95, 61, 181),
                )
                continue
            background_draw.ellipse(
                [
                    (coords[0] - 35, coords[1] - 35),
                    (coords[0] + 35, coords[1] + 35),
                ],
                fill=(
                    faction_colour[data.planets[index].current_owner]
                    if data.planets[index].name in available_planets
                    else faction_colour[data.planets[index].current_owner.lower()]
                ),
            )
        target_coords = planets_coords[planet_index]
        background_draw.line(
            (
                target_coords[0] - 7,
                target_coords[1] + 25,
                target_coords[0] + 75,
                target_coords[1] + 100,
            ),
            width=30,
        )
        background_draw.line(
            (
                target_coords[0] + 7,
                target_coords[1] + 25,
                target_coords[0] - 75,
                target_coords[1] + 100,
            ),
            width=30,
        )
        background_draw.line(
            (
                target_coords[0],
                target_coords[1] + 25,
                target_coords[0],
                target_coords[1] + 250,
            ),
            width=30,
        )
        background.save(f"resources/map_{language}.webp")
    embed.set_image(file=File(f"resources/map_{language}.webp"))
    return embed


def skipped_planets(campaigns: list, total_players):
    player_minimum = total_players * 0.05
    factions = ("Terminids", "Automaton", "Illuminate")
    results = []
    for faction in factions:
        results.append(
            [
                campaign
                for campaign in campaigns
                if (
                    campaign.planet.stats["playerCount"] <= player_minimum
                    or 1 - campaign.planet.health / campaign.planet.max_health <= 0.0001
                )
                and campaign.planet.current_owner == faction
            ]
        )
    results.append(
        [
            campaign
            for campaign in campaigns
            if (
                campaign.planet.stats["playerCount"] > player_minimum
                and 1 - campaign.planet.health / campaign.planet.max_health > 0.0001
            )
        ]
    )
    return results
