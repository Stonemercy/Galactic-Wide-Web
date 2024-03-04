from os import getenv
from disnake import Embed, Colour, File
from aiohttp import ClientSession
from json import dumps, loads
from datetime import datetime


class Dashboard:
    def __init__(self):
        self.defend_embed = Embed(title="Defending", colour=Colour.blue())
        self.attack_embed = Embed(title="Attacking", colour=Colour.red())
        self.other_embed = Embed(title="Other", colour=Colour.green())
        self.embeds = []

    async def get_data(self):
        api = getenv("API")
        self.now = datetime.now()
        async with ClientSession() as session:
            async with session.get(f"{api}/activePlanets") as r:
                if r.status == 200:
                    js = await r.json()
                    self.data = loads(dumps(js))
                    await session.close()
                else:
                    return self.other_embed.add_field(
                        "Error with API", "Please contact my owner"
                    )

    def set_data(self):
        for i in self.data:
            if i["planet"] == "Other Planets**":
                self.other_embed.add_field(
                    f"__**Other Planets***__",
                    (
                        f"Heroes: `{i['players']}`\n"
                        f"Status: `Not contributing to Democracy`\n"
                    ),
                    inline=False,
                )
                continue
            predicted_time = ""
            if i["predicted_time"] is not None:
                pred_dt = datetime.fromisoformat(i["predicted_time"]).replace(
                    tzinfo=None
                )
                if pred_dt > self.now:
                    predicted_time = f"<t:{int(pred_dt.timestamp())}:R>"
            if i["time_left"] is None:
                atk_def = "⚔️"
            else:
                atk_def = "🛡️"
            status_dict = {
                "LOSING GROUND. Send Reinforcements!": "⚠️",
                "At a stalemate": "⏸️",
                "FAILING": "🛑",
                "LIBERATING": "🟢",
            }
            status_icon = status_dict[i["status"]]
            name = f"{i['id']} - __**{i['planet']}**__ {atk_def}"
            value = (
                f"Time left: `{i['time_left']}`\n"
                f"Liberation: `{i['liberation'].capitalize()}`\n"
                f"Heroes: `{i['players']}`\n"
                f"Status: `{i['status']}` {predicted_time} {status_icon}\n"
                f"Super Earth Forces: `{i['forces']['super_earth_forces']}`\n"
                f"Enemy Forces: `{i['forces']['enemy_forces']}`\n"
                f"Net gain/loss: `{i['forces']['net']}`\n\u200b\n"
            )
            if atk_def == "⚔️":
                self.attack_embed.add_field(
                    name,
                    value,
                    inline=False,
                )
            else:
                self.defend_embed.add_field(
                    name,
                    value,
                    inline=False,
                )
        self.other_embed.add_field(
            "\u200b\n",
            "*Players who are playing the game as an individual, and are having very little impact to the galactic war",
        ).set_footer(text=f"Updated at {self.now.strftime('%H:%M')}GMT")
        if len(self.defend_embed.fields) < 1:
            self.defend_embed.add_field(
                "There are no threats to our Freedom", "||for now...||"
            )
        self.embeds = [self.defend_embed, self.attack_embed, self.other_embed]


class Planet(Embed):
    def __init__(self, planet: str):
        super().__init__()
        self.planet = planet
        self.data = None

    async def get_data(self):
        api = getenv("API")
        async with ClientSession() as session:
            async with session.get(f"{api}/activePlanets/{self.planet}") as r:
                if r.status == 200:
                    js = await r.json()
                    self.data = loads(dumps(js))
                    await session.close()

    def set_data(self):
        self.set_footer(text=f"As of {datetime.now().strftime('%H:%M')}GMT")
        predicted_time = ""
        if self.data["predicted_time"] is not None:
            pred_dt = datetime.fromisoformat(self.data["predicted_time"]).replace(
                tzinfo=None
            )
            if pred_dt > datetime.now():
                predicted_time = f"<t:{int(pred_dt.timestamp())}:R>"
        if self.data["time_left"] is None:
            atk_def = "⚔️"
        else:
            atk_def = "🛡️"
        status_dict = {
            "LOSING GROUND. Send Reinforcements!": "⚠️",
            "At a stalemate": "⏸️",
            "FAILING": "🛑",
            "LIBERATING": "🟢",
        }
        status_icon = status_dict[self.data["status"]]
        self.add_field(
            name=f"{self.data['id']} - __**{self.data['planet']}**__ {atk_def}",
            value=(
                f"Time left: `{self.data['time_left']}`\n"
                f"Liberation: `{self.data['liberation'].capitalize()}`\n"
                f"Heroes: `{self.data['players']}`\n"
                f"Status: `{self.data['status']}` {predicted_time} {status_icon}\n"
                f"Super Earth Forces: `{self.data['forces']['super_earth_forces']}`\n"
                f"Enemy Forces: `{self.data['forces']['enemy_forces']}`\n"
                f"Net gain/loss: `{self.data['forces']['net']}`\n\u200b\n"
            ),
        )
        self.set_thumbnail(file=File(f"resources/freedom.gif"))


class HelpEmbed(Embed):
    def __init__(self):
        super().__init__(colour=Colour.green(), title="Help")
