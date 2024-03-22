from os import getenv
from disnake import Embed, Colour, File
from aiohttp import ClientSession
from json import dumps, loads
from datetime import datetime
from helpers.functions import health_bar


class Planet(Embed):
    def __init__(self, planet: str):
        super().__init__(colour=Colour.blue())
        self.planet_name = planet
        self.status = None

    async def get_data(self):
        api = getenv("API")
        async with ClientSession() as session:
            try:
                async with session.get(f"{api}/status") as r:
                    if r.status == 200:
                        js = await r.json()
                        self.status = loads(dumps(js))
                        await session.close()
                    else:
                        return self.add_field(
                            "Error with API", "Please contact my owner"
                        )
            except Exception as e:
                print(("Planet Embed", e))

    def set_data(self):
        if self.status == None:
            return False
        self.set_footer(text=f"As of {datetime.now().strftime('%H:%M')}GMT")
        self.planet_status = self.status["planet_status"]
        for i in self.planet_status:
            if i["planet"]["name"] == self.planet_name:
                if i["owner"] != "Humans":
                    atk_def = "atk"
                else:
                    atk_def = "def"
                planet_health_bar = health_bar(
                    i["health"], i["planet"]["max_health"], atk_def
                )
                self.add_field(
                    f"__**{i['planet']['name']}**__",
                    (
                        f"Liberation: `{i['liberation']:.0f}%`\n"
                        f"Heroes: `{i['players']:,}`\n"
                        f"Planet health:\n"
                        f"{planet_health_bar}\n"
                        f"`{i['health']:>10,}/{i['planet']['max_health']:<11,} +{i['regen_per_second']:.0f}/s`\n"
                        "\u200b\n"
                    ),
                )
                if i["owner"] == "Automatons":
                    self.set_author(
                        name="Liberation Progress",
                        icon_url="https://cdn.discordapp.com/emojis/1215036421551685672.webp?size=44&quality=lossless",
                    )
                elif i["owner"] == "Terminids":
                    self.set_author(
                        name="Liberation Progress",
                        icon_url="https://cdn.discordapp.com/emojis/1215036423090999376.webp?size=44&quality=lossless",
                    )
                break
        self.set_thumbnail(file=File(f"resources/freedom.gif"))


class HelpEmbed(Embed):
    def __init__(self):
        super().__init__(colour=Colour.green(), title="Help")


class BotDashboardEmbed(Embed):
    def __init__(self, dt: datetime):
        super().__init__(colour=Colour.green(), title="GWW Overview")
        self.description = (
            "This is the dashboard for all information about the GWW itself"
        )
        self.set_footer(text=f"Updated at {dt.strftime('%H:%M')}GMT")


class Weapons:
    class All(Embed):
        def __init__(self, data: list):
            super().__init__(colour=Colour.blue(), title="The Arsenal")
            self.data = data
            for n, i in enumerate(self.data):
                self.fire_modes = []
                stats = i[1]
                if stats["fire modes"]["semi"]:
                    self.fire_modes.append("Semi-automatic")
                if stats["fire modes"]["burst"]:
                    self.fire_modes.append("Burst")
                if stats["fire modes"]["auto"]:
                    self.fire_modes.append("Automatic")
                self.fire_modes = ", ".join(self.fire_modes)

                self.add_field(
                    name=f"{n + 1} - {i[0]}",
                    value=(
                        f"Type: `{stats['type']}`\n"
                        f"Damage: `{stats['damage']}`\n"
                        f"Fire Rate: `{stats['fire rate']}`\n"
                        f"DPS: `{stats['dps']}`\n"
                        f"Recoil: `{stats['recoil']}`\n"
                        f"Capacity: `{stats['capacity']}`\n"
                        f"Armour Pen: `{stats['armour penetration']}`\n"
                        f"Fire Modes: `{self.fire_modes}`\n"
                        f"Special Effects: `{stats['effects']}`\n"
                    ),
                )

    class Single(Embed):
        def __init__(self, name: str, data: dict):
            super().__init__(colour=Colour.blue())
            self.data = data
            self.fire_modes = []
            if self.data["fire modes"]["semi"]:
                self.fire_modes.append("Semi-automatic")
            if self.data["fire modes"]["burst"]:
                self.fire_modes.append("Burst")
            if self.data["fire modes"]["auto"]:
                self.fire_modes.append("Automatic")
            self.fire_modes = ", ".join(self.fire_modes)

            self.add_field(
                name=name,
                value=(
                    f"Type: `{self.data['type']}`\n"
                    f"Damage: `{self.data['damage']}`\n"
                    f"Fire Rate: `{self.data['fire rate']}`\n"
                    f"DPS: `{self.data['dps']}`\n"
                    f"Recoil: `{self.data['recoil']}`\n"
                    f"Capacity: `{self.data['capacity']}`\n"
                    f"Armour Pen: `{self.data['armour penetration']}`\n"
                    f"Fire Modes: `{self.fire_modes}`\n"
                    f"Special Effects: `{self.data['effects']}`\n"
                ),
            )
            try:
                file_name = name.replace(" ", "-")
                self.set_thumbnail(file=File(f"resources/weapons/{file_name}.png"))
            except Exception as e:
                print("passing", e)
                pass


class Dashboard:
    def __init__(self):
        self.major_order = None
        self.major_order_backup = None
        self.defend_embed = Embed(title="Defending", colour=Colour.blue())
        self.attack_embed = Embed(title="Attacking", colour=Colour.red())
        self.major_orders_embed = Embed(title="Major Orders", colour=Colour.red())
        self.embeds = []

    async def get_data(self):
        api = getenv("API")
        self.now = datetime.now()
        async with ClientSession() as session:
            try:
                async with session.get(f"{api}/status") as r:
                    if r.status == 200:
                        js = await r.json()
                        self.status = loads(dumps(js))
                        await session.close()
                    else:
                        pass
            except Exception as e:
                print(("Dashboard Embed - status", e))
        async with ClientSession() as session:
            try:
                async with session.get(f"{api}/events/latest") as r:
                    if r.status == 200:
                        js = await r.json()
                        self.major_order = loads(dumps(js))
                        await session.close()
                    else:
                        pass
            except Exception as e:
                print(("Dashboard Embed - events", e))
        async with ClientSession() as session:
            try:
                async with session.get(f"{api}/feed") as r:
                    if r.status == 200:
                        js = await r.json()
                        self.feed = loads(dumps(js))
                        await session.close()
                    else:
                        pass
            except Exception as e:
                print(("Dashboard Embed - feed", e))
        if self.major_order == None:
            async with ClientSession(
                headers={"Accept-Language": "en-GB,en;q=0.5"}
            ) as session:
                try:
                    async with session.get(
                        f"https://api.live.prod.thehelldiversgame.com/api/v2/Assignment/War/801"
                    ) as r:
                        if r.status == 200:
                            js = await r.json()
                            self.major_order_backup = loads(dumps(js))
                            await session.close()
                        else:
                            pass
                except Exception as e:
                    print(("Dashboard Embed - major order backup", e))

    def set_data(self):
        self.defending_planets = self.status["planet_events"]
        self.planet_status = self.status["planet_status"]
        self.attacking_planets = self.status["planet_attacks"][::2]
        self.planets_list = []

        # Major Orders
        if self.major_order != None:
            title = self.major_order["title"]
            description = self.major_order["message"]["en"]
            self.major_orders_embed.add_field(
                f"MESSAGE #{self.major_order['id']} - {title}",
                f"`{description}`\n\u200b\n",
                inline=False,
            )
            if self.feed != None:
                self.major_orders_embed.add_field(
                    "Latest update:", self.feed[-1]["message"]["en"]
                )
        elif self.major_order_backup != None:
            title = self.major_order_backup[0]["setting"]["overrideTitle"]
            description = f"{self.major_order_backup[0]['setting']['overrideBrief']}\n{self.major_order_backup[0]['setting']['taskDescription']}"
            self.major_orders_embed.add_field(
                f"MESSAGE #BU{self.major_order_backup[0]['id32']} - {title}",
                f"`{description}`\n\u200b\n",
                inline=False,
            )

        # Defending
        for i in self.defending_planets:
            self.planet = self.planet_status[i["planet"]["index"]]
            if self.planet["planet"]["name"] in self.planets_list:
                continue
            self.planets_list.append(self.planet["planet"]["name"])
            if i["race"] == "Automaton":
                faction_icon = "<:automaton:1215036421551685672>"
            elif i["race"] == "Terminids":
                faction_icon = "<:terminid:1215036423090999376> "
            time = datetime.fromisoformat(i["expire_time"]).replace(tzinfo=None)
            time_remaining = "N/A"
            if time > datetime.now():
                time_remaining = f"<t:{time.timestamp():.0f}:f>"
            planet_health_bar = health_bar(
                self.planet["health"], i["planet"]["max_health"]
            )
            event_health_bar = health_bar(i["health"], i["max_health"], "atk")
            self.defend_embed.add_field(
                f"{faction_icon} - __**{i['planet']['name']}**__",
                (
                    f"Time left: {time_remaining}\n"
                    f"Liberation: `{(self.planet['liberation']):.0f}%`\n"
                    f"Heroes: `{self.planet['players']:,}`\n\n"
                    f"Event health:\n"
                    f"{event_health_bar}\n"
                    f"`{i['health']:>10,}/{i['max_health']:<11,}`\n\n"
                    f"Planet health:\n"
                    f"{planet_health_bar}\n"
                    f"`{self.planet['health']:>10,}/{i['planet']['max_health']:<11,} +{self.planet_status[i['planet']['index']]['regen_per_second']:.0f}/s`\n"
                    "\u200b\n"
                ),
                inline=False,
            )

        # Attacking
        for i in self.attacking_planets:
            i = i["target"]
            self.planet = self.planet_status[i["index"]]
            if self.planet["planet"]["name"] in self.planets_list:
                continue
            self.planets_list.append(self.planet["planet"]["name"])
            faction_dict = {
                "Automaton": "<:automaton:1215036421551685672>",
                "Terminids": "<:terminid:1215036423090999376>",
            }
            faction_icon = faction_dict[self.planet["owner"]]
            planet_health_bar = health_bar(
                self.planet["health"], self.planet["planet"]["max_health"], "atk"
            )
            if self.planet["owner"] == "Automaton":
                self.attack_embed.insert_field_at(
                    0,
                    f"{faction_icon} - __**{i['name']}**__",
                    (
                        f"Liberation: `{(self.planet['liberation']):.0f}%`\n"
                        f"Heroes: `{self.planet['players']:,}`\n"
                        f"Planet Health:\n"
                        f"{planet_health_bar}\n"
                        f"`{self.planet['health']:>10,}/{i['max_health']:<11,} +{self.planet_status[i['index']]['regen_per_second']:.0f}/s`\n"
                        "\u200b\n"
                    ),
                    inline=False,
                )
            else:
                self.attack_embed.add_field(
                    f"{faction_icon} - __**{i['name']}**__",
                    (
                        f"Liberation: `{(self.planet['liberation']):.0f}%`\n"
                        f"Heroes: `{self.planet['players']:,}`\n"
                        f"Planet Health:\n"
                        f"{planet_health_bar}\n"
                        f"`{self.planet['health']:>10,}/{i['max_health']:<11,} +{self.planet_status[i['index']]['regen_per_second']:.0f}/s`\n"
                        "\u200b\n"
                    ),
                    inline=False,
                )

        # Other
        self.timestamp = int(self.now.timestamp())
        self.attack_embed.add_field(
            "\u200b",
            f"Updated on <t:{self.timestamp}:f> - <t:{self.timestamp}:R>",
            inline=False,
        )
        if len(self.defend_embed.fields) < 1:
            self.defend_embed.add_field(
                "There are no threats to our Freedom", "||for now...||"
            )
        if len(self.major_orders_embed.fields) < 1:
            self.major_orders_embed.add_field("There are no Major Orders", "\u200b")
        self.attack_embed.set_image("https://i.imgur.com/cThNy4f.png")
        self.defend_embed.set_image("https://i.imgur.com/cThNy4f.png")
        self.major_orders_embed.set_image("https://i.imgur.com/cThNy4f.png")
        self.embeds = [
            self.major_orders_embed,
            self.defend_embed,
            self.attack_embed,
        ]


class Terminid(Embed):
    def __init__(self, species_name: str, species_data: dict, variation: bool = False):
        super().__init__(
            colour=Colour.dark_gold(),
            title=species_name,
            description=species_data["desc"],
        )
        difficulty_dict = {
            1: "<:trivial:1219233272987648070>",
            2: "<:easy:1219232432671428608>",
            3: "<:medium:1219232485536432138>",
            4: "<:challenging:1219232486693928970>",
            5: "<:hard:1219232488602337291>",
            6: ":extreme:1219232490288451595>",
            7: "<:suicide_mission:1219239152332312696>",
            8: "<:impossible:1219234932145131570>",
            9: "<:helldive:1219238179551318067>",
            "?": "?",
        }
        file_name = species_name.replace(" ", "-")
        self.add_field(
            "Introduced",
            f"Difficulty {species_data['start']} {difficulty_dict[species_data['start']]}",
            inline=False,
        ).add_field("Tactics", species_data["tactics"], inline=False).add_field(
            "Weak Spots", species_data["weak spots"], inline=False
        )
        variations = []
        if variation == False and species_data["variations"] != None:
            for i in species_data["variations"]:
                variations.append(i)
            self.add_field("Variations", ", ".join(variations))
        try:
            self.set_thumbnail(
                file=File(f"resources/enemies/terminids/{file_name}.png")
            )
        except:
            pass


class Automaton(Embed):
    def __init__(self, bot_name: str, bot_data: dict, variation: bool = False):
        super().__init__(
            colour=Colour.brand_red(),
            title=bot_name,
            description=bot_data["desc"],
        )
        difficulty_dict = {
            1: "<:trivial:1219233272987648070>",
            2: "<:easy:1219232432671428608>",
            3: "<:medium:1219232485536432138>",
            4: "<:challenging:1219232486693928970>",
            5: "<:hard:1219232488602337291>",
            6: ":extreme:1219232490288451595>",
            7: "<:suicide_mission:1219239152332312696>",
            8: "<:impossible:1219234932145131570>",
            9: "<:helldive:1219238179551318067>",
            "?": "?",
        }
        file_name = bot_name.replace(" ", "-")
        self.add_field(
            "Introduced",
            f"Difficulty {bot_data['start']} {difficulty_dict[bot_data['start']]}",
            inline=False,
        ).add_field("Tactics", bot_data["tactics"], inline=False).add_field(
            "Weak Spots", bot_data["weak spots"], inline=False
        )
        variations = []
        if variation == False and bot_data["variations"] != None:
            for i in bot_data["variations"]:
                variations.append(i)
            self.add_field("Variations", ", ".join(variations))
        try:
            self.set_thumbnail(
                file=File(f"resources/enemies/automatons/{file_name}.png")
            )
        except:
            pass
