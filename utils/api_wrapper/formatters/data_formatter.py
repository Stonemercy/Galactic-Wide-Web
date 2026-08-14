from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from utils.api_wrapper.models import (
    Assignment,
    Campaign,
    ControlCentre,
    Dispatch,
    DSS,
    EndpointItem,
    GalacticWarEffect,
    GlobalEvent,
    GlobalResource,
    PersonalOrder,
    Planet,
    SpaceStation,
    SteamNews,
    Superstore,
)
from utils.dataclasses import Factions, Languages
from utils.dataclasses.communities import arsenal
from utils.dataclasses.enums import AssignmentTaskType, EventType, SpaceStationType

CORRECT_SECTORS = {
    "SOL": [0],
    "ALTUS": [1, 4, 2, 5, 3],
    "KELVIN": [42, 21, 19, 20, 22],
    "BARNARD": [8, 9, 6, 31, 10, 30],
    "CANTOLUS": [15, 17, 14, 39, 38],
    "CANCRI": [11, 35, 32, 12, 33],
    "GOTHMAR": [37, 13, 36],
    "IDUN": [41, 63, 40, 18],
    "CELESTE": [51, 27, 64, 85, 26, 52, 25],
    "MARSPIRA": [43, 66, 44, 45, 67],
    "KORPUS": [81, 53, 29, 83, 28],
    "IPTUS": [48, 47, 24, 23, 71, 73],
    "SAGAN": [65, 108, 106],
    "MERIDIAN": [103, 61, 62, 102],
    "TALUS": [116, 69, 46, 68],
    "MORGON": [55, 89, 56, 88],
    "SALERIA": [97, 60, 96, 59],
    "RICTUS": [95, 92, 91, 57, 94, 58, 90],
    "ORION": [127, 49, 77, 16, 79, 76, 80, 269, 271],
    "GALLUX": [134, 135, 136, 87, 54, 86],
    "HYDRA": [113, 203, 112],
    "NANOS": [110, 109, 111, 72],
    "TARRAGON": [147, 148, 149, 101, 146],
    "UMLAUT": [168, 125, 126, 270],
    "THESEUS": [150, 151, 105, 192, 104, 239],
    "GUANG": [273, 144, 145, 98, 187],
    "URSA": [132, 133, 174, 84],
    "HANZO": [137, 138, 139, 182, 93],
    "AKIRA": [140, 141, 142, 143, 186],
    "BORGUS": [130, 131, 128, 82],
    "ANDROMEDA": [156, 157, 198, 199, 200],
    "LACAILLE": [159, 160, 194, 115],
    "FERRIS": [176, 178, 180, 7],
    "ARTURION": [74, 164, 165, 118, 119, 121, 120],
    "TANIS": [161, 162, 163, 117, 250, 251],
    "ALSTRAD": [188, 189, 190],
    "FALSTAFF": [124, 122, 75, 123],
    "DRACO": [78, 169, 170],
    "MIRIN": [34, 211, 212, 258],
    "XZAR": [153, 261, 155, 197, 154, 107],
    "JIN XI": [129, 171, 172, 173, 214, 217, 268],
    "OMEGA": [184, 185, 227, 228, 229, 99],
    "LEO": [177, 179, 222, 223],
    "VALDIS": [114, 260, 202, 204, 205, 248],
    "RIGEL": [181, 183, 224, 226, 225, 272],
    "QUINTUS": [193, 234, 235, 236, 237],
    "TRIGON": [158, 262, 266, 240, 242, 243, 244],
    "XI TAURI": [230, 231, 232, 233],
    "FARSIGHT": [175, 218, 219, 220, 221],
    "L'ESTRADE": [256, 166, 167, 257, 209, 210, 259],
    "YMIR": [201, 246, 245, 247, 249],
    "GELLERT": [70, 206, 207, 252, 253],
    "SEVERIN": [152, 195, 196, 238, 241],
    "HAWKING": [255, 191, 208, 254],
    "STEN": [50, 213, 215, 216, 100, 267],
    "THE VOID": [278, 281, 280, 279, 274, 277, 276, 275],
}


@dataclass
class FormattedDataContext:
    war_id: int
    steam_player_count: int
    war_status: dict[str, dict]
    news_feed: dict[str, list[dict]]
    assignments: dict[str, list[dict]]
    war_stats: dict
    war_info: dict
    war_effects: list
    personal_order: dict
    space_stations: list[dict]
    steam_news: list
    control_centre: dict[str, list[dict]]
    superstore: list[dict]
    items_data: list[dict]

    # community targets
    arsenal_targets: list[int]

    json_dict: dict


class FormattedData:
    def __init__(
        self,
        context: FormattedDataContext,
    ):
        """Formats the data provided and sets the properties of `this_object`"""
        self.total_players: int = 0
        self.steam_player_count: int = 0
        self.galactic_impact_mod: float = 0.0
        self.war_start_timestamp: int = 0
        self.planets: dict[int, Planet] = {}
        self.gambit_planets: dict[int, Planet] = {}
        self.war_effects: dict[int, GalacticWarEffect] = {}
        self.global_events: dict[str, list[GlobalEvent]] = {}
        self.global_resources: list[GlobalResource] = []
        self.dispatches: dict[str, list[Dispatch]] = {}
        self.assignments: dict[str, list[Assignment]] = {}
        self.space_stations: list[SpaceStation] = []
        self.event_campaigns: list[Campaign] = []
        self.campaigns: list[Campaign] = []
        self.steam_news: list[SteamNews] = []
        self.control_centre: dict[str, ControlCentre] = {}
        self.superstore: Superstore | None = None
        self.items_data: list[dict] = []
        self.organised_items: list[EndpointItem] = []
        self.personal_order: PersonalOrder = None

        if context.items_data != []:
            self.items_data = context.items_data
            for i in self.items_data:
                self.organised_items.append(EndpointItem(i))

        if context.steam_player_count:
            self.steam_player_count: int = context.steam_player_count

        if context.war_status.get("en"):
            self.war_start_timestamp: int = (
                int(datetime.now(tz=timezone.utc).timestamp())
                - context.war_status["en"]["time"]
            )

        if context.war_info:
            for raw_planet in context.war_info["planetInfos"]:
                planet = Planet(
                    raw_planet_info=raw_planet,
                    planets_json=context.json_dict["planets"].get(
                        str(raw_planet["settingsHash"]),
                        {
                            "names": {
                                lang.long_code: f"UNKNOWN PLANET {raw_planet['index']}"
                                for lang in Languages.all
                            },
                            "description": "",
                        },
                    ),
                    sectors_json=context.json_dict["sectors"],
                )
                self.planets[planet.index] = planet
                if planet.index not in CORRECT_SECTORS.get(planet.sector, []):
                    planet.sector = next(
                        (s for s, pl in CORRECT_SECTORS.items() if planet.index in pl),
                        "UNKNOWN",
                    )

            for homeworld in context.war_info["homeWorlds"]:
                for planet_index in homeworld["planetIndices"]:
                    planet = self.planets.get(planet_index)
                    if planet:
                        planet.homeworld = Factions.get_from_identifier(
                            number=homeworld["race"]
                        )

        if context.war_effects:
            for war_effect in context.war_effects:
                self.war_effects[war_effect["id"]] = GalacticWarEffect(
                    gwa=war_effect, json_dict=context.json_dict
                )
            self.war_effects = dict(
                sorted(self.war_effects.items(), key=lambda x: x[0])
            )

        if context.war_status.get("en"):
            self.galactic_impact_mod: float = context.war_status["en"][
                "impactMultiplier"
            ]
            for planet_status in context.war_status["en"]["planetStatus"]:
                planet = self.planets.get(planet_status["index"])
                if planet:
                    planet.add_data_from_status(raw_planet_status=planet_status)
                else:
                    print(
                        f"data_formatter - Planet not found for status {planet_status['index']}"
                    )

            self.total_players: int = sum(
                [planet.stats.player_count for planet in self.planets.values()]
            )

            for planet_attack in context.war_status["en"]["planetAttacks"]:
                attacking_planet = self.planets.get(planet_attack["source"])
                if attacking_planet:
                    attacking_planet.attack_targets.append(planet_attack["target"])
                defending_planet = self.planets.get(planet_attack["target"])
                if defending_planet:
                    defending_planet.defending_from.append(planet_attack["source"])

            for planet_event in context.war_status["en"]["planetEvents"]:
                planet = self.planets.get(planet_event["planetIndex"])
                planet.event = Planet.Event(
                    raw_event_data=planet_event,
                    war_start_timestamp=self.war_start_timestamp,
                )
                if planet.event.type == EventType.UrgentLiberation:
                    planet.event.faction = planet.faction

            for active_effect in context.war_status["en"]["planetActiveEffects"]:
                planet = self.planets.get(active_effect["index"])
                effect = self.war_effects.get(active_effect["galacticEffectId"])
                if planet and effect:
                    planet.active_effects.add(effect)

            for campaign in context.war_status["en"]["campaigns"]:
                c_planet = self.planets.get(campaign["planetIndex"])
                if c_planet:
                    self.campaigns.append(
                        Campaign(raw_campaign_data=campaign, campaign_planet=c_planet)
                    )
            if self.campaigns != []:
                self.campaigns = sorted(
                    self.campaigns,
                    key=lambda i: i.planet.stats.player_count,
                    reverse=True,
                )
                self.gambit_planets = {}
                for campaign in [
                    c
                    for c in self.campaigns
                    if c.planet.faction != Factions.humans
                    and c.planet.defending_from
                    and not c.planet.is_hidden
                    and c.planet.regen_perc_per_hour <= 0.03
                ]:
                    for defending_index in campaign.planet.attack_targets:
                        defending_planet = self.planets.get(defending_index)
                        if defending_planet and (
                            len(defending_planet.defending_from) < 2
                            and defending_planet.event
                        ):
                            self.gambit_planets[defending_index] = campaign.planet
                for campaign in self.campaigns:
                    campaign.planet.active_campaign = True

            if context.war_info:
                for region in context.war_info["planetRegions"]:
                    planet = self.planets.get(region["planetIndex"])
                    if planet:
                        planet.regions[region["regionIndex"]] = Planet.Region(
                            planet_regions_json_dict=context.json_dict["planetRegions"],
                            raw_planet_region_data=region,
                            planet_owner=planet.faction,
                        )
                        planet.regions[region["regionIndex"]].planet = planet

            for region_status in context.war_status.get("en", {"planetRegions": []})[
                "planetRegions"
            ]:
                planet = self.planets.get(region_status["planetIndex"])
                if planet:
                    region = planet.regions.get(region_status["regionIndex"])
                    if region:
                        region.update_from_status_data(
                            raw_region_status_data=region_status
                        )

            self.event_campaigns: list[Campaign] = sorted(
                [c for c in self.campaigns if c.planet.event],
                key=lambda c: c.planet.stats.player_count,
                reverse=True,
            )

            for lang, status in context.war_status.items():
                self.global_events[lang] = [
                    GlobalEvent(
                        raw_global_event_data=ge_data,
                        war_time=self.war_start_timestamp,
                        war_effect_list=self.war_effects,
                    )
                    for ge_data in status["globalEvents"]
                ]

            for global_resource in context.war_status["en"]["globalResources"]:
                self.global_resources.append(
                    GlobalResource.from_id(raw_gr_data=global_resource)
                )

        if context.news_feed.get("en"):
            for lang, dispatches in context.news_feed.items():
                self.dispatches[lang] = [
                    Dispatch(
                        raw_dispatch_data=dispatch_data,
                        war_start_timestamp=self.war_start_timestamp,
                    )
                    for dispatch_data in sorted(dispatches, key=lambda x: x["id"])
                ]

        if context.steam_news:
            self.steam_news = [
                SteamNews(raw_steam_data=steam_news)
                for steam_news in context.steam_news
            ]

        if context.assignments.get("en") != None:
            for lang, assignments in context.assignments.items():
                self.assignments[lang] = sorted(
                    [
                        Assignment(
                            raw_assignment_data=assignment_data,
                            war_start_timestamp=self.war_start_timestamp,
                        )
                        for assignment_data in assignments
                    ],
                    key=lambda x: x.ends_at_datetime,
                    reverse=True,
                )
                for assignment in self.assignments.get(lang, []):
                    if assignment.briefing and assignment.briefing.count("_") > 5:
                        english_assignment = next(
                            (
                                a
                                for a in self.assignments.get("en", [])
                                if a.id == assignment.id
                            ),
                            None,
                        )
                        if english_assignment:
                            if (
                                english_assignment.briefing
                                and english_assignment.briefing.count("_") < 5
                            ):
                                assignment.briefing = english_assignment.briefing

            # in_assignment
            for assignment in self.assignments.get("en", []):
                for task in assignment.tasks:
                    match task.type:
                        case (
                            AssignmentTaskType.ExtractFromLocations
                            | AssignmentTaskType.ExtractWithItem
                            | AssignmentTaskType.KillEnemies
                            | AssignmentTaskType.CompleteObjectives
                            | AssignmentTaskType.PlayObjectives
                            | AssignmentTaskType.UseItems
                            | AssignmentTaskType.ExtractFromMission
                            | AssignmentTaskType.CompleteOperations
                            | AssignmentTaskType.LiberateLocationsSpecific
                        ):
                            if task.progress_perc >= 1:
                                continue
                            if task.planet_index != None:
                                planet = self.planets.get(task.planet_index)
                                if planet:
                                    planet.in_assignment = True
                            elif task.sector_index:
                                for planet in (
                                    p
                                    for p in self.planets.values()
                                    if p.sector == task.sector_index
                                ):
                                    planet.in_assignment = True
                            elif task.faction:
                                for planet in (
                                    p
                                    for p in self.planets.values()
                                    if p.faction == task.faction
                                    and p.active_campaign
                                    or p.event
                                    and p.event.faction == task.faction
                                ):
                                    planet.in_assignment = True
                        case AssignmentTaskType.DonateItems:
                            if task.progress_perc >= 1:
                                continue
                            pass
                        case AssignmentTaskType.DefendFromAttacks:
                            if task.progress_perc >= 1:
                                continue
                            if task.sector_index:
                                if task.faction:
                                    for event_campaign in (
                                        c
                                        for c in self.event_campaigns
                                        if c.planet.sector == task.sector_index
                                        and c.planet.event.faction == task.faction
                                    ):
                                        event_campaign.planet.in_assignment = True
                                else:
                                    for event_campaign in (
                                        c
                                        for c in self.event_campaigns
                                        if c.planet.sector == task.sector_index
                                    ):
                                        event_campaign.planet.in_assignment = True
                            elif task.planet_index != None:
                                planet = self.planets.get(task.planet_index)
                                if planet:
                                    if planet.event:
                                        if task.faction:
                                            if planet.event.faction == task.faction:
                                                planet.in_assignment = True
                                        else:
                                            if planet.event:
                                                planet.in_assignment = True
                            elif task.faction:
                                for event_campaign in (
                                    c
                                    for c in self.event_campaigns
                                    if c.planet.event.faction == task.faction
                                ):
                                    event_campaign.planet.in_assignment = True
                            else:
                                for event_campaign in self.event_campaigns:
                                    event_campaign.planet.in_assignment = True
                        case AssignmentTaskType.HoldLocationsUntilEnd:
                            if task.sector_index:
                                for planet in (
                                    p
                                    for p in self.planets.values()
                                    if p.sector == task.sector_index
                                    and (
                                        planet.faction != Factions.humans
                                        or (
                                            planet.event
                                            and planet.event.type == EventType.Defence
                                        )
                                    )
                                ):
                                    planet.in_assignment = True
                            elif task.planet_index != None:
                                planet = self.planets.get(task.planet_index)
                                if planet and (
                                    planet.faction != Factions.humans
                                    or (
                                        planet.event
                                        and planet.event.type == EventType.Defence
                                    )
                                ):
                                    planet.in_assignment = True
                        case (
                            AssignmentTaskType.LiberateLocationsCount
                            | AssignmentTaskType.NetLiberation
                        ):
                            if task.faction:
                                for campaign in (
                                    c
                                    for c in self.campaigns
                                    if c.faction == task.faction
                                ):
                                    campaign.planet.in_assignment = True
                        case _:
                            pass

        for space_station_json in context.space_stations:
            space_station = None
            ss_planet = self.planets.get(space_station_json.get("planetIndex", 0))
            match SpaceStationType(space_station_json["id32"]):
                case SpaceStationType.DSS:
                    if space_station_json.get("flags") == 0:
                        planet_with_1217 = next(
                            (p for p in self.planets.values() if 1217 in p.effect_ids),
                            None,
                        )
                        if planet_with_1217:
                            ss_planet = planet_with_1217

                    space_station = DSS(
                        raw_space_station_data=space_station_json,
                        ss_planet=ss_planet,
                        planets=self.planets,
                        war_start_timestamp=self.war_start_timestamp,
                    )

                    space_station.planet.dss_in_orbit = True

                    if eagle_storm := space_station.get_ta_by_name("EAGLE STORM"):
                        if (
                            eagle_storm.status == 2
                            and space_station.planet.event
                            and space_station.planet.event.type == EventType.Defence
                        ):
                            space_station.planet.eagle_storm_active = True
                            dss_moving = False
                            if space_station.votes:
                                next_planet = space_station.votes.available_planets[0][
                                    0
                                ]
                                if space_station.planet != next_planet:
                                    time_until_move = (
                                        space_station.move_timer_datetime
                                        - datetime.now(tz=timezone.utc)
                                    ).total_seconds()
                                    space_station.planet.event.end_time_datetime += (
                                        timedelta(seconds=time_until_move)
                                    )
                                    dss_moving = True

                            if not dss_moving:
                                space_station.planet.event.end_time_datetime += (
                                    timedelta(
                                        seconds=(
                                            eagle_storm.status_end_datetime
                                            - datetime.now(tz=timezone.utc)
                                        ).total_seconds()
                                    )
                                )
                case _:
                    space_station = SpaceStation(
                        raw_space_station_data=space_station_json,
                        ss_planet=ss_planet,
                        planets=self.planets,
                        war_start_timestamp=self.war_start_timestamp,
                    )

            if ss_effects := next(
                (
                    ss
                    for ss in context.war_status.get("en", {}).get("spaceStations", [])
                    if ss["id32"] == space_station.id
                ),
                {},
            ).get("activeEffectIds", []):
                for effect in ss_effects:
                    space_station.active_effects.append(self.war_effects.get(effect))
                    for effect in space_station.active_effects:
                        space_station.planet.active_effects.add(effect)

            self.space_stations.append(space_station)

        if self.planets:
            if context.war_stats:
                for pstat in context.war_stats["planets_stats"]:
                    planet = self.planets.get(pstat["planetIndex"])
                    if planet:
                        planet.stats.update(raw_stats_info=pstat)

        if context.personal_order:
            correct_po = next(
                (
                    po
                    for po in context.personal_order
                    if po["setting"]["rewards"] != []
                    and 8 not in (task["type"] for task in po["setting"]["tasks"])
                ),
                None,
            )
            if correct_po:
                self.personal_order: PersonalOrder = PersonalOrder(
                    personal_order=correct_po, json_dict=context.json_dict
                )

        if self.planets:
            for region in (
                r for p in self.planets.values() for r in p.regions.values()
            ):
                for index in region._connection_indices:
                    if connected_region_list := [
                        r
                        for p in self.planets.values()
                        for r in p.regions.values()
                        if r.settings_hash == index
                    ]:
                        connected_region = connected_region_list[0]
                        region.connections.append(connected_region)

            for p in self.planets.values():
                for wplanet in (self.planets.get(wp) for wp in p.waypoints):
                    wplanet.nearby.append(p.index)

            for ge in self.global_events.get("en", []):
                if ge.effects and ge.planet_indices:
                    for planet in (self.planets.get(i) for i in ge.planet_indices):
                        planet.active_effects.update(set(ge.effects))

            # community targets
            if context.arsenal_targets:
                for i in context.arsenal_targets:
                    planet = self.planets.get(i)
                    if planet:
                        planet.community_targets.append(arsenal)

        if context.control_centre.get("en"):
            self.control_centre = {
                lang: ControlCentre(
                    context.control_centre.get(lang),
                    context.json_dict,
                    self.war_start_timestamp,
                )
                for lang in context.control_centre
            }

        if context.superstore != []:
            self.superstore = Superstore(
                context.superstore,
                context.json_dict["items"]["items"],
                self.organised_items,
            )

        self.formatted_at = datetime.now(tz=timezone.utc)

    def copy(self):
        """Returns a deep copy of the data"""
        return deepcopy(self)

    @property
    def dss(self) -> DSS | None:
        """Returns the DSS data"""
        return next(
            (ss for ss in self.space_stations if ss.type == SpaceStationType.DSS), None
        )
