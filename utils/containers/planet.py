from datetime import datetime
from disnake import Colour, ui
from utils.data import Planet
from utils.dataclasses import Factions, PlanetFeatures, SpecialUnits
from utils.emojis import Emojis
from utils.functions import short_format
from utils.interactables import HDCButton, WikiButton
from utils.mixins import ReprMixin


class PlanetContainers(list[ui.Container]):
    def __init__(self, planet: Planet, containers_json: dict, faction_json: dict):
        self.append(
            self.PlanetContainer(
                planet=planet,
                container_json=containers_json["PlanetContainer"],
                faction_json=faction_json,
            )
        )
        if planet.regions:
            self.append(
                self.RegionContainer(
                    planet=planet, container_json=containers_json["RegionContainer"]
                )
            )
        self.append(
            ui.ActionRow(
                *[
                    WikiButton(
                        link="https://helldivers.wiki.gg/wiki/Planets_and_Sectors#Planet_List"
                    ),
                    HDCButton(
                        link=f"https://helldiverscompanion.com/#hellpad/planets/{planet.index}"
                    ),
                ]
            )
        )

    class PlanetContainer(ui.Container, ReprMixin):
        def __init__(self, planet: Planet, container_json: dict, faction_json: dict):
            self.components = []
            self.add_planet_info(
                planet=planet,
                component_json=container_json["planet_info"],
                factions_json=faction_json,
            )
            self.add_mission_stats(
                planet=planet, component_json=container_json["mission_stats"]
            )
            self.add_hero_stats(
                planet=planet, component_json=container_json["hero_stats"]
            )
            self.add_misc_stats(
                planet=planet,
                component_json=container_json["misc_stats"],
                faction_json=faction_json,
            )
            super().__init__(
                *self.components,
                accent_colour=Colour.from_rgb(
                    *(
                        planet.faction.colour
                        if not planet.event
                        else planet.event.faction.colour
                    )
                ),
            )

        def add_planet_info(
            self, planet: Planet, component_json: dict, factions_json: dict
        ):
            self.components.extend(
                [
                    ui.Section(
                        ui.TextDisplay(
                            (
                                f"# {planet.faction.emoji} {planet.name} {planet.exclamations}"
                                f"\n{component_json['sector']}: **{planet.sector}**"
                                f"\n{component_json['owner']}: **{factions_json[planet.faction.full_name]}**{planet.faction.emoji}"
                            )
                        ),
                        accessory=WikiButton(
                            label=f"HD Wiki - {planet.sector}",
                            link=f"https://helldivers.wiki.gg/wiki/{planet.sector.replace(' ', '_')}_Sector",
                        ),
                    ),
                    ui.Separator(),
                ]
            )

            hazards_text = f"\n🌪️ {component_json['hazards']}:"
            for hazard in planet.hazards:
                hazards_text += f"\n- {getattr(Emojis.Weather, hazard['name'].replace(' ', '_').lower(), '')} **{hazard['name']}**\n  - -# {hazard['description']}"

            self.components.append(
                ui.TextDisplay(
                    (
                        f"🏔️ {component_json['biome']}:\n-# **{planet.biome['name']}**\n - -# {planet.biome['description']}"
                        f"{hazards_text}"
                    )
                )
            )

            effects_text = f"Features:"
            for pf in PlanetFeatures.get_from_effects_list(planet.active_effects):
                effects_text += f"\n-# {pf[1]} {pf[0]}"
            if effects_text != "Features:":
                self.components.append(ui.TextDisplay(effects_text))

            su_text = f"Special Units:"
            for su in SpecialUnits.get_from_effects_list(planet.active_effects):
                su_text += f"\n-# {su[1]} {su[0]}"
            if su_text != "Special Units:":
                self.components.append(ui.TextDisplay(su_text))

            self.components.append(
                ui.TextDisplay(
                    f"**{planet.stats.player_count:,}** {component_json['heroes']}"
                )
            )

            health_text = (
                f"{planet.health_bar}"
                f"\n`{planet.health_perc if not planet.event else planet.event.progress:^25.2%}`"
            )
            if planet.tracker and planet.tracker.change_rate_per_hour > 0:
                change = f"{planet.tracker.change_rate_per_hour:+.2%}/hr"
                health_text += (
                    f"\n`{change:^25}`"
                    f"\n-# {component_json['liberated']} **<t:{int(planet.tracker.complete_time.timestamp())}:R>**"
                )
            self.components.extend(
                [
                    ui.TextDisplay(health_text),
                    ui.Separator(),
                ]
            )

        def add_mission_stats(self, planet: Planet, component_json: dict):
            self.components.append(
                ui.TextDisplay(
                    (
                        f"## {component_json['title']}"
                        f"\n{component_json['missions_won']}: **{short_format(planet.stats.missions_won)}**"
                        f"\n{component_json['missions_lost']}: **{short_format(planet.stats.missions_lost)}**"
                        f"\n{component_json['missions_winrate']}: **{planet.stats.mission_success_rate}%**"
                        f"\n{component_json['missions_time_spent']}: **{planet.stats.mission_time/31556952:.1f} {component_json['years']}**"
                    )
                )
            )

        def add_hero_stats(self, planet: Planet, component_json: dict):
            self.components.append(
                ui.TextDisplay(
                    (
                        f"## {component_json['title']}"
                        f"\n{component_json['active_heroes']}: **{planet.stats.player_count:,}**"
                        f"\n{component_json['heroes_lost']}: **{short_format(planet.stats.deaths)}**"
                        f"\n{component_json['accidentals']}: **{short_format(planet.stats.friendlies)}**"
                        f"\n{component_json['shots_fired']}: **{short_format(planet.stats.bullets_fired)}**"
                        f"\n{component_json['shots_hit']}: **{short_format(planet.stats.bullets_hit)}**"
                        f"\n{component_json['accuracy']}: **{planet.stats.accuracy}%**"
                    )
                )
            )

        def add_misc_stats(
            self, planet: Planet, component_json: dict, faction_json: dict
        ):
            faction = planet.faction if not planet.event else planet.event.faction
            if faction != Factions.humans:
                self.components.append(
                    ui.TextDisplay(
                        (
                            f"💀 {faction_json[faction.full_name]} {component_json['killed']}: "
                            f"**{short_format(getattr(planet.stats, f'{faction.singular}_kills'))}**"
                        )
                    )
                )

    class RegionContainer(ui.Container, ReprMixin):
        def __init__(self, planet: Planet, container_json: dict):
            self.components = []
            now_seconds = int(datetime.now().timestamp())
            for region in planet.regions.values():
                text_display = ui.TextDisplay(f"{region.owner.emoji} **{region.name}**")
                text_display.content += f"\n{getattr(getattr(Emojis.RegionIcons, region.owner.full_name), f'_{region.size}')} {region.type}"
                if region.description:
                    text_display.content += f"\n-# {region.description}"
                if region.is_available:
                    text_display.content += f"\n-# {container_json['heroes']}: **{region.players}** ({region.players / planet.stats.player_count:.2%})"
                    health_to_get_from = (
                        planet.max_health
                        if not planet.event
                        else planet.event.max_health
                    )
                    text_display.content += f"\n{container_json['boost_when_liberated']}: **{(region.max_health * 1.5) / health_to_get_from:.2%}**"
                    if (
                        region.tracker
                        and region.tracker.change_rate_per_hour > 0
                        and (
                            planet.tracker
                            and planet.tracker.change_rate_per_hour > 0
                            and (
                                region.tracker.complete_time
                                < planet.tracker.complete_time
                            )
                        )
                    ):
                        percent_at = planet.tracker.percentage_at(
                            region.tracker.complete_time
                        )
                        percent_total = percent_at + (
                            (region.max_health * 1.5) / health_to_get_from
                        )
                        text_display.content += f"\n-# *from **{percent_at:.2%}** to **{percent_total:.2%}** at time of liberation!*"
                    text_display.content += f"\n{region.health_bar}"
                    text_display.content += f"\n`{region.perc:^25,.2%}`"
                    if region.tracker and region.tracker.change_rate_per_hour > 0:
                        change = f"{region.tracker.change_rate_per_hour:.2%}/hr"
                        text_display.content += (
                            f"\n`{change:^25}`"
                            f"\n-# {container_json['liberated']} <t:{int(region.tracker.complete_time.timestamp())}:R>"
                        )
                elif region.owner.full_name != "Humans":
                    stat_to_use = (
                        container_json["liberation"]
                        if not planet.event
                        else container_json["defence_duration"]
                    )
                    if region.availability_factor != 1 and (
                        region.availability_factor
                    ) > (
                        planet.event.progress
                        if planet.event
                        else 1 - planet.health_perc
                    ):
                        text_display.content += container_json["unlocked_when"].format(
                            stat_to_use=stat_to_use,
                            av_factor=f"{region.availability_factor:.0%}",
                        )
                    if planet.event:
                        current_percentage = (
                            now_seconds - planet.event.start_time_datetime.timestamp()
                        ) / (
                            planet.event.end_time_datetime.timestamp()
                            - planet.event.start_time_datetime.timestamp()
                        )
                        region_avail_timestamp = int(
                            now_seconds
                            + (
                                (
                                    (region.availability_factor - current_percentage)
                                    / (1 - current_percentage)
                                )
                                * (
                                    planet.event.end_time_datetime.timestamp()
                                    - now_seconds
                                )
                            )
                        )
                        text_display.content += f"\n-# <t:{region_avail_timestamp}:R>"
                self.components.append(text_display)

            super().__init__(
                *self.components,
                accent_colour=Colour.from_rgb(*planet.faction.colour),
            )
