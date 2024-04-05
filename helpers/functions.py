from json import dumps, loads
from math import ceil
from os import getenv
from aiohttp import ClientSession


def health_bar(current_health: int, max_health: int, atk_def: str = "def"):
    if atk_def not in ["atk", "def"]:
        return ""
    prog_dict = {
        "def": {10: "🟦", 7: "🟩", 5: "🟨", 3: "🟧", 0: "🟥"},
        "atk": {9: "🟥", 6: "🟧", 4: "🟨", 2: "🟩", 0: "🟦"},
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


async def get_info():
    status = None
    major_order = None
    api = getenv("API")
    bu_api = getenv("BU_API")
    major_order_dict = {
        "es": None,
        "fr": None,
        "de": None,
        "en": None,
        "it": None,
        "ru": None,
        "zh": None,
    }
    async with ClientSession() as session:
        try:
            async with session.get(f"{api}/status") as r:
                if r.status == 200:
                    js = await r.json()
                    status = loads(dumps(js))
                    await session.close()
        except Exception as e:
            print(("Dashboard Embed - status", e))
    async with ClientSession() as session:
        try:
            async with session.get(f"{api}/events/latest") as r:
                if r.status == 200:
                    js = await r.json()
                    major_order = loads(dumps(js))
                    await session.close()
        except Exception as e:
            print(("Dashboard Embed - events", e))
        if major_order == None:
            for i in major_order_dict:
                async with ClientSession(headers={"Accept-Language": i}) as session:
                    try:
                        async with session.get(f"{bu_api}") as r:
                            if r.status == 200:
                                js = await r.json()
                                major_order_dict[i] = loads(dumps(js))
                                await session.close()
                    except Exception as e:
                        print(("Dashboard Embed - major order backup", e))
    return {
        "status": status,
        "major order": major_order,
        "major order dict": major_order_dict,
    }
