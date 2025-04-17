from aiohttp import ClientSession, ClientSSLError
from asyncio import sleep
from copy import deepcopy
from datetime import datetime, timedelta
from disnake import TextChannel
from logging import Logger
from os import getenv
from typing import ItemsView, ValuesView
from utils.functions import health_bar, steam_format
from utils.mixins import ReprMixin
from utils.trackers import LiberationChangesTracker

api = getenv(key="API")
backup_api = getenv(key="BU_API")


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
        "personal_order",
        "global_events",
        "loaded",
        "liberation_changes",
        "dark_energy_changes",
        "meridia_position",
        "galactic_impact_mod",
    )

    def __init__(self) -> None:
        """The object to retrieve and organise all 3rd-party data used by the bot"""
        self.__data__: dict[str,] = {
            "assignments": None,
            "campaigns": None,
            "dispatches": None,
            "planets": None,
            "steam": None,
            "thumbnails": None,
            "superstore": None,
            "dss": None,
            "personal_order": None,
            "status": None,
        }
        self.loaded: bool = False
        self.liberation_changes: LiberationChangesTracker = LiberationChangesTracker()
        self.dark_energy_changes: dict = {"total": 0, "changes": []}
        self.meridia_position: None | tuple[int, int] = None
        self.personal_order = None
        self.fetched_at = None
        self.assignment = None
        self.galactic_impact_mod: float = 0.0
        self.global_events: list[GlobalEvent] | list = []

    async def pull_from_api(
        self, logger: Logger, moderator_channel: TextChannel
    ) -> None:
        """Pulls the data from each endpoint"""
        api_to_use = api
        async with ClientSession(
            headers={
                "Accept-Language": "en-GB",
                "X-Super-Client": "Galactic Wide Web",
                "X-Super-Contact": "Stonemercy",
            }
        ) as session:
            try:
                async with session.get(url=f"{api_to_use}") as r:
                    if r.status != 200:
                        api_to_use = backup_api
                        logger.critical(msg="API/USING BACKUP")
                        await moderator_channel.send(content=f"API/USING BACKUP\n{r}")
            except ClientSSLError as e:
                print(e)

            for endpoint in list(self.__data__.keys()):
                if endpoint == "thumbnails":
                    async with session.get(
                        url="https://helldivers.news/api/planets"
                    ) as r:
                        if r.status == 200:
                            self.__data__[endpoint] = await r.json()
                        else:
                            logger.error(msg=f"API/THUMBNAILS, {r.status}")
                    continue
                if endpoint == "superstore":
                    continue
                    async with session.get(
                        url="https://api.diveharder.com/v1/store_rotation"
                    ) as r:
                        if r.status == 200:
                            self.__data__[endpoint] = await r.json()
                        else:
                            logger.error(msg=f"API/SUPERSTORE, {r.status}")
                    continue
                if endpoint == "dss":
                    async with session.get(
                        url="https://api.diveharder.com/raw/dss"
                    ) as r:
                        if r.status == 200:
                            data = await r.json()
                            if data == "Error":
                                self.__data__[endpoint] = data
                                continue
                            if type(data[0]) == str:
                                logger.error(msg=f"API/DSS, {data[0] = }")
                                continue
                            tactical_actions = data[0].get("tacticalActions", None)
                            if tactical_actions:
                                names_present = tactical_actions[0].get("name", None)
                                if not names_present:
                                    logger.error(
                                        msg=f"API/DSS, Tactical Action has no name"
                                    )
                                    continue
                            self.__data__[endpoint] = data[0]
                        else:
                            logger.error(msg=f"API/DSS, {r.status}")
                    continue
                if endpoint == "personal_order":
                    continue
                    async with session.get(
                        url="https://api.diveharder.com/v1/personal_order"
                    ) as r:
                        if r.status == 200:
                            data = await r.json()
                            self.__data__[endpoint] = data[-1]
                        elif r.status == 204:
                            continue
                        else:
                            logger.error(msg=f"API/Personal_Order, {r.status}")
                    continue
                if endpoint == "status":
                    async with session.get(
                        url="https://api.diveharder.com/raw/status"
                    ) as r:
                        if r.status == 200:
                            data = await r.json()
                            self.__data__[endpoint] = data
                        else:
                            logger.error(msg=f"API/Status, {r.status}")
                    continue

                try:
                    async with session.get(url=f"{api_to_use}/api/v1/{endpoint}") as r:
                        if r.status == 200:
                            json = await r.json()
                            if endpoint == "dispatches":
                                if not json[0]["message"]:
                                    continue
                            elif endpoint == "assignments":
                                if json not in ([], None):
                                    if not json[0]["briefing"]:
                                        continue
                            self.__data__[endpoint] = json
                        else:
                            logger.error(msg=f"API/{endpoint.upper()}, {r.status}")
                            await moderator_channel.send(
                                content=f"API/{endpoint.upper()}\n{r}"
                            )
                except Exception as e:
                    logger.error(msg=f"API/{endpoint.upper()}, {e}")
                    await moderator_channel.send(content=f"API/{endpoint.upper()}\n{r}")
                if api_to_use == backup_api:
                    await sleep(2)

        self.format_data()
        self.update_liberation_rates()
        self.update_dark_energy_rate()
        self.get_needed_players()
        self.fetched_at = datetime.now()
        if not self.loaded:
            self.loaded = True

    def format_data(self) -> None:
        """Formats the data in `this_object.__data__` and sets the properties of `this_object`"""
        if self.__data__["status"]:
            self.war_start_timestamp: int = (
                int(datetime.now().timestamp()) - self.__data__["status"]["time"]
            )

        if self.__data__["planets"]:
            self.planets: Planets = Planets(raw_planets_data=self.__data__["planets"])
            self.total_players: int = sum(
                [planet.stats["playerCount"] for planet in self.planets.values()]
            )

        if self.__data__["dss"]:
            if self.__data__["dss"] != "Error":
                dss_planet: Planet = self.planets[self.__data__["dss"]["planetIndex"]]
                dss_planet.dss_in_orbit = True
                self.dss: DSS = DSS(
                    raw_dss_data=self.__data__["dss"],
                    planet=dss_planet,
                    war_start_timestamp=self.war_start_timestamp,
                )
            else:
                self.dss = self.__data__["dss"]

        if self.planets:
            self.planet_events: list[Planet] = sorted(
                [planet for planet in self.planets.values() if planet.event],
                key=lambda planet: planet.stats["playerCount"],
                reverse=True,
            )

        if self.__data__["assignments"] not in ([], None):
            self.assignment: Assignment = Assignment(
                raw_assignment_data=self.__data__["assignments"][0]
            )
            factions = {
                1: "Humans",
                2: "Terminids",
                3: "Automaton",
                4: "Illuminate",
            }
            for task in self.assignment.tasks:
                if task.type == 2:
                    self.planets[task.values[8]].in_assignment = True
                elif task.type == 3:
                    if task.progress == 1:
                        continue
                    if task.values[9] != 0:
                        self.planets[task.values[9]].in_assignment = True
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
                            if planet.event.faction == factions[task.values[1]]
                        ]:
                            self.planets[index].in_assignment = True
                elif task.type in (11, 13):
                    self.planets[task.values[2]].in_assignment = True
        else:
            self.assignment = None

        if self.__data__["campaigns"] not in ([], None):
            self.campaigns: list[Campaign] = sorted(
                [
                    Campaign(
                        raw_campaign_data=raw_campaign_data,
                        campaign_planet=self.planets[
                            raw_campaign_data["planet"]["index"]
                        ],
                    )
                    for raw_campaign_data in self.__data__["campaigns"]
                ],
                key=lambda item: item.planet.stats["playerCount"],
                reverse=True,
            )

        if self.__data__["dispatches"]:
            self.dispatches: list[Dispatch] = [
                Dispatch(raw_dispatch_data=data)
                for data in self.__data__["dispatches"][:10][::-1]
            ]

        if self.__data__["thumbnails"]:
            self.thumbnails = self.__data__["thumbnails"]
            if self.planets:
                for thumbnail_data in self.thumbnails:
                    self.planets[thumbnail_data["planet"]["index"]].thumbnail = (
                        f"https://helldivers.news{thumbnail_data['planet']['image'].replace(' ', '%20')}"
                    )

        if self.__data__["steam"]:
            self.steam: list[Steam] = [
                Steam(raw_steam_data=raw_steam_data)
                for raw_steam_data in self.__data__["steam"]
            ]

        if self.__data__["superstore"]:  # SHELVED
            self.superstore: Superstore = Superstore(self.__data__["superstore"])

        if self.__data__["personal_order"]:  # SHELVED
            self.personal_order: PersonalOrder = PersonalOrder(
                self.__data__["personal_order"]
            )

        if self.__data__["status"]:
            self.galactic_impact_mod: float = self.__data__["status"][
                "impactMultiplier"
            ]
            for raw_global_event_data in self.__data__["status"]["globalEvents"]:
                raw_global_event_data: dict
                title = raw_global_event_data.get("title", None)
                if title != None:
                    self.global_events.append(
                        GlobalEvent(raw_global_event_data=raw_global_event_data)
                    )
                else:
                    continue
            self.global_resources: GlobalResources = GlobalResources(
                raw_global_resources_data=self.__data__["status"]["globalResources"]
            )
            self.meridia_position: tuple[int, int] = (
                self.__data__["status"]["planetStatus"][64]["position"]["x"],
                self.__data__["status"]["planetStatus"][64]["position"]["y"],
            )
            self.planets[64].position = {
                "x": self.meridia_position[0],
                "y": self.meridia_position[1],
            }
            planets_with_buildup: dict[int, int] = {}
            for planet in self.__data__["status"]["planetEvents"]:
                if planet["potentialBuildUp"] != 0:
                    planets_with_buildup[planet["planetIndex"]] = planet[
                        "potentialBuildUp"
                    ]
            for index, buildup in planets_with_buildup.items():
                planet: Planet = self.planets[index]
                if planet.event:
                    planet.event.potential_buildup = buildup
            self.planet_active_effects = self.__data__["status"]["planetActiveEffects"]
            for planet_effect in self.planet_active_effects:
                planet = self.planets[planet_effect["index"]]
                planet.active_effects.add(planet_effect["galacticEffectId"])
            for ge in self.global_events:
                for planet_index in ge.planet_indices:
                    self.planets[planet_index].active_effects |= set(ge.effect_ids)

            for planet_attack in self.__data__["status"]["planetAttacks"]:
                source_planet = self.planets[planet_attack["source"]]
                target_planet = self.planets[planet_attack["target"]]
                source_planet.attack_targets.append(target_planet.index)
                target_planet.defending_from.append(source_planet.index)

    def update_liberation_rates(self) -> None:
        """Update the liberation changes in the tracker for each active campaign"""
        for campaign in self.campaigns:
            if campaign.planet.index not in self.liberation_changes.tracked_planets:
                self.liberation_changes.add_new_entry(
                    planet_index=campaign.planet.index, liberation=campaign.progress
                )
            else:
                self.liberation_changes.update_liberation(
                    planet_index=campaign.planet.index, new_liberation=campaign.progress
                )

    def update_dark_energy_rate(self) -> None:
        """Update the changes in dark energy"""
        if self.global_resources.dark_energy:
            if self.dark_energy_changes["total"] != 0:
                if len(self.dark_energy_changes["changes"]) == 5:
                    self.dark_energy_changes["changes"].pop(0)
                while len(self.dark_energy_changes["changes"]) < 5:
                    self.dark_energy_changes["changes"].append(
                        (
                            self.global_resources.dark_energy.perc
                            - self.dark_energy_changes["total"]
                        )
                    )
            self.dark_energy_changes["total"] = self.global_resources.dark_energy.perc

    def get_needed_players(self) -> None:
        """Update the planets with their required helldivers for victory"""
        now = datetime.now()
        if not self.planet_events:
            return
        for planet in self.planet_events:
            lib_changes = self.liberation_changes.get_by_index(
                planet_index=planet.index
            )
            if lib_changes.rate_per_hour == 0:
                return
            progress_needed = 100 - lib_changes.liberation
            seconds_to_complete = int(
                (progress_needed / lib_changes.rate_per_hour) * 3600
            )
            win_time = planet.event.end_time_datetime
            eagle_storm = self.dss.get_ta_by_name("EAGLE STORM")
            if planet.dss_in_orbit and eagle_storm.status == 2:
                win_time += timedelta(
                    seconds=(eagle_storm.status_end_datetime - now).total_seconds()
                )
            winning = now + timedelta(seconds=seconds_to_complete) < win_time
            if not winning:
                hours_left = (win_time - now).total_seconds() / 3600
                progress_needed_per_hour = progress_needed / hours_left
                amount_ratio = progress_needed_per_hour / lib_changes.rate_per_hour
                required_players = planet.stats["playerCount"] * amount_ratio
                planet.event.required_players = required_players

    @property
    def plot_coordinates(self) -> dict[int, tuple]:
        """Returns the coordinates of the planets for use in the 2000x2000 map"""
        return {
            planet.index: (
                (planet.position["x"] + 1) / 2 * 2000,
                (planet.position["y"] + 1) / 2 * 2000,
            )
            for planet in self.planets.values()
        }

    def copy(self):
        """Returns a deep copy of the data"""
        return deepcopy(self)


class Assignment(ReprMixin):
    def __init__(self, raw_assignment_data: dict) -> None:
        """Organised data of an Assignment or Major Order"""
        self.id: int = raw_assignment_data["id"]
        self.title: str = (
            steam_format(content=raw_assignment_data["briefing"])
            if raw_assignment_data["briefing"] not in ([], None)
            else ""
        )
        self.description: str = (
            steam_format(content=raw_assignment_data["description"])
            if raw_assignment_data["description"]
            not in ([], None, raw_assignment_data["briefing"])
            else ""
        )
        self.tasks: list[Assignment.Task] = []
        for index, task in enumerate(iterable=raw_assignment_data["tasks"]):
            self.tasks.append(
                Assignment.Task(
                    task=task, current_progress=raw_assignment_data["progress"][index]
                )
            )
        self.rewards: list[dict] = raw_assignment_data["rewards"]
        self.ends_at: str = raw_assignment_data["expiration"]
        self.ends_at_datetime: datetime = datetime.fromisoformat(self.ends_at)

    class Task(ReprMixin):
        def __init__(self, task: dict, current_progress: int | float) -> None:
            """Organised data of an Assignment Task"""
            self.type: int = task["type"]
            self.progress: float = current_progress
            self.values: list = task["values"]
            self.value_types: list = task["valueTypes"]

        @property
        def health_bar(self) -> str:
            """Returns a health_bar based on the task type and progress"""
            if self.type == 2:
                return health_bar(
                    self.progress_perc, "MO" if self.progress != 1 else "Humans"
                )
            elif self.type == 3:
                return health_bar(
                    self.progress_perc,
                    (self.values[0] if self.progress != 1 else "Humans"),
                )
            elif self.type == 11:
                return
            elif self.type == 12:
                return health_bar(
                    self.progress_perc,
                    "MO" if self.progress < 1 else "Humans",
                )
            elif self.type == 13:
                return ""
            elif self.type == 15:
                percent = {i: (i + 10) / 20 for i in range(-10, 12, 2)}[
                    [key for key in range(-10, 12, 2) if key <= self.progress][-1]
                ]
                return health_bar(
                    percent,
                    "Humans" if self.progress > 0 else "Automaton",
                )

        @property
        def progress_perc(self) -> float:
            """Returns the progress of the task as a float (0-1)"""
            if self.type in (15, 12):
                progress_value = self.values[0]
            elif self.type in (13, 11):
                progress_value = 1
            elif self.type in (3, 2):
                progress_value = self.values[2]
            return self.progress / progress_value


class Dispatch(ReprMixin):
    def __init__(self, raw_dispatch_data: dict) -> None:
        """Organised data of a dispatch"""
        self.id: int = raw_dispatch_data["id"]
        self.message = (
            steam_format(content=raw_dispatch_data["message"])
            if raw_dispatch_data["message"]
            else ""
        )


class GlobalEvent(ReprMixin):
    def __init__(self, raw_global_event_data: dict) -> None:
        """Organised data of a global event"""
        self.id: int = raw_global_event_data["eventId"]
        self.title: str = steam_format(raw_global_event_data["title"])
        self.message: str = steam_format(content=raw_global_event_data["message"])
        self.faction: int = raw_global_event_data["race"]
        self.flag: int = raw_global_event_data["flag"]
        self.assignment_id: int = raw_global_event_data["assignmentId32"]
        self.effect_ids: list[int] | list = raw_global_event_data["effectIds"]
        self.planet_indices: list[int] | list = raw_global_event_data["planetIndices"]

    @property
    def split_message(self) -> list[str]:
        """Returns the message split into chunks with character lengths of 1024 or less"""
        sentences = self.message.split(sep="\n\n")
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


class GlobalResource(ReprMixin):
    def __init__(self, raw_global_resource_data: dict) -> None:
        """Organised data of a global resource"""
        self.id: int = raw_global_resource_data["id32"]
        self.current_value: int = raw_global_resource_data["currentValue"]
        self.max_value: int = raw_global_resource_data["maxValue"]
        self.perc: float = self.current_value / self.max_value


class DarkEnergy(GlobalResource):
    def __init__(self, raw_global_resource_data: dict) -> None:
        """Organised data for Dark Energy"""
        super().__init__(raw_global_resource_data=raw_global_resource_data)

    @property
    def health_bar(self) -> str:
        """Returns the health bar set up for Dark Energy"""
        return health_bar(self.perc, "Illuminate")


class GlobalResources(list[GlobalResource]):
    def __init__(self, raw_global_resources_data: list[dict]) -> None:
        """An organised list of Global Resources."""
        for raw_global_resource_data in raw_global_resources_data:
            if raw_global_resource_data["id32"] == 194773219:
                self.dark_energy: DarkEnergy = DarkEnergy(
                    raw_global_resource_data=raw_global_resource_data
                )
            else:
                self.append(
                    GlobalResource(raw_global_resource_data=raw_global_resource_data)
                )


class Planet(ReprMixin):
    def __init__(self, raw_planet_data: dict) -> None:
        """Organised data for a specific planet"""
        self.index: int = raw_planet_data["index"]
        self.name: str = raw_planet_data["name"]
        self.sector: str = raw_planet_data["sector"]
        self.biome: dict = raw_planet_data["biome"]
        self.hazards: list[dict] = raw_planet_data["hazards"]
        self.position: dict = raw_planet_data["position"]
        self.waypoints: list[int] = raw_planet_data["waypoints"]
        self.max_health: int = raw_planet_data["maxHealth"]
        self.health: int = raw_planet_data["health"]
        self.health_perc: float = self.health / self.max_health
        self.current_owner: str = raw_planet_data["currentOwner"]
        self.regen: float = raw_planet_data["regenPerSecond"]
        self.regen_perc_per_hour: float = round(
            number=(((self.regen * 3600) / self.max_health) * 100), ndigits=2
        )
        self.event: Planet.Event | None = (
            Planet.Event(raw_event_data=raw_planet_data["event"])
            if raw_planet_data["event"]
            else None
        )
        self.stats: dict = raw_planet_data["statistics"]
        self.thumbnail = None
        self.feature: str | None = {
            5: "Repulsive Gravity Field Generator Construction Site",
            45: "Center for Civilian Surveillance",
            64: "Meridian Singularity",
            125: "Centre of Science",
            126: "Xenoentomology Center",
            130: "Factory Hub",
            161: "Deep Mantle Forge Complex",
        }.get(self.index, None)
        self.dss_in_orbit: bool = False
        self.in_assignment: bool = False
        self.active_effects: set[int] | set = set()
        self.attack_targets: list[int] | list = []
        self.defending_from: list[int] | list = []

        # BIOME/SECTOR/HAZARDS OVERWRITE #
        if self.index == 64:
            self.biome = {
                "name": "Black Hole",
                "description": "The planet is gone, the ultimate price to pay in the war for humanity's survival.",
            }
            self.sector = "Orion"
            self.hazards = []
        elif self.index in (127,):
            self.biome = {
                "name": "Fractured Planet",
                "description": "All that remains of a planet torn apart by the Meridian singularity. A solemn reminder of the desolation Tyranny leaves in its wake.",
            }
            self.hazards = []

    @property
    def map_waypoints(self) -> tuple[float, float]:
        return (
            (self.position["x"] * 1000) + 1000,
            ((self.position["y"] * -1) * 1000) + 1000,
        )

    class Event(ReprMixin):
        def __init__(self, raw_event_data) -> None:
            """Organised data for a planet's event (defence campaign)"""
            self.id: int = raw_event_data["id"]
            self.type: int = raw_event_data["eventType"]
            self.faction: str = raw_event_data["faction"]
            self.health: int = raw_event_data["health"]
            self.max_health: int = raw_event_data["maxHealth"]
            self.start_time: str = raw_event_data["startTime"]
            self.end_time: str = raw_event_data["endTime"]
            self.start_time_datetime: datetime = datetime.fromisoformat(
                self.start_time
            ).replace(tzinfo=None) + timedelta(hours=1)
            self.end_time_datetime: datetime = datetime.fromisoformat(
                self.end_time
            ).replace(tzinfo=None) + timedelta(hours=1)
            self.progress: float = self.health / self.max_health
            self.required_players: int = 0
            self.level: int = int(self.max_health / 50000)
            self.potential_buildup: int = 0

        @property
        def remaining_dark_energy(self) -> float:
            """Returns the remaining dark energy on the planet

            example:
                If the `12 hour event` has `6 hours left` and the `potential_buildup is 120000`
                the `remaining_dark_energy is 60000`"""
            return self.potential_buildup * (
                1
                - (datetime.now() - self.start_time_datetime).total_seconds()
                / (self.end_time_datetime - self.start_time_datetime).total_seconds()
            )

        @property
        def health_bar(self) -> str:
            """Returns the health bar for the planet's event"""
            return health_bar(perc=self.progress, race=self.faction, reverse=True)


class Planets(dict):
    def __init__(self, raw_planets_data: list[dict]) -> None:
        """A dict in the format of `{int: Planet}` containing all of the current planets"""
        for raw_planet_data in raw_planets_data:
            self[raw_planet_data["index"]] = Planet(raw_planet_data=raw_planet_data)

    def get_by_name(self, name: str) -> Planet | None:
        planet_list = [
            planet for planet in self.values() if planet.name.upper() == name.upper()
        ]
        return None if not planet_list else planet_list[0]

    # For typehinting #
    def items(self) -> ItemsView[int, Planet]:
        return super().items()

    def values(self) -> ValuesView[Planet]:
        return super().values()

    def __getitem__(self, key) -> Planet:
        return super().__getitem__(key)


class Campaign(ReprMixin):
    def __init__(self, raw_campaign_data: dict, campaign_planet: Planet) -> None:
        """Organised data for a campaign"""
        self.id: int = raw_campaign_data["id"]
        self.planet: Planet = campaign_planet
        self.type: int = raw_campaign_data["type"]
        self.count: int = raw_campaign_data["count"]
        self.progress: float = (
            (1 - (self.planet.health / self.planet.max_health)) * 100
            if not self.planet.event
            else (1 - (self.planet.event.progress)) * 100
        )
        self.faction: str = (
            self.planet.event.faction
            if self.planet.event
            else self.planet.current_owner
        )


class Steam(ReprMixin):
    def __init__(self, raw_steam_data: dict) -> None:
        """Organised data for a Steam announcements"""
        self.id: int = int(raw_steam_data["id"])
        self.title: str = raw_steam_data["title"]
        self.content: str = steam_format(content=raw_steam_data["content"])
        self.author: str = raw_steam_data["author"]
        self.url: str = raw_steam_data["url"]


class Superstore(ReprMixin):  # SHELVED
    def __init__(self, superstore):
        self.expiration = superstore["expire_time"]
        self.items: dict = superstore["items"]


class DSS(ReprMixin):
    def __init__(
        self, raw_dss_data: dict, planet: Planet, war_start_timestamp: int
    ) -> None:
        """Organised data for the DSS"""
        self.planet: Planet = planet
        self.move_timer_timestamp: int = raw_dss_data["currentElectionEndWarTime"]
        self.move_timer_datetime: datetime = datetime.fromtimestamp(
            war_start_timestamp + self.move_timer_timestamp
        )
        self.tactical_actions: list[DSS.TacticalAction] = [
            DSS.TacticalAction(
                tactical_action_raw_data=tactical_action_raw_data,
                war_start_time=war_start_timestamp,
            )
            for tactical_action_raw_data in raw_dss_data["tacticalActions"]
        ]

    def get_ta_by_name(self, name: str):
        if name in [ta.name for ta in self.tactical_actions]:
            return [ta for ta in self.tactical_actions if ta.name == name][0]
        else:
            return None

    class TacticalAction(ReprMixin):
        def __init__(self, tactical_action_raw_data: dict, war_start_time: int) -> None:
            """A Tactical Action for the DSS"""
            self.name: str = tactical_action_raw_data["name"]
            self.description: str = tactical_action_raw_data["description"]
            self.status: int = tactical_action_raw_data["status"]
            self.status_end: int = tactical_action_raw_data[
                "statusExpireAtWarTimeSeconds"
            ]
            self.status_end_datetime: datetime = datetime.fromtimestamp(
                war_start_time + self.status_end
            )
            self.strategic_description: str = steam_format(
                content=tactical_action_raw_data["strategicDescription"]
            )
            self.cost: DSS.TacticalAction.Cost = DSS.TacticalAction.Cost(
                tactical_action_raw_data["cost"][0]
            )

        class Cost(ReprMixin):
            def __init__(self, cost) -> None:
                """Organised data for the cost of a Tactical Action"""
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


class PersonalOrder(ReprMixin):  # SHELVED
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
