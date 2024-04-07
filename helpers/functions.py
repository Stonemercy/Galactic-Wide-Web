from json import dumps, loads
from math import ceil
from os import getenv
from re import sub
from aiohttp import ClientSession


def health_bar(current_health: int, max_health: int, atk_def: str = "def"):
    if atk_def not in ["atk", "def"]:
        return ""
    prog_dict = {
        "def": {10: "🟦", 7: "🟩", 5: "🟨", 3: "🟧", 0: "🟥"},
        "atk": {9: "🟥", 6: "🟧", 3: "🟨", 1: "🟩", 0: "🟦"},
    }
    prog_dict = prog_dict[atk_def]
    perc = (current_health / max_health) * 10
    prog_ico = ""
    for i in prog_dict:
        if perc >= i:
            prog_ico = prog_dict[i]
            break
        else:
            continue
    progress_bar = prog_ico * ceil(perc)
    while len(progress_bar) < 10:
        progress_bar += "⬛"
    return progress_bar


async def pull_from_api(
    get_war_state: bool = False,
    get_assignments: bool = False,
    get_campaigns: bool = False,
    get_dispatches: bool = False,  # first index is newest
    get_planets: bool = False,
    get_planet_events: bool = False,
    get_steam: bool = False,  # first index is newest
    language: str = "en-GB",
):

    api = getenv("API")
    results = {
        "war_state": None,
        "assignments": None,
        "campaigns": None,
        "dispatches": None,
        "planets": None,
        "planet_events": None,
        "steam": None,
    }
    if get_war_state:
        async with ClientSession(headers={"Accept-Language": language}) as session:
            try:
                async with session.get(f"{api}/war") as r:
                    if r.status == 200:
                        js = await r.json()
                        results["war_state"] = loads(dumps(js))
                        await session.close()
            except Exception as e:
                print(("API/WAR", e))
    if get_assignments:
        async with ClientSession(headers={"Accept-Language": language}) as session:
            try:
                async with session.get(f"{api}/assignments") as r:
                    if r.status == 200:
                        js = await r.json()
                        results["assignments"] = loads(dumps(js))
                        await session.close()
            except Exception as e:
                print(("API/ASSIGNMENTS", e))
    if get_campaigns:
        async with ClientSession(headers={"Accept-Language": language}) as session:
            try:
                async with session.get(f"{api}/campaigns") as r:
                    if r.status == 200:
                        js = await r.json()
                        results["campaigns"] = loads(dumps(js))
                        await session.close()
            except Exception as e:
                print(("API/CAMPAIGNS", e))
    if get_dispatches:
        async with ClientSession(headers={"Accept-Language": language}) as session:
            try:
                async with session.get(f"{api}/dispatches") as r:
                    if r.status == 200:
                        js = await r.json()
                        results["dispatches"] = loads(dumps(js))
                        await session.close()
            except Exception as e:
                print(("API/DISPATCHES", e))
    if get_planets:
        async with ClientSession(headers={"Accept-Language": language}) as session:
            try:
                async with session.get(f"{api}/planets") as r:
                    if r.status == 200:
                        js = await r.json()
                        results["planets"] = loads(dumps(js))
                        if results["planets"] == None:
                            print("Planets = None")
                        await session.close()
            except Exception as e:
                print(("API/PLANETS", e))
    if get_planet_events:
        async with ClientSession(headers={"Accept-Language": language}) as session:
            try:
                async with session.get(f"{api}/planet-events") as r:
                    if r.status == 200:
                        js = await r.json()
                        results["planet_events"] = loads(dumps(js)) or None
                        await session.close()
            except Exception as e:
                print(("API/PLANET-EVENTS", e))
    if get_steam:
        async with ClientSession(headers={"Accept-Language": language}) as session:
            try:
                async with session.get(f"{api}/steam") as r:
                    if r.status == 200:
                        js = await r.json()
                        results["steam"] = loads(dumps(js))
                        await session.close()
            except Exception as e:
                print(("API/STEAM", e))
    return results


def short_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num = round(num / 1000.0, 2)
    return "{:.{}f}{}".format(num, 2, ["", "K", "M", "B", "T", "Q"][magnitude])


def dispatch_format(message: str):
    message = message.replace("<i=3>", "").replace("</i>", "")
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
    content = sub(r"\[\*\]", r"  - ", content)
    content = sub(
        r"\[previewyoutube=(.+);full\]\[/previewyoutube\]",
        "[YouTube](https://www.youtube.com/watch?v=" + r"\1)",
        content,
    )
    content = sub(r"\[img\](.*?\..{3,4})\[/img\]\n\n", "", content)
    return content
