from json import dumps, loads
from logging import getLogger
from os import getenv
from aiohttp import ClientSession
from helpers.functions import steam_format

logger = getLogger("disnake")


class API:
    def __init__(self):
        self._api = getenv("API")
        self._backup_api = getenv("BU_API")
        self.error = None
        self.war = None
        self.assignment = None
        self.campaigns = None
        self.dispatches = None
        self.planets = None
        self.planet_events = None
        self.steam = None
        self.thumbnails = None

    async def pull_from_api(
        self,
        get_war: bool = False,
        get_assignment: bool = False,
        get_campaigns: bool = False,
        get_dispatches: bool = False,  # first index is newest
        get_planets: bool = False,
        get_planet_events: bool = False,
        get_steam: bool = False,  # first index is newest
        get_thumbnail: bool = False,
    ):
        async with ClientSession(headers={"Accept-Language": "en-GB"}) as session:
            async with session.get(f"{self._api}") as r:
                if r.status != 200:
                    self._api = self._backup_api
                    logger.critical("API/USING BACKUP")
                if get_war:
                    try:
                        async with session.get(f"{self._api}/api/v1/war") as r:
                            if r.status == 200:
                                js = await r.json()
                                self.war = loads(dumps(js))
                            else:
                                self.error = ("API/WAR", r.status)
                                logger.error(f"API/WAR, {r.status}")
                    except Exception as e:
                        self.error = ("API/WAR", e)
                        logger.error(f"API/WAR, {e}")
                if get_assignment:
                    try:
                        async with session.get(f"{self._api}/api/v1/assignments") as r:
                            if r.status == 200:
                                js = await r.json()
                                self.assignment = loads(dumps(js))
                                if self.assignment != []:
                                    self.assignment = self.assignment[0]
                            else:
                                self.error = ("API/ASSIGNMENT", r.status)
                                logger.error(f"API/ASSIGNMENT, {r.status}")
                    except Exception as e:
                        self.error = ("API/ASSIGNMENT", e)
                        logger.error(f"API/ASSIGNMENT, {e}")
                if get_campaigns:
                    try:
                        async with session.get(f"{self._api}/api/v1/campaigns") as r:
                            if r.status == 200:
                                js = await r.json()
                                self.campaigns = loads(dumps(js))
                            else:
                                self.error = ("API/CAMPAIGNS", r.status)
                                logger.error(f"API/CAMPAIGNS, {r.status}")
                    except Exception as e:
                        self.error = ("API/CAMPAIGNS", e)
                        logger.error(f"API/CAMPAIGNS, {e}")
                if get_dispatches:
                    try:
                        async with session.get(f"{self._api}/api/v1/dispatches") as r:
                            if r.status == 200:
                                js = await r.json()
                                self.dispatches = loads(dumps(js))
                            else:
                                self.error = ("API/DISPATCHES", r.status)
                                logger.error(f"API/DISPATCHES, {r.status}")
                    except Exception as e:
                        self.error = ("API/DISPATCHES", e)
                        logger.error(f"API/DISPATCHES, {e}")
                if get_planets:
                    try:
                        async with session.get(f"{self._api}/api/v1/planets") as r:
                            if r.status == 200:
                                js = await r.json()
                                self.planets = loads(dumps(js))
                            else:
                                self.error = ("API/PLANETS", r.status)
                                logger.error(f"API/PLANETS, {r.status}")
                    except Exception as e:
                        self.error = ("API/PLANETS", e)
                        logger.error(f"API/PLANETS, {e}")
                if get_planet_events:
                    try:
                        async with session.get(
                            f"{self._api}/api/v1/planet-events"
                        ) as r:
                            if r.status == 200:
                                js = await r.json()
                                self.planet_events = loads(dumps(js)) or None
                            else:
                                self.error = ("API/PLANET-EVENTS", r.status)
                                logger.error(f"API/PLANET-EVENTS, {r.status}")
                    except Exception as e:
                        self.error = ("API/PLANET-EVENTS", e)
                        logger.error(f"API/PLANET-EVENTS, {e}")
                if get_steam:
                    try:
                        async with session.get(f"{self._api}/api/v1/steam") as r:
                            if r.status == 200:
                                js = await r.json()
                                self.steam = loads(dumps(js))
                            else:
                                self.error = ("API/STEAM", r.status)
                                logger.error(f"API/STEAM, {r.status}")
                    except Exception as e:
                        self.error = ("API/STEAM", e)
                        logger.error(f"API/STEAM, {e}")
                if get_thumbnail:
                    try:
                        async with session.get(
                            f"https://helldivers.news/api/planets"
                        ) as r:
                            if r.status == 200:
                                js = await r.json()
                                self.thumbnails = loads(dumps(js))
                            else:
                                self.error = ("API/THUMBNAILS", r.status)
                                logger.error(f"API/THUMBNAILS, {r.status}")
                    except Exception as e:
                        self.error = ("API/THUMBNAILS", e)
                        logger.error(f"API/THUMBNAILS, {e}")
        self.all = {
            "self.war": self.war,
            "self.assignment": self.assignment,
            "self.campaigns": self.campaigns,
            "self.dispatches": self.dispatches,
            "self.planets": self.planets,
            "self.planet_events": self.planet_events,
            "self.steam": self.steam,
            "self.thumbnails": self.thumbnails,
        }


class Data:
    def __init__(self, data_from_api: API):
        self.__data__ = data_from_api
        self.assignment = None
        self.assignment_planets = None

        self.planet_events = (
            PlanetEvents(self.__data__.planet_events)
            if self.__data__.planet_events
            else None
        )

        if self.__data__.planets:
            self.planets: dict[int, Planet] = {
                planet["index"]: Planet(planet) for planet in self.__data__.planets
            }
            self.total_players = sum(
                [planet.stats["playerCount"] for planet in self.planets.values()]
            )

        if self.__data__.assignment not in ([], None):
            self.assignment = Assignment(self.__data__.assignment)
            self.assignment_planets = []
            for task in self.assignment.tasks:
                task: Tasks.Task
                if task.type in (11, 13):
                    self.assignment_planets.append(self.planets[task.values[2]].name)
                elif task.type == 12:
                    if self.planet_events:
                        factions = {
                            1: "Humans",
                            2: "Terminids",
                            3: "Automaton",
                            4: "Illuminate",
                        }
                        self.assignment_planets += [
                            planet.name
                            for planet in self.planet_events
                            if planet.event
                            and planet.event.faction == factions[task.values[1]]
                        ]

        if self.__data__.campaigns not in ([], None):
            self.campaigns: list[Campaign] = []
            for campaign in self.__data__.campaigns:
                self.campaigns.append(Campaign(campaign))
            self.campaigns = sorted(
                self.campaigns,
                key=lambda item: item.planet.stats["playerCount"],
                reverse=True,
            )

        if self.__data__.dispatches:
            self.dispatch = Dispatch(self.__data__.dispatches[0])

        if self.__data__.thumbnails:
            self.thumbnails = self.__data__.thumbnails
            # TODO link thumbnails to planets

        if self.__data__.steam:
            self.steam = Steam(self.__data__.steam[0])

    def __repr__(self):
        text = "Raw data:"
        for name, data in self.__data__.all.items():
            text += f"\n{name} = PRESENT" if data else f"\n{name} = MISSING"
        return text


class War:
    """Currently Not Used"""

    pass


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
        self.reward = self.__assignment["reward"]
        self.ends_at = self.__assignment["expiration"]

    def __repr__(self):
        text = (
            f"{'ASSIGNMENT':=^35}"
            f"\nID: {self.id}:"
            f"\nTitle: {self.title}"
            f"\nDescription: {self.description}"
            f"\nTasks:"
        )
        for task in self.tasks:
            text += f"\n    {task}"
        text += f"\nReward: {self.reward}"
        return text


class Tasks(list):
    def __init__(self, assignment):
        self.__assignment = assignment
        for index, task in enumerate(self.__assignment["tasks"]):
            formatted_task = self.Task(task)
            progress_value = {
                13: formatted_task.values[0],
                12: formatted_task.values[1],
                11: formatted_task.values[0],
                3: formatted_task.values[2],
                2: formatted_task.values[2],
            }[formatted_task.type]
            formatted_task.progress = (
                self.__assignment["progress"][index] / progress_value
            )
            self.append(formatted_task)

    class Task:
        def __init__(self, task):
            self.type: int = task["type"]
            self.progress: float = 0
            self.values: list = task["values"]
            self.valueTypes: list = task["valueTypes"]
            self.health_bar: str = ""

        def __repr__(self):
            return f"Type: {self.type} - Progress: {self.progress:.2%} - Values: {self.values} - ValueTypes: {self.valueTypes}"


class Campaign:
    def __init__(self, campaign):
        self.id: int = campaign["id"]
        self.planet = Planet(campaign["planet"])
        self.type: int = campaign["type"]
        self.count: int = campaign["count"]

    def __repr__(self):
        return (
            f"{'CAMPAIGN':=^35}"
            f"\nID: {self.id}:"
            f"\nPlanet: {self.planet.name}"
            f"\nDefense: {self.planet.event is not None}"
            f"\nType: {self.type}"
            f"\nCount: {self.count}"
        )


class Dispatch:
    def __init__(self, dispatch):
        self.id: int = dispatch["id"]
        self.message = steam_format(dispatch["message"])

    def __repr__(self):
        return f"{self.id} - {self.message}"


class Planet:
    def __init__(self, planet):
        self.index: int = planet["index"]
        self.name: str = planet["name"]
        self.sector: str = planet["sector"]
        self.biome: dict = planet["biome"]
        self.hazards: list[dict] = planet["hazards"]
        self.position: dict = planet["position"]
        self.waypoints: list[int] = planet["waypoints"]
        self.max_health: int = planet["maxHealth"]
        self.health: int = planet["health"]
        self.current_owner: str = planet["currentOwner"]
        self.regen: float = planet["regenPerSecond"]
        self.event = self.Event(planet["event"]) if planet["event"] else None
        self.stats: dict = planet["statistics"]

    def __repr__(self):
        atk_def = {True: "Defense", False: "Attack"}[self.event is not None]
        return f"{self.name} - {self.current_owner} - {atk_def}"

    class Event:
        def __init__(self, event):
            self.id: int = event["id"]
            self.type: int = event["eventType"]
            self.faction: str = event["faction"]
            self.health: int = event["health"]
            self.max_health: int = event["maxHealth"]
            self.start_time = event["startTime"]
            self.end_time = event["endTime"]

        def __repr__(self):
            return f"{self.id} - {self.type} - {self.faction}"


class PlanetEvents(list):
    def __init__(self, planet_events):
        for planet in planet_events:
            self.append(Planet(planet))

    def __repr__(self):
        return f"Planet events: {len(self)}"


class Steam:
    def __init__(self, steam):
        self.id = steam["id"]
        self.title = steam["title"]
        self.content = steam_format(steam["content"])
        self.author = steam["author"]
        self.url = steam["url"]

    def __repr__(self):
        return f"Steam: {self.id} - {self.url} - {len(self.content)}"


class Thumbnail:
    pass
