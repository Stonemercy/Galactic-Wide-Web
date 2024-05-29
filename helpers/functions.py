from datetime import datetime
from json import dumps, load, loads
from logging import getLogger
from math import ceil
from os import getenv
from re import sub
from aiohttp import ClientSession
from PIL import Image
from disnake import Colour, Embed, File, TextChannel
from helpers.db import Guilds
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from data.lists import supported_languages


logger = getLogger("disnake")


def health_bar(current_health: int, max_health: int, race: str, reverse: bool = False):
    if race not in ("Terminids", "Automaton", "Illuminate", "Humans", "MO"):
        print(race, "race not in health_bar func")
        return ""
    perc = ceil((current_health / max_health) * 10)
    if reverse:
        perc = 10 - perc
    health_icon_dict = {
        "Terminids": "<:tc:1229360523217342475>",
        "Automaton": "<:ac:1229360519689801738>",
        "Illuminate": "<:ic:1229360521002618890>",
        "Humans": "<:hc:1229362077974401024>",
        "MO": "<:moc:1229360522181476403>",
    }
    progress_bar = health_icon_dict[race] * perc
    while perc < 10:
        progress_bar += "<:nc:1229450109901606994>"
        perc += 1
    return progress_bar


async def pull_from_api(
    get_war_state: bool = False,
    get_assignments: bool = False,
    get_campaigns: bool = False,
    get_dispatches: bool = False,  # first index is newest
    get_planets: bool = False,
    get_planet_events: bool = False,
    get_steam: bool = False,  # first index is newest
    get_thumbnail: bool = False,
    language: str = "en-GB",
):
    api = getenv("API")
    results = {}
    if get_war_state:
        async with ClientSession(headers={"Accept-Language": language}) as session:
            try:
                async with session.get(f"{api}/war") as r:
                    if r.status == 200:
                        js = await r.json()
                        results["war_state"] = loads(dumps(js))
                        await session.close()
            except Exception as e:
                results["war_state"] = None
                logger.error(("API/WAR", e))
    if get_assignments:
        async with ClientSession(headers={"Accept-Language": language}) as session:
            try:
                async with session.get(f"{api}/assignments") as r:
                    if r.status == 200:
                        js = await r.json()
                        results["assignments"] = loads(dumps(js))
                        await session.close()
            except Exception as e:
                results["assignments"] = None
                logger.error(("API/ASSIGNMENTS", e))
    if get_campaigns:
        async with ClientSession(headers={"Accept-Language": language}) as session:
            try:
                async with session.get(f"{api}/campaigns") as r:
                    if r.status == 200:
                        js = await r.json()
                        results["campaigns"] = loads(dumps(js))
                        await session.close()
            except Exception as e:
                results["campaigns"] = None
                logger.error(("API/CAMPAIGNS", e))
    if get_dispatches:
        async with ClientSession(headers={"Accept-Language": language}) as session:
            try:
                async with session.get(f"{api}/dispatches") as r:
                    if r.status == 200:
                        js = await r.json()
                        results["dispatches"] = loads(dumps(js))
                        await session.close()
            except Exception as e:
                results["dispatches"] = None
                logger.error(("API/DISPATCHES", e))
    if get_planets:
        async with ClientSession(headers={"Accept-Language": language}) as session:
            try:
                async with session.get(f"{api}/planets") as r:
                    if r.status == 200:
                        js = await r.json()
                        results["planets"] = loads(dumps(js))
                        await session.close()
            except Exception as e:
                results["planets"] = None
                logger.error(("API/PLANETS", e))
    if get_planet_events:
        async with ClientSession(headers={"Accept-Language": language}) as session:
            try:
                async with session.get(f"{api}/planet-events") as r:
                    if r.status == 200:
                        js = await r.json()
                        results["planet_events"] = loads(dumps(js)) or None
                        await session.close()
            except Exception as e:
                results["planet_events"] = None
                logger.error(("API/PLANET-EVENTS", e))
    if get_steam:
        async with ClientSession(headers={"Accept-Language": language}) as session:
            try:
                async with session.get(f"{api}/steam") as r:
                    if r.status == 200:
                        js = await r.json()
                        results["steam"] = loads(dumps(js))
                        await session.close()
            except Exception as e:
                results["steam"] = None
                logger.error(("API/STEAM", e))
    if get_thumbnail:
        async with ClientSession() as session:
            try:
                async with session.get(f"https://helldivers.news/api/planets") as r:
                    if r.status == 200:
                        js = await r.json()
                        results["thumbnails"] = loads(dumps(js))
                        await session.close()
                    else:
                        pass
            except Exception as e:
                results["thumbnails"] = None
                logger.error(("API/THUMBNAILS", e))
    return results


def short_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num = round(num / 1000.0, 2)
    return "{:.{}f}{}".format(num, 2, ["", "K", "M", "B", "T", "Q"][magnitude])


def dispatch_format(message: str):
    try:
        message = (
            message.replace("<i=3>", "")
            .replace("</i=2>", "")
            .replace("</i=3>", "")
            .replace("</i=1>", "")
            .replace("</i>", "")
            .replace("<i=1>", "")
            .replace("<i=2>", "")
            .replace("<br>", "\n")
        )
    except Exception as e:
        logger.error(("dispatch_format", e))
    return message


def steam_format(content: str):  # thanks Chats
    content = sub(r"\[h1\](.*?)\[/h1\]", r"# \1", content)
    content = sub(r"\[h2\](.*?)\[/h2\]", r"## \1", content)
    content = sub(r"\[h3\](.*?)\[/h3\]", r"### \1", content)
    content = sub(r"\[h3\](.*?)\[/h4\]", r"### \1", content)
    content = sub(r"\[h3\](.*?)\[/h5\]", r"### \1", content)
    content = sub(r"\[h3\](.*?)\[/h6\]", r"### \1", content)
    content = sub(r"\[url=(.+?)](.+?)\[/url\]", r"[\2]\(\1\)", content)
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


async def dashboard_maps(data: dict, channel: TextChannel):
    faction_colour = {
        "Automaton": (252, 76, 79),
        "automaton": (126, 38, 22),
        "Terminids": (253, 165, 58),
        "terminids": (126, 82, 29),
        "Illuminate": (116, 163, 180),
        "illuminate": (58, 81, 90),
        "Humans": (36, 205, 76),
        "humans": (18, 102, 38),
    }
    planet_names_loc = load(open(f"data/json/planets/planets.json", encoding="UTF-8"))
    languages = Guilds.get_used_languages()
    planets_coords = {}
    available_planets = [planet["planet"]["name"] for planet in data["campaigns"]]
    for i in data["planets"]:
        planets_coords[i["index"]] = (
            (i["position"]["x"] * 2000) + 2000,
            ((i["position"]["y"] - (i["position"]["y"] * 2)) * 2000) + 2000,
        )
    map_dict = {}
    for lang in languages:
        embed = Embed()
        embed.add_field("Updated", f"<t:{int(datetime.now().timestamp())}:R>")
        embed.colour = Colour.dark_purple()
        with Image.open("resources/map.webp") as background:
            background_draw = Draw(background)
            for index, coords in planets_coords.items():
                for i in data["planets"][index]["waypoints"]:
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
                background_draw.ellipse(
                    [
                        (coords[0] - 35, coords[1] - 35),
                        (coords[0] + 35, coords[1] + 35),
                    ],
                    fill=(
                        faction_colour[data["planets"][index]["currentOwner"]]
                        if data["planets"][index]["name"] in available_planets
                        else faction_colour[
                            data["planets"][index]["currentOwner"].lower()
                        ]
                    ),
                )
            for index, coords in planets_coords.items():
                if data["planets"][index]["name"] in available_planets:
                    font = truetype("gww-font.ttf", 50)
                    background_draw.multiline_text(
                        xy=coords,
                        text=planet_names_loc[str(index)]["names"][
                            supported_languages[lang]
                        ].replace(" ", "\n"),
                        anchor="md",
                        font=font,
                        stroke_width=3,
                        stroke_fill="black",
                        align="center",
                        spacing=-15,
                    )
            background.save(f"resources/map_{lang}.webp")
        message_for_url = await channel.send(
            file=File(f"resources/map_{lang}.webp"),
        )
        embed.set_image(message_for_url.attachments[0].url)
        map_dict[lang] = embed
        continue

    return map_dict


def planet_map(data: dict, planet, language):
    embed = Embed()
    embed.colour = Colour.dark_purple()
    faction_colour = {
        "Automaton": (252, 76, 79),
        "automaton": (126, 38, 22),
        "Terminids": (253, 165, 58),
        "terminids": (126, 82, 29),
        "Illuminate": (116, 163, 180),
        "illuminate": (58, 81, 90),
        "Humans": (36, 205, 76),
        "humans": (18, 102, 38),
    }
    planet_names_loc = load(open(f"data/json/planets/planets.json", encoding="UTF-8"))
    planets_coords = {}
    available_planets = [planet["planet"]["name"] for planet in data["campaigns"]]
    for i in data["planets"]:
        planets_coords[i["index"]] = (
            (i["position"]["x"] * 2000) + 2000,
            ((i["position"]["y"] - (i["position"]["y"] * 2)) * 2000) + 2000,
        )
    with Image.open("resources/map.webp") as background:
        background_draw = Draw(background)
        for index, coords in planets_coords.items():
            for i in data["planets"][index]["waypoints"]:
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
            background_draw.ellipse(
                [
                    (coords[0] - 35, coords[1] - 35),
                    (coords[0] + 35, coords[1] + 35),
                ],
                fill=(
                    faction_colour[data["planets"][index]["currentOwner"]]
                    if data["planets"][index]["name"] in available_planets
                    else faction_colour[data["planets"][index]["currentOwner"].lower()]
                ),
            )
        target_coords = planets_coords[planet["index"]]
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
