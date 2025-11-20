from aiohttp import ClientSession, ClientSSLError, ClientTimeout
from asyncio import sleep, TimeoutError, wait_for
from copy import deepcopy
from data.lists import stratagem_id_dict
from datetime import datetime, timedelta
from utils.dataclasses import Factions, SpecialUnits, Languages, Config, PlanetFeatures
from utils.dataclasses.factions import Faction
from utils.dbv2 import GWWGuilds
from utils.emojis import Emojis
from utils.functions import dispatch_format, health_bar
from utils.logger import GWWLogger
from utils.mixins import GWEReprMixin, ReprMixin
from utils.trackers import BaseTracker, BaseTrackerEntry

REGION_TYPES = {
    4: "Mega City",
    3: "City",
    2: "Town",
    1: "Settlement",
}

DEF_LEVEL_EXC = {
    0: "",
    5: "!",
    20: "!!",
    33: "!!!",
    50: " :warning:",
    100: " :skull:",
    250: " :skull_crossbones:",
}

TIMEOUT = ClientTimeout(total=15)


class Data(ReprMixin):
    __slots__ = (
        "_data",
        "json_dict",
        "fetched_at",
        "assignments",
        "campaigns",
        "dispatches",
        "planets",
        "planet_events",
        "total_players",
        "steam",
        "dss",
        "global_events",
        "loaded",
        "liberation_changes",
        "region_changes",
        "major_order_changes",
        "galactic_impact_mod",
        "steam_playercount",
        "galactic_war_effects",
    )

    def __init__(self, json_dict: dict, logger: GWWLogger) -> None:
        """The object to retrieve and organise all 3rd-party data used by the bot"""
        self.json_dict = json_dict
        self.logger = logger
        self.default_data_dict: dict[str,] = {
            "assignments": {},
            "campaigns": None,
            "dispatches": {},
            "planets": None,
            "steam": None,
            "dss": None,
            "status": {},
            "warinfo": None,
            "steam_playercount": None,
            "galactic_war_effects": None,
        }
        self._data: dict[str,] = self.default_data_dict.copy()
        self.loaded: bool = False
        self.liberation_changes: BaseTracker = BaseTracker()
        self.global_resource_changes: BaseTracker = BaseTracker()
        self.tactical_action_changes: BaseTracker = BaseTracker()
        self.region_changes: BaseTracker = BaseTracker()
        self.major_order_changes: BaseTracker = BaseTracker()
        self.fetched_at = None
        self.fetching = False
        self.assignments = {}
        self.dispatches: dict = {}
        self.dss = None
        self.planets = None
        self.global_resources = None
        self.steam_playercount = 0
        self.gambit_planets: dict[int, Planet] = {}
        self.galactic_impact_mod: float = 0.0
        self.galactic_war_effects: list[GalacticWarEffect] = []
        self.global_events: dict[str, list] = {}

    async def get_api_to_use(self, session: ClientSession):
        try:
            async with session.get(url=f"{self.api_to_use}") as r:
                if r.status != 200:
                    self.api_to_use = Config.BACKUP_API_BASE
                    self.logger.critical("API/USING BACKUP")
        except ClientSSLError as e:
            raise e

    async def get_endpoint(
        self,
        endpoint_type: str,
        url: str,
        session: ClientSession,
        lang: str = None,
        params: dict = None,
    ):
        try:
            async with session.get(url=url, params=params) as r:
                print(
                    f"[{''.join([s for s in endpoint_type.title() if s.isupper()])}-",
                    end="",
                )
                if r.status == 200:
                    json = await r.json()
                    if lang:
                        self._data[endpoint_type][lang] = json
                    else:
                        self._data[endpoint_type] = json
                    print(f"\033[32m{r.status}\033[0m]", end="")
                else:
                    print(f"\033[31mERR[{r.status}]\033[0m]", end="")
        except Exception as e:
            raise e

    async def pull_from_api(self) -> None:
        """Pulls the data from each endpoint"""
        print("=" * 50)
        print(
            f"pull_from_api function started at {datetime.now().strftime('%H:%M:%S')}"
        )
        self.fetching = True
        self.api_to_use = Config.API_BASE
        async with ClientSession(
            headers={
                "Accept-Language": "en-GB",
                "X-Super-Client": "Galactic Wide Web",
                "X-Super-Contact": "Stonemercy",
            },
            timeout=TIMEOUT,
        ) as session:
            print(f"[\033[32mSession\033[0m]\nLoc", end="")
            await self.get_api_to_use(session=session)
            self._data = self.default_data_dict.copy()

            unique_languages = GWWGuilds.unique_languages()
            in_use_languages = [
                l for l in Languages.all if l.short_code in unique_languages
            ]
            for lang in in_use_languages:
                session.headers["Accept-Language"] = lang.long_code
                print(f"\n{lang.long_code}:", end="")
                try:
                    # status
                    await wait_for(
                        self.get_endpoint(
                            endpoint_type="status",
                            url="https://api.live.prod.thehelldiversgame.com/api/WarSeason/801/Status",
                            session=session,
                            lang=lang.short_code,
                        ),
                        timeout=15,
                    )

                    # variable is either
                    # wartime (if available) - 2 weeks
                    # or
                    # estimated wartime - 2 weeks
                    time_for_dispatches = int(
                        (
                            self._data.get("status", {})
                            .get("en", {})
                            .get(
                                "time",
                                (
                                    datetime.now()
                                    - datetime(
                                        year=2024, month=2, day=14, hour=15, minute=11
                                    )
                                ).total_seconds(),
                            )
                        )
                        - timedelta(weeks=1).total_seconds()
                    )
                    # dispatches
                    await wait_for(
                        self.get_endpoint(
                            endpoint_type="dispatches",
                            url=f"https://api.live.prod.thehelldiversgame.com/api/NewsFeed/801?fromTimestamp={time_for_dispatches}",
                            session=session,
                            lang=lang.short_code,
                        ),
                        timeout=15,
                    )

                    # major orders
                    await wait_for(
                        self.get_endpoint(
                            endpoint_type="assignments",
                            url=f"{self.api_to_use}/api/v1/assignments",
                            session=session,
                            lang=lang.short_code,
                        ),
                        timeout=15,
                    )
                except (TimeoutError, Exception) as e:
                    print(f"[ERROR {e}]")
                if self.api_to_use == Config.BACKUP_API_BASE:
                    # for HD2 community API rate limit
                    await sleep(2)

            # non-localized endpoints
            print("\nNon-loc")
            session.headers["Accept-Language"] = "en-GB"
            for endpoint in list(self._data.keys()):
                if endpoint in (
                    "dispatches",
                    "assignments",
                    "status",
                ):
                    continue
                match endpoint:
                    case "dss":
                        await wait_for(
                            self.get_endpoint(
                                endpoint_type=endpoint,
                                url="https://api.live.prod.thehelldiversgame.com/api/SpaceStation/801/749875195",
                                session=session,
                            ),
                            timeout=15,
                        )
                    case "warinfo":
                        await wait_for(
                            self.get_endpoint(
                                endpoint_type=endpoint,
                                url="https://api.live.prod.thehelldiversgame.com/api/WarSeason/801/WarInfo",
                                session=session,
                            ),
                            timeout=15,
                        )
                    case "galactic_war_effects":
                        await wait_for(
                            self.get_endpoint(
                                endpoint_type=endpoint,
                                url="https://api.live.prod.thehelldiversgame.com/api/WarSeason/GalacticWarEffects",
                                session=session,
                            ),
                            timeout=15,
                        )
                    case "steam_playercount":
                        await wait_for(
                            self.get_endpoint(
                                endpoint_type=endpoint,
                                url="https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/",
                                session=session,
                                params={"appid": 553850},
                            ),
                            timeout=15,
                        )
                    case _:
                        await wait_for(
                            self.get_endpoint(
                                endpoint_type=endpoint,
                                url=f"{self.api_to_use}/api/v1/{endpoint}",
                                session=session,
                            ),
                            timeout=15,
                        )

                if self.api_to_use == Config.BACKUP_API_BASE:
                    # for HD2 community API rate limit
                    await sleep(2)

        self.format_data()
        self.update_liberation_rates()
        self.update_region_changes()
        if self.assignments["en"]:
            self.update_major_order_rates()
        if self.dss:
            self.update_tactical_action_rates()

        self.fetched_at = datetime.now()
        print(f"\nself.fetched_at = {self.fetched_at.strftime('%H:%M:%S')}")
        if not self.loaded:
            print("FIRST LOAD, UPDATING SELF.LOADED")
            self.loaded = True
            print(f"self.loaded is now {self.loaded}")
        self.fetching = False
        print("COMPLETE")
        print("=" * 50)

    def format_data(self) -> None:
        """Formats the data in `this_object._data` and sets the properties of `this_object`"""
        if self._data["steam_playercount"]:
            self.steam_playercount: int = self._data["steam_playercount"]["response"][
                "player_count"
            ]

        if self._data["status"]["en"]:
            self.war_start_timestamp: int = (
                int(datetime.now().timestamp()) - self._data["status"]["en"]["time"]
            )

        if self._data["planets"]:
            self.planets: Planets = Planets(
                raw_planets_data=self._data["planets"],
                planet_names_json=self.json_dict["planets"],
            )
            self.total_players: int = sum(
                [planet.stats.player_count for planet in self.planets.values()]
            )

        if self._data["dss"]:
            dss_planet: Planet = self.planets[self._data["dss"]["planetIndex"]]
            if self._data["dss"]["flags"] == 1:
                dss_planet.dss_in_orbit = True
            self.dss: DSS = DSS(
                raw_dss_data=self._data["dss"],
                planet=dss_planet,
                war_start_timestamp=self.war_start_timestamp,
            )
            if eagle_storm := self.dss.get_ta_by_name("EAGLE STORM"):
                if eagle_storm.status == 2:
                    if dss_planet.event:
                        dss_planet.eagle_storm_active = True
                        dss_planet.event.end_time_datetime += timedelta(
                            seconds=(
                                eagle_storm.status_end_datetime - datetime.now()
                            ).total_seconds()
                        )

        if self.planets:
            self.planet_events: list[Planet] = sorted(
                [planet for planet in self.planets.values() if planet.event],
                key=lambda planet: planet.stats.player_count,
                reverse=True,
            )

        if self._data["assignments"]:
            for lang, assignments_list in self._data["assignments"].items():
                self.assignments[lang] = sorted(
                    [
                        Assignment(raw_assignment_data=assignment)
                        for assignment in assignments_list
                    ],
                    key=lambda x: x.ends_at_datetime,
                    reverse=True,
                )
                self.assignments: dict[str, list[Assignment]]
            for assignment in self.assignments["en"]:
                for task in assignment.tasks:
                    match task.type:
                        case 2:
                            """Successfully extract with {amount} {item}[ on {planet}][ in the __{sector}__ SECTOR][ from any {faction} controlled planet]"""
                            if task.planet_index:
                                self.planets[task.planet_index].in_assignment = True
                            elif task.sector_index:
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
                            elif task.faction:
                                if task.progress_perc == 1:
                                    continue
                                for planet in [
                                    p
                                    for p in self.planets.values()
                                    if p.faction == task.faction
                                ]:
                                    planet.in_assignment = True
                        case 3:
                            """Kill {amount} {enemy_type}[ using the __{item_to_use}__][ on {planet}]"""
                            if task.planet_index:
                                self.planets[task.planet_index].in_assignment = True
                            else:
                                for index in [
                                    planet.index
                                    for planet in self.planets.values()
                                    if planet.faction == task.faction
                                    or (
                                        planet.event
                                        and planet.event.faction == task.faction
                                    )
                                ]:
                                    self.planets[index].in_assignment = True
                        case 7 | 9:
                            """
                            Extract from a successful Mission against {faction} {number} times
                            |
                            Complete an Operation[ against {faction}][ on {difficulty} or higher] {amount} times
                            """
                            if task.faction:
                                for planet in [
                                    p
                                    for p in self.planets.values()
                                    if p.faction == task.faction
                                    or p.event
                                    and p.event.faction == task.faction
                                ]:
                                    planet.in_assignment = True
                        case 12:
                            """Defend[ {planet}] against {amount} attacks[ from the {faction}]"""
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
                            """
                            Liberate a planet
                            |
                            Hold {planet} when the order expires"""
                            if (
                                self.planets[task.planet_index].event
                                and self.planets[task.planet_index].event.type == 2
                            ):
                                continue
                            else:
                                self.planets[task.planet_index].in_assignment = True
        else:
            self.assignments = {}

        if self._data["campaigns"] not in ([], None):
            self.campaigns: list[Campaign] = sorted(
                [
                    Campaign(
                        raw_campaign_data=raw_campaign_data,
                        campaign_planet=self.planets[
                            raw_campaign_data["planet"]["index"]
                        ],
                    )
                    for raw_campaign_data in self._data["campaigns"]
                ],
                key=lambda item: item.planet.stats.player_count,
                reverse=True,
            )

        if self._data["dispatches"]:
            for lang, dispatches in self._data["dispatches"].items():
                self.dispatches[lang] = [
                    Dispatch(
                        raw_dispatch_data=data,
                        war_start_timestamp=self.war_start_timestamp,
                    )
                    for data in sorted(dispatches, key=lambda x: x["id"])
                ]
                self.dispatches: dict[str, list[Dispatch]]

        if self._data["steam"]:
            self.steam: list[Steam] = [
                Steam(raw_steam_data=raw_steam_data)
                for raw_steam_data in self._data["steam"]
            ]

        if self._data["galactic_war_effects"]:
            self.galactic_war_effects: list[GalacticWarEffect] = sorted(
                [
                    GalacticWarEffect(gwa=gwa, json_dict=self.json_dict)
                    for gwa in self._data["galactic_war_effects"]
                ],
                key=lambda x: x.id,
                reverse=True,
            )

        if self._data["status"]:
            self.galactic_impact_mod: float = self._data["status"]["en"][
                "impactMultiplier"
            ]
            self.global_events.clear()
            for lang, status in self._data["status"].items():
                if lang not in self.global_events:
                    self.global_events[lang] = []
                for raw_global_event_data in status["globalEvents"]:
                    self.global_events[lang].append(
                        GlobalEvent(
                            raw_global_event_data=raw_global_event_data,
                            war_time=self.war_start_timestamp,
                            gwe_list=self.galactic_war_effects,
                        )
                    )
                    self.global_events: dict[str, list[GlobalEvent]]

            self.global_resources: list[GlobalResource] = [
                GlobalResource(raw_global_resources_data=gr)
                for gr in self._data["status"]["en"]["globalResources"]
            ]

            self.planets[64].position = {  # meridia
                "x": self._data["status"]["en"]["planetStatus"][64]["position"]["x"],
                "y": self._data["status"]["en"]["planetStatus"][64]["position"]["y"],
            }
            self.planets[260].position = {  # cyberstan
                "x": self._data["status"]["en"]["planetStatus"][260]["position"]["x"],
                "y": self._data["status"]["en"]["planetStatus"][260]["position"]["y"],
            }

            for planet_effect in self._data["status"]["en"]["planetActiveEffects"]:
                planet = self.planets[planet_effect["index"]]
                gwe = [
                    g
                    for g in self.galactic_war_effects
                    if g.id == planet_effect["galacticEffectId"]
                ]
                gwe = gwe[0] if gwe != [] else None
                if gwe:
                    planet.active_effects.add(gwe)
            for ge in self.global_events["en"]:
                for planet_index in ge.planet_indices:
                    self.planets[planet_index].active_effects |= set(
                        [
                            gwe
                            for gwe in self.galactic_war_effects
                            if gwe.id in [j.id for j in ge.effects]
                        ]
                    )
                    self.planets[planet_index].active_effects = set(
                        sorted(
                            self.planets[planet_index].active_effects,
                            key=lambda x: x.id,
                        )
                    )

            for planet_attack in self._data["status"]["en"]["planetAttacks"]:
                source_planet = self.planets[planet_attack["source"]]
                target_planet = self.planets[planet_attack["target"]]
                source_planet.attack_targets.append(target_planet.index)
                target_planet.defending_from.append(source_planet.index)

            self.gambit_planets.clear()
            for campaign in [
                c
                for c in self.campaigns
                if c.planet.faction != Factions.humans and c.planet.attack_targets
            ]:
                for defending_index in campaign.planet.attack_targets:
                    defending_planet = self.planets[defending_index]
                    if (
                        len(defending_planet.attack_targets) < 2
                        and defending_planet.event
                        and campaign.planet.regen_perc_per_hour <= 0.03
                    ):
                        self.gambit_planets[defending_index] = campaign.planet

        if self._data["warinfo"]:
            if not self._data["warinfo"].get("planetRegions") or not self._data[
                "status"
            ]["en"].get("planetRegions"):
                pass
            else:
                for region in self._data["warinfo"]["planetRegions"]:
                    self.planets[region["planetIndex"]].regions[
                        region["regionIndex"]
                    ] = Planet.Region(
                        planet_regions_json_dict=self.json_dict["planetRegions"],
                        raw_planet_region_data=region,
                        planet_owner=self.planets[region["planetIndex"]].faction,
                    )
                    self.planets[region["planetIndex"]].regions[
                        region["regionIndex"]
                    ].planet = self.planets[region["planetIndex"]]

                for region in self._data["status"]["en"]["planetRegions"]:
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
            campaign.planet.tracker = self.liberation_changes.get_entry(
                campaign.planet.index
            )

    def update_tactical_action_rates(self) -> None:
        """Update the changes in global resources"""
        for ta in self.dss.tactical_actions:
            for cost in ta.cost:
                self.tactical_action_changes.add_entry(
                    key=(ta.id, cost.item), value=cost.progress
                )
                ta.cost_changes[cost.item] = self.tactical_action_changes.get_entry(
                    key=(ta.id, cost.item)
                )

    def update_major_order_rates(self) -> None:
        """Update the changes in Major Order tasks"""
        if self.assignments:
            for assignment in self.assignments["en"]:
                for task_index, task in enumerate(assignment.tasks, start=1):
                    if task.type in [12, 15]:
                        continue
                    self.major_order_changes.add_entry(
                        key=(assignment.id, task_index), value=task.progress_perc
                    )
            for assignments in self.assignments.values():
                for assignment in assignments:
                    for task_index, task in enumerate(assignment.tasks, start=1):
                        task.tracker = self.major_order_changes.get_entry(
                            key=(assignment.id, task_index)
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
                    region.tracker = self.region_changes.get_entry(
                        key=region.settings_hash
                    )

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
            (
                raw_assignment_data["briefing"]
                if raw_assignment_data["briefing"] not in ([], None)
                else ""
            )
            .strip("\n")
            .replace("\n", "\n-# ")
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
            "min_players",
            "value10",
            "difficulty",
            "planet_index",
            "sector_index",
            "type",
            "progress",
            "tracker",
        )

        def __init__(self, task: dict, current_progress: int | float) -> None:
            self.type: int = task["type"]
            self.progress: int | float = current_progress
            self.values_dict = dict(zip(task["valueTypes"], task["values"]))
            self.faction = self.target = self.enemy_id = self.item_id = (
                self.objective
            ) = self.min_players = self.difficulty = self.value10 = (
                self.planet_index
            ) = self.sector_index = None
            self.tracker: BaseTrackerEntry | None = None

            if faction := self.values_dict.get(1):
                self.faction: Faction | None = Factions.get_from_identifier(
                    number=faction
                )
            if personal := self.values_dict.get(2):
                self.personal = personal
            if target := self.values_dict.get(3):
                self.target: int | float = target
            if enemy_id := self.values_dict.get(4):
                self.enemy_id: int = enemy_id
            if self.values_dict.get(6):
                self.item_id = self.values_dict.get(5)
            if objective := self.values_dict.get(7):
                self.objective = objective
                print(f"VALUETYPE 7 - OBJECTIVE: {self.objective}")
            if min_players := self.values_dict.get(8):
                self.min_players: int = min_players
            if difficulty := self.values_dict.get(9):
                self.difficulty = difficulty
            if value10 := self.values_dict.get(10):
                self.value10 = value10
                print(f"VALUETYPE 10 - UNKNOWN: {self.value10}")
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
            anim = False
            increasing = False
            if self.tracker != None:
                anim = True
                increasing = self.tracker.change_rate_per_hour > 0

            match self.type:
                case 2:
                    """Successfully extract with {amount} {item}[ on {planet}][ in the __{sector}__ SECTOR][ from any {faction} controlled planet]"""
                    return health_bar(
                        self.progress_perc,
                        Factions.humans,
                        anim=anim,
                        increasing=increasing,
                    )
                case 3:
                    """Kill {amount} {enemy_type}[ using the __{item_to_use}__][ on {planet}]"""
                    return health_bar(
                        self.progress_perc,
                        self.faction or "MO",
                        anim=anim,
                        increasing=increasing,
                    )
                case 7:
                    """Extract from a successful Mission against {faction} {number} times"""
                    return health_bar(
                        self.progress_perc,
                        Factions.humans,
                        anim=anim,
                        increasing=increasing,
                    )
                case 9:
                    """Complete an Operation[ against {faction}][ on {difficulty} or higher] {amount} times"""
                    return health_bar(
                        self.progress_perc,
                        Factions.humans,
                        anim=anim,
                        increasing=increasing,
                    )
                case 11:
                    """Liberate a planet"""
                    return
                case 12:
                    """Defend[ {planet}] against {amount} attacks[ from the {faction}]"""
                    return health_bar(self.progress_perc, "MO")
                case 13:
                    """Hold {planet} when the order expires"""
                    return
                case 15:
                    """Liberate more planets than are lost during the order duration"""
                    percent = {i: (i + 10) / 20 for i in range(-10, 12, 2)}[
                        [key for key in range(-10, 12, 2) if key <= self.progress][-1]
                    ]
                    return health_bar(
                        percent,
                        Factions.humans if self.progress > 0 else Factions.automaton,
                    )


class Dispatch(ReprMixin):
    __slots__ = ("id", "published_at", "full_message")

    def __init__(self, raw_dispatch_data: dict, war_start_timestamp: int) -> None:
        """Organised data of a dispatch"""
        self.id: int = raw_dispatch_data["id"]
        self.published_at: datetime = datetime.fromtimestamp(
            war_start_timestamp + raw_dispatch_data.get("published", 0)
        )
        self.full_message: str = dispatch_format(
            text=raw_dispatch_data.get("message", "")
        )
        split_lines = self.full_message.splitlines(True)
        if split_lines:
            self.title = split_lines[0].replace("*", "")
            self.description = "".join(split_lines[1:]).strip()
        else:
            self.title = "New Dispatch"
            self.description = self.full_message


class GalacticWarEffect(GWEReprMixin):
    __slots__ = (
        "id",
        "gameplay_effect_id32",
        "effect_type",
        "flags",
        "name_hash",
        "fluff_description_hash",
        "long_description_hash",
        "short_description_hash",
        "values_dict",
        "effect_description",
        "planet_effect",
        "count",
        "percent",
        "faction",
        "mix_id",
        "value5",
        "DEPRECATED_enemy_group",
        "DEPRECATED_item_package",
        "value8",
        "value9",
        "reward_multiplier_id",
        "value11",
        "item_tag",
        "hash_id",
        "planet_body_type",
        "value15",
        "resource_hash",
    )

    def __init__(self, gwa: dict, json_dict: dict) -> None:
        """Organised data for a galactic war effect"""
        self.id: int = gwa["id"]
        self.gameplay_effect_id32: int = gwa["gameplayEffectId32"]
        self.effect_type: int = gwa["effectType"]
        self.flags: int = gwa["flags"]
        self.name_hash: int = gwa["nameHash"]
        self.fluff_description_hash: int = gwa["descriptionFluffHash"]
        self.long_description_hash: int = gwa["descriptionGamePlayLongHash"]
        self.short_description_hash: int = gwa["descriptionGamePlayShortHash"]
        self.values_dict: dict = dict(zip(gwa["valueTypes"], gwa["values"]))
        self.effect_description: dict = json_dict["galactic_war_effects"].get(
            str(gwa["effectType"]),
            {"name": "UNKNOWN", "simplified_name": "", "description": ""},
        )
        self.planet_effect: dict | None = json_dict["planet_effects"].get(
            str(self.id),
            {
                "name": f"UNKNOWN [{self.id}]",
                "description_long": "",
                "description_short": "",
            },
        )
        self.count = self.percent = self.faction = self.mix_id = self.value5 = (
            self.DEPRECATED_enemy_group
        ) = self.DEPRECATED_item_package = self.value8 = self.value9 = (
            self.reward_multiplier_id
        ) = self.value11 = self.item_tag = self.hash_id = self.planet_body_type = (
            self.value15
        ) = self.resource_hash = self.found_enemy = self.found_stratagem = (
            self.found_booster
        ) = None

        if count := self.values_dict.get(1):
            self.count: int | float = count
        if percent := self.values_dict.get(2):
            self.percent: int | float = percent
        if faction := self.values_dict.get(3):
            self.faction: Faction | None = Factions.get_from_identifier(number=faction)
        if mix_id := self.values_dict.get(4):
            self.mix_id: int = mix_id
            if stratagem := stratagem_id_dict.get(self.mix_id, None):
                self.found_stratagem: str = stratagem
            elif booster := json_dict["items"]["boosters"].get(str(self.mix_id), {}):
                self.found_booster: dict = booster
        if value5 := self.values_dict.get(5):
            self.value5 = value5
            print(f"VALUE5 USED: {self.id} {self.value5 = }")
        if DEPRECATED_enemy_group := self.values_dict.get(6):
            self.DEPRECATED_enemy_group = DEPRECATED_enemy_group
        if DEPRECATED_item_package := self.values_dict.get(7):
            self.DEPRECATED_item_package = DEPRECATED_item_package
        if value8 := self.values_dict.get(8):
            self.value8 = value8
            print(f"VALUE8 USED: {self.id} {self.value8 = }")
        if value9 := self.values_dict.get(9):
            self.value9 = value9
            print(f"VALUE9 USED: {self.id} {self.value9 = }")
        if reward_multiplier_id := self.values_dict.get(10):
            # refer to: /api/Mission/RewardEntries
            self.reward_multiplier_id = reward_multiplier_id
        if value11 := self.values_dict.get(11):
            self.value11 = value11
            print(f"VALUE11 USED: {self.id} {self.value11 = }")
        if item_tag := self.values_dict.get(12):
            # or item group; gets used in /Progression/Items
            self.item_tag = item_tag
        if hash_id := self.values_dict.get(13):
            self.hash_id = hash_id
            if enemy := json_dict["enemy_ids"].get(str(self.hash_id), None):
                self.found_enemy: str = enemy
        if planet_body_type := self.values_dict.get(14):
            # BlackHole = 1, UNKNOWN = 2
            self.planet_body_type = planet_body_type
        if value15 := self.values_dict.get(15):
            # might be a boolean flag, only used with game_OperationModToggle so far
            self.value15 = value15
        if resource_hash := self.values_dict.get(16):
            # murmur2 resource hash
            self.resource_hash = resource_hash
            if enemy := json_dict["enemy_ids"].get(str(self.resource_hash), None):
                self.found_enemy = enemy

    def __hash__(self):
        return hash((self.id))

    def __eq__(self, value):
        if not isinstance(value, type(self)):
            return False
        return self.id == value.id


class GlobalEvent(ReprMixin):
    __slots__ = (
        "id",
        "title",
        "message",
        "faction",
        "flag",
        "assignment_id",
        "effects",
        "planet_indices",
        "expire_time",
    )

    def __init__(
        self,
        raw_global_event_data: dict,
        war_time: float,
        gwe_list: list[GalacticWarEffect],
    ) -> None:
        """Organised data of a global event"""
        self.id: int = raw_global_event_data["eventId"]
        self.title: str = dispatch_format(raw_global_event_data["title"])
        self.message: str = dispatch_format(text=raw_global_event_data["message"])
        self.faction: Faction = Factions.get_from_identifier(
            number=raw_global_event_data["race"]
        )
        self.flag: int = raw_global_event_data["flag"]
        self.assignment_id: int = raw_global_event_data["assignmentId32"]
        self.effects: list[GalacticWarEffect] = [
            gwe for gwe in gwe_list if gwe.id in raw_global_event_data["effectIds"]
        ]
        self.planet_indices: list[int] = raw_global_event_data["planetIndices"]
        self.expire_time: int = raw_global_event_data["expireTime"] + war_time

    @property
    def split_message(self) -> list[str]:
        """Returns the message split into chunks with character lengths of 1024 or less"""
        sentences = self.message.split(sep="\n")
        formatted_sentences = [
            f"-# {sentence}" for sentence in sentences if sentence != ""
        ]
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
    __slots__ = ("id", "current_value", "max_value", "perc")

    def __init__(self, raw_global_resource_data: dict) -> None:
        """Organised data of a global resource"""
        self.id: int = raw_global_resource_data["id32"]
        self.current_value: int = raw_global_resource_data["currentValue"]
        self.max_value: int = raw_global_resource_data["maxValue"]
        self.perc: float = self.current_value / self.max_value


class Planet(ReprMixin):
    __slots__ = (
        "index",
        "name",
        "sector",
        "health_perc",
        "faction",
        "regen_perc_per_hour",
        "event",
        "dss_in_orbit",
        "in_assignment",
    )

    def __init__(self, raw_planet_data: dict, planet_names) -> None:
        """Organised data for a specific planet"""
        self.index: int = raw_planet_data["index"]
        self.name: str = raw_planet_data["name"]
        self.loc_names: dict = planet_names
        self.sector: str = raw_planet_data["sector"]
        self.biome: dict = raw_planet_data["biome"]
        self.hazards: list[dict] = raw_planet_data["hazards"]
        self.position: dict = raw_planet_data["position"]
        self.waypoints: set[int] = set(raw_planet_data["waypoints"])
        self.max_health: int = raw_planet_data["maxHealth"]
        self.health: int = raw_planet_data["health"]
        self.health_perc: float = min(self.health / self.max_health, 1)
        self.faction: Faction | None = Factions.get_from_identifier(
            name=raw_planet_data["currentOwner"]
        )
        self.regen: float = raw_planet_data["regenPerSecond"]
        self.regen_perc_per_hour: float = round(
            number=(((self.regen * 3600) / self.max_health)), ndigits=4
        )
        self.event: Planet.Event | None = (
            Planet.Event(raw_event_data=raw_planet_data["event"])
            if raw_planet_data["event"]
            else None
        )
        self.stats: Planet.Stats = Planet.Stats(
            raw_stats_data=raw_planet_data["statistics"]
        )
        self.dss_in_orbit: bool = False
        self.eagle_storm_active: bool = False
        self.in_assignment: bool = False
        self.active_effects: set[GalacticWarEffect] = set()
        self.attack_targets: list[int] = []
        self.defending_from: list[int] = []
        self.regions: dict[int, Planet.Region] = {}
        self.tracker: None | BaseTrackerEntry = None

        # BIOME/SECTOR/HAZARDS OVERWRITE #
        if self.index == 64:
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
    def health_bar(self):
        progress = (1 - self.health_perc) if not self.event else self.event.progress
        faction = self.faction if not self.event else self.event.faction
        if self.tracker and self.tracker.change_rate_per_hour != 0:
            return health_bar(
                perc=progress,
                faction=faction,
                anim=True,
                increasing=self.tracker.change_rate_per_hour > 0,
            )
        else:
            return health_bar(perc=progress, faction=faction)

    @property
    def map_waypoints(self) -> tuple[int, int]:
        return (
            int((self.position["x"] * 1000) + 1000),
            int(((self.position["y"] * -1) * 1000) + 1000),
        )

    @property
    def exclamations(self) -> str:
        result = ""
        if self.event:
            result += f":shield:{self.event.faction.emoji}"
        if self.in_assignment:
            result += Emojis.Icons.mo
        if self.dss_in_orbit:
            result += Emojis.DSS.icon
        for special_unit in SpecialUnits.get_from_effects_list(
            active_effects=self.active_effects
        ):
            result += special_unit[1]
        for feature in PlanetFeatures.get_from_effects_list(
            active_effects=self.active_effects
        ):
            result += feature[1]
        return result

    class Event(ReprMixin):
        __slots__ = (
            "id",
            "type",
            "faction",
            "health",
            "max_health",
            "progress",
            "start_time_datetime",
            "end_time_datetime",
            "level",
            "potential_buildup",
        )

        def __init__(self, raw_event_data) -> None:
            """Organised data for a planet's event (defence campaign)"""
            self.id: int = raw_event_data["id"]
            self.type: int = raw_event_data["eventType"]
            self.faction: Faction | None = Factions.get_from_identifier(
                name=raw_event_data["faction"]
            )
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
            self.level: int = int(self.max_health / 50000)
            self.level_exclamation: str = DEF_LEVEL_EXC[
                [key for key in DEF_LEVEL_EXC.keys() if key <= self.level][-1]
            ]
            self.potential_buildup: int = 0

        def __hash__(self):
            return hash((self.id))

        def __eq__(self, value):
            if not isinstance(value, type(self)):
                return False
            return self.id == value.id

    class Region(ReprMixin):
        __slots__ = (
            "planet_index",
            "index",
            "name",
            "description",
            "owner",
            "availability_factor",
            "is_available",
            "players",
            "type",
        )

        def __init__(
            self,
            planet_regions_json_dict: dict,
            raw_planet_region_data: dict,
            planet_owner: Faction,
        ):
            self.settings_hash: int = raw_planet_region_data["settingsHash"]
            json_entry: dict = planet_regions_json_dict.get(str(self.settings_hash), {})
            self.planet_index: int = raw_planet_region_data["planetIndex"]
            self.planet: Planet | None = None
            self.index: int = raw_planet_region_data["regionIndex"]
            self.name: str = json_entry.get("name", "COLONY")
            self.names: dict[str, str] = json_entry.get("names", {})
            self.description: str | None = json_entry.get("description")
            self.descriptions: dict[str, str] | None = json_entry.get(
                "descriptions", {}
            )
            self.owner: Faction = planet_owner
            self.health: int = raw_planet_region_data["maxHealth"]
            self.max_health: int = raw_planet_region_data["maxHealth"]
            self.regen_per_sec: int = 0
            self.availability_factor: float = 0.0
            self.is_available: bool = False
            self.players: int = 0
            self.size: int = raw_planet_region_data["regionSize"] + 1
            self.type: str = REGION_TYPES.get(self.size, "")
            self.tracker: BaseTrackerEntry | None = None

        @property
        def emoji(self) -> str:
            return getattr(
                getattr(Emojis.RegionIcons, self.owner.full_name),
                f"_{self.size}",
            )

        @property
        def regen_perc_per_hour(self) -> float:
            return (self.regen_per_sec * 3600) / self.max_health

        @property
        def perc(self):
            return 1 - self.health / self.max_health

        @property
        def health_bar(self) -> str:
            """Returns the health bar for the region"""
            return health_bar(perc=self.perc, faction=self.owner.full_name)

        @property
        def planet_damage_perc(self) -> float:
            """Returns how much percentage points it does the the planet upon liberation"""
            return (self.max_health * 1.5) / (
                self.planet.max_health
                if not self.planet.event
                else self.planet.event.max_health
            )

        def update_from_status_data(self, raw_planet_region_data: dict):
            self.owner: Faction | None = Factions.get_from_identifier(
                number=raw_planet_region_data["owner"]
            )
            self.health: int = raw_planet_region_data["health"]
            self.regen_per_sec: int = raw_planet_region_data.get(
                "regenPerSecond"
            ) or raw_planet_region_data.get("regerPerSecond")
            self.availability_factor: float = (
                1 - raw_planet_region_data["availabilityFactor"]
            )
            self.is_available: bool = raw_planet_region_data["isAvailable"]
            self.players: int = raw_planet_region_data["players"]

    class Stats:
        def __init__(self, raw_stats_data: dict) -> None:
            self.missions_won = raw_stats_data["missionsWon"]
            self.missions_lost = raw_stats_data["missionsLost"]
            self.mission_success_rate = raw_stats_data["missionSuccessRate"]
            self.mission_time = raw_stats_data["missionTime"]
            self.terminid_kills = raw_stats_data["terminidKills"]
            self.automaton_kills = raw_stats_data["automatonKills"]
            self.illuminate_kills = raw_stats_data["illuminateKills"]
            self.bullets_fired = raw_stats_data["bulletsFired"]
            self.bullets_hit = raw_stats_data["bulletsHit"]
            self.accuracy = raw_stats_data["accuracy"]
            self.time_played = raw_stats_data["timePlayed"]
            self.deaths = raw_stats_data["deaths"]
            self.revives = raw_stats_data["revives"]
            self.friendlies = raw_stats_data["friendlies"]
            self.player_count = raw_stats_data["playerCount"]


class Planets(dict[int, Planet]):
    def __init__(self, raw_planets_data: list[dict], planet_names_json: dict) -> None:
        """A dict in the format of `{int: Planet}` containing all of the current planets"""
        for raw_planet_data in raw_planets_data:
            self[raw_planet_data["index"]] = Planet(
                raw_planet_data=raw_planet_data,
                planet_names=planet_names_json[str(raw_planet_data["index"])]["names"],
            )


class Campaign(ReprMixin):
    __slots__ = ("id", "planet", "type", "count", "progress", "faction")

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
        self.faction: Faction = (
            self.planet.event.faction if self.planet.event else self.planet.faction
        )


class Steam(ReprMixin):
    def __init__(self, raw_steam_data: dict) -> None:
        """Organised data for a Steam announcements"""
        self.id: int = int(raw_steam_data["id"])
        self.title: str = raw_steam_data["title"]
        self.author: str = raw_steam_data["author"]
        self.url: str = raw_steam_data["url"]
        self.published_at: datetime = datetime.fromisoformat(
            raw_steam_data["publishedAt"]
        )


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
        self.votes: None | DSS.Votes = None

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
            self.cost_changes: dict[BaseTrackerEntry] = {}
            self.emoji = getattr(Emojis.DSS, self.name.lower().replace(" ", "_"), "")

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

    class Votes(ReprMixin):
        def __init__(self, planets: Planets, raw_votes_data: dict):
            self.total_votes: int = sum([o["count"] for o in raw_votes_data["options"]])
            self.available_planets: list[tuple[Planet, int]] = []
            for option in raw_votes_data["options"]:
                planet = planets[option["metaId"]]
                self.available_planets.append((planet, option["count"]))

