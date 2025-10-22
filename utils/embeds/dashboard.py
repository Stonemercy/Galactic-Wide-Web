from datetime import datetime, timedelta
from data.lists import (
    CUSTOM_COLOURS,
    stratagem_id_dict,
    ATTACK_EMBED_ICONS,
    DEFENCE_EMBED_ICONS,
)
from disnake import Colour, Embed
from utils.data import (
    Assignment,
    Campaign,
    Data,
    DSS,
    GlobalEvent,
    Planet,
    Planets,
)
from utils.dataclasses import AssignmentImages, Factions, SpecialUnits, PlanetFeatures
from utils.emojis import Emojis
from utils.functions import get_end_time, health_bar, short_format
from utils.mixins import EmbedReprMixin
from utils.trackers import BaseTrackerEntry

STATUS_DICT = {
    0: "inactive",
    1: "preparing",
    2: "active",
    3: "on_cooldown",
}


class Dashboard:
    def __init__(
        self,
        data: Data,
        language_code: str,
        json_dict: dict,
        compact_level: int = 0,
    ):
        language_json = json_dict["languages"][language_code]
        self.embeds: list[Embed] = []

        # Major Order embeds
        if assignments := data.assignments.get(language_code):
            for assignment in assignments:
                self.embeds.append(
                    self.MajorOrderEmbed(
                        assignment=assignment,
                        planets=data.planets,
                        gambit_planets=data.gambit_planets,
                        language_json=language_json,
                        json_dict=json_dict,
                        compact_level=compact_level,
                    )
                )

        # DSS Eembed
        if data.dss and data.dss.flags not in (0, 2):
            self.embeds.append(
                self.DSSEmbed(
                    dss=data.dss,
                    language_json=language_json,
                    gambit_planets=data.gambit_planets,
                )
            )

        # Defence embed
        if data.planet_events:
            eagle_storm = data.dss.get_ta_by_name("EAGLE STORM") if data.dss else None
            self.embeds.append(
                self.DefenceEmbed(
                    planet_events=data.planet_events,
                    language_json=language_json,
                    total_players=data.total_players,
                    eagle_storm=eagle_storm,
                    gambit_planets=data.gambit_planets,
                    compact_level=compact_level,
                )
            )

        # Attack embeds
        self.embeds.append(
            self.AttackEmbed(
                campaigns=[
                    campaign
                    for campaign in data.campaigns
                    if campaign.faction == Factions.illuminate
                    and not campaign.planet.event
                ],
                language_json=language_json,
                faction="Illuminate",
                total_players=data.total_players,
                gambit_planets=data.gambit_planets,
                planets=data.planets,
                compact_level=compact_level,
            )
        )
        self.embeds.append(
            self.AttackEmbed(
                campaigns=[
                    campaign
                    for campaign in data.campaigns
                    if campaign.faction == Factions.automaton
                    and not campaign.planet.event
                ],
                language_json=language_json,
                faction="Automaton",
                total_players=data.total_players,
                gambit_planets=data.gambit_planets,
                planets=data.planets,
                compact_level=compact_level,
            )
        )
        self.embeds.append(
            self.AttackEmbed(
                campaigns=[
                    campaign
                    for campaign in data.campaigns
                    if campaign.faction == Factions.terminids
                    and not campaign.planet.event
                ],
                language_json=language_json,
                faction="Terminids",
                total_players=data.total_players,
                gambit_planets=data.gambit_planets,
                planets=data.planets,
                compact_level=compact_level,
            )
        )
        self.embeds.append(
            self.FooterEmbed(
                language_json=language_json,
                total_players=data.total_players,
                steam_players=data.steam_playercount,
                data_time=data.fetched_at,
            )
        )

        for embed in self.embeds.copy():
            if len(embed.fields) == 0:
                self.embeds.remove(embed)
            else:
                # add blank line (max size, dont change)
                embed.set_image("https://i.imgur.com/cThNy4f.png")
        embeds_to_skip = (self.DSSEmbed,)

        if self.character_count() > 5900 or compact_level > 0:
            self.embeds = [
                embed
                for embed in self.embeds.copy()
                if type(embed) not in embeds_to_skip
            ]

    def character_count(self):
        total_characters = 0
        for embed in self.embeds:
            if embed.title:
                total_characters += len(embed.title.strip())
            if embed.description:
                total_characters += len(embed.description.strip())
            if embed.footer:
                total_characters += len(embed._footer.get("text", "").strip())
            if embed.author:
                total_characters += len(embed._author.get("name", "").strip())
            if embed.fields:
                for field in embed.fields:
                    total_characters += len(field.name.strip())
                    total_characters += len(field.value.strip())
        return total_characters

    class MajorOrderEmbed(Embed, EmbedReprMixin):
        def __init__(
            self,
            assignment: Assignment,
            planets: Planets,
            gambit_planets: dict[int, Planet] | dict,
            language_json: dict,
            json_dict: dict,
            compact_level: int = 0,
        ):
            self.assignment = assignment
            self.planets = planets
            self.gambit_planets = gambit_planets
            self.language_json = language_json
            self.json_dict = json_dict
            self.compact_level = compact_level
            self.completion_timestamps = []
            self.total_players = sum(
                [p.stats.player_count for p in self.planets.values()]
            )

            super().__init__(
                title=self.assignment.title,
                colour=Colour.from_rgb(*CUSTOM_COLOURS["MO"]),
            )

            self._set_thumbnail()

            if self.compact_level < 2:
                self._add_description()

            self._collect_completion_timestamps()

            for task in self.assignment.tasks:
                match task.type:
                    case 2:
                        """Successfully extract with {amount} {item}[ on {planet}][ in the __{sector}__ SECTOR][ from any {faction} controlled planet]"""
                        self.add_type_2(task=task)
                    case 3:
                        """Kill {amount} {enemy_type}[ using the __{item_to_use}__][ on {planet}]"""
                        self.add_type_3(task=task)
                    case 7:
                        """Extract from a successful Mission against {faction} {number} times"""
                        self.add_type_7(task=task)
                    case 9:
                        """Complete an Operation[ against {faction}][ on {difficulty} or higher] {amount} times"""
                        self.add_type_9(task=task)
                    case 11:
                        """Liberate a planet"""
                        self.add_type_11(task=task)
                    case 12:
                        """Defend[ {planet}] against {amount} attacks[ from the {faction}]"""
                        self.add_type_12(task=task)
                    case 13:
                        """Hold {planet} when the order expires"""
                        self.add_type_13(task=task)
                    case 15:
                        """Liberate more planets than are lost during the order duration"""
                        self.add_type_15(task=task)
                    case _:
                        self.add_type_UNK(task=task)
                if (
                    self.assignment.flags in (2, 3)
                    and len(self.assignment.tasks) > 1
                    and task != self.assignment.tasks[-1]
                ):
                    self.add_field("or", "", inline=False)

            self._add_rewards()

            self.add_field(
                "",
                f"-# {self.language_json['ends']} <t:{int(self.assignment.ends_at_datetime.timestamp())}:R>",
            )

            self._add_outlook_text()

        def add_type_2(self, task: Assignment.Task) -> None:
            """Successfully extract with `{count}` `{item}` `[ on {planet}]` `[ in the __{sector}__ SECTOR]` `[ from any {faction} controlled planet]`"""
            field_name = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]["type2"].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                amount=short_format(task.target),
                item=self.language_json["currencies"][
                    self.json_dict["items"]["item_names"][str(task.item_id)]["name"]
                ],
            )
            if task.planet_index:
                # [ on {planet}]
                planet: Planet = self.planets.get(task.planet_index)
                field_name += self.language_json["embeds"]["Dashboard"][
                    "MajorOrderEmbed"
                ]["tasks"]["type2_planet"].format(
                    planet=planet.loc_names[self.language_json["code_long"]]
                )
            elif task.sector_index:
                # [ in the __{sector}__ SECTOR]
                sector_name: str = self.json_dict["sectors"][str(task.sector_index)]
                field_name += self.language_json["embeds"]["Dashboard"][
                    "MajorOrderEmbed"
                ]["tasks"]["type2_sector"].format(sector=sector_name)
            elif task.faction:
                # [ from any {faction} controlled planet]
                field_name += self.language_json["embeds"]["Dashboard"][
                    "MajorOrderEmbed"
                ]["tasks"]["type2_faction"].format(
                    faction=self.language_json["factions"][task.faction.full_name]
                )

            field_value = ""
            field_value += f"{self.language_json['embeds']['Dashboard']['progress']}: **{task.progress:,.0f}**"
            if task.progress_perc != 1:
                if self.compact_level < 1:
                    field_value += f"\n{task.health_bar}"
                field_value += f"\n`{(task.progress_perc):^25,.2%}`"
                if task.tracker and task.tracker.change_rate_per_hour != 0:
                    rate = f"{task.tracker.change_rate_per_hour:+.2%}/hour"
                    field_value += f"\n`{rate:^25}`"
                    winning = (
                        task.tracker.change_rate_per_hour > 0
                        and task.tracker.complete_time
                        < self.assignment.ends_at_datetime
                    )
                    outlook_text = (
                        self.language_json["complete"]
                        if winning
                        else self.language_json["failure"]
                    )
                    field_value += f"\n-# {outlook_text} <t:{int(task.tracker.complete_time.timestamp())}:R>"

            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_3(self, task: Assignment.Task) -> None:
            """Kill {amount} {enemy_type}[ using the __{item_to_use}__][ on {planet}]"""
            field_name = ""
            if task.enemy_id:
                enemy_type = (
                    self.json_dict["enemies"]["enemy_ids"].get(
                        str(task.enemy_id), f"||UNKNOWN [{task.enemy_id}]||"
                    )
                    + "s"
                )
            else:
                enemy_type = task.faction.plural.title()
            field_name += self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]["type3"].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                amount=short_format(task.target),
                target=enemy_type,
            )
            if task.item_id:
                field_name += self.language_json["embeds"]["Dashboard"][
                    "MajorOrderEmbed"
                ]["tasks"]["type3_item"].format(
                    item_to_use=stratagem_id_dict.get(
                        task.item_id, f"||UNKNOWN [{task.item_id}]||"
                    )
                )
            if task.planet_index:
                field_name += self.language_json["embeds"]["Dashboard"][
                    "MajorOrderEmbed"
                ]["tasks"]["type3_planet"].format(
                    planet=self.planets[task.planet_index].loc_names[
                        self.language_json["code_long"]
                    ]
                )
            field_value = ""
            if task.progress_perc != 1:
                field_value += f"{self.language_json['embeds']['Dashboard']['progress']}: **{(task.progress):,.0f}**"
                if self.compact_level < 1:
                    field_value += f"\n{task.health_bar}"
                field_value += f"\n`{(task.progress_perc):^25,.2%}`"
                if task.tracker and task.tracker.change_rate_per_hour != 0:
                    rate = f"{task.tracker.change_rate_per_hour:+.2%}/hour"
                    field_value += f"\n`{rate:^25}`"
                    winning = (
                        task.tracker.change_rate_per_hour > 0
                        and task.tracker.complete_time
                        < self.assignment.ends_at_datetime
                    )
                    outlook_text = (
                        self.language_json["completes"]
                        if winning
                        else self.language_json["failure"]
                    )
                    field_value += f"\n-# {outlook_text} <t:{int(task.tracker.complete_time.timestamp())}:R>"

            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_7(self, task: Assignment.Task) -> None:
            """Extract from a successful Mission against {faction} {number} times"""
            field_name = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]["type7"].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                faction=self.language_json["factions"][task.faction.full_name],
                amount=f"{task.target:,}",
            )
            field_value = ""
            if task.progress_perc != 1:
                field_value += f"{self.language_json['embeds']['Dashboard']['progress']}: **{(task.progress):,.0f}**"
                if self.compact_level < 1:
                    field_value += f"\n{task.health_bar}"
                field_value += f"\n`{(task.progress_perc):^25,.2%}`"
                if task.tracker and task.tracker.change_rate_per_hour != 0:
                    rate = f"{task.tracker.change_rate_per_hour:+.2%}/hour"
                    field_value += f"\n`{rate:^25}`"
                    winning = (
                        task.tracker.change_rate_per_hour > 0
                        and task.tracker.complete_time
                        < self.assignment.ends_at_datetime
                    )
                    if winning:
                        outlook_text = self.language_json["complete"]
                    else:
                        outlook_text = self.language_json["failure"]
                    field_value += f"\n-# {outlook_text} <t:{int(task.tracker.complete_time.timestamp())}:R>"

            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_9(self, task: Assignment.Task) -> None:
            """Complete an Operation[ against {faction}][ on {difficulty} or higher] {amount} times"""
            against_faction = ""
            on_difficulty = ""
            if task.faction:
                # [ against {faction}]
                against_faction = self.language_json["embeds"]["Dashboard"][
                    "MajorOrderEmbed"
                ]["tasks"]["type9_against_faction"].format(
                    faction=self.language_json["factions"][task.faction.full_name]
                )
            if task.difficulty:
                # [ on {difficulty} or higher]
                on_difficulty = self.language_json["embeds"]["Dashboard"][
                    "MajorOrderEmbed"
                ]["tasks"]["type9_on_difficulty"].format(
                    difficulty=self.language_json["difficulty"][str(task.difficulty)]
                )

            field_name = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]["type9"].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                against_faction=against_faction,
                on_difficulty=on_difficulty,
                amount=task.target,
            )
            field_value = ""
            if task.progress_perc != 1:
                field_value += f"{self.language_json['embeds']['Dashboard']['progress']}: **{(task.progress):,.0f}**\n"
                if self.compact_level < 1:
                    field_value += f"\n{task.health_bar}\n"
                field_value += f"\n`{(task.progress_perc):^25,.2%}`"
                if task.tracker and task.tracker.change_rate_per_hour != 0:
                    rate = f"{task.tracker.change_rate_per_hour:+.2%}/hour"
                    field_value += f"\n`{rate:^25}`"
                    winning = (
                        task.tracker.change_rate_per_hour > 0
                        and task.tracker.complete_time
                        < self.assignment.ends_at_datetime
                    )
                    outlook_text = (
                        self.language_json["completes"]
                        if winning
                        else self.language_json["failure"]
                    )
                    field_value += f"\n-# {outlook_text} <t:{int(task.tracker.complete_time.timestamp())}:R>"

            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_11(self, task: Assignment.Task) -> None:
            """Liberate a planet"""
            planet = self.planets[task.planet_index]
            field_name = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]["type11"].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                planet=planet.loc_names[self.language_json["code_long"]],
            )
            field_value = ""
            if task.progress_perc != 1 and planet.stats.player_count > (
                self.total_players * 0.05
            ):
                for su in SpecialUnits.get_from_effects_list(planet.active_effects):
                    field_value += f"\n-# {su[1]} {su[0]}"
                for feature in PlanetFeatures.get_from_effects_list(
                    planet.active_effects
                ):
                    field_value += f"\n-# {feature[1]} {feature[0]}"
                field_value += f"\n{self.language_json['embeds']['Dashboard']['heroes'].format(heroes=f'{planet.stats.player_count:,}')}"
                if planet.event:
                    field_value += f"{self.language_json['ends']} **<t:{planet.event.end_time_datetime.timestamp():.0f}:R>**"
                    end_time_info = get_end_time(planet, self.gambit_planets)
                    if end_time_info.end_time:
                        if end_time_info.end_time < planet.event.end_time_datetime:
                            field_value += f"\n{self.language_json['victory']} **<t:{int(planet.tracker.complete_time.timestamp())}:R>**"
                        else:
                            field_value += f"\n**{self.language_json['defeat']}**"
                    if self.compact_level < 1:
                        field_value += f"\n{planet.health_bar}"
                    field_value += f"\n`{(1-planet.event.progress):^25,.2%}`"
                else:
                    end_time_info = get_end_time(planet)
                    if end_time_info.end_time:
                        if end_time_info.regions:
                            regions_list = f"\n-# ".join(
                                [
                                    f" {r.emoji} {r.names[self.language_json['code_long']]}"
                                    for r in end_time_info.regions
                                ]
                            )
                            field_value += f"\n{self.language_json['victory']} **<t:{int(end_time_info.end_time.timestamp())}:R>**\n{self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['if_regions']}:\n-# {regions_list}"
                        elif end_time_info.source_planet:
                            field_value += f"\n{self.language_json['victory']} **<t:{int(end_time_info.end_time.timestamp())}:R>**"
                    if self.compact_level < 1:
                        field_value += f"\n{planet.health_bar}"
                    field_value += f"\n`{(1-planet.health_perc):^25,.2%}`"
                if planet.tracker and planet.tracker.change_rate_per_hour != 0:
                    change = f"{planet.tracker.change_rate_per_hour:+.2%}/hr"
                    field_value += f"\n`{change:^25}`"
            elif task.progress_perc != 1 and planet.stats.player_count < (
                self.total_players * 0.05
            ):
                for waypoint in planet.waypoints:
                    way_planet = self.planets[waypoint]
                    if way_planet.stats.player_count > (self.total_players * 0.05):
                        way_planet_end_info = get_end_time(
                            way_planet, self.gambit_planets
                        )
                        if way_planet_end_info.end_time:
                            field_value += self.language_json["embeds"]["Dashboard"][
                                "MajorOrderEmbed"
                            ]["avail_thanks_to_wp"].format(
                                timestamp=int(way_planet_end_info.end_time.timestamp()),
                                planet_name=way_planet.loc_names[
                                    self.language_json["code_long"]
                                ],
                            )

            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_12(self, task: Assignment.Task) -> None:
            """Defend[ {planet}] against {amount} attacks[ from the {faction}]"""
            planet_text = ""
            if task.planet_index:
                planet = self.planets.get(task.planet_index)
                planet_text = f"{self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['tasks']['type12_planet'].format(planet=planet.loc_names[self.language_json['code_long']])}"
            field_name = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]["type12"].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                planet=planet_text,
                amount=task.target,
            )
            if task.faction:
                field_name += self.language_json["embeds"]["Dashboard"][
                    "MajorOrderEmbed"
                ]["tasks"]["type12_faction"].format(
                    faction=self.language_json["factions"][task.faction.full_name]
                )
            field_value = ""
            if task.progress_perc != 1:
                if planet:
                    # if planet.feature: TODO
                    #     field_value += f"{language_json['embeds']['Dashboard']['MajorOrderEmbed']['feature']}: **{planet.feature}**"
                    field_value += f"\n{self.language_json['embeds']['Dashboard']['heroes'].format(heroes=planet.stats.player_count)}"
                    if planet.event:
                        field_value += f"\n{self.language_json['ends']} <t:{int(planet.event.end_time_datetime.timestamp())}:R>"
                        f"\n{self.language_json['embeds']['Dashboard']['DefenceEmbed']['level']} {planet.event.level}{planet.event.level_exclamation}"
                    if planet.tracker and planet.tracker.change_rate_per_hour != 0:
                        winning = (
                            planet.tracker.complete_time
                            < planet.event.end_time_datetime
                        )
                        if winning:
                            field_value += f"\n{self.language_json['embeds']['Dashboard']['outlook']}: **{self.language_json['victory']}** <t:{int(planet.tracker.complete_time.timestamp())}:R>"
                        else:
                            field_value += f"\n{self.language_json['embeds']['Dashboard']['outlook']}: **{self.self.language_json['defeat']}**"
                        field_value += f"\n{self.language_json['embeds']['Dashboard']['progress']}:"
                        if self.compact_level < 1:
                            field_value += f"\n{planet.health_bar}🛡️"
                        field_value += f"\n`{planet.event.progress:^25,.2%}`"
                        change = f"{planet.tracker.change_rate_per_hour:+.2%}/hour"
                        field_value += f"\n`{change:^25}`"
                else:
                    field_value += (
                        f"{self.language_json['embeds']['Dashboard']['progress']}: {int(task.progress)}/{task.target}"
                        f"\n{task.health_bar}"
                        f"\n`{(task.progress_perc):^25,.2%}`"
                    )

                self.add_field(
                    name=field_name,
                    value=field_value,
                    inline=False,
                )

        def add_type_13(self, task: Assignment.Task) -> None:
            """Hold {planet} when the order expires"""
            planet = self.planets[task.planet_index]
            field_name = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]["type13"].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                planet=planet.loc_names[self.language_json["code_long"]],
            )
            field_value = ""
            if task.progress_perc != 1 or planet.event:
                for planet_feature in PlanetFeatures.get_from_effects_list(
                    planet.active_effects
                ):
                    field_value += f"\n> -# {planet_feature[1]} {planet_feature[0]}"
                for special_unit in SpecialUnits.get_from_effects_list(
                    active_effects=planet.active_effects
                ):
                    field_value += f"\n-# {special_unit[1]} {self.language_json['special_units'][special_unit[0]]}"
                if planet.stats.player_count > 500:
                    formatted_heroes = f"{planet.stats.player_count:,}"
                    field_value += f"\n{self.language_json['embeds']['Dashboard']['heroes'].format(heroes=formatted_heroes)}"
                else:
                    for waypoint in planet.waypoints:
                        way_planet = self.planets[waypoint]
                        calc_end_time = get_end_time(
                            way_planet, gambit_planets=self.gambit_planets
                        )
                        if calc_end_time.end_time:
                            field_value += self.language_json["embeds"]["Dashboard"][
                                "MajorOrderEmbed"
                            ]["avail_thanks_to_wp"].format(
                                timestamp=int(calc_end_time.end_time.timestamp()),
                                planet_name=way_planet.loc_names[
                                    self.language_json["code_long"]
                                ],
                            )
                            break
                calc_end_time = get_end_time(planet, self.gambit_planets)
                if planet.event:
                    field_value += f"\n{self.language_json['ends']} <t:{int(planet.event.end_time_datetime.timestamp())}:R>"
                    field_value += f"\n{self.language_json['embeds']['Dashboard']['DefenceEmbed']['level']} **{planet.event.level}**{planet.event.level_exclamation}"
                    if calc_end_time.end_time:
                        winning = (
                            calc_end_time.end_time < planet.event.end_time_datetime
                        )
                        if winning:
                            if calc_end_time.regions:
                                regions_list = f"\n-# ".join(
                                    [
                                        f" {r.emoji} {r.names[self.language_json['code_long']]}"
                                        for r in calc_end_time.regions
                                    ]
                                )
                                field_value += f"\n{self.language_json['victory']} **<t:{int(calc_end_time.end_time.timestamp())}:R>**\n{self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['if_regions']}:\n-# {regions_list}"
                            elif calc_end_time.source_planet:
                                field_value += f"\n**{self.language_json['victory']}** <t:{int(planet.tracker.complete_time.timestamp())}:R>"
                    else:
                        field_value += f"\n**{self.language_json['defeat']}**"
                    if self.compact_level < 1:
                        field_value += f"\n{planet.health_bar} 🛡️"
                    field_value += f"\n`{planet.event.progress:^25,.2%}`"
                    if planet.tracker and planet.tracker.change_rate_per_hour != 0:
                        change = f"{planet.tracker.change_rate_per_hour:+.2%}/hr"
                        field_value += f"\n`{change:^25}`"
                else:
                    if calc_end_time.end_time:
                        if calc_end_time.regions:
                            regions_list = f"\n-# ".join(
                                [
                                    f" {r.emoji} {r.names[self.language_json['code_long']]}"
                                    for r in calc_end_time.regions
                                ]
                            )
                            field_value += f"\n{self.language_json['victory']} **<t:{int(calc_end_time.end_time.timestamp())}:R>**\n{self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['if_regions']}:\n-# {regions_list}"
                        elif calc_end_time.source_planet:
                            field_value += f"\n**{self.language_json['victory']}** <t:{int(planet.tracker.complete_time.timestamp())}:R>"
                        if self.compact_level < 1:
                            field_value += f"\n{planet.health_bar}"
                        if planet.tracker and planet.tracker.change_rate_per_hour != 0:
                            change = f"{planet.tracker.change_rate_per_hour:+.2%}/hr"
                            field_value += f"\n`{1 - (planet.health_perc):^25,.2%}`"
                            field_value += f"\n`{change:^25}`"
            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_15(self, task: Assignment.Task) -> None:
            """Liberate more planets than are lost during the order duration"""
            field_name = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]["type15"].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc >= 1
                    else Emojis.Icons.mo_task_incomplete
                )
            )
            field_value = ""
            if task.progress_perc != 1:
                if self.compact_level < 1:
                    field_value += f"\n{task.health_bar}"
                field_value += f"`{task.progress_perc:^25,}`\n"

            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_UNK(self, task: Assignment.Task) -> None:
            """This is for unknown/unassigned task types"""
            self.add_field(
                name=self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                    "tasks"
                ]["typeNew"].format(alert_emoji=Emojis.Decoration.alert_icon),
                value=(
                    f"-# ||{task}||\n"
                    f"{'|'.join(str(f'{k}:{v}') for k, v in task.values_dict.items())}"
                ),
                inline=False,
            )

        def _set_thumbnail(self) -> None:
            """Sets the thumbnail based on the Assignment's task types"""
            task_numbers = [task.type for task in self.assignment.tasks]
            task_for_image = max(set(task_numbers), key=task_numbers.count)
            self.set_thumbnail(url=AssignmentImages.get(task_for_image))

        def _add_description(self) -> None:
            """Adds the description of the MO, if available. And sets the footer to the assignment ID"""
            self.add_field(
                name="",
                value=f"-# {self.assignment.briefing}",
                inline=False,
            )
            self.set_footer(
                text=self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                    "assignment"
                ].format(id=self.assignment.id)
            )

        def _add_rewards(self) -> None:
            rewards_text = ""
            for reward in self.assignment.rewards:
                reward_name: str = self.json_dict["items"]["reward_types"].get(
                    str(reward["type"]), "Unknown Item"
                )
                localized_name = self.language_json["currencies"].get(reward_name)
                rewards_text += f"{reward['amount']:,} **{self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['reward_pluralized'].format(reward=localized_name)}** {getattr(Emojis.Items, reward_name.replace(' ', '_').lower(), '')}\n"
            if rewards_text != "":
                self.add_field(
                    self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                        "rewards"
                    ],
                    rewards_text,
                )

        def _add_outlook_text(self) -> None:
            outlook_text = ""
            if datetime.now() < self.assignment.ends_at_datetime - timedelta(days=2):
                return outlook_text
            winning_all_tasks = [
                ts < self.assignment.ends_at_datetime.timestamp()
                for ts in self.completion_timestamps
            ]
            type_13_tasks = [t for t in self.assignment.tasks if t.type == 13]
            complete_type_13s = [
                True
                for t in type_13_tasks
                if t.progress_perc == 1 and not self.planets[t.planet_index].event
            ]
            complete_tasks = (
                [
                    True
                    for t in self.assignment.tasks
                    if t.progress_perc == 1 and t.type != 13
                ]
                + [b for b in winning_all_tasks if b]
                + complete_type_13s
            )
            if (
                self.assignment.flags == 1
                and (len(complete_tasks) == len(self.assignment.tasks))
            ) or (
                self.assignment.flags in [2, 3]
                and (any(complete_tasks) or any(winning_all_tasks))
            ):
                outlook_text = self.language_json["complete"]
                if {13, 15} & set([t.type for t in self.assignment.tasks]):
                    outlook_text += (
                        f" <t:{int(self.assignment.ends_at_datetime.timestamp())}:R>"
                    )
                else:
                    oldest_time: datetime = sorted(
                        self.completion_timestamps, reverse=True
                    )[0]
                    outlook_text += f" <t:{int(oldest_time)}:R>"
                    time_diff = (
                        self.assignment.ends_at_datetime.timestamp() - oldest_time
                    )
                    hours = f"{time_diff // 3600:.0f}"
                    minutes = f"{(time_diff % 3600) // 60:.0f}"
                    outlook_text += self.language_json["embeds"]["Dashboard"][
                        "MajorOrderEmbed"
                    ]["ahead_of_schedule"].format(hours=hours, minutes=minutes)
            else:
                outlook_text += f"{self.language_json['failure']} <t:{int(self.assignment.ends_at_datetime.timestamp())}:R>"
                if self.completion_timestamps != []:
                    oldest_timestamp: int = sorted(
                        self.completion_timestamps, reverse=True
                    )[0]
                    time_diff = (
                        oldest_timestamp - self.assignment.ends_at_datetime.timestamp()
                    )
                    hours = f"{time_diff // 3600:.0f}"
                    minutes = f"{(time_diff % 3600) // 60:.0f}"
                    if 0 < time_diff // 3600 < 250:
                        outlook_text += self.language_json["embeds"]["Dashboard"][
                            "MajorOrderEmbed"
                        ]["behind_schedule"].format(hours=hours, minutes=minutes)

            if outlook_text != "":
                self.add_field(
                    self.language_json["embeds"]["Dashboard"]["outlook"],
                    f"{outlook_text}",
                    inline=False,
                )

        def _collect_completion_timestamps(self) -> None:
            """Fills `self.completion_timestamps` with estimated timestamps for each task (if possible)"""
            for task in self.assignment.tasks:
                if task.type in [11, 13]:
                    planet = self.planets[task.planet_index]
                    end_time_info = get_end_time(
                        source_planet=planet, gambit_planets=self.gambit_planets
                    )
                if task.tracker and task.tracker.change_rate_per_hour != 0:
                    self.completion_timestamps.append(
                        task.tracker.complete_time.timestamp()
                    )
                elif task.type == 11:
                    if end_time_info.end_time:
                        self.completion_timestamps.append(
                            end_time_info.end_time.timestamp()
                        )
                elif task.type == 13:
                    if planet.event:
                        if (
                            planet.event.end_time_datetime
                            > self.assignment.ends_at_datetime
                        ):
                            pass
                        if end_time_info.end_time:
                            self.completion_timestamps.append(
                                end_time_info.end_time.timestamp()
                            )
                    else:
                        if end_time_info.end_time:
                            self.completion_timestamps.append(
                                end_time_info.end_time.timestamp()
                            )

        def add_briefing(self, briefing: GlobalEvent) -> None:
            """Add a the briefing from a Global Event"""
            self.insert_field_at(
                0,
                briefing.title,
                briefing.split_message[0],
                inline=False,
            )
            for index, chunk in enumerate(briefing.split_message[1:], 1):
                self.insert_field_at(index, "", chunk, inline=False)

    class DSSEmbed(Embed, EmbedReprMixin):
        def __init__(
            self,
            dss: DSS | None,
            language_json: dict,
            gambit_planets: dict[int, Planet],
        ):
            super().__init__(
                title=language_json["dss"]["title"],
                colour=Colour.from_rgb(*CUSTOM_COLOURS["DSS"]),
            )
            self.set_thumbnail(
                url="https://media.discordapp.net/attachments/1212735927223590974/1413612410819969114/0xfbbeedfa99b09fec.png?ex=68bc90a6&is=68bb3f26&hm=cd8bf236a355bbed28f4847d3d62b5908d050a7eeb7396bb9a891e108acc0241&=&format=webp&quality=lossless"
            )
            self.description = language_json["embeds"]["Dashboard"]["DSSEmbed"][
                "stationed_at"
            ].format(
                planet=dss.planet.loc_names[language_json["code_long"]],
                faction_emoji=dss.planet.exclamations,
            )
            move_time = int(dss.move_timer_datetime.timestamp())
            end_time_info = get_end_time(dss.planet, gambit_planets)
            if (
                end_time_info.end_time
                and int(end_time_info.end_time.timestamp()) < move_time
            ):
                move_time = int(end_time_info.end_time.timestamp())

            self.description += language_json["embeds"]["Dashboard"]["DSSEmbed"][
                "next_move"
            ].format(timestamp=f"<t:{move_time}:R>")

            time_until_move = move_time - int(datetime.now().timestamp())
            if time_until_move < 1800:
                self.description += f"\n-# {Emojis.Decoration.alert_icon} MOVING SOON - REMEMBER TO VOTE {Emojis.Decoration.alert_icon}"
            ta_jsons = language_json["embeds"]["Dashboard"]["DSSEmbed"][
                "tactical_actions"
            ]
            for tactical_action in dss.tactical_actions:
                if tactical_action.name.upper() in ta_jsons:
                    field_name = f"{tactical_action.emoji} {ta_jsons[tactical_action.name.upper()]['name']}"
                else:
                    field_name = tactical_action.name.upper()
                status = STATUS_DICT[tactical_action.status]
                field_value = f"{language_json['embeds']['Dashboard']['DSSEmbed']['status']}: **{language_json['embeds']['Dashboard']['DSSEmbed'][status]}**"
                match status:
                    case "preparing":
                        for ta_cost in tactical_action.cost:
                            cost_change: BaseTrackerEntry = (
                                tactical_action.cost_changes[ta_cost.item]
                            )
                            if (
                                cost_change
                                and cost_change.change_rate_per_hour != 0
                                and 2 not in [ta.status for ta in dss.tactical_actions]
                            ):
                                field_value += f"\n{health_bar(perc=ta_cost.progress, faction='MO', anim=True, increasing=cost_change.change_rate_per_hour > 0)}"
                                field_value += f"\n`{ta_cost.progress:^25.2%}`"
                                change = f"{cost_change.change_rate_per_hour:+.2%}/hr"
                                field_value += f"\n`{change:^25}`"
                                field_value += f"\n-# {language_json['embeds']['Dashboard']['DSSEmbed']['active']} <t:{int(cost_change.complete_time.timestamp())}:R>"
                            else:
                                field_value += f"\n{health_bar(perc=ta_cost.progress, faction='MO')}"
                                field_value += f"\n`{ta_cost.progress:^25.2%}`"
                    case "active":
                        field_value += f"\n{language_json['ends']} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
                        if tactical_action.name.upper() in ta_jsons:
                            field_value += f'\n{language_json["embeds"]["Dashboard"]["DSSEmbed"]["tactical_actions"][tactical_action.name.upper()]["description"]}'
                        else:
                            field_value += f"\n{tactical_action.description}"
                    case "on_cooldown":
                        field_value += f"\n-# {language_json['embeds']['Dashboard']['DSSEmbed']['off_cooldown']} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
                    case _:
                        continue

                self.add_field(
                    name=field_name,
                    value=field_value,
                    inline=False,
                )

    class DefenceEmbed(Embed, EmbedReprMixin):
        def __init__(
            self,
            planet_events: list[Planet],
            language_json: dict,
            total_players: int,
            eagle_storm: DSS.TacticalAction | None,
            gambit_planets: dict[int, Planet],
            compact_level: int = 0,
        ):
            self.language_json = language_json
            self.eagle_storm = eagle_storm
            self.gambit_planets = gambit_planets
            self.total_players = total_players
            self.compact_level = compact_level
            self.now = datetime.now()
            total_players_doing_defence = (
                sum(planet.stats.player_count for planet in planet_events)
                / total_players
            )
            super().__init__(
                title=f"{language_json['embeds']['Dashboard']['DefenceEmbed']['title']} ({total_players_doing_defence:.2%})",
                colour=Colour.blue(),
            )
            if planet_events:
                defence_factions = [
                    p.event.faction.full_name.lower() for p in planet_events
                ]
                if len(set(defence_factions)) > 1:
                    thumbnail = "https://cdn.discordapp.com/attachments/1212735927223590974/1414958449967632466/0x7d2b143494a63666.png?ex=68c1763f&is=68c024bf&hm=9c1978e23c9c7991376201637f004791471d0b7e0968dfec6d1af4d4a6a9ff09&"
                else:
                    thumbnail = DEFENCE_EMBED_ICONS.get(defence_factions[0])
                self.set_thumbnail(thumbnail)
                for planet in planet_events:
                    match planet.event.type:
                        case 1:
                            # Regular defence campaign
                            self.add_event_type_1(planet=planet)
                        case _:
                            # Unconfigured campaigns
                            self.add_unconfigured_event_type()

        def add_event_type_1(self, planet: Planet):
            field_name = ""
            field_value = ""

            field_name += f"{planet.loc_names[self.language_json['code_long']]} {planet.exclamations}"
            for su in SpecialUnits.get_from_effects_list(planet.active_effects):
                field_value += (
                    f"\n-# {su[1]} {self.language_json['special_units'][su[0]]}"
                )

            for planet_feature in PlanetFeatures.get_from_effects_list(
                (ae for ae in planet.active_effects if ae.effect_type == 71)
            ):
                field_value += f"\n> -# {planet_feature[1]} {planet_feature[0]}"

            if (
                planet.dss_in_orbit
                and self.eagle_storm
                and self.eagle_storm.status == 2
            ):
                field_value += self.language_json["embeds"]["Dashboard"][
                    "DefenceEmbed"
                ]["defence_held_by_dss"]

            field_value += f"\n{self.language_json['embeds']['Dashboard']['DefenceEmbed']['ends']} **<t:{int(planet.event.end_time_datetime.timestamp())}:R>**"
            field_value += f"\n{self.language_json['embeds']['Dashboard']['DefenceEmbed']['invasion_level']} **{planet.event.level}**{planet.event.level_exclamation}"

            calculated_end_time = get_end_time(planet, self.gambit_planets)
            if (
                calculated_end_time.end_time
                and self.now
                < calculated_end_time.end_time
                < planet.event.end_time_datetime
            ):
                field_value += f"\n{self.language_json['embeds']['Dashboard']['DefenceEmbed']['victory']} **<t:{int(calculated_end_time.end_time.timestamp())}:R>**"
                if calculated_end_time.gambit_planet:
                    field_value += f" {self.language_json['embeds']['Dashboard']['DefenceEmbed']['thanks_to_gambit'].format(planet=calculated_end_time.gambit_planet.loc_names[self.language_json['code_long']])}"
                elif calculated_end_time.regions:
                    regions_list = f"\n-# ".join(
                        [f" {r.emoji} {r.name}" for r in calculated_end_time.regions]
                    )
                    field_value += self.language_json["embeds"]["Dashboard"][
                        "DefenceEmbed"
                    ]["if_region_lib"].format(regions_list=regions_list)
            elif planet.tracker and planet.tracker.change_rate_per_hour > 0:
                field_value += f"\n**{self.language_json['embeds']['Dashboard']['DefenceEmbed']['loss']}**"
                if planet.index in self.gambit_planets and planet.event.progress < 0.5:
                    gambit_planet = self.gambit_planets[planet.index]
                    field_value += f"\n-# :chess_pawn: {gambit_planet.loc_names[self.language_json['code_long']]} GAMBIT"

            field_value += f"\n{self.language_json['embeds']['Dashboard']['DefenceEmbed']['heroes']}: **{planet.stats.player_count:,}**"
            if self.compact_level < 1:
                field_value += f"\n{planet.health_bar}"
            field_value += f"\n`{planet.event.progress:^25.2%}`"
            if planet.tracker and planet.tracker.change_rate_per_hour > 0:
                change = f"{planet.tracker.change_rate_per_hour:+.2%}/hr"
                field_value += f"\n`{change:^25}`"

            for region in planet.regions.values():
                if region.is_available:
                    field_value += f"\n-# ↳ {region.emoji} {self.language_json['regions'][region.type]} **{region.names[self.language_json['code_long']]}** - {region.perc:.0%}"
                    if (
                        self.compact_level < 2
                        and region.tracker
                        and region.tracker.change_rate_per_hour != 0
                    ):
                        field_value += (
                            f" **{region.tracker.change_rate_per_hour:+.1%}**/hr"
                        )
                else:
                    now_seconds = int(datetime.now().timestamp())
                    event_progression = (
                        now_seconds - planet.event.start_time_datetime.timestamp()
                    ) / (
                        planet.event.end_time_datetime.timestamp()
                        - planet.event.start_time_datetime.timestamp()
                    )
                    if (
                        region.availability_factor > event_progression
                        and region.owner != Factions.humans
                        and self.compact_level < 2
                    ):
                        region_avail_datetime = datetime.fromtimestamp(
                            now_seconds
                            + (
                                (
                                    (region.availability_factor - event_progression)
                                    / (1 - event_progression)
                                )
                                * (
                                    planet.event.end_time_datetime.timestamp()
                                    - now_seconds
                                )
                            )
                        )
                        if (
                            calculated_end_time.end_time
                            and region_avail_datetime < calculated_end_time.end_time
                        ):
                            field_value += f"\n-# ↳ {region.emoji} {self.language_json['regions'][region.type]} **{region.names[self.language_json['code_long']]}** - {self.language_json['embeds']['Dashboard']['DefenceEmbed']['available']} <t:{int(region_avail_datetime.timestamp())}:R>"
                        break

            self.add_field(field_name, field_value, inline=False)

        def add_unconfigured_event_type(self, planet: Planet):
            self.add_field(
                f"{Emojis.Decoration.alert_icon} NON-CONFIGURED DEFENCE TYPE",
                (
                    f"-# {planet.event.type}|{planet.event.health}/{planet.event.max_health}\n"
                ),
                inline=False,
            )

    class AttackEmbed(Embed, EmbedReprMixin):
        def __init__(
            self,
            campaigns: list[Campaign],
            language_json: dict,
            faction: str,
            total_players: int,
            gambit_planets: dict[int, Planet],
            planets: Planets,
            compact_level: int = 0,
        ):
            super().__init__(
                title=language_json["embeds"]["Dashboard"]["AttackEmbed"][
                    "title"
                ].format(faction=language_json["factions"][faction]),
                colour=Colour.from_rgb(
                    *Factions.get_from_identifier(name=faction).colour
                ),
            )
            self.set_thumbnail(ATTACK_EMBED_ICONS[faction.lower()])
            total_players_doing_faction = (
                sum(campaign.planet.stats.player_count for campaign in campaigns)
                / total_players
            )
            self.title += f" ({total_players_doing_faction:.2%})"
            skipped_campaigns: list[Campaign] = []
            for campaign in campaigns:
                field_name = ""
                field_value = ""
                if campaign.planet.stats.player_count < (
                    total_players * max((compact_level * 0.05), 0.05)
                ):
                    skipped_campaigns.append(campaign)
                    continue
                else:
                    field_name += f"{campaign.faction.emoji} - **{campaign.planet.loc_names[language_json['code_long']]}** {campaign.planet.exclamations}"
                    field_value += f"{language_json['embeds']['Dashboard']['AttackEmbed']['heroes']}: **{campaign.planet.stats.player_count:,}**"

                    for su in SpecialUnits.get_from_effects_list(
                        campaign.planet.active_effects
                    ):
                        field_value += (
                            f"\n-# {su[1]} {language_json['special_units'][su[0]]}"
                        )

                    for feature in PlanetFeatures.get_from_effects_list(
                        campaign.planet.active_effects
                    ):
                        field_value += f"\n-# {feature[1]} {feature[0]}"
                    if campaign.planet.regen_perc_per_hour < 0.001:
                        field_value += f"\n-# :warning: {campaign.planet.regen_perc_per_hour:+.2%}/hr :warning:"

                    calc_end_time = get_end_time(campaign.planet)
                    if calc_end_time.end_time:
                        if calc_end_time.regions:
                            regions_list = f"\n-# ".join(
                                [
                                    f" {r.emoji} {r.names[language_json['code_long']]}"
                                    for r in calc_end_time.regions
                                ]
                            )
                            field_value += f"\n{language_json['embeds']['Dashboard']['AttackEmbed']['victory']} **<t:{int(calc_end_time.end_time.timestamp())}:R>**\n-# {language_json['embeds']['Dashboard']['AttackEmbed']['if_regions']}:\n-# {regions_list}"
                        elif calc_end_time.source_planet:
                            field_value += f"\n{language_json['embeds']['Dashboard']['AttackEmbed']['victory']} **<t:{int(campaign.planet.tracker.complete_time.timestamp())}:R>**"
                    if campaign.planet.index in [
                        p.index for p in gambit_planets.values()
                    ]:
                        gambit_planet = planets[
                            {v.index: k for k, v in gambit_planets.items()}[
                                campaign.planet.index
                            ]
                        ]
                        field_value += f"\n-# :chess_pawn: GAMBIT FOR {gambit_planet.loc_names[language_json['code_long']]}"
                    if compact_level < 1:
                        field_value += f"\n{campaign.planet.health_bar}"
                    field_value += f"\n`{(1 - (campaign.planet.health_perc)):^25.2%}`"  # 1 - {health} because we need it to reach 0
                    if (
                        campaign.planet.tracker
                        and campaign.planet.tracker.change_rate_per_hour != 0
                    ):
                        change = (
                            f"{campaign.planet.tracker.change_rate_per_hour:+.2%}/hr"
                        )
                        field_value += f"\n`{change:^25}`"

                    available_regions = [
                        r for r in campaign.planet.regions.values() if r.is_available
                    ]
                    if available_regions:
                        for region in available_regions:
                            field_value += f"\n-# ↳ {region.emoji} {language_json['regions'][region.type]} **{region.names[language_json['code_long']]}** {region.perc:.2%}"
                            if (
                                region.tracker
                                and region.tracker.change_rate_per_hour != 0
                            ):
                                field_value += (
                                    f" | {region.tracker.change_rate_per_hour:+.2%}/hr"
                                )
                    elif campaign.planet.regions:
                        for region in sorted(
                            [
                                r
                                for r in campaign.planet.regions.values()
                                if r.owner != Factions.humans
                            ],
                            key=lambda x: x.availability_factor,
                        ):
                            field_value += f"\n-# ↳ {region.emoji} {language_json['regions'][region.type]} **{region.names[language_json['code_long']]}** available at **{region.availability_factor:.2%}**"
                            break

                    self.add_field(
                        field_name,
                        field_value,
                        inline=False,
                    )

            if skipped_campaigns != []:
                skipped_planets_text = ""
                for campaign in skipped_campaigns:
                    exclamation = campaign.planet.exclamations
                    if campaign.planet.regen_perc_per_hour < 0.001:
                        exclamation += f":warning: {campaign.planet.regen_perc_per_hour:+.2%}/hr :warning:"
                    if campaign.planet.index in [
                        planet.index for planet in gambit_planets.values()
                    ]:
                        exclamation += ":chess_pawn:"
                    skipped_planets_text += f"-# {campaign.planet.loc_names[language_json['code_long']]} - **{campaign.planet.stats.player_count:,}** {exclamation}\n"
                    if compact_level < 2:
                        for region in campaign.planet.regions.values():
                            if (
                                region.is_available
                                and region.players > total_players * 0.001
                            ):
                                skipped_planets_text += f"-# ↳ {region.emoji} {language_json['regions'][region.type]} **{region.names[language_json['code_long']]}** - {region.perc:.2%}\n"
                if skipped_planets_text != "":
                    self.add_field(
                        f"{language_json['embeds']['Dashboard']['AttackEmbed']['low_impact']}",
                        skipped_planets_text,
                        inline=False,
                    )

    class FooterEmbed(Embed, EmbedReprMixin):
        def __init__(
            self,
            language_json: dict,
            total_players: int,
            steam_players: int,
            data_time: datetime,
        ):
            super().__init__(colour=Colour.dark_embed())
            now = datetime.now()
            self.add_field(
                "",
                (
                    f"-# {language_json['embeds']['Dashboard']['FooterEmbed']['other_updated']}\n"
                    f"-# <t:{int(now.timestamp())}:f> - <t:{int(now.timestamp())}:R>\n"
                    f"||-# Data from <t:{int(data_time.timestamp())}:R>||"
                ),
                inline=False,
            )
            self.add_field(
                "",
                (
                    f"-# {language_json['embeds']['Dashboard']['FooterEmbed']['total_players']}\n"
                    f"-# {Emojis.Icons.steam} {steam_players:,}\n"
                    f"-# {Emojis.Icons.playstation}/{Emojis.Icons.xbox} {total_players - steam_players:,}"
                ),
                inline=False,
            )
            special_dates = {
                "liberty_day": {
                    "dates": ["26/10"],
                    "text": language_json["embeds"]["Dashboard"]["FooterEmbed"][
                        "liberty_day"
                    ],
                },
                "malevelon_creek_day": {
                    "dates": ["03/04"],
                    "text": language_json["embeds"]["Dashboard"]["FooterEmbed"][
                        "malevelon_creek_day"
                    ],
                },
                "festival_of_reckoning": {
                    "dates": ["24/12", "25/12", "26/12"],
                    "text": language_json["embeds"]["Dashboard"]["FooterEmbed"][
                        "festival_of_reckoning"
                    ],
                },
                "new_year": {
                    "dates": ["31/12", "01/01"],
                    "text": language_json["embeds"]["Dashboard"]["FooterEmbed"][
                        "new_year"
                    ],
                },
            }
            for details in special_dates.values():
                if now.strftime("%d/%m") in details["dates"]:
                    self.set_footer(text=details["text"])
                    break
