from aiohttp import ClientSession, ClientSSLError
from asyncio import sleep
from copy import deepcopy
from datetime import datetime, timedelta
from disnake import TextChannel
from logging import Logger
from os import getenv
from typing import ItemsView, ValuesView
from data.lists import SpecialUnits
from utils.emojis import Emojis
from utils.functions import dispatch_format, health_bar, steam_format
from utils.mixins import ReprMixin
from utils.trackers import BaseTracker

api = getenv(key="API")
backup_api = getenv(key="BU_API")

factions = {
    1: "Humans",
    2: "Terminids",
    3: "Automaton",
    4: "Illuminate",
}

region_types = {4: "Mega City", 3: "City", 2: "Town", 1: "Settlement"}


class Data(ReprMixin):
    __slots__ = (
        "__data__",
        "json_dict",
        "fetched_at",
        "assignments",
        "campaigns",
        "dispatch",
        "planets",
        "planet_events",
        "total_players",
        "steam",
        "thumbnails",
        "dss",
        "global_events",
        "loaded",
        "liberation_changes",
        "dark_energy_changes",
        "region_changes",
        "major_order_changes",
        "meridia_position",
        "galactic_impact_mod",
        "sieges",
        "steam_playercount",
    )

    def __init__(self, json_dict: dict) -> None:
        """The object to retrieve and organise all 3rd-party data used by the bot"""
        self.json_dict = json_dict
        self.__data__: dict[str,] = {
            "assignments": None,
            "campaigns": None,
            "dispatches": None,
            "planets": None,
            "steam": None,
            "thumbnails": None,
            "dss": None,
            "status": None,
            "warinfo": None,
            "steam_playercount": None,
        }
        self.loaded: bool = False
        self.liberation_changes: BaseTracker = BaseTracker()
        self.global_resource_changes: BaseTracker = BaseTracker()
        self.siege_fleet_changes: BaseTracker = BaseTracker()
        self.region_changes: BaseTracker = BaseTracker()
        self.major_order_changes: BaseTracker = BaseTracker()
        self.meridia_position: None | tuple[float, float] = None
        self.fetched_at = None
        self.assignments = []
        self.dss = None
        self.dispatches: list = []
        self.sieges = None
        self.global_resources = None
        self.steam_playercount = 0
        self.gambit_planets = {}
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
                raise e

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
                elif endpoint == "dss":
                    async with session.get(
                        url="https://api.live.prod.thehelldiversgame.com/api/SpaceStation/801/749875195"
                    ) as r:
                        if r.status == 200:
                            data = await r.json()
                            tactical_actions = data.get("tacticalActions", None)
                            if tactical_actions:
                                names_present = tactical_actions[0].get("name", None)
                                if not names_present:
                                    logger.error(
                                        msg=f"API/DSS, Tactical Action has no name"
                                    )
                                    continue
                            self.__data__[endpoint] = data
                        else:
                            logger.error(msg=f"API/DSS, {r.status}")
                    continue
                elif endpoint == "status":
                    async with session.get(
                        url="https://api.live.prod.thehelldiversgame.com/api/WarSeason/801/Status"
                    ) as r:
                        if r.status == 200:
                            data = await r.json()
                            self.__data__[endpoint] = data
                        else:
                            logger.error(msg=f"API/Status, {r.status}")
                    continue
                elif endpoint == "warinfo":
                    async with session.get(
                        url="https://api.live.prod.thehelldiversgame.com/api/WarSeason/801/WarInfo"
                    ) as r:
                        if r.status == 200:
                            self.__data__[endpoint] = await r.json()
                        else:
                            logger.error(msg=f"API/WARINFO, {r.status}")
                    continue
                elif endpoint == "steam_playercount":
                    async with session.get(
                        url="https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/",
                        params={"appid": 553850},
                    ) as r:
                        if r.status == 200:
                            data = await r.json()
                            self.steam_playercount = data["response"]["player_count"]
                        else:
                            logger.error(msg=f"API/STEAM_PLAYERCOUNT, {r.status}")
                    continue
                elif endpoint == "dispatches":
                    async with session.get(
                        url=f"https://api.live.prod.thehelldiversgame.com/api/NewsFeed/801?maxEntries=1024"
                    ) as r:
                        if r.status == 200:
                            json = await r.json()
                            self.__data__[endpoint] = json
                        elif r.status != 500:
                            logger.error(msg=f"API/{endpoint.upper()}, {r.status}")
                            await moderator_channel.send(
                                content=f"API/{endpoint.upper()}\n{r}"
                            )
                        continue
                try:
                    async with session.get(url=f"{api_to_use}/api/v1/{endpoint}") as r:
                        if r.status == 200:
                            json = await r.json()
                            if endpoint == "dispatches":
                                if not json[0]["message"]:
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
        self.update_region_changes()
        if self.assignments:
            self.update_major_order_rates()
        if self.global_resources:
            self.update_global_resource_rates()
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
            dss_planet: Planet = self.planets[self.__data__["dss"]["planetIndex"]]
            if self.__data__["dss"]["flags"] == 1:
                dss_planet.dss_in_orbit = True
            self.dss: DSS = DSS(
                raw_dss_data=self.__data__["dss"],
                planet=dss_planet,
                war_start_timestamp=self.war_start_timestamp,
            )

        if self.planets:
            self.planet_events: list[Planet] = sorted(
                [planet for planet in self.planets.values() if planet.event],
                key=lambda planet: planet.stats["playerCount"],
                reverse=True,
            )

        if self.__data__["assignments"] not in ([], None):
            self.assignments: list[Assignment] = [
                Assignment(raw_assignment_data=assignment)
                for assignment in self.__data__["assignments"]
            ]
            for assignment in self.assignments:
                for task in assignment.tasks:
                    if task.progress_perc == 1:
                        continue
                    match task.type:
                        case 2:
                            if task.sector_index:
                                sector_name: str = self.json_dict["sectors"][
                                    str(task.sector_index)
                                ]
                                planets_in_assignment = [
                                    p
                                    for p in self.planets.values()
                                    if p.sector.lower() == sector_name.lower()
                                ]
                                for planet in planets_in_assignment:
                                    planet.in_assignment = True
                            elif task.planet_index:
                                self.planets[task.planet_index].in_assignment = True
                            elif task.faction:
                                for planet in [
                                    p
                                    for p in self.planets.values()
                                    if p.current_owner == task.faction
                                ]:
                                    planet.in_assignment = True
                        case 3:
                            if task.planet_index:
                                self.planets[task.planet_index].in_assignment = True
                                continue
                            for index in [
                                planet.index
                                for planet in self.planets.values()
                                if planet.current_owner == task.faction
                                or (
                                    planet.event
                                    and planet.event.faction == task.faction
                                )
                            ]:
                                self.planets[index].in_assignment = True
                        case 12:
                            if self.planet_events:
                                if task.planet_index:
                                    self.planets[task.planet_index].in_assignment = True
                                    continue
                                for index in [
                                    planet.index
                                    for planet in self.planet_events
                                    if planet.event.faction == task.faction
                                ]:
                                    self.planets[index].in_assignment = True
                        case 11 | 13:
                            if (
                                self.planets[task.planet_index].event
                                and self.planets[task.planet_index].event.type == 2
                            ):
                                continue
                            else:
                                self.planets[task.planet_index].in_assignment = True
        else:
            self.assignments = []

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
                Dispatch(raw_dispatch_data=data) for data in self.__data__["dispatches"]
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

            self.meridia_position: tuple[float, float] = (
                self.__data__["status"]["planetStatus"][64]["position"]["x"],
                self.__data__["status"]["planetStatus"][64]["position"]["y"],
            )
            self.planets[64].position = {
                "x": self.meridia_position[0],
                "y": self.meridia_position[1],
            }
            for planet in self.__data__["status"]["planetEvents"]:
                if planet["potentialBuildUp"] != 0:
                    self.planets[planet["planetIndex"]].event.potential_buildup = (
                        planet["potentialBuildUp"]
                    )
                if global_resource_id := planet.get("globalResourceId", None):
                    self.planets[planet["planetIndex"]].event.siege_fleet = (
                        self.global_resources.get_by_id(global_resource_id)
                    )
                    if self.planets[planet["planetIndex"]].event.siege_fleet:
                        self.planets[
                            planet["planetIndex"]
                        ].event.siege_fleet.faction = self.planets[
                            planet["planetIndex"]
                        ].event.faction

            for planet_effect in self.__data__["status"]["planetActiveEffects"]:
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

            self.gambit_planets.clear()
            for campaign in self.campaigns:
                if (
                    campaign.planet.current_owner == "Humans"
                    or len(campaign.planet.defending_from) == 0
                    or 1190 in campaign.planet.active_effects
                ):
                    continue
                else:
                    for defending_index in campaign.planet.attack_targets:
                        defending_planet = self.planets[defending_index]
                        if (
                            len(defending_planet.defending_from) == 1
                            and defending_planet.event
                        ):
                            self.gambit_planets[defending_index] = campaign.planet

        if self.__data__["warinfo"]:
            if not self.__data__["warinfo"].get("planetRegions") or not self.__data__[
                "status"
            ].get("planetRegions"):
                pass
            else:
                for region in self.__data__["warinfo"]["planetRegions"]:
                    self.planets[region["planetIndex"]].regions[
                        region["regionIndex"]
                    ] = Planet.Region(
                        planet_regions_json_dict=self.json_dict["planetRegions"],
                        raw_planet_region_data=region,
                    )

                for region in self.__data__["status"]["planetRegions"]:
                    if region["planetIndex"] not in self.planets:
                        continue
                    else:
                        planet_region = self.planets[region["planetIndex"]].regions.get(
                            region["regionIndex"], None
                        )
                        if planet_region:
                            planet_region.update_from_status_data(
                                raw_planet_region_data=region
                            )

                for planet in self.planets.values():
                    planet.regions = {
                        region.index: region
                        for region in sorted(
                            planet.regions.copy().values(),
                            key=lambda region: region.availability_factor,
                        )
                    }

    def update_liberation_rates(self) -> None:
        """Update the liberation changes in the tracker for each active campaign"""
        for campaign in self.campaigns:
            self.liberation_changes.add_entry(
                key=campaign.planet.index, value=campaign.progress
            )

    def update_global_resource_rates(self) -> None:
        """Update the changes in global resources"""
        if self.global_resources:
            for gr in self.global_resources:
                self.global_resource_changes.add_entry(key=gr.id, value=gr.perc)

    def update_major_order_rates(self) -> None:
        """Update the changes in Major Order tasks"""
        if self.assignments:
            for assignment in self.assignments:
                for index, task in enumerate(assignment.tasks, start=1):
                    self.major_order_changes.add_entry(
                        key=(assignment.id, index), value=task.progress_perc
                    )

    def update_region_changes(self) -> None:
        """Update the liberation changes in the tracker for each active region"""
        planets_with_regions = [p for p in self.planets.values() if p.regions]
        for planet in planets_with_regions:
            for region in planet.regions.values():
                if region.is_available:
                    self.region_changes.add_entry(
                        key=region.settings_hash, value=region.perc
                    )

    def get_needed_players(self) -> None:
        """Update the planets with their required helldivers for victory"""
        if not self.planet_events:
            return
        now = datetime.now()
        for planet in self.planet_events:
            lib_changes = self.liberation_changes.get_entry(key=planet.index)
            if not lib_changes or lib_changes.change_rate_per_hour == 0:
                continue
            win_time = planet.event.end_time_datetime
            if planet.dss_in_orbit:
                eagle_storm = self.dss.get_ta_by_name("EAGLE STORM")
                if eagle_storm and eagle_storm.status == 2:
                    win_time += timedelta(
                        seconds=(eagle_storm.status_end_datetime - now).total_seconds()
                    )
            winning = (
                now + timedelta(seconds=lib_changes.seconds_until_complete) < win_time
            )
            if not winning:
                hours_left = (win_time - now).total_seconds() / 3600
                progress_needed_per_hour = (1 - lib_changes.value) / hours_left
                amount_ratio = (
                    progress_needed_per_hour / lib_changes.change_rate_per_hour
                )
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
        self.title: str = raw_assignment_data["title"]
        self.briefing: str = (
            raw_assignment_data["briefing"]
            if raw_assignment_data["briefing"] not in ([], None)
            else ""
        )
        self.description: str = (
            raw_assignment_data["description"]
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
        self.ends_at_datetime: datetime = datetime.fromisoformat(self.ends_at).replace(
            tzinfo=None
        )
        self.flags: int = raw_assignment_data.get("flags", 0)

    class Task(ReprMixin):
        """Organised data of an Assignment Task"""

        __slots__ = (
            "faction",
            "target",
            "enemy_id",
            "item_id",
            "objective",
            "value8",
            "value10",
            "difficulty",
            "location_type",
            "planet_index",
            "sector_index",
            "type",
            "progress",
        )

        def __init__(self, task: dict, current_progress: int | float) -> None:
            self.type: int = task["type"]
            self.progress: int | float = current_progress
            self.values_dict = dict(zip(task["valueTypes"], task["values"]))
            self.faction = self.target = self.enemy_id = self.item_id = (
                self.objective
            ) = self.value8 = self.difficulty = self.value10 = self.planet_index = (
                self.sector_index
            ) = None

            if faction := self.values_dict.get(1):
                self.faction: str = factions.get(faction, "Unknown")
            if value2 := self.values_dict.get(2):
                self.value2 = value2
                print(f"VALUE2 USED: {self.type, self.value2 = }")
            if target := self.values_dict.get(3):
                self.target: int | float = target
            if enemy_id := self.values_dict.get(4):
                self.enemy_id: int = enemy_id
            if self.values_dict.get(6):
                self.item_id = self.values_dict.get(5)
            if objective := self.values_dict.get(7):
                self.objective = objective
                print(f"OBJECTIVE USED: {self.type, self.objective = }")
            if value8 := self.values_dict.get(8):
                self.value8 = value8
                print(f"VALUE8 USED: {self.type, self.value8 = }")
            if difficulty := self.values_dict.get(9):
                self.difficulty = difficulty
            if value10 := self.values_dict.get(10):
                self.value10 = value10
                print(f"VALUE10 USED: {self.type, self.value10 = }")
            if location_type := self.values_dict.get(11):
                if location_type == 1:
                    self.planet_index: int = self.values_dict.get(12)
                elif location_type == 2:
                    self.sector_index: int = self.values_dict.get(12)

        @property
        def progress_perc(self) -> float:
            """Returns the progress of the task as a float (0-1)"""
            return self.progress / self.target

        @property
        def health_bar(self) -> str:
            """Returns a health_bar based on the task type and progress"""
            match self.type:
                case 2:
                    return health_bar(
                        self.progress_perc,
                        "Humans",
                    )
                case 3:
                    return health_bar(
                        self.progress_perc,
                        (self.faction if self.progress_perc != 1 else "Humans"),
                    )
                case 7:
                    return health_bar(self.progress_perc, self.faction)
                case 9:
                    return health_bar(self.progress_perc, "Humans")
                case 11:
                    return
                case 12:
                    return health_bar(
                        self.progress_perc,
                        "MO" if self.progress_perc < 1 else "Humans",
                    )
                case 13:
                    return ""
                case 15:
                    percent = {i: (i + 10) / 20 for i in range(-10, 12, 2)}[
                        [key for key in range(-10, 12, 2) if key <= self.progress][-1]
                    ]
                    return health_bar(
                        percent,
                        "Humans" if self.progress > 0 else "Automaton",
                    )


class Dispatch(ReprMixin):
    def __init__(self, raw_dispatch_data: dict) -> None:
        """Organised data of a dispatch"""
        self.id: int = raw_dispatch_data["id"]
        self.message = dispatch_format(text=raw_dispatch_data.get("message", ""))


class GlobalEvent(ReprMixin):
    def __init__(self, raw_global_event_data: dict) -> None:
        """Organised data of a global event"""
        self.id: int = raw_global_event_data["eventId"]
        self.title: str = dispatch_format(raw_global_event_data["title"])
        self.message: str = dispatch_format(text=raw_global_event_data["message"])
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


known_fleets = {
    175685818: {
        "name": "THE GREAT HOST",
        "description": "The Illuminate invasion fleet, constructed in secret behind the veil of the Meridian Wormhole. It is headed for Super Earth itself.",
    }
}


class SiegeFleet(GlobalResource):
    def __init__(self, raw_global_resource_data: dict) -> None:
        """Organised data of a Siege Fleet"""
        self.id: int = raw_global_resource_data["id32"]
        known_fleet_entry = known_fleets.get(
            self.id,
            {
                "name": "Unknown",
                "description": "This fleet is new to the GWW and we are gathering data.",
            },
        )
        self.name = known_fleet_entry["name"]
        self.description = known_fleet_entry["description"]
        self.current_value: int = raw_global_resource_data["currentValue"]
        self.max_value: int = raw_global_resource_data["maxValue"]
        self.perc: float = self.current_value / self.max_value
        self.faction: str | None = None

    @property
    def health_bar(self) -> str:
        """Returns the health bar set up for the Siege Fleet"""
        return health_bar(self.perc, self.faction)


class DarkEnergy(GlobalResource):
    def __init__(self, raw_global_resource_data: dict) -> None:
        """Organised data for Dark Energy"""
        super().__init__(raw_global_resource_data=raw_global_resource_data)

    @property
    def health_bar(self) -> str:
        """Returns the health bar set up for Dark Energy"""
        return health_bar(self.perc, "Illuminate")


class TheGreatHost(SiegeFleet):
    def __init__(self, raw_global_resource_data: dict) -> None:
        """Organised data for The Great Host"""
        super().__init__(raw_global_resource_data=raw_global_resource_data)
        self.faction = "Illuminate"


class GlobalResources(list[GlobalResource]):
    def __init__(self, raw_global_resources_data: list[dict]) -> None:
        """An organised list of Global Resources."""
        self.dark_energy = self.the_great_host = None
        for raw_global_resource_data in raw_global_resources_data:
            if raw_global_resource_data["id32"] == 194773219:
                self.dark_energy: DarkEnergy = DarkEnergy(
                    raw_global_resource_data=raw_global_resource_data
                )
                self.append(self.dark_energy)
            elif raw_global_resource_data["id32"] == 175685818:
                self.the_great_host: TheGreatHost = TheGreatHost(
                    raw_global_resource_data=raw_global_resource_data
                )
                self.append(self.the_great_host)
            else:
                self.append(
                    GlobalResource(raw_global_resource_data=raw_global_resource_data)
                )

    def get_by_id(self, id: int):
        if gr_list := [gr for gr in self if gr.id == id]:
            return gr_list[0]


class Planet(ReprMixin):
    def __init__(self, raw_planet_data: dict) -> None:
        """Organised data for a specific planet"""
        self.index: int = raw_planet_data["index"]
        self.name: str = raw_planet_data["name"]
        self.sector: str = raw_planet_data["sector"]
        self.biome: dict = raw_planet_data["biome"]
        self.hazards: list[dict] = raw_planet_data["hazards"]
        self.position: dict = raw_planet_data["position"]
        self.waypoints: set[int] = set(raw_planet_data["waypoints"])
        self.max_health: int = raw_planet_data["maxHealth"]
        self.health: int = raw_planet_data["health"]
        self.health_perc: float = min(self.health / self.max_health, 1)
        self.current_owner: str = raw_planet_data["currentOwner"]
        self.regen: float = raw_planet_data["regenPerSecond"]
        self.regen_perc_per_hour: float = round(
            number=(((self.regen * 3600) / self.max_health)), ndigits=4
        )
        self.event: Planet.Event | None = (
            Planet.Event(raw_event_data=raw_planet_data["event"])
            if raw_planet_data["event"]
            else None
        )
        self.stats: dict = raw_planet_data["statistics"]
        self.thumbnail = None
        self.feature: str | None = {
            45: "Center for Civilian Surveillance",  # Mastia
            64: "Meridian Black Hole",  # Meridia
            114: "Jet Brigade Factories",  # Aurora Bay
            125: "Centre of Science",  # Fenrir III
            126: "Xenoentomology Center",  # Turing
            130: "Factory Hub",  # Achernar Secundus
            161: "Deep Mantle Forge Complex",  # Claorell
        }.get(self.index, None)
        self.dss_in_orbit: bool = False
        self.in_assignment: bool = False
        self.active_effects: set[int] | set = set()
        self.attack_targets: list[int] | list = []
        self.defending_from: list[int] | list = []
        self.regions: dict[int, Planet.Region] | dict = {}

        # BIOME/SECTOR/HAZARDS OVERWRITE #
        if self.index == 0:
            self.biome = {
                "name": "Super Earth",
                "description": "Super Earth is the blinding beacon that shines the light of democracy through the stars. The sprawling heart that beats in time to mankind's quest of liberation. Here live the wealthy, important and proud. Here live those who have pulled themselves up by their bootstraps and achieved their dreams. Here live the citizens of Super Earth.",
            }
        elif self.index == 64:
            self.biome = {
                "name": "Black Hole",
                "description": "The planet is gone, the ultimate price to pay in the war for humanity's survival.",
            }
            self.sector = "Celeste"
            self.hazards = []
        elif self.index in (127, 85, 51):
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

    @property
    def exclamations(self) -> str:
        result = ""
        if self.event:
            result += f":shield:{getattr(Emojis.Factions, self.event.faction.lower())}"
        if self.in_assignment:
            result += Emojis.Icons.mo
        if self.dss_in_orbit:
            result += Emojis.DSS.icon
        for special_unit in SpecialUnits.get_from_effects_list(
            active_effects=self.active_effects
        ):
            result += special_unit[1]
        return result

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
            ).replace(tzinfo=None)
            self.end_time_datetime: datetime = datetime.fromisoformat(
                self.end_time
            ).replace(tzinfo=None)
            self.progress: float = 1 - (self.health / self.max_health)
            """A float from 0-1"""
            self.required_players: int = 0
            self.level: int = int(self.max_health / 50000)
            self.potential_buildup: int = 0
            self.siege_fleet: SiegeFleet | None = None

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
            return health_bar(perc=self.progress, race=self.faction)

    class Region(ReprMixin):
        def __init__(
            self, planet_regions_json_dict: dict, raw_planet_region_data: dict
        ):
            self.settings_hash: int = raw_planet_region_data["settingsHash"]
            self.is_updated: bool = False
            self.planet_index: int = raw_planet_region_data["planetIndex"]
            self.index: int = raw_planet_region_data["regionIndex"]
            self.name: str = planet_regions_json_dict.get(
                str(self.settings_hash), {}
            ).get("name", "Colony")
            self.description: str = planet_regions_json_dict.get(
                str(self.settings_hash), {}
            ).get("description", "")
            self.owner: str = "Humans"
            self.health: int = raw_planet_region_data["maxHealth"]
            self.max_health: int = raw_planet_region_data["maxHealth"]
            self.regen_per_sec: int = 0
            self.availability_factor: int = 0
            self.is_available: bool = False
            self.players: int = 0
            self.size: int = raw_planet_region_data["regionSize"] + 1
            self.type: str = region_types.get(self.size, "")

        @property
        def regen_per_hour(self) -> float:
            return ((self.regen_per_sec * 3600) / self.max_health) * 100

        @property
        def perc(self):
            return 1 - self.health / self.max_health

        @property
        def health_bar(self) -> str:
            """Returns the health bar for the region"""
            return health_bar(perc=self.perc, race=self.owner)

        def update_from_status_data(self, raw_planet_region_data: dict):
            self.owner: str = factions[raw_planet_region_data["owner"]]
            self.health: int = raw_planet_region_data["health"]
            self.regen_per_sec: int = raw_planet_region_data.get(
                "regenPerSecond"
            ) or raw_planet_region_data.get("regerPerSecond")
            self.availability_factor: int = raw_planet_region_data["availabilityFactor"]
            self.is_available: bool = raw_planet_region_data["isAvailable"]
            self.players: int = raw_planet_region_data["players"]
            self.is_updated: bool = True


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
            (1 - (self.planet.health / self.planet.max_health))
            if not self.planet.event
            else self.planet.event.progress
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
        self.content: str = steam_format(text=raw_steam_data["content"])
        self.author: str = raw_steam_data["author"]
        self.url: str = raw_steam_data["url"]


class DSS(ReprMixin):
    def __init__(
        self, raw_dss_data: dict, planet: Planet, war_start_timestamp: int
    ) -> None:
        """Organised data for the DSS"""
        self.planet: Planet = planet
        self.flags: int = raw_dss_data["flags"]
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
            self.id: int = tactical_action_raw_data["id32"]
            self.name: str = tactical_action_raw_data["name"]
            self.description: str = tactical_action_raw_data["description"]
            self.status: int = tactical_action_raw_data["status"]
            self.status_end: int = tactical_action_raw_data[
                "statusExpireAtWarTimeSeconds"
            ]
            self.status_end_datetime: datetime = datetime.fromtimestamp(
                war_start_time + self.status_end
            )
            self.strategic_description: str = dispatch_format(
                text=tactical_action_raw_data["strategicDescription"]
            )
            self.cost: list[DSS.TacticalAction.Cost] = [
                DSS.TacticalAction.Cost(cost=cost)
                for cost in tactical_action_raw_data["cost"]
            ]

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
