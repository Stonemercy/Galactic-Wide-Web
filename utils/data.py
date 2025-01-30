from copy import deepcopy
from aiohttp import ClientSession
from asyncio import sleep
from data.lists import task_type_15_progress_dict
from datetime import datetime, timedelta
from os import getenv
from utils.functions import health_bar, steam_format

api = getenv("API")
backup_api = getenv("BU_API")


class Data:
    __slots__ = (
        "__data__",
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
        "planets_with_player_reqs",
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
            "global_events": None,
        }
        self.loaded = False
        self.liberation_changes = {}
        self.planets_with_player_reqs = {}

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
                    if endpoint == "global_events":
                        async with session.get(
                            "https://api.diveharder.com/v1/status"
                        ) as r:
                            if r.status == 200:
                                data = await r.json()
                                self.__data__[endpoint] = data["globalEvents"]
                            else:
                                bot.logger.error(f"API/Global_Events, {r.status}")
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
        if not self.loaded:
            now = datetime.now()
            bot.logger.info(
                f"setup complete | bot.ready_time: {bot.ready_time.strftime('%H:%M:%S')} -> {now.strftime('%H:%M:%S')} - saved {int((bot.ready_time - now).total_seconds())} seconds"
            )
            bot.ready_time = now
            self.loaded = True
        self.format_data()
        self.update_liberation_rates()
        self.get_needed_players()

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

        if self.__data__["global_events"]:
            self.global_events: GlobalEvents = GlobalEvents(
                self.__data__["global_events"]
            )

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


class Assignment:
    def __init__(self, assignment: dict):
        self.__assignment = assignment
        self.id: int = self.__assignment["id"]
        self.title = (
            steam_format(self.__assignment["briefing"])
            if self.__assignment["briefing"] not in ([], None)
            else ""
        )
        self.description = (
            steam_format(self.__assignment["description"])
            if self.__assignment["description"]
            not in ([], None, self.__assignment["briefing"])
            else ""
        )
        self.tasks = Tasks(self.__assignment)
        self.rewards = self.__assignment["rewards"]
        self.ends_at = self.__assignment["expiration"]
        self.ends_at_datetime = datetime.fromisoformat(self.ends_at)

    def __repr__(self):
        return (
            f"Assignment(id={self.id}, title={self.title}, description={self.description}, tasks={self.tasks} "
            f"rewards={self.rewards}, ends_at={self.ends_at}, ends_at_datetime={self.ends_at_datetime})"
        )


class Tasks(list):
    def __init__(self, assignment):
        self.__assignment = assignment
        for index, task in enumerate(self.__assignment["tasks"]):
            task = self.Task(task)
            if task.type in (15, 12):
                progress_value = task.values[0]
            elif task.type in (13, 11):
                progress_value = 1
            elif task.type in (3, 2):
                progress_value = task.values[2]
            task.progress = self.__assignment["progress"][index] / progress_value
            self.append(task)

    class Task:
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

        def __repr__(self):
            return (
                f"Task(type={self.type}, progress={self.progress}, values={self.values} "
                f"value_types={self.value_types}, health_bar={self.health_bar})"
            )


class Campaign:
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

    def __repr__(self):
        return f"Campaign(id={self.id}, planet={self.planet}, type={self.type}, count={self.count}, progress={self.progress}, faction={self.faction})"


class Dispatch:
    def __init__(self, dispatch):
        self.id: int = dispatch["id"]
        self.message = steam_format(dispatch["message"]) if dispatch["message"] else ""

    def __repr__(self):
        return f"Dispatch(id={self.id}, message={self.message})"


class GlobalEvents(list):
    def __init__(self, global_events):
        for global_event in global_events:
            self.append(self.GlobalEvent(global_event))

    class GlobalEvent:
        def __init__(self, global_event):
            self.id = global_event["eventId"]
            self.title = global_event["title"]
            self.message = steam_format(global_event["message"])
            self.faction = global_event["race"]
            self.flag = global_event["flag"]
            self.assignment_id = global_event["assignmentId32"]

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

        def __repr__(self):
            return f"GlobalEvent({self.id, self.title, self.message, self.faction, self.flag, self.assignment_id})"


class Planet:
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
        self.regen_perc_per_hour = ((self.regen * 3600) / self.max_health) * 100
        self.event = self.Event(planet_json["event"]) if planet_json["event"] else None
        self.stats: dict = planet_json["statistics"]
        self.thumbnail = None
        self.feature = {
            45: "Center for Civilian Surveillance",
            125: "Centre of Science",
            126: "Xenoentomology Center",
            130: "Factory Hub",
            160: "Jet Brigade Factories",
            161: "Deep Mantle Forge Complex",
        }.get(self.index, None)
        self.dss = False
        self.in_assignment = False

    def __repr__(self):
        return (
            f"Planet(index={self.index}, name='{self.name}', sector='{self.sector}', "
            f"biome={self.biome}, hazards={self.hazards}, position={self.position}, "
            f"waypoints={self.waypoints}, max_health={self.max_health}, health={self.health}, "
            f"current_owner='{self.current_owner}', regen={self.regen}, event={self.event}, "
            f"stats={self.stats}, thumbnail={self.thumbnail}, feature={self.feature}, "
            f"dss={self.dss}, in_assignment={self.in_assignment})"
        )

    class Event:
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

        @property
        def health_bar(self) -> str:
            return health_bar(self.progress, self.faction, True)

        def __repr__(self):
            return (
                f"Event(id={self.id}, type={self.type}, faction={self.faction}, health={self.health}) "
                f"max_health={self.max_health}, start_time={self.start_time}, end_time={self.end_time}, progress={self.progress})"
            )


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


class Steam:
    def __init__(self, steam):
        self.id: int = int(steam["id"])
        self.title: str = steam["title"]
        self.content: str = steam_format(steam["content"])
        self.author: str = steam["author"]
        self.url: str = steam["url"]

    def __repr__(self):
        return f"Steam(id={self.id}, title={self.title}, content={self.content}, author={self.author}, url={self.url})"


class Superstore:
    def __init__(self, superstore):
        self.expiration = superstore["expire_time"]
        self.items: dict = superstore["items"]

    def __repr__(self):
        return f"Superstore(expiration={self.expiration}, item1={self.item1}, item2={self.item2}, item3={self.item3}, item4={self.item4})"


class DSS:
    def __init__(self, dss, planets, war_time):
        self.planet: Planet = planets[dss["planetIndex"]]
        self.planet.dss = True
        self.election_war_time: int = dss["currentElectionEndWarTime"]
        self.election_date_time = datetime.fromtimestamp(
            war_time + self.election_war_time
        )
        self.tactical_actions: list[self.TacticalAction] = [
            self.TacticalAction(tactical_action, war_time)
            for tactical_action in dss["tacticalActions"]
        ]

    class TacticalAction:
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

        class Cost:
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


class PersonalOrder:
    def __init__(self, personal_order: dict):
        self.id: int = personal_order["id32"]
        self.expiration_secs_from_now: int = personal_order["expiresIn"]
        self.expiration_datetime: datetime = datetime.fromtimestamp(
            datetime.now().timestamp() + self.expiration_secs_from_now
        )
        self.setting = self.Setting(personal_order["setting"])

    def __repr__(self):
        return f"PersonalOrder(id={self.id}, expiration_secs_from_now={self.expiration_secs_from_now}, expiration_datetime={self.expiration_datetime}, setting={self.setting})"

    class Setting:
        def __init__(self, setting: dict):
            self.type: int = setting["type"]
            self.title: str = setting["overrideTitle"]
            self.brief: str = setting["overrideBrief"]
            self.description: str = setting["taskDescription"]
            self.tasks = self.Tasks(setting["tasks"])
            self.rewards = self.Rewards(setting["rewards"])
            self.flags: int = setting["flags"]

        def __repr__(self):
            return f"Setting(type={self.type}, title={self.title}, brief={self.brief}, description={self.description}, tasks={self.tasks}, rewards={self.rewards}, flags={self.flags})"

        class Tasks(list):
            def __init__(self, tasks: list):
                for task in tasks:
                    self.append(self.Task(task))

            class Task:
                def __init__(self, task: dict):
                    self.type: int = task["type"]
                    self.values: dict = task["values"]
                    self.value_types: dict = task["valueTypes"]

                def __repr__(self):
                    return f"Task(type={self.type}, values={self.values}, value_types={self.value_types})"

        class Rewards(list):
            def __init__(self, rewards: list):
                for reward in rewards:
                    self.append(self.Reward(reward))

            class Reward:
                def __init__(self, reward: dict):
                    self.type: int = reward["type"]
                    self.amount: int = reward["amount"]

                def __repr__(self):
                    return f"Reward(type={self.type}, amount={self.amount})"
