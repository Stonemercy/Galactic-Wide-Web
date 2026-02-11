from datetime import datetime
from ...mixins import ReprMixin
from ...dataclasses import Faction, Factions, PlanetFeatures, SpecialUnits
from ...emojis import Emojis
from .galactic_war import GalacticWarEffect
from ...trackers import BaseTrackerEntry
from ...functions.health_bar import health_bar
from ..utils.constants import DEFENCE_LEVEL_EXCLAMATION_DICT, RegionType


class Planet(ReprMixin):
    __slots__ = (
        "index",
        "name",
        "sector",
        "event",
        "dss_in_orbit",
        "in_assignment",
    )

    def __init__(
        self,
        raw_planet_info: dict,
        planets_json: dict[str, dict],
        sectors_json: dict[int, str],
    ) -> None:
        """Organise data for a specific planet"""
        self.index: int = raw_planet_info["index"]
        self.settings_hash: int = raw_planet_info["settingsHash"]
        self.names: dict[str, str] = planets_json.get("names", {})
        self.description: str = planets_json.get("description", "")
        self.position: dict = raw_planet_info["position"]
        self.waypoints: list[int] = raw_planet_info["waypoints"]
        self._sector = raw_planet_info["sector"]
        self.sector: int = sectors_json.get(str(raw_planet_info["sector"]))
        self.dss_in_orbit: bool = False
        self.active_campaign: bool = False
        self.eagle_storm_active: bool = False
        self.in_assignment: bool = False
        self.active_effects: set[GalacticWarEffect] = set()
        self.attack_targets: list[int] = []
        self.defending_from: list[int] = []
        self.health: int = 0
        self.max_health: int = raw_planet_info["maxHealth"]
        self.regen_per_second: float = 0.0
        self.disabled: bool = raw_planet_info["disabled"]
        self.initial_owner: int = raw_planet_info["initialOwner"]
        self.owner: int = 0
        self.homeworld: Faction | None = None
        self.event: Planet.Event | None = None
        self.regions: dict[int, Planet.Region] = {}
        self.tracker: BaseTrackerEntry | None = None
        self.stats: Planet.Stats = Planet.Stats()

    def add_data_from_status(self, raw_planet_status: dict) -> None:
        self.owner: int = raw_planet_status["owner"]
        self.health: int = raw_planet_status["health"]
        self.regen_per_second: float = raw_planet_status["regenPerSecond"]
        self.stats.player_count = raw_planet_status["players"]
        self.position = raw_planet_status["position"]

    @property
    def faction(self) -> Faction:
        return Factions.get_from_identifier(number=self.owner)

    @property
    def regen_perc_per_hour(self) -> float:
        return round(
            number=(((self.regen_per_second * 3600) / self.max_health)), ndigits=4
        )

    @property
    def health_perc(self) -> float:
        return min(self.health / self.max_health, 1)

    @property
    def health_bar(self) -> str:
        progress = (1 - self.health_perc) if not self.event else self.event.progress
        faction = self.faction if not self.event else self.event.faction
        if self.tracker and self.tracker.change_rate_per_hour != 0:
            return health_bar(
                perc=progress,
                faction=faction,
                anim=True,
                increasing=self.tracker.change_rate_per_hour > 0,
            )
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

        def __init__(self, raw_event_data: dict, war_start_timestamp: int) -> None:
            """Organised data for a planet's event (defence campaign)"""
            self.id: int = raw_event_data["id"]
            self.type: int = raw_event_data["eventType"]
            self.faction: Faction | None = Factions.get_from_identifier(
                number=raw_event_data["race"]
            )
            self.health: int = raw_event_data["health"]
            self.max_health: int = raw_event_data["maxHealth"]
            self.start_time: str = raw_event_data["startTime"]
            self.end_time: str = raw_event_data["expireTime"]
            self.start_time_datetime: datetime = datetime.fromtimestamp(
                self.start_time + war_start_timestamp
            ).replace(tzinfo=None)
            self.end_time_datetime: datetime = datetime.fromtimestamp(
                self.end_time + war_start_timestamp
            ).replace(tzinfo=None)
            self.progress: float = 1 - (self.health / self.max_health)
            """A float from 0-1"""
            self.level: int = int(self.max_health / 50000)
            self.level_exclamation: str = DEFENCE_LEVEL_EXCLAMATION_DICT[
                [
                    key
                    for key in DEFENCE_LEVEL_EXCLAMATION_DICT.keys()
                    if key <= self.level
                ][-1]
            ]
            self.potential_buildup: int = 0

        def __hash__(self):
            return hash(self.id)

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
            self.damage_multiplier: float = raw_planet_region_data["damageMultiplier"]
            self.regen_per_sec: int = 0
            self.availability_factor: float = 0.0
            self.is_available: bool = False
            self.players: int = 0
            self.size: int = raw_planet_region_data["regionSize"] + 1
            self.type: RegionType = RegionType(self.size)
            self.tracker: BaseTrackerEntry | None = None

        @property
        def emoji(self) -> str:
            if self.planet.homeworld:
                return getattr(
                    getattr(Emojis.RegionIcons, self.owner.full_name),
                    f"homeworld{self.size}",
                )
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
            if self.tracker and self.tracker.change_rate_per_hour != 0:
                return health_bar(
                    perc=self.perc,
                    faction=self.owner,
                    anim=True,
                    increasing=self.tracker.change_rate_per_hour > 0,
                )
            return health_bar(perc=self.perc, faction=self.owner)

        @property
        def planet_damage_perc(self) -> float:
            """Returns how much percentage points it does the the planet upon liberation"""
            return (self.max_health * self.damage_multiplier) / (
                self.planet.max_health
                if not self.planet.event
                else self.planet.event.max_health
            )

        def update_from_status_data(self, raw_region_status_data: dict):
            self.owner: Faction | None = Factions.get_from_identifier(
                number=raw_region_status_data["owner"]
            )
            self.health: int = raw_region_status_data["health"]
            self.regen_per_sec: int = raw_region_status_data.get(
                "regenPerSecond"
            ) or raw_region_status_data.get("regerPerSecond")
            self.availability_factor: float = (
                1 - raw_region_status_data["availabilityFactor"]
            )
            self.is_available: bool = raw_region_status_data["isAvailable"]
            self.players: int = raw_region_status_data["players"]

    class Stats:
        def __init__(self) -> None:
            self.missions_won: int = 0
            self.missions_lost: int = 0
            self.mission_time: int = 0
            self.terminid_kills: int = 0
            self.automaton_kills: int = 0
            self.illuminate_kills: int = 0
            self.bullets_fired: int = 0
            self.bullets_hit: int = 0
            self.time_played: int = 0
            self.deaths: int = 0
            self.revives: int = 0
            self.friendlies: int = 0
            self.player_count: int = 0
            self.mission_success_rate: int = 0
            self.accuracy: int = 0

        def update(self, raw_stats_info: dict[str, int]) -> None:
            self.missions_won = raw_stats_info["missionsWon"]
            self.missions_lost = raw_stats_info["missionsLost"]
            self.mission_time = raw_stats_info["missionTime"]
            self.terminid_kills = raw_stats_info["bugKills"]
            self.automaton_kills = raw_stats_info["automatonKills"]
            self.illuminate_kills = raw_stats_info["illuminateKills"]
            self.bullets_fired = raw_stats_info["bulletsFired"]
            self.bullets_hit = raw_stats_info["bulletsHit"]
            self.time_played = raw_stats_info["timePlayed"]
            self.deaths = raw_stats_info["deaths"]
            self.revives = raw_stats_info["revives"]
            self.friendlies = raw_stats_info["friendlies"]
            self.mission_success_rate = raw_stats_info["missionSuccessRate"]
            self.accuracy = raw_stats_info["accurracy"]  # misspelled lol
