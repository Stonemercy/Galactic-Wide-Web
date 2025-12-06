from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from ..models import (
    Assignment,
    Campaign,
    Dispatch,
    DSS,
    GalacticWarEffect,
    GlobalEvent,
    GlobalResource,
    PersonalOrder,
    Planet,
    SteamNews,
)
from ...dataclasses import Factions


@dataclass
class FormattedDataContext:
    war_id: int
    dss_id: int
    steam_player_count: int
    war_status: dict[str, dict]
    news_feed: dict[str, list[dict]]
    assignments: dict[str, list[dict]]
    dss: dict
    dss_votes: dict
    war_stats: dict
    war_info: dict
    war_effects: list
    personal_order: dict
    steam_news: list

    json_dict: dict


class FormattedData:
    __slots__ = (
        "total_players",
        "steam_player_count",
        "galactic_impact_mod",
        "war_start_timestamp",
        "planets",
        "gambit_planets",
        "war_effects",
        "global_events",
        "global_resources",
        "dispatches",
        "assignments",
        "dss",
        "planet_events",
        "campaigns",
        "steam_news",
        "personal_order",
        "formatted_at",
    )

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
        self.dss: DSS = None
        self.planet_events: list[Planet] = []
        self.campaigns: list[Campaign] = []
        self.steam_news: list[SteamNews] = []
        self.personal_order: PersonalOrder = None

        if context.steam_player_count:
            self.steam_player_count: int = context.steam_player_count

        if context.war_status["en"]:
            self.war_start_timestamp: int = (
                int(datetime.now().timestamp()) - context.war_status["en"]["time"]
            )

        if context.war_info:
            for raw_planet in context.war_info["planetInfos"]:
                planet = Planet(
                    raw_planet_info=raw_planet,
                    planets_json=context.json_dict["planets"],
                )
                self.planets[planet.index] = planet

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

        if context.war_status["en"]:
            self.galactic_impact_mod = context.war_status["en"]["impactMultiplier"]
            for planet_status in context.war_status["en"]["planetStatus"]:
                planet = self.planets.get(planet_status["index"])
                if planet:
                    planet.add_data_from_status(raw_planet_status=planet_status)

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
                for campaign in [
                    c
                    for c in self.campaigns
                    if c.planet.faction != Factions.humans and c.planet.attack_targets
                ]:
                    for defending_index in campaign.planet.attack_targets:
                        defending_planet = self.planets.get(defending_index)
                        if defending_planet and (
                            len(defending_planet.attack_targets) < 2
                            and defending_planet.event
                            and campaign.planet.regen_perc_per_hour <= 0.03
                        ):
                            self.gambit_planets[defending_index] = campaign.planet

            for planet_event in context.war_status["en"]["planetEvents"]:
                pass

            for active_effect in context.war_status["en"]["planetActiveEffects"]:
                planet = self.planets.get(active_effect["index"])
                effect = self.war_effects.get(active_effect["galacticEffectId"])
                if planet and effect:
                    planet.active_effects.add(effect)

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

            for region_status in context.war_status["en"]["planetRegions"]:
                planet = self.planets.get(region_status["planetIndex"])
                if planet:
                    region = planet.regions.get(region_status["regionIndex"])
                    if region:
                        region.update_from_status_data(
                            raw_region_status_data=region_status
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
                    GlobalResource(raw_global_resource_data=global_resource)
                )

        if context.news_feed["en"]:
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

        if context.assignments["en"]:
            for lang, assignments in context.assignments.items():
                self.assignments[lang] = sorted(
                    [
                        Assignment(raw_assignment_data=assignment_data)
                        for assignment_data in assignments
                    ],
                    key=lambda x: x.ends_at_datetime,
                    reverse=True,
                )

            for assignment in self.assignments["en"]:
                for task in assignment.tasks:
                    if task.progress_perc >= 1:
                        continue
                    match task.type:
                        case 1 | 2 | 3 | 4 | 5 | 6 | 7 | 9 | 11:
                            if task.planet_index:
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
                                ):
                                    planet.in_assignment = True
                        case 10:
                            pass
                        case 12:
                            if task.sector_index:
                                if task.faction:
                                    for planet_event in (
                                        pe
                                        for pe in self.planet_events
                                        if pe.sector == task.sector_index
                                        and pe.event.faction == task.faction
                                    ):
                                        planet_event.in_assignment = True
                                else:
                                    for planet_event in (
                                        pe
                                        for pe in self.planet_events
                                        if pe.sector == task.sector_index
                                    ):
                                        planet_event.in_assignment = True
                            elif task.planet_index:
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
                                for planet_event in (
                                    pe
                                    for pe in self.planet_events
                                    if pe.event.faction == task.faction
                                ):
                                    planet_event.in_assignment = True
                            else:
                                for planet_event in self.planet_events:
                                    planet_event.in_assignment = True
                        case 13:
                            if task.sector_index:
                                for planet in (
                                    p
                                    for p in self.planets.values()
                                    if p.sector == task.sector_index
                                ):
                                    planet.in_assignment = True
                            elif task.planet_index:
                                planet = self.planets.get(task.planet_index)
                                if planet:
                                    planet.in_assignment = True
                        case 14 | 15:
                            if task.faction:
                                for campaign in (
                                    c
                                    for c in self.campaigns
                                    if c.faction == task.faction
                                ):
                                    campaign.planet.in_assignment = True
                            else:
                                for campaign in self.campaigns:
                                    campaign.planet.in_assignment = True
                        case _:
                            pass

        if context.dss:
            dss_planet = self.planets.get(context.dss["planetIndex"])
            if dss_planet:
                if context.dss["flags"] == 1:
                    dss_planet.dss_in_orbit = True
                self.dss: DSS = DSS(
                    raw_dss_data=context.dss,
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
                if context.dss_votes:
                    self.dss.votes = DSS.Votes(
                        planets=self.planets,
                        raw_votes_data=context.dss_votes,
                    )

        if self.planets:
            self.planet_events: list[Planet] = sorted(
                [planet for planet in self.planets.values() if planet.event],
                key=lambda planet: planet.stats.player_count,
                reverse=True,
            )
            if context.war_stats:
                for pstat in context.war_stats["planets_stats"]:
                    planet = self.planets.get(pstat["planetIndex"])
                    if planet:
                        planet.stats.update(raw_stats_info=pstat)

        if context.personal_order:
            self.personal_order: PersonalOrder = PersonalOrder(
                personal_order=context.personal_order[1], json_dict=context.json_dict
            )

        self.formatted_at = datetime.now()

    def copy(self):
        """Returns a deep copy of the data"""
        return deepcopy(self)
