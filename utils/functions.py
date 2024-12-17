from datetime import datetime
from re import sub
from PIL import Image
from disnake import Colour, Embed, File, TextChannel
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from data.lists import supported_languages, faction_colours


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


def steam_format(content: str):
    replacements = {
        "": [
            "[/h1]",
            "[/h2]",
            "[/h3]",
            "[/h4]",
            "[/h5]",
            "[/h6]",
            "[/quote]",
            "[list]",
            "[list]\n",
            "[/list]",
            "[/*]",
        ],
        "# ": ["[h1]"],
        "## ": ["[h2]"],
        "### ": ["[h3]", "[h4]", "[h5]", "[h6]"],
        "*": ["[i]", "[/i]"],
        "**": ["<i=1>", "<i=3>", "</i>", "[b]", "[/b]"],
        "> ": ["[quote]"],
        "__": ["[u]", "[/u]"],
        "- ": ["[*]\n", "[*]"],
    }
    for replacement, replacees in replacements.items():
        for replacee in replacees:
            content = content.replace(replacee, replacement)
    content = sub(r"\[url=(.+?)](.+?)\[/url\]", r"[\2]\(\1\)", content)
    content = sub(r"\[img\](.*?)\[\/img\]", r"", content)
    content = sub(
        r"\[previewyoutube=(.+);full\]\[/previewyoutube\]",
        "[YouTube](https://www.youtube.com/watch?v=" + r"\1)",
        content,
    )
    content = sub(r"\[img\](.*?\..{3,4})\[/img\]\n\n", "", content)
    return content


async def dashboard_maps(
    data, channel: TextChannel, planets_json: dict, language_code: dict
):
    planets_coords = {
        planet.index: (
            (planet.position["x"] * 2000) + 2000,
            ((planet.position["y"] * -1) * 2000) + 2000,
        )
        for planet in data.planets.values()
    }
    available_planets = {campaign.planet.index for campaign in data.campaigns}
    embed = Embed(colour=Colour.dark_purple())
    embed.add_field(name="Updated", value=f"<t:{int(datetime.now().timestamp())}:R>")
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
                    background_draw, task, planets_coords, faction_colours, data
                )
        if data.dss and data.dss != "Error":
            draw_dss_ring_on_map(background_draw, planets_coords, faction_colours, data)
        for index, coords in planets_coords.items():
            draw_planet_on_map(
                background_draw,
                index,
                coords,
                available_planets,
                data,
                faction_colours,
            )
        if data.dss and data.dss != "Error":
            dss_icon = Image.open("resources/DSS.png")
            dss_icon = dss_icon.convert("RGBA")
            dss_coords = (
                int(planets_coords[data.dss.planet.index][0]) - 22,
                int(planets_coords[data.dss.planet.index][1]) - 180,
            )
            dss_icon = background.paste(dss_icon, dss_coords, dss_icon)
        for index, coords in planets_coords.items():
            if index in available_planets:
                draw_planet_names(
                    background_draw,
                    coords,
                    planets_json,
                    index,
                    language_code,
                    data.planets[index],
                )
        background.save(f"resources/map_{language_code}.webp")
    message_for_url = await channel.send(
        file=File(f"resources/map_{language_code}.webp")
    )
    embed.set_image(url=message_for_url.attachments[0].url)
    return embed


def draw_task_on_map(background_draw, task, planets_coords, faction_colours, data):
    faction_mapping = {
        1: "Humans",
        2: "Terminids",
        3: "Automaton",
        4: "Illuminate",
    }
    if task.type in (11, 13):
        draw_ellipse(
            background_draw, planets_coords[task.values[2]], faction_colours["MO"]
        )
    elif task.type == 12 and data.planet_events:
        for planet in data.planet_events:
            if (
                planet.current_owner == "Humans"
                and planet.event.faction == faction_mapping[task.values[1]]
            ):
                draw_ellipse(
                    background_draw, planets_coords[planet.index], faction_colours["MO"]
                )
    elif task.type == 2:
        draw_ellipse(
            background_draw, planets_coords[task.values[8]], faction_colours["MO"]
        )
    elif task.type == 3 and task.progress != 1:
        for campaign in data.campaigns:
            if campaign.faction == faction_mapping[task.values[0]]:
                draw_ellipse(
                    background_draw,
                    planets_coords[campaign.planet.index],
                    faction_colours["MO"],
                )


def draw_dss_ring_on_map(background_draw, planets_coords, faction_colours, data):
    draw_ellipse(
        background_draw,
        planets_coords[data.dss.planet.index],
        faction_colours["DSS"],
        42,
    )


def draw_planet_on_map(
    background_draw, index, coords, available_planets, data, faction_colours
):
    if index == 64:
        inside = (28, 22, 48)
        outside = (106, 76, 180)
        background_draw.ellipse(
            [(coords[0] - 35, coords[1] - 35), (coords[0] + 35, coords[1] + 35)],
            fill=outside,
        )
        background_draw.ellipse(
            [(coords[0] - 25, coords[1] - 25), (coords[0] + 25, coords[1] + 25)],
            fill=inside,
        )
    else:
        current_owner = data.planets[index].current_owner
        background_draw.ellipse(
            [(coords[0] - 35, coords[1] - 35), (coords[0] + 35, coords[1] + 35)],
            fill=(
                faction_colours[current_owner]
                if index in available_planets
                else faction_colours[current_owner.lower()]
            ),
        )


def draw_ellipse(draw, coords, fill_color, radius=50):
    draw.ellipse(
        [
            (coords[0] - radius, coords[1] - radius),
            (coords[0] + radius, coords[1] + radius),
        ],
        fill=fill_color,
    )


def draw_planet_names(draw, coords, planet_names_loc, index, lang, planet):
    font = truetype("gww-font.ttf", 50)
    name_text = planet_names_loc[str(index)]["names"][
        supported_languages[lang]
    ].replace(" ", "\n")
    border_colour = "black" if not planet.dss else "deepskyblue"
    draw.multiline_text(
        xy=coords,
        text=name_text,
        anchor="md",
        font=font,
        stroke_width=3,
        stroke_fill=border_colour,
        align="center",
        spacing=-15,
    )


def planet_map(data, planet_index, language):
    embed = Embed(colour=Colour.dark_purple())
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
                    faction_colours[data.planets[index].current_owner]
                    if data.planets[index].name in available_planets
                    else faction_colours[data.planets[index].current_owner.lower()]
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
