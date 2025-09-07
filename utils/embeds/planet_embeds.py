from datetime import datetime, timedelta
from disnake import Colour, Embed, File
from math import sqrt
from utils.data import Planet
from utils.dataclasses import Factions, SpecialUnits
from utils.emojis import Emojis
from utils.functions import health_bar, short_format
from utils.mixins import EmbedReprMixin
from utils.trackers import BaseTracker, BaseTrackerEntry


class PlanetEmbeds(list):
    def __init__(
        self,
        planet_name: str,
        planet: Planet,
        language_json: dict,
        liberation_change: BaseTrackerEntry,
        region_changes: BaseTracker,
        total_players: int,
    ):
        self.append(
            self.PlanetEmbed(
                planet_name=planet_name,
                planet=planet,
                language_json=language_json,
                liberation_change=liberation_change,
                total_players=total_players,
            )
        )
        if planet.regions != {}:
            self.append(
                self.RegionEmbed(
                    planet=planet,
                    planet_changes=liberation_change,
                    region_changes=region_changes,
                )
            )

    class PlanetEmbed(Embed, EmbedReprMixin):
        def __init__(
            self,
            planet_name: str,
            planet: Planet,
            language_json: dict,
            liberation_change: BaseTrackerEntry,
            total_players: int,
        ):
            super().__init__(
                colour=Colour.from_rgb(
                    *(
                        planet.current_owner.colour
                        if not planet.event
                        else planet.event.faction.colour
                    )
                )
            )
            self.add_planet_info(
                planet_name=planet_name,
                planet=planet,
                language_json=language_json,
                liberation_change=liberation_change,
                total_players=total_players,
            )
            self.add_mission_stats(planet=planet, language_json=language_json)
            self.add_hero_stats(planet=planet, language_json=language_json)
            self.add_field(name="", value="", inline=False)
            self.add_misc_stats(planet=planet, language_json=language_json)
            self.set_footer(text=planet.index)

        def add_planet_info(
            self,
            planet_name: str,
            planet: Planet,
            language_json: dict,
            liberation_change: BaseTrackerEntry | None,
            total_players: int,
        ):
            sector = language_json["PlanetEmbed"]["sector"].format(sector=planet.sector)
            owner = language_json["PlanetEmbed"]["owner"].format(
                faction=language_json["factions"][planet.current_owner.full_name],
                faction_emoji=getattr(
                    Emojis.Factions, planet.current_owner.full_name.lower()
                ),
            )
            biome = language_json["PlanetEmbed"]["biome"].format(
                biome_name=planet.biome["name"],
                biome_description=planet.biome["description"],
            )
            environmentals = language_json["PlanetEmbed"]["environmentals"].format(
                environmentals="".join(
                    [
                        f"\n- {getattr(Emojis.Weather, hazard['name'].replace(' ', '_').lower(), '')} **{hazard['name']}**\n  - -# {hazard['description']}"
                        for hazard in planet.hazards
                    ]
                )
            )
            title_exclamation = ""
            if planet.dss_in_orbit:
                title_exclamation += Emojis.DSS.icon
                title_exclamation += Emojis.DSS.operational_support
            if planet.in_assignment:
                title_exclamation += Emojis.Icons.mo
            self.add_field(
                f"__**{planet_name}**__ {title_exclamation}",
                (f"{sector}" f"{owner}" f"{biome}" f"{environmentals}"),
                inline=False,
            )

            outlook_text = ""
            required_players = ""
            liberation_text = ""
            if planet.event:
                planet_health_bar = (
                    health_bar(planet.event.progress, planet.event.faction, True)
                    + f" 🛡️ {getattr(Emojis.Factions, planet.event.faction.full_name.lower())}"
                )
                if liberation_change and liberation_change.change_rate_per_hour != 0:
                    estimated_end_timestamp = int(
                        datetime.now().timestamp()
                        + liberation_change.seconds_until_complete
                    )
                    winning = (
                        datetime.fromtimestamp(estimated_end_timestamp)
                        < planet.event.end_time_datetime
                    )
                    if winning:
                        outlook_text = f"{language_json['dashboard']['outlook']}: **{language_json['victory']}** <t:{estimated_end_timestamp}:R>\n"
                    else:
                        outlook_text = f"{language_json['dashboard']['outlook']}: **{language_json['defeat']}**\n"
                    change = f"{liberation_change.change_rate_per_hour:+.2%}/hour"
                    liberation_text = f"\n`{change:^25}`"
                    if planet.event.required_players:
                        if 0 < planet.event.required_players < 2.5 * total_players:
                            required_players = f"\n{language_json['dashboard']['DefenceEmbed']['players_required']}: **~{planet.event.required_players:,.0f}+**"
                        else:
                            if (
                                planet.event.start_time_datetime
                                > datetime.now() - timedelta(hours=1)
                            ):
                                required_players = f"\n{language_json['dashboard']['DefenceEmbed']['players_required']}: *Gathering Data*"
                            else:
                                required_players = f"\n{language_json['dashboard']['DefenceEmbed']['players_required']}: **IMPOSSIBLE**"
                health_text = f"{planet.event.progress:^25,.2%}"
                self.add_field(
                    "",
                    (
                        f"{outlook_text}"
                        f"Heroes: **{planet.stats.player_count:,}**"
                        f"{required_players}"
                        f"\n{language_json['PlanetEmbed']['liberation_progress']}"
                        f"\n{planet_health_bar}"
                        f"\n`{health_text}`"
                        f"{liberation_text}"
                        "\u200b\n"
                    ),
                    inline=False,
                )
            else:
                health_text = (
                    f"{1 - (planet.health_perc):^25,.2%}"
                    if planet.current_owner != Factions.humans
                    else f"{(planet.health_perc):^25,.2%}"
                )
                planet_health_bar = health_bar(
                    planet.health_perc,
                    planet.current_owner,
                    True if planet.current_owner != Factions.humans else False,
                )
                if liberation_change and liberation_change.change_rate_per_hour > 0:
                    estimated_end_timestamp = int(
                        datetime.now().timestamp()
                        + liberation_change.seconds_until_complete
                    )
                    change = f"{liberation_change.change_rate_per_hour:+.2f}%/hour"
                    liberation_text = f"\n`{change:^25}`"
                    outlook_text = f"{language_json['dashboard']['outlook']}: **{language_json['victory']}** <t:{estimated_end_timestamp}:R>\n"
                self.add_field(
                    "",
                    (
                        f"{outlook_text}"
                        f"Heroes: **{planet.stats.player_count:,}**"
                        f"\n{language_json['PlanetEmbed']['liberation_progress']}"
                        f"\n{planet_health_bar}"
                        f"\n`{health_text}`"
                        f"{liberation_text}"
                        "\u200b\n"
                    ),
                    inline=False,
                )
            if planet.dss_in_orbit:
                self.add_field(
                    f"{Emojis.DSS.operational_support} Operational Support",
                    f"The presence of the {Emojis.DSS.icon} DSS near this planet provides a slight boost to **Liberation Campaign** progress.",
                    inline=False,
                )
            for special_unit in SpecialUnits.get_from_effects_list(
                planet.active_effects
            ):
                self.add_field(
                    "",
                    f"\n- **{language_json['special_units'][special_unit[0]]}** {special_unit[1]}",
                )

            effects = ""
            for ae in planet.active_effects:
                if ae.planet_effect:
                    effects += f"\n- **{ae.planet_effect['name']}**\n  - -# {ae.planet_effect['description']}"
            if effects:
                self.add_field("Planetary Effects", effects, inline=False)
            self.add_field(
                "Distance from Super Earth",
                f"**{sqrt(planet.position['x']**2 + planet.position['y']**2) * 1000:.2f}** SU",
                inline=False,
            )

        def add_mission_stats(self, planet: Planet, language_json: dict):
            self.add_field(
                language_json["PlanetEmbed"]["mission_stats"],
                (
                    f"{language_json['PlanetEmbed']['missions_won']}: **`{short_format(planet.stats.missions_won)}`**\n"
                    f"{language_json['PlanetEmbed']['missions_lost']}: **`{short_format(planet.stats.missions_lost)}`**\n"
                    f"{language_json['PlanetEmbed']['missions_winrate']}: **`{planet.stats.mission_success_rate}%`**\n"
                    f"{language_json['PlanetEmbed']['missions_time_spent']}: **`{planet.stats.mission_time/31556952:.1f} years`**"
                ),
            )

        def add_hero_stats(self, planet: Planet, language_json: dict):
            self.add_field(
                language_json["PlanetEmbed"]["hero_stats"],
                (
                    f"{language_json['PlanetEmbed']['active_heroes']}: **`{planet.stats.player_count:,}`**\n"
                    f"{language_json['PlanetEmbed']['heroes_lost']}: **`{short_format(planet.stats.deaths)}`**\n"
                    f"{language_json['PlanetEmbed']['accidentals']}: **`{short_format(planet.stats.friendlies)}`**\n"
                    f"{language_json['PlanetEmbed']['shots_fired']}: **`{short_format(planet.stats.bullets_fired)}`**\n"
                    f"{language_json['PlanetEmbed']['shots_hit']}: **`{short_format(planet.stats.bullets_hit)}`**\n"
                    f"{language_json['PlanetEmbed']['accuracy']}: **`{planet.stats.accuracy}%`**\n"
                ),
            )

        def add_misc_stats(self, planet: Planet, language_json: dict):
            faction = planet.current_owner if not planet.event else planet.event.faction
            if faction != Factions.humans:
                self.add_field(
                    f"💀 {language_json['factions'][faction.full_name]} {language_json['PlanetEmbed']['killed']}:",
                    f"**{short_format(getattr(planet.stats, f'{faction.singular}_kills'))}**",
                    inline=False,
                ).set_author(
                    name=language_json["PlanetEmbed"]["liberation_progress"],
                    icon_url={
                        "Automaton": "https://cdn.discordapp.com/emojis/1215036421551685672.webp?size=44&quality=lossless",
                        "Terminids": "https://cdn.discordapp.com/emojis/1215036423090999376.webp?size=44&quality=lossless",
                        "Illuminate": "https://cdn.discordapp.com/emojis/1317057914145603635.webp?size=44&quality=lossless",
                    }.get(
                        faction.full_name,
                        None,
                    ),
                )
            if planet.feature:
                self.add_field("Feature", planet.feature)
            if planet.thumbnail:
                self.set_thumbnail(url=planet.thumbnail)
            elif planet.index == 64:
                self.set_thumbnail(
                    url="https://cdn.discordapp.com/emojis/1331357764039086212.webp?size=96"
                )
            try:
                self.set_image(
                    file=File(
                        f"resources/biomes/{planet.biome['name'].lower().replace(' ', '_')}.png"
                    )
                )
                self.image_set = True
            except:
                self.image_set = False

    class RegionEmbed(Embed, EmbedReprMixin):
        def __init__(
            self,
            planet: Planet,
            planet_changes: BaseTrackerEntry | None,
            region_changes: BaseTracker | None,
        ):
            super().__init__(colour=Colour.from_rgb(*planet.current_owner.colour))
            now_seconds = int(datetime.now().timestamp())
            for region in planet.regions.values():
                region_emojis = getattr(Emojis.RegionIcons, region.owner.full_name)
                level_emoji = getattr(region_emojis, f"_{region.size}")
                description = f"{level_emoji} **{region.type}**"
                if region.description:
                    description += f"\n-# {region.description}"
                if region.is_available:
                    description += f"\n-# Heroes: **{region.players}** ({region.players / planet.stats.player_count:.2%})"
                    health_to_get_from = (
                        planet.max_health
                        if not planet.event
                        else planet.event.max_health
                    )
                    description += f"\nBoost when liberated: **{(region.max_health * 1.5) / health_to_get_from:.2%}**"
                    description += f"\n{region.health_bar}"
                    description += f"\n`{region.perc:^25,.2%}`"
                    region_change = region_changes.get_entry(region.settings_hash)
                    if region_change:
                        change = f"{region_change.change_rate_per_hour:+.2%}/hour"
                        description += f"\n`{change:^25}`"
                        if region_change.change_rate_per_hour > 0:
                            description += f"\nLiberated <t:{now_seconds + region_change.seconds_until_complete}:R>"
                elif region.owner.full_name != "Humans":
                    stat_to_use = (
                        "liberation" if not planet.event else "defence duration"
                    )
                    if region.availability_factor != 1 and (
                        region.availability_factor
                    ) > (
                        planet.event.progress
                        if planet.event
                        else 1 - planet.health_perc
                    ):
                        description += f"\nUnlocks when **{stat_to_use}** reaches **{region.availability_factor:.0%}**"
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
                        description += f"\n-# <t:{region_avail_timestamp}:R>"
                    elif planet_changes and planet_changes.change_rate_per_hour > 0:
                        seconds_until_we_win = planet_changes.seconds_until_complete
                        current_progress = 1 - planet.health_perc
                        progress_needed = (
                            region.availability_factor
                        ) - current_progress
                        time_to_unlock = seconds_until_we_win * progress_needed
                        description += f"\n-# <t:{int(datetime.now().timestamp() + time_to_unlock)}:R>"

                self.add_field(
                    f"{getattr(Emojis.Factions, region.owner.full_name.lower() or planet.current_owner.full_name.lower())} {region.name}",
                    description,
                    inline=False,
                )
                self.set_image("https://i.imgur.com/cThNy4f.png")
