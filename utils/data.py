from aiohttp import ClientSession
from asyncio import sleep
from copy import deepcopy
from data.lists import task_type_15_progress_dict
from datetime import datetime, timedelta
from os import getenv
from utils.functions import health_bar, steam_format
from utils.mixins import ReprMixin

api = getenv("API")
backup_api = getenv("BU_API")


class Data(ReprMixin):
    __slots__ = (
        "__data__",
        "fetched_at",
        "assignment",
        "campaigns",
        "dispatch",
        "planets",
        "planet_events",
        "total_players",
        "steam",
        "thumbnails",
        "superstore",
        "dss",
        "war_time",
        "personal_order",
        "global_events",
        "loaded",
        "liberation_changes",
        "dark_energy_changes",
        "planets_with_player_reqs",
        "meridia_position",
    )

    def __init__(self):
        self.__data__ = {
            "assignments": None,
            "campaigns": None,
            "dispatches": None,
            "planets": None,
            "steam": None,
            "thumbnails": None,
            "superstore": None,
            "dss": None,
            "war_time": None,
            "personal_order": None,
            "status": None,
        }
        self.fetched_at = None
        self.loaded = False
        self.liberation_changes = {}
        self.dark_energy_changes = {"total": 0, "changes": []}
        self.planets_with_player_reqs = {}
        self.meridia_position = None

    async def pull_from_api(self, bot):
        api_to_use = api
        async with ClientSession(
            headers={
                "Accept-Language": "en-GB",
                "X-Super-Client": "Galactic Wide Web",
                "X-Super-Contact": "Stonemercy",
            }
        ) as session:
            async with session.get(f"{api_to_use}") as r:
                if r.status != 200:
                    api_to_use = backup_api
                    bot.logger.critical("API/USING BACKUP")
                    await bot.moderator_channel.send(f"API/USING BACKUP\n{r}")

                for endpoint in list(self.__data__.keys()):
                    if endpoint == "thumbnails":
                        async with session.get(
                            "https://helldivers.news/api/planets"
                        ) as r:
                            if r.status == 200:
                                self.__data__[endpoint] = await r.json()
                            else:
                                bot.logger.error(f"API/THUMBNAILS, {r.status}")
                        continue
                    if endpoint == "superstore":
                        async with session.get(
                            "https://api.diveharder.com/v1/store_rotation"
                        ) as r:
                            if r.status == 200:
                                self.__data__[endpoint] = await r.json()
                            else:
                                bot.logger.error(f"API/SUPERSTORE, {r.status}")
                        continue
                    if endpoint == "war_time":
                        async with session.get(
                            "https://api.diveharder.com/raw/smdb"
                        ) as r:
                            if r.status == 200:
                                data = await r.json()
                                self.__data__[endpoint] = data["time"]
                            else:
                                bot.logger.error(f"API/WAR_TIME, {r.status}")
                        continue
                    if endpoint == "dss":
                        async with session.get(
                            "https://api.diveharder.com/raw/dss"
                        ) as r:
                            if r.status == 200:
                                data = await r.json()
                                if data == "Error":
                                    self.__data__[endpoint] = data
                                    continue
                                if type(data[0]) == str:
                                    bot.logger.error(f"API/DSS, {data[0] = }")
                                    continue
                                tactical_actions = data[0].get("tacticalActions", None)
                                if tactical_actions:
                                    names_present = tactical_actions[0].get(
                                        "name", None
                                    )
                                    if not names_present:
                                        bot.logger.error(
                                            f"API/DSS, Tactical Action has no name"
                                        )
                                        continue
                                self.__data__[endpoint] = data[0]
                            else:
                                bot.logger.error(f"API/DSS, {r.status}")
                        continue
                    if endpoint == "personal_order":
                        async with session.get(
                            "https://api.diveharder.com/v1/personal_order"
                        ) as r:
                            if r.status == 200:
                                data = await r.json()
                                self.__data__[endpoint] = data[-1]
                            else:
                                bot.logger.error(f"API/Personal_Order, {r.status}")
                        continue
                    if endpoint == "status":
                        async with session.get(
                            "https://api.diveharder.com/raw/status"
                        ) as r:
                            if r.status == 200:
                                data = await r.json()
                                self.__data__[endpoint] = data
                            else:
                                bot.logger.error(f"API/Status, {r.status}")
                        continue

                    try:
                        async with session.get(f"{api_to_use}/api/v1/{endpoint}") as r:
                            if r.status == 200:
                                if endpoint == "dispatches":
                                    json = await r.json()
                                    if not json[0]["message"]:
                                        continue
                                elif endpoint == "assignments":
                                    json = await r.json()
                                    if json not in ([], None):
                                        if not json[0]["briefing"]:
                                            continue
                                self.__data__[endpoint] = await r.json()
                            else:
                                bot.logger.error(f"API/{endpoint.upper()}, {r.status}")
                                await bot.moderator_channel.send(
                                    f"API/{endpoint.upper()}\n{r}"
                                )
                    except Exception as e:
                        bot.logger.error(f"API/{endpoint.upper()}, {e}")
                        await bot.moderator_channel.send(f"API/{endpoint.upper()}\n{r}")
                    if api_to_use == backup_api:
                        await sleep(2)
        self.format_data()
        self.update_liberation_rates()
        self.update_dark_energy_rate()
        self.get_needed_players()
        self.fetched_at = datetime.now()
        if not self.loaded:
            now = datetime.now()
            bot.logger.info(
                f"setup complete | bot.ready_time: {bot.ready_time.strftime('%H:%M:%S')} -> {now.strftime('%H:%M:%S')} - saved {int((bot.ready_time - now).total_seconds())} seconds"
            )
            bot.ready_time = now
            self.loaded = True

    def format_data(self):
        self.assignment = None

        if self.__data__["war_time"]:
            self.war_time: int = (
                int(datetime.now().timestamp()) - self.__data__["war_time"]
            )

        if self.__data__["planets"]:
            self.planets: Planets = Planets(self.__data__["planets"])
            self.total_players = sum(
                [planet.stats["playerCount"] for planet in self.planets.values()]
            )

        if self.__data__["dss"]:
            if self.__data__["dss"] != "Error":
                self.dss: DSS = DSS(self.__data__["dss"], self.planets, self.war_time)
            else:
                self.dss: str = "Error"

        self.planet_events: list[Planet] = sorted(
            [planet for planet in self.planets.values() if planet.event],
            key=lambda planet: planet.stats["playerCount"],
            reverse=True,
        )

        if self.__data__["assignments"] not in ([], None):
            self.assignment: Assignment = Assignment(self.__data__["assignments"][0])
            factions = {
                1: "Humans",
                2: "Terminids",
                3: "Automaton",
                4: "Illuminate",
            }
            for task in self.assignment.tasks:
                task: Tasks.Task
                if task.type == 2:
                    self.planets[task.values[8]].in_assignment = True
                elif task.type == 3:
                    if task.progress == 1:
                        continue
                    for index in [
                        planet.index
                        for planet in self.planets.values()
                        if planet.current_owner == factions[task.values[0]]
                        or (
                            planet.event
                            and planet.event.faction == factions[task.values[0]]
                        )
                    ]:
                        self.planets[index].in_assignment = True
                elif task.type == 12:
                    if self.planet_events:
                        if task.values[3] != 0:
                            self.planets[task.values[3]].in_assignment = True
                            continue
                        for index in [
                            planet.index
                            for planet in self.planet_events
                            if planet.event
                            and planet.event.faction == factions[task.values[1]]
                        ]:
                            self.planets[index].in_assignment = True
                elif task.type in (11, 13):
                    self.planets[task.values[2]].in_assignment = True

        if self.__data__["campaigns"] not in ([], None):
            self.campaigns: list[Campaign] = sorted(
                [
                    Campaign(campaign, self.planets)
                    for campaign in self.__data__["campaigns"]
                ],
                key=lambda item: item.planet.stats["playerCount"],
                reverse=True,
            )

        if self.__data__["dispatches"]:
            self.dispatch: Dispatch = Dispatch(self.__data__["dispatches"][0])

        if self.__data__["thumbnails"]:
            self.thumbnails = self.__data__["thumbnails"]
            if self.planets:
                for thumbnail_data in self.thumbnails:
                    self.planets[thumbnail_data["planet"]["index"]].thumbnail = (
                        f"https://helldivers.news{thumbnail_data['planet']['image'].replace(' ', '%20')}"
                    )

        if self.__data__["steam"]:
            self.steam: list[Steam] = [Steam(notes) for notes in self.__data__["steam"]]

        if self.__data__["superstore"]:
            self.superstore: Superstore = Superstore(self.__data__["superstore"])

        if self.__data__["personal_order"]:
            self.personal_order: PersonalOrder = PersonalOrder(
                self.__data__["personal_order"]
            )

        if self.__data__["status"]:
            self.global_events: GlobalEvents = GlobalEvents(
                self.__data__["status"]["globalEvents"]
            )
            self.global_resources: GlobalResources = GlobalResources(
                self.__data__["status"]["globalResources"]
            )
            self.meridia_position = (
                self.__data__["status"]["planetStatus"][64]["position"]["x"],
                self.__data__["status"]["planetStatus"][64]["position"]["y"],
            )
            self.planets[64].position = {
                "x": self.meridia_position[0],
                "y": self.meridia_position[1],
            }
            planets_with_buildup = {
                planet_event["planetIndex"]: planet_event["potentialBuildUp"]
                for planet_event in self.__data__["status"]["planetEvents"]
                if planet_event["potentialBuildUp"] != 0
            }
            for index, buildup in planets_with_buildup.items():
                self.planets[index].event.potential_buildup = buildup

    def update_liberation_rates(self):
        for campaign in self.campaigns:
            if campaign.planet.index not in self.liberation_changes:
                self.liberation_changes[campaign.planet.index] = {
                    "liberation": campaign.progress,
                    "liberation_changes": [],
                }
            else:
                changes = self.liberation_changes[campaign.planet.index]
                if len(changes["liberation_changes"]) == 60:
                    changes["liberation_changes"].pop(0)
                while len(changes["liberation_changes"]) < 60:
                    changes["liberation_changes"].append(
                        campaign.progress - changes["liberation"]
                    )
                changes["liberation"] = campaign.progress

    def update_dark_energy_rate(self):
        if self.global_resources.dark_energy:
            if not self.dark_energy_changes["total"]:
                self.dark_energy_changes["total"] = (
                    self.global_resources.dark_energy.perc
                )
            else:
                if len(self.dark_energy_changes["changes"]) == 5:
                    self.dark_energy_changes["changes"].pop(0)
                while len(self.dark_energy_changes["changes"]) < 5:
                    self.dark_energy_changes["changes"].append(
                        (
                            self.global_resources.dark_energy.perc
                            - self.dark_energy_changes["total"]
                        )
                    )
                self.dark_energy_changes["total"] = (
                    self.global_resources.dark_energy.perc
                )

    def get_needed_players(self):
        now = datetime.now()
        if not self.planet_events:
            return
        for planet in self.planet_events:
            lib_changes = self.liberation_changes[planet.index]
            if (
                len(lib_changes["liberation_changes"]) == 0
                or sum(lib_changes["liberation_changes"]) == 0
            ):
                return
            progress_needed = 100 - lib_changes["liberation"]
            seconds_to_complete = int(
                (progress_needed / sum(lib_changes["liberation_changes"])) * 3600
            )
            winning = (
                now + timedelta(seconds=seconds_to_complete)
                < planet.event.end_time_datetime
            )
            if not winning:
                hours_left = (
                    planet.event.end_time_datetime - now
                ).total_seconds() / 3600
                progress_needed_per_hour = progress_needed / hours_left
                amount_ratio = progress_needed_per_hour / sum(
                    lib_changes["liberation_changes"]
                )
                required_players = planet.stats["playerCount"] * amount_ratio
                planet.event.required_players = required_players
        self.planets_with_player_reqs = {
            planet.index: planet.event.required_players
            for planet in self.planet_events
            if planet.event.required_players != 0
        }

    def copy(self):
        return deepcopy(self)


class Assignment(ReprMixin):
    def __init__(self, assignment: dict):
        self.id: int = assignment["id"]
        self.title = (
            steam_format(assignment["briefing"])
            if assignment["briefing"] not in ([], None)
            else ""
        )
        self.description = (
            steam_format(assignment["description"])
            if assignment["description"] not in ([], None, assignment["briefing"])
            else ""
        )
        self.tasks = Tasks(assignment)
        self.rewards = assignment["rewards"]
        self.ends_at = assignment["expiration"]
        self.ends_at_datetime = datetime.fromisoformat(self.ends_at)


class Tasks(list):
    def __init__(self, assignment):
        for index, task in enumerate(assignment["tasks"]):
            task = self.Task(task)
            if task.type in (15, 12):
                progress_value = task.values[0]
            elif task.type in (13, 11):
                progress_value = 1
            elif task.type in (3, 2):
                progress_value = task.values[2]
            task.progress = assignment["progress"][index] / progress_value
            self.append(task)

    class Task(ReprMixin):
        def __init__(self, task):
            self.type: int = task["type"]
            self.progress: float = 0
            self.values: list = task["values"]
            self.value_types: list = task["valueTypes"]

        @property
        def health_bar(self) -> str:
            if self.type == 2:
                return health_bar(
                    self.progress, "MO" if self.progress != 1 else "Humans"
                )
            elif self.type == 3:
                return health_bar(
                    self.progress,
                    (self.values[0] if self.progress != 1 else "Humans"),
                )
            elif self.type == 11:
                return
            elif self.type == 12:
                return health_bar(
                    self.progress,
                    "MO" if self.progress < 1 else "Humans",
                )
            elif self.type == 13:
                return ""
            elif self.type == 15:
                percent = task_type_15_progress_dict[
                    [
                        key
                        for key in task_type_15_progress_dict.keys()
                        if key <= self.progress
                    ][-1]
                ]
                return health_bar(
                    percent,
                    "Humans" if self.progress > 0 else "Automaton",
                )


class Campaign(ReprMixin):
    def __init__(self, campaign, planets):
        self.id: int = campaign["id"]
        self.planet: Planet = planets[campaign["planet"]["index"]]
        self.type: int = campaign["type"]
        self.count: int = campaign["count"]
        self.progress: float = (
            (1 - (self.planet.health / self.planet.max_health)) * 100
            if not self.planet.event
            else (1 - (self.planet.event.progress)) * 100
        )
        self.faction = (
            self.planet.event.faction
            if self.planet.event
            else self.planet.current_owner
        )


class Dispatch(ReprMixin):
    def __init__(self, dispatch):
        self.id: int = dispatch["id"]
        self.message = steam_format(dispatch["message"]) if dispatch["message"] else ""


class GlobalEvents(list):
    def __init__(self, global_events):
        for global_event in global_events:
            if not global_event.get("title", None):
                continue
            self.append(self.GlobalEvent(global_event))

    class GlobalEvent(ReprMixin):
        def __init__(self, global_event):
            self.id = global_event["eventId"]
            self.title = global_event["title"]
            self.message = steam_format(global_event["message"])
            self.faction = global_event["race"]
            self.flag = global_event["flag"]
            self.assignment_id = global_event["assignmentId32"]
            self.effect_ids = global_event["effectIds"]
            self.planet_indices = global_event["planetIndices"]

        @property
        def split_message(self):
            sentences = self.message.split("\n\n")
            formatted_sentences = [f"-# {sentence}" for sentence in sentences]
            chunks = []
            current_chunk = ""
            for sentence in formatted_sentences:
                if len(current_chunk) + len(sentence) + 2 <= 1024:
                    current_chunk += sentence + "\n\n"
                else:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence + "\n\n"
            if current_chunk:
                chunks.append(current_chunk.strip())
            return chunks


class GlobalResources(list):
    def __init__(self, global_resources):
        for global_resource in global_resources:
            if global_resource["id32"] == 194773219:
                self.dark_energy = self.DarkEnergy(global_resource)
            else:
                self.append(self.GlobalResource(global_resource))

    class GlobalResource(ReprMixin):
        def __init__(self, global_resource):
            self.id = global_resource["id32"]
            self.current_value = global_resource["currentValue"]
            self.max_value = global_resource["maxValue"]
            self.perc = self.current_value / self.max_value

    class DarkEnergy(GlobalResource):
        def __init__(self, global_resource):
            super().__init__(global_resource)

        @property
        def health_bar(self):
            return health_bar(self.perc, "Illuminate")


class Planet(ReprMixin):
    def __init__(self, planet_json: dict):
        self.index: int = planet_json["index"]
        self.name: str = planet_json["name"]
        self.sector: str = planet_json["sector"]
        self.biome: dict = planet_json["biome"]
        self.hazards: list[dict] = planet_json["hazards"]
        self.position: dict = planet_json["position"]
        self.waypoints: list[int] = planet_json["waypoints"]
        self.max_health: int = planet_json["maxHealth"]
        self.health: int = planet_json["health"]
        self.health_perc: float = self.health / self.max_health
        self.current_owner: str = planet_json["currentOwner"]
        self.regen: float = planet_json["regenPerSecond"]
        self.regen_perc_per_hour = round(
            (((self.regen * 3600) / self.max_health) * 100), 2
        )
        self.event = self.Event(planet_json["event"]) if planet_json["event"] else None
        self.stats: dict = planet_json["statistics"]
        self.thumbnail = None
        self.feature = {
            45: "Center for Civilian Surveillance",
            125: "Centre of Science",
            126: "Xenoentomology Center",
            130: "Factory Hub",
            161: "Deep Mantle Forge Complex",
        }.get(self.index, None)
        self.dss = False
        self.in_assignment = False

    class Event(ReprMixin):
        def __init__(self, event):
            self.id: int = event["id"]
            self.type: int = event["eventType"]
            self.faction: str = event["faction"]
            self.health: int = event["health"]
            self.max_health: int = event["maxHealth"]
            self.start_time = event["startTime"]
            self.end_time = event["endTime"]
            self.start_time_datetime = datetime.fromisoformat(self.start_time).replace(
                tzinfo=None
            )
            self.end_time_datetime = datetime.fromisoformat(self.end_time).replace(
                tzinfo=None
            )
            self.progress: float = self.health / self.max_health
            self.required_players: int = 0
            self.level: int = int(self.max_health / 50000)
            self.potential_buildup = 0

        @property
        def remaining_dark_energy(self) -> float:
            return self.potential_buildup * (
                1
                - (datetime.now() - self.start_time_datetime).total_seconds()
                / (self.end_time_datetime - self.start_time_datetime).total_seconds()
            )

        @property
        def health_bar(self) -> str:
            return health_bar(self.progress, self.faction, True)


class Planets(dict[int, Planet]):
    def __init__(self, planets: dict):
        for planet in planets:
            self[planet["index"]] = Planet(planet)

    def get_by_name(self, name: str) -> Planet | None:
        planet_list = [
            planet for planet in self.values() if planet.name.upper() == name.upper()
        ]
        return None if not planet_list else planet_list[0]


class PlanetEvents(list[Planet]):
    def __init__(self, planet_events):
        for planet in planet_events:
            self.append(Planet(planet))


class Steam(ReprMixin):
    def __init__(self, steam):
        self.id: int = int(steam["id"])
        self.title: str = steam["title"]
        self.content: str = steam_format(steam["content"])
        self.author: str = steam["author"]
        self.url: str = steam["url"]


class Superstore(ReprMixin):
    def __init__(self, superstore):
        self.expiration = superstore["expire_time"]
        self.items: dict = superstore["items"]


class DSS(ReprMixin):
    def __init__(self, dss, planets, war_time):
        self.planet: Planet = planets[dss["planetIndex"]]
        self.planet.dss = True
        self.election_war_time: int = dss["currentElectionEndWarTime"]
        self.election_date_time = datetime.fromtimestamp(
            war_time + self.election_war_time
        )
        self.tactical_actions: list[DSS.TacticalAction] = [
            self.TacticalAction(tactical_action, war_time)
            for tactical_action in dss["tacticalActions"]
        ]

    class TacticalAction(ReprMixin):
        def __init__(self, tactical_action, war_time):
            self.name: str = tactical_action["name"]
            self.description: str = tactical_action["description"]
            self.status: int = tactical_action["status"]
            self.status_end: int = tactical_action["statusExpireAtWarTimeSeconds"]
            self.status_end_datetime = datetime.fromtimestamp(
                war_time + self.status_end
            )
            self.strategic_description: str = steam_format(
                tactical_action["strategicDescription"]
            )
            self.cost = self.Cost(tactical_action["cost"][0])

        class Cost(ReprMixin):
            def __init__(self, cost):
                self.item: str = {
                    2985106497: "Rare Sample",
                    3992382197: "Common Sample",
                    3608481516: "Requisition Slip",
                }.get(cost["itemMixId"], "Unknown")
                self.target: int = cost["targetValue"]
                self.current: float = cost["currentValue"]
                self.progress: float = self.current / self.target
                self.max_per_seconds: tuple = (
                    cost["maxDonationAmount"],
                    cost["maxDonationPeriodSeconds"],
                )


class PersonalOrder(ReprMixin):
    def __init__(self, personal_order: dict):
        self.id: int = personal_order["id32"]
        self.expiration_secs_from_now: int = personal_order["expiresIn"]
        self.expiration_datetime: datetime = datetime.fromtimestamp(
            datetime.now().timestamp() + self.expiration_secs_from_now
        )
        self.setting = self.Setting(personal_order["setting"])

    class Setting(ReprMixin):
        def __init__(self, setting: dict):
            self.type: int = setting["type"]
            self.title: str = setting["overrideTitle"]
            self.brief: str = setting["overrideBrief"]
            self.description: str = setting["taskDescription"]
            self.tasks = self.Tasks(setting["tasks"])
            self.rewards = self.Rewards(setting["rewards"])
            self.flags: int = setting["flags"]

        class Tasks(list):
            def __init__(self, tasks: list):
                for task in tasks:
                    self.append(self.Task(task))

            class Task(ReprMixin):
                def __init__(self, task: dict):
                    self.type: int = task["type"]
                    self.values: dict = task["values"]
                    self.value_types: dict = task["valueTypes"]

        class Rewards(list):
            def __init__(self, rewards: list):
                for reward in rewards:
                    self.append(self.Reward(reward))

            class Reward(ReprMixin):
                def __init__(self, reward: dict):
                    self.type: int = reward["type"]
                    self.amount: int = reward["amount"]
