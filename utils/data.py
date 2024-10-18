from datetime import datetime, timedelta
from utils.functions import steam_format


class Data:
    def __init__(self, data_from_api: dict):
        self.__data__ = data_from_api
        self.assignment = self.assignment_planets = None
        planet_events_list = sorted(
            [planet for planet in self.__data__["planets"] if planet["event"]],
            key=lambda planet: planet["statistics"]["playerCount"],
            reverse=True,
        )
        self.planet_events: PlanetEvents = (
            PlanetEvents(planet_events_list) if planet_events_list != [] else None
        )

        if self.__data__["planets"]:
            self.planets: dict[int, Planet] = {
                planet["index"]: Planet(planet) for planet in self.__data__["planets"]
            }
            self.total_players = sum(
                [planet.stats["playerCount"] for planet in self.planets.values()]
            )

        if self.__data__["assignments"] not in ([], None):
            self.assignment = Assignment(self.__data__["assignments"][0])
            self.assignment_planets = []
            for task in self.assignment.tasks:
                task: Tasks.Task
                if task.type in (11, 13):
                    self.assignment_planets.append(self.planets[task.values[2]].index)
                elif task.type in (3, 12):
                    if self.planet_events:
                        factions = {
                            1: "Humans",
                            2: "Terminids",
                            3: "Automaton",
                            4: "Illuminate",
                        }
                        self.assignment_planets += [
                            planet.index
                            for planet in self.planet_events
                            if planet.event
                            and planet.event.faction == factions[task.values[1]]
                        ]

        if self.__data__["campaigns"] not in ([], None):
            self.campaigns: list[Campaign] = [
                Campaign(campaign) for campaign in self.__data__["campaigns"]
            ]
            self.campaigns = sorted(
                self.campaigns,
                key=lambda item: item.planet.stats["playerCount"],
                reverse=True,
            )

        if self.__data__["dispatches"]:
            self.dispatch = Dispatch(self.__data__["dispatches"][0])

        if self.__data__["thumbnails"]:
            self.thumbnails = self.__data__["thumbnails"]
            if self.planets:
                for thumbnail_data in self.thumbnails:
                    self.planets[thumbnail_data["planet"]["index"]].thumbnail = (
                        f"https://helldivers.news{thumbnail_data['planet']['image'].replace(' ', '%20')}"
                    )

        if self.__data__["steam"]:
            self.steam = Steam(self.__data__["steam"][0])


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
        self.ends_at_datetime = datetime.fromisoformat(self.ends_at)

    def __repr__(self):
        return (
            f"Assignment(id={self.id}, title={self.title}, description={self.description}, tasks={self.tasks} "
            f"reward={self.reward}, ends_at={self.ends_at}, ends_at_datetime={self.ends_at_datetime})"
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
            self.health_bar: str = ""

        def __repr__(self):
            return (
                f"Task(type={self.type}, progress={self.progress}, values={self.values} "
                f"value_types={self.value_types}, health_bar={self.health_bar})"
            )


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
        return f"Campaign(id={self.id}, planet={self.planet}, type={self.type}, count={self.count}, progress={self.progress}, faction={self.faction})"


class Dispatch:
    def __init__(self, dispatch):
        self.id: int = dispatch["id"]
        self.message = steam_format(dispatch["message"]) if dispatch["message"] else ""

    def __repr__(self):
        return f"Dispatch(id={self.id}, message={self.message})"


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
        self.feature = {
            116: "DSS Construction Site",
            126: "Xenoentomology Center",
            161: "Deep Mantle Forge Complex",
        }.get(self.index, None)

    def __repr__(self):
        return (
            f"Planet(index={self.index}, name={self.name}, sector={self.sector} "
            f"biome={self.biome}, hazards={self.hazards}, position={self.position} "
            f"waypoints={self.waypoints}, max_health={self.max_health}, health={self.health} "
            f"current_owner={self.current_owner}, regen={self.regen}, event={self.event} "
            f"stats={self.stats}, thumbnail={self.thumbnail})"
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
            ) + timedelta(hours=1)
            self.end_time_datetime = datetime.fromisoformat(self.end_time).replace(
                tzinfo=None
            ) + timedelta(hours=1)
            self.progress: float = self.health / self.max_health

        def __repr__(self):
            return (
                f"Event(id={self.id}, type={self.type}, faction={self.faction}, health={self.health}) "
                f"max_health={self.max_health}, start_time={self.start_time}, end_time={self.end_time}, progress={self.progress})"
            )


class PlanetEvents(list[Planet]):
    def __init__(self, planet_events):
        for planet in planet_events:
            self.append(Planet(planet))


class Steam:
    def __init__(self, steam):
        self.id = steam["id"]
        self.title = steam["title"]
        self.content = steam_format(steam["content"])
        self.author = steam["author"]
        self.url = steam["url"]

    def __repr__(self):
        return f"Steam(id={self.id}, title={self.title}, content={self.content}, author={self.author}, url={self.url})"


class Thumbnail:
    pass
