from json import dumps, loads
from logging import getLogger
from os import getenv
from aiohttp import ClientSession
from utils.functions import steam_format

logger = getLogger("disnake")


class API:
    def __init__(self):
        self._api = getenv("API")
        self._backup_api = getenv("BU_API")
        self.error: tuple[str, Exception | int] | None = None
        self.war = self.assignments = self.campaigns = self.dispatches = (
            self.planets
        ) = self.planet_events = self.steam = self.thumbnails = None

    async def fetch_data(self, session: ClientSession, endpoint: str, attr_name):
        try:
            async with session.get(f"{self._api}/api/v1/{endpoint}") as r:
                if r.status == 200:
                    setattr(self, attr_name, await r.json())
                else:
                    self.error = (f"API/{endpoint.upper()}", r.status)
                    logger.error(f"API/{endpoint.upper()}, {r.status}")
        except Exception as e:
            self.error = (f"API/{endpoint.upper()}", e)
            logger.error(f"API/{endpoint.upper()}, {e}")

    async def pull_from_api(
        self,
        get_war: bool = False,
        get_assignments: bool = False,
        get_campaigns: bool = False,
        get_dispatches: bool = False,  # first index is newest
        get_planets: bool = False,
        get_planet_events: bool = False,
        get_steam: bool = False,  # first index is newest
        get_thumbnail: bool = False,
    ):
        self.endpoints = {
            "war": get_war,
            "assignments": get_assignments,
            "campaigns": get_campaigns,
            "dispatches": get_dispatches,
            "planets": get_planets,
            "planet-events": get_planet_events,
            "steam": get_steam,
        }
        async with ClientSession(headers={"Accept-Language": "en-GB"}) as session:
            async with session.get(f"{self._api}") as r:
                if r.status != 200:
                    self._api = self._backup_api
                    logger.critical("API/USING BACKUP")

                for endpoint, should_fetch in self.endpoints.items():
                    if should_fetch:
                        await self.fetch_data(
                            session, endpoint, endpoint.replace("-", "_")
                        )
                if get_thumbnail:
                    try:
                        async with session.get(
                            f"https://helldivers.news/api/planets"
                        ) as r:
                            if r.status == 200:
                                self.thumbnails = await r.json()
                            else:
                                self.error = ("API/THUMBNAILS", r.status)
                                logger.error(f"API/THUMBNAILS, {r.status}")
                    except Exception as e:
                        self.error = ("API/THUMBNAILS", e)
                        logger.error(f"API/THUMBNAILS, {e}")

        self.all = {
            "self.war": {"wanted": get_war, "recieved": self.war != None},
            "self.assignment": {
                "wanted": get_assignments,
                "recieved": self.assignments != None,
            },
            "self.campaigns": {
                "wanted": get_campaigns,
                "recieved": self.campaigns != None,
            },
            "self.dispatches": {
                "wanted": get_dispatches,
                "recieved": self.dispatches != None,
            },
            "self.planets": {"wanted": get_planets, "recieved": self.planets != None},
            "self.planet_events": {
                "wanted": get_planet_events,
                "recieved": self.planet_events != None,
            },
            "self.steam": {"wanted": get_steam, "recieved": self.steam != None},
            "self.thumbnails": {
                "wanted": get_thumbnail,
                "recieved": self.thumbnails != None,
            },
        }


class Data:
    def __init__(self, data_from_api: API):
        self.__data__ = data_from_api
        self.assignment = self.assignment_planets = None

        self.planet_events: PlanetEvents = (
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

        if self.__data__.assignments not in ([], None):
            self.assignment = Assignment(self.__data__.assignments[0])
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
            self.campaigns: list[Campaign] = [
                Campaign(campaign) for campaign in self.__data__.campaigns
            ]
            self.campaigns = sorted(
                self.campaigns,
                key=lambda item: item.planet.stats["playerCount"],
                reverse=True,
            )

        if self.__data__.dispatches:
            self.dispatch = Dispatch(self.__data__.dispatches[0])

        if self.__data__.thumbnails:
            self.thumbnails = self.__data__.thumbnails
            if self.planets:
                for thumbnail_data in self.thumbnails:
                    self.planets[thumbnail_data["planet"]["index"]].thumbnail = (
                        f"https://helldivers.news{thumbnail_data['planet']['image'].replace(' ', '%20')}"
                    )

        if self.__data__.steam:
            self.steam = Steam(self.__data__.steam[0])

    def __str__(self) -> str:
        text = f"Data"
        for name, data in self.__data__.all.items():
            if data["wanted"]:
                text += f"\n{name}:\n    Correct: {data['wanted'] == data['recieved']}"
        text += "\n=====END====="
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
            task = self.Task(task)
            progress_value = {
                13: 1,
                12: task.values[0],
                11: 1,
                3: task.values[2],
                2: task.values[2],
            }[task.type]
            task.progress = self.__assignment["progress"][index] / progress_value
            self.append(task)

    class Task:
        def __init__(self, task):
            self.type: int = task["type"]
            self.progress: float = 0
            self.values: list = task["values"]
            self.value_types: list = task["valueTypes"]
            self.health_bar: str = ""

        def __repr__(self):
            return f"Type: {self.type} - Progress: {self.progress:.2%} - Values: {self.values} - ValueTypes: {self.value_types}"


class Campaign:
    def __init__(self, campaign):
        self.id: int = campaign["id"]
        self.planet = Planet(campaign["planet"])
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
        self.thumbnail = None

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
            self.progress: float = self.health / self.max_health

        def __repr__(self):
            return f"{self.id} - {self.type} - {self.faction}"


class PlanetEvents(list[Planet]):
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
