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
from utils.dataclasses import AssignmentImages, Factions, SpecialUnits, PlanetEffects
from utils.emojis import Emojis
from utils.functions import health_bar, short_format
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
        if data.assignments:
            for assignment in data.assignments[language_code]:
                self.embeds.append(
                    self.MajorOrderEmbed(
                        assignment=assignment,
                        planets=data.planets,
                        language_json=language_json,
                        json_dict=json_dict,
                        compact_level=compact_level,
                    )
                )
        else:
            self.embeds.append(
                self.MajorOrderEmbed(
                    assignment=None,
                    planets=None,
                    language_json=language_json,
                    json_dict=None,
                )
            )

        # DSS Eembed
        if data.dss and data.dss.flags not in (0, 2):
            self.embeds.append(
                self.DSSEmbed(
                    dss=data.dss,
                    language_json=language_json,
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
            assignment: Assignment | None,
            planets: Planets | None,
            language_json: dict,
            json_dict: dict | None,
            compact_level: int = 0,
        ):
            self.compact_level = compact_level
            self.assignment = assignment
            self.completion_timestamps = []
            super().__init__(
                colour=Colour.from_rgb(*CUSTOM_COLOURS["MO"]),
            )
            if not self.assignment:
                self.title = language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                    "mo_missing"
                ]
                self.add_field(
                    name="",
                    value=language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                        "MO_unavailable"
                    ],
                )
                self.set_thumbnail(
                    url="https://cdn.discordapp.com/attachments/1212735927223590974/1403681687111471144/icon.png?ex=68986ff1&is=68971e71&hm=64cf789e34c6480613f7710fbdfc24072fe3ff8daa7741b276a12f7e467b3ca4&"
                )
            else:
                self.title = assignment.title
                self.total_players = sum(
                    [p.stats.player_count for p in planets.values()]
                )
                task_numbers = [task.type for task in assignment.tasks]
                task_for_image = max(set(task_numbers), key=task_numbers.count)
                self.set_thumbnail(url=AssignmentImages.get(task_for_image))
                if self.compact_level < 2:
                    self.add_description(
                        assignment=assignment, language_json=language_json
                    )
                self.completion_timestamps.clear()
                for task in assignment.tasks:
                    lib_changes = None
                    if task.type in [11, 13]:
                        lib_changes = planets[task.planet_index].tracker
                    if task.tracker and task.tracker.change_rate_per_hour != 0:
                        self.completion_timestamps.append(
                            task.tracker.complete_time.timestamp()
                        )
                    elif task.type == 11:
                        if lib_changes and lib_changes.change_rate_per_hour > 0:
                            self.completion_timestamps.append(
                                lib_changes.complete_time.timestamp()
                            )
                    elif task.type == 13:
                        planet = planets[task.planet_index]
                        if lib_changes and lib_changes.change_rate_per_hour > 0:
                            if planet.event:
                                if (
                                    planet.event.end_time_datetime
                                    > assignment.ends_at_datetime
                                ):
                                    pass
                                elif (
                                    planet.event.end_time_datetime
                                    > lib_changes.complete_time
                                ):
                                    self.completion_timestamps.append(
                                        lib_changes.complete_time.timestamp()
                                    )
                                else:
                                    # set to end time to indicate failure
                                    self.completion_timestamps.append(
                                        assignment.ends_at_datetime.timestamp()
                                    )
                            else:
                                self.completion_timestamps.append(
                                    lib_changes.complete_time.timestamp()
                                )
                    match task.type:
                        case 2:
                            planet = sector_name = None
                            if task.planet_index:
                                planet: Planet = planets.get(task.planet_index)
                            elif task.sector_index:
                                sector_name: str = json_dict["sectors"][
                                    str(task.sector_index)
                                ]
                            self.add_type_2(
                                task=task,
                                language_json=language_json,
                                item_names_json=json_dict["items"]["item_names"],
                                planet=planet,
                                sector_name=sector_name,
                            )
                        case 3:
                            self.add_type_3(
                                planets=planets,
                                task=task,
                                language_json=language_json,
                                enemy_dict=json_dict["enemies"]["enemy_ids"],
                            )
                        case 7:
                            self.add_type_7(
                                task=task,
                                language_json=language_json,
                            )
                        case 9:
                            self.add_type_9(
                                task=task,
                                language_json=language_json,
                            )
                        case 11:
                            self.add_type_11(
                                language_json=language_json,
                                planet=planets[task.planet_index],
                                task=task,
                            )
                        case 12:
                            self.add_type_12(
                                task=task,
                                language_json=language_json,
                                planet=planets.get(task.planet_index),
                            )
                        case 13:
                            self.add_type_13(
                                task=task,
                                language_json=language_json,
                                planets=planets,
                            )
                        case 15:
                            self.add_type_15(
                                task=task,
                                language_json=language_json,
                            )
                        case _:
                            self.add_field(
                                name=language_json["embeds"]["Dashboard"][
                                    "MajorOrderEmbed"
                                ]["tasks"]["typeNew"].format(
                                    alert_emoji=Emojis.Decoration.alert_icon
                                ),
                                value=(
                                    f"-# ||{task}||\n"
                                    f"{'|'.join(str(f'{k}:{v}') for k, v in task.values_dict.items())}"
                                ),
                                inline=False,
                            )
                    if (
                        assignment.flags in [2, 3]
                        and len(assignment.tasks) > 1
                        and task != assignment.tasks[-1]
                    ):
                        self.add_field("or", "", inline=False)

                self.add_rewards(
                    rewards=assignment.rewards,
                    language_json=language_json,
                    reward_names=json_dict["items"]["reward_types"],
                )
                outlook_text = ""
                winning_all_tasks = [
                    ts < assignment.ends_at_datetime.timestamp()
                    for ts in self.completion_timestamps
                ]
                if (
                    assignment.flags == 1
                    and (
                        (winning_all_tasks != [] and all(winning_all_tasks))
                        and (
                            len(
                                [True for t in assignment.tasks if t.progress_perc == 1]
                                + winning_all_tasks
                            )
                            == len(assignment.tasks)
                        )
                    )
                ) or (
                    assignment.flags in [2, 3]
                    and (
                        any([t.progress_perc == 1 for t in assignment.tasks])
                        or any(winning_all_tasks)
                    )
                ):
                    outlook_text = language_json["complete"]
                    if {13, 15} & set([t.type for t in assignment.tasks]):
                        outlook_text += (
                            f" <t:{int(assignment.ends_at_datetime.timestamp())}:R>"
                        )
                    else:
                        oldest_time: datetime = sorted(
                            self.completion_timestamps, reverse=True
                        )[0]
                        outlook_text += f" <t:{int(oldest_time)}:R>"
                        time_diff = (
                            assignment.ends_at_datetime.timestamp() - oldest_time
                        )
                        hours = f"{time_diff // 3600:.0f}"
                        minutes = f"{(time_diff % 3600) // 60:.0f}"
                        outlook_text += language_json["embeds"]["Dashboard"][
                            "MajorOrderEmbed"
                        ]["ahead_of_schedule"].format(hours=hours, minutes=minutes)
                else:
                    if self.completion_timestamps != [] and len(
                        self.completion_timestamps
                    ) == len([True for t in assignment.tasks if t.progress_perc != 1]):
                        oldest_time: datetime = sorted(
                            self.completion_timestamps, reverse=True
                        )[0]
                        outlook_text += f"{language_json['failure']} <t:{int(assignment.ends_at_datetime.timestamp())}:R>"
                        time_diff = (
                            oldest_time - assignment.ends_at_datetime.timestamp()
                        )
                        hours = f"{time_diff // 3600:.0f}"
                        minutes = f"{(time_diff % 3600) // 60:.0f}"
                        if 0 < time_diff // 3600 < 250:
                            outlook_text += language_json["embeds"]["Dashboard"][
                                "MajorOrderEmbed"
                            ]["behind_schedule"].format(hours=hours, minutes=minutes)

                self.add_field(
                    "",
                    f"-# {language_json['ends']} <t:{int(assignment.ends_at_datetime.timestamp())}:R>",
                    inline=False,
                )
                if outlook_text != "":
                    self.add_field(
                        language_json["embeds"]["Dashboard"]["outlook"],
                        f"{outlook_text}",
                        inline=False,
                    )

        def add_type_2(
            self,
            task: Assignment.Task,
            language_json: dict,
            item_names_json: dict,
            planet: Planet | None,
            sector_name: str | None,
        ):
            """Successfully extract with {amount} {item}[ on {planet}][ in the __{sector}__ SECTOR][ from any {faction} controlled planet]"""
            field_name = language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]["type2"].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                amount=short_format(task.target),
                item=language_json["currencies"][
                    item_names_json[str(task.item_id)]["name"]
                ],
            )
            if planet:
                # [ on {planet}]
                field_name += language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                    "tasks"
                ]["type2_planet"].format(
                    planet=planet.loc_names[language_json["code_long"]]
                )
            elif sector_name:
                # [ in the __{sector}__ SECTOR]
                field_name += language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                    "tasks"
                ]["type2_sector"].format(sector=sector_name)
            elif task.faction:
                # [ from any {faction} controlled planet]
                field_name += language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                    "tasks"
                ]["type2_faction"].format(
                    faction=language_json["factions"][task.faction.full_name]
                )

            field_value = ""
            field_value += f"{language_json['embeds']['Dashboard']['progress']}: **{task.progress:,.0f}**"
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
                        language_json["complete"]
                        if winning
                        else language_json["failure"]
                    )
                    field_value += f"\n-# {outlook_text} <t:{int(task.tracker.complete_time.timestamp())}:R>"

            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_3(
            self,
            planets: Planets,
            task: Assignment.Task,
            language_json: dict,
            enemy_dict: dict,
        ):
            """Kill {amount} {enemy_type}[ using the __{item_to_use}__][ on {planet}]"""
            field_name = ""
            if task.enemy_id:
                enemy_type = (
                    enemy_dict.get(str(task.enemy_id), f"||UNKNOWN [{task.enemy_id}]||")
                    + "s"
                )
            else:
                enemy_type = task.faction.plural.title()
            field_name += language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
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
                field_name += language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                    "tasks"
                ]["type3_item"].format(
                    item_to_use=stratagem_id_dict.get(
                        task.item_id, f"||UNKNOWN [{task.item_id}]||"
                    )
                )
            if task.planet_index:
                field_name += language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                    "tasks"
                ]["type3_planet"].format(
                    planet=planets[task.planet_index].loc_names[
                        language_json["code_long"]
                    ]
                )
            field_value = ""
            if task.progress_perc != 1:
                field_value += f"{language_json['embeds']['Dashboard']['progress']}: **{(task.progress):,.0f}**"
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
                        language_json["completes"]
                        if winning
                        else language_json["failure"]
                    )
                    field_value += f"\n-# {outlook_text} <t:{int(task.tracker.complete_time.timestamp())}:R>"

            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_7(
            self,
            task: Assignment.Task,
            language_json: dict,
        ):
            """Extract from a successful Mission against {faction} {number} times"""
            field_name = language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]["type7"].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                faction=language_json["factions"][task.faction.full_name],
                amount=f"{task.target:,}",
            )
            field_value = ""
            if task.progress_perc != 1:
                field_value += f"{language_json['embeds']['Dashboard']['progress']}: **{(task.progress):,.0f}**"
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
                        outlook_text = language_json["complete"]
                    else:
                        outlook_text = language_json["failure"]
                    field_value += f"\n-# {outlook_text} <t:{int(task.tracker.complete_time.timestamp())}:R>"

            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_9(
            self,
            task: Assignment.Task,
            language_json: dict,
        ):
            """Complete an Operation[ against {faction}][ on {difficulty} or higher] {amount} times"""
            against_faction = ""
            on_difficulty = ""
            if task.faction:
                # [ against {faction}]
                against_faction = language_json["embeds"]["Dashboard"][
                    "MajorOrderEmbed"
                ]["tasks"]["type9_against_faction"].format(
                    faction=language_json["factions"][task.faction.full_name]
                )
            if task.difficulty:
                # [ on {difficulty} or higher]
                on_difficulty = language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                    "tasks"
                ]["type9_on_difficulty"].format(
                    difficulty=language_json["difficulty"][str(task.difficulty)]
                )

            field_name = language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
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
                field_value += f"{language_json['embeds']['Dashboard']['progress']}: **{(task.progress):,.0f}**\n"
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
                        language_json["completes"]
                        if winning
                        else language_json["failure"]
                    )
                    field_value += f"\n-# {outlook_text} <t:{int(task.tracker.complete_time.timestamp())}:R>"

            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_11(
            self,
            language_json: dict,
            task: Assignment.Task,
            planet: Planet,
        ):
            """Liberate a planet"""
            field_name = language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]["type11"].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                planet=planet.loc_names[language_json["code_long"]],
            )
            field_value = ""
            if task.progress_perc != 1 and planet.stats.player_count > (
                self.total_players * 0.05
            ):
                field_value += language_json["embeds"]["Dashboard"]["heroes"].format(
                    heroes=f"{planet.stats.player_count:,}"
                )
                # if planet.feature: TODO
                #     field_value += f"\n{language_json['embeds']['Dashboard']['MajorOrderEmbed']['feature']}: **{planet.feature}**"
                if planet.event:
                    winning = False
                    if planet.tracker and planet.tracker.change_rate_per_hour > 0:
                        winning = (
                            planet.tracker.complete_time
                            < planet.event.end_time_datetime
                        )
                    field_value += f"{language_json['ends']} <t:{planet.event.end_time_datetime.timestamp():.0f}:R>"
                    if winning:
                        field_value += f"\n{language_json['embeds']['Dashboard']['outlook']}: **{language_json['victory']}** <t:{int(planet.tracker.complete_time.timestamp())}:R>"
                    else:
                        field_value += f"\n{language_json['embeds']['Dashboard']['outlook']}: **{language_json['defeat']}**"
                    field_value += (
                        f"\n{language_json['embeds']['Dashboard']['progress']}:"
                    )
                    if self.compact_level < 1:
                        field_value += f"\n{planet.health_bar}"
                    field_value += f"\n`{(1-planet.event.progress):^25,.2%}`"
                else:
                    if planet.tracker and planet.tracker.change_rate_per_hour > 0:
                        field_value += f"\n{language_json['embeds']['Dashboard']['outlook']}: **{language_json['victory']}** <t:{int(planet.tracker.complete_time.timestamp())}:R>"
                    field_value += (
                        f"\n{language_json['embeds']['Dashboard']['progress']}:"
                    )
                    if self.compact_level < 1:
                        field_value += f"\n{planet.health_bar}"
                    field_value += f"\n`{(1-planet.health_perc):^25,.2%}`"
                if planet.tracker and planet.tracker.change_rate_per_hour > 0:
                    change = f"{planet.tracker.change_rate_per_hour:+.2%}/hour"
                    field_value += f"\n`{change:^25}`"

            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_12(
            self,
            task: Assignment.Task,
            language_json: dict,
            planet: Planet | None,
        ):
            """Defend[ {planet}] against {amount} attacks[ from the {faction}]"""
            planet_text = ""
            if planet:
                planet_text = f"{language_json['embeds']['Dashboard']['MajorOrderEmbed']['tasks']['type12_planet'].format(planet=planet.loc_names[language_json['code_long']])}"
            field_name = language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
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
                field_name += language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                    "tasks"
                ]["type12_faction"].format(
                    faction=language_json["factions"][task.faction.full_name]
                )
            field_value = ""
            if task.progress_perc != 1:
                if planet:
                    # if planet.feature: TODO
                    #     field_value += f"{language_json['embeds']['Dashboard']['MajorOrderEmbed']['feature']}: **{planet.feature}**"
                    field_value += f"\n{language_json['embeds']['Dashboard']['heroes'].format(heroes=planet.stats.player_count)}"
                    if planet.event:
                        field_value += f"\n{language_json['ends']} <t:{int(planet.event.end_time_datetime.timestamp())}:R>"
                        f"\n{language_json['embeds']['Dashboard']['DefenceEmbed']['level']} {planet.event.level}{planet.event.level_exclamation}"
                    if planet.tracker and planet.tracker.change_rate_per_hour != 0:
                        winning = (
                            planet.tracker.complete_time
                            < planet.event.end_time_datetime
                        )
                        if winning:
                            field_value += f"\n{language_json['embeds']['Dashboard']['outlook']}: **{language_json['victory']}** <t:{int(planet.tracker.complete_time.timestamp())}:R>"
                        else:
                            field_value += f"\n{language_json['embeds']['Dashboard']['outlook']}: **{language_json['defeat']}**"
                        field_value += (
                            f"\n{language_json['embeds']['Dashboard']['progress']}:"
                        )
                        if self.compact_level < 1:
                            field_value += f"\n{planet.health_bar}🛡️"
                        field_value += f"\n`{planet.event.progress:^25,.2%}`"
                        change = f"{planet.tracker.change_rate_per_hour:+.2%}/hour"
                        field_value += f"\n`{change:^25}`"
                else:
                    field_value += (
                        f"{language_json['embeds']['Dashboard']['progress']}: {int(task.progress)}/{task.target}"
                        f"\n{task.health_bar}"
                        f"\n`{(task.progress_perc):^25,.2%}`"
                    )

                self.add_field(
                    name=field_name,
                    value=field_value,
                    inline=False,
                )

        def add_type_13(
            self,
            task: Assignment.Task,
            language_json: dict,
            planets: Planets,
        ):
            """Hold {planet} when the order expires"""
            planet = planets[task.planet_index]
            field_name = language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]["type13"].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                planet=planet.loc_names[language_json["code_long"]],
            )
            field_value = ""
            if task.progress_perc != 1 or planet.event:
                for ae in planet.active_effects:
                    if ae.effect_type == 71:
                        planet_effects = PlanetEffects.get_from_effects_list([ae])
                        if planet_effects:
                            planet_effect = list(planet_effects)[0]
                            field_value += (
                                f"\n> -# {planet_effect[1]} **{planet_effect[0]}**"
                            )
                            if ae.planet_effect["description_long"]:
                                field_value += (
                                    f"\n> -# {ae.planet_effect['description_long']}"
                                )
                            if ae.planet_effect["description_short"]:
                                field_value += (
                                    f"\n> -# {ae.planet_effect['description_short']}"
                                )
                for special_unit in SpecialUnits.get_from_effects_list(
                    active_effects=planet.active_effects
                ):
                    field_value += f"\n-# {special_unit[1]} {language_json['special_units'][special_unit[0]]}"
                if planet.stats.player_count > 500:
                    formatted_heroes = f"{planet.stats.player_count:,}"
                    field_value += f"\n{language_json['embeds']['Dashboard']['heroes'].format(heroes=formatted_heroes)}"
                else:
                    for waypoint in planet.waypoints:
                        way_planet = planets[waypoint]
                        if (
                            way_planet.tracker
                            and way_planet.tracker.change_rate_per_hour > 0
                        ):
                            region_victory = False
                            for way_region in way_planet.regions.values():
                                if (
                                    way_region.tracker
                                    and way_region.tracker.change_rate_per_hour > 0
                                    and way_region.tracker.complete_time
                                    < way_planet.tracker.complete_time
                                    and way_planet.tracker.percentage_at(
                                        way_region.tracker.complete_time
                                    )
                                    >= 1
                                    - (
                                        (way_region.max_health * 1.5)
                                        / way_planet.max_health
                                    )
                                ):
                                    field_value += f"\nUnlocked **<t:{int(way_region.tracker.complete_time.timestamp())}:R>**\n> -# thanks to **{way_region.name}** {way_region.emoji} liberation on **{way_planet.name}** {way_planet.faction.emoji}"
                                    region_victory = True
                                    break
                            if not region_victory:
                                field_value += f"\nUnlocked **<t:{int(way_planet.tracker.complete_time.timestamp())}:R>**\n> -# thanks to **{way_planet.name}** {way_planet.faction.emoji} liberation"
                            break
                if planet.event:
                    field_value += f"\n{language_json['ends']} <t:{int(planet.event.end_time_datetime.timestamp())}:R>"
                    field_value += f"\n{language_json['embeds']['Dashboard']['DefenceEmbed']['level']} **{planet.event.level}**"
                    if planet.tracker and planet.tracker.change_rate_per_hour != 0:
                        winning = (
                            planet.tracker.complete_time
                            < planet.event.end_time_datetime
                        )
                        if winning:
                            field_value += f"\n{language_json['embeds']['Dashboard']['outlook']}: **{language_json['victory']}** <t:{int(planet.tracker.complete_time.timestamp())}:R>"
                        else:
                            field_value += f"\n{language_json['embeds']['Dashboard']['outlook']}: **{language_json['defeat']}**"
                    field_value += (
                        f"\n{language_json['embeds']['Dashboard']['progress']}:"
                    )
                    if self.compact_level < 1:
                        field_value += f"\n{planet.health_bar} 🛡️"
                    field_value += f"\n`{planet.event.progress:^25,.2%}`"
                    if planet.tracker and planet.tracker.change_rate_per_hour != 0:
                        change = f"{planet.tracker.change_rate_per_hour:+.2%}/hour"
                        field_value += f"\n`{change:^25}`"
                else:
                    if planet.tracker and planet.tracker.change_rate_per_hour != 0:
                        if planet.tracker.change_rate_per_hour > 0:
                            field_value += f"\n{language_json['embeds']['Dashboard']['outlook']}: **{language_json['victory']}** <t:{int(planet.tracker.complete_time.timestamp())}:R>"
                        field_value += (
                            f"\n{language_json['embeds']['Dashboard']['progress']}:"
                        )
                        if self.compact_level < 1:
                            field_value += f"\n{planet.health_bar}"
                        if planet.tracker and planet.tracker.change_rate_per_hour != 0:
                            change = f"{planet.tracker.change_rate_per_hour:+.2%}/hour"
                            field_value += f"\n`{1 - (planet.health_perc):^25,.2%}`"
                            field_value += f"\n`{change:^25}`"
            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_15(self, task: Assignment.Task, language_json: dict):
            """Liberate more planets than are lost during the order duration"""
            field_name = language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
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

        def add_description(self, assignment: Assignment, language_json: dict):
            self.add_field(
                name="",
                value=f"-# {assignment.briefing}",
                inline=False,
            )
            self.set_footer(
                text=language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                    "assignment"
                ].format(id=assignment.id)
            )

        def add_rewards(self, rewards: dict, language_json: dict, reward_names: dict):
            rewards_text = ""
            for reward in rewards:
                reward_name = reward_names.get(str(reward["type"]), "Unknown Item")
                localized_name = language_json["currencies"].get(reward_name)
                rewards_text += f"{reward['amount']:,} **{language_json['embeds']['Dashboard']['MajorOrderEmbed']['reward_pluralized'].format(reward=localized_name)}** {getattr(Emojis.Items, reward_name.replace(' ', '_').lower(), '')}\n"
            if rewards_text != "":
                self.add_field(
                    language_json["embeds"]["Dashboard"]["MajorOrderEmbed"]["rewards"],
                    rewards_text,
                )

        def add_briefing(self, briefing: GlobalEvent):
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
        ):
            super().__init__(
                title=language_json["dss"]["title"],
                colour=Colour.from_rgb(*CUSTOM_COLOURS["DSS"]),
            )
            self.set_thumbnail(
                url="https://media.discordapp.net/attachments/1212735927223590974/1413612410819969114/0xfbbeedfa99b09fec.png?ex=68bc90a6&is=68bb3f26&hm=cd8bf236a355bbed28f4847d3d62b5908d050a7eeb7396bb9a891e108acc0241&=&format=webp&quality=lossless"
            )
            emojis = dss.planet.faction.emoji
            for special_unit in SpecialUnits.get_from_effects_list(
                active_effects=dss.planet.active_effects
            ):
                emojis += special_unit[1]
            self.description = language_json["embeds"]["Dashboard"]["DSSEmbed"][
                "stationed_at"
            ].format(
                planet=dss.planet.loc_names[language_json["code_long"]],
                faction_emoji=emojis,
            )
            move_time = int(dss.move_timer_datetime.timestamp())
            if dss.planet.event:
                if dss.planet.tracker and dss.planet.tracker.change_rate_per_hour > 0:
                    if (
                        dss.planet.tracker.complete_time
                        < dss.planet.event.end_time_datetime
                    ):
                        if (
                            int(dss.planet.tracker.complete_time.timestamp())
                            < move_time
                        ):
                            move_time = int(
                                dss.planet.tracker.complete_time.timestamp()
                            )
            elif dss.planet.tracker and dss.planet.tracker.change_rate_per_hour > 0:
                if int(dss.planet.tracker.complete_time.timestamp()) < move_time:
                    move_time = int(dss.planet.tracker.complete_time.timestamp())
            self.description += language_json["embeds"]["Dashboard"]["DSSEmbed"][
                "next_move"
            ].format(timestamp=f"<t:{move_time}:R>")

            for tactical_action in dss.tactical_actions:
                field_name = f"{tactical_action.emoji} {language_json['embeds']['Dashboard']['DSSEmbed']['tactical_actions'][tactical_action.name.upper()]['name']}"
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
                        desc_fmtd = tactical_action.strategic_description.replace(
                            ". ", ".\n-# "
                        )
                        field_value += f"\n-# {desc_fmtd}"
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

            for effect in PlanetEffects.get_from_effects_list(planet.active_effects):
                field_value += f"\n-# {effect[0]} {effect[1]}"

            field_value += (
                f"\nEnds **<t:{int(planet.event.end_time_datetime.timestamp())}:R>**"
            )
            field_value += f"\nInvasion Level **{planet.event.level}**{planet.event.level_exclamation}"

            winning = False

            end_time = planet.event.end_time_datetime
            if planet.dss_in_orbit:
                if self.eagle_storm and self.eagle_storm.status == 2:
                    end_time += timedelta(
                        seconds=(
                            self.eagle_storm.status_end_datetime - self.now
                        ).total_seconds()
                    )
                    field_value += f"\n> DEFENCE HELD BY DSS"

            if (
                planet.tracker.change_rate_per_hour != 0
                and planet.tracker.complete_time < end_time
            ):
                winning = True
                field_value += f"\nVictory **<t:{int(planet.tracker.complete_time.timestamp())}:R>**"

            if not winning and planet.index in self.gambit_planets:
                gambit_planet = self.gambit_planets[planet.index]
                if (
                    gambit_planet.tracker.change_rate_per_hour != 0
                    and gambit_planet.tracker.complete_time < end_time
                ):
                    winning = True
                    field_value += f"\n> Ends **<t:{int(gambit_planet.tracker.complete_time.timestamp())}:R>** thanks to **{gambit_planet.loc_names[self.language_json['code_long']]}** liberation"
                else:
                    field_value += f"\n> Can be ended by liberating **{self.gambit_planets[planet.index].loc_names[self.language_json['code_long']]}**"

            if not winning:
                for region in planet.regions.values():
                    if not region.is_available:
                        continue
                    if (
                        region.tracker.change_rate_per_hour != 0
                        and region.tracker.complete_time < end_time
                        and planet.tracker.percentage_at(region.tracker.complete_time)
                        >= 1 - ((region.max_health * 1.5) / planet.max_health)
                        and region.tracker.complete_time < planet.tracker.complete_time
                    ):
                        winning = True
                        field_value += f"\n> Ends **<t:{int(region.tracker.complete_time.timestamp())}:R>** thanks to **{region.name}** liberation"

            if not winning:
                field_value += f"\n**Losing**"

            field_value += f"\nHeroes: **{planet.stats.player_count:,}**"
            field_value += f"\nDefence progress:"
            if self.compact_level < 1:
                field_value += f"\n{planet.health_bar}"
            field_value += f"\n`{planet.event.progress:^25.2%}`"
            if planet.tracker:
                change = f"{planet.tracker.change_rate_per_hour:+.2%}/hr"
                field_value += f"\n`{change:^25}`"

            for region in planet.regions.values():
                if region.is_available:
                    field_value += f"\n-# ↳ {region.emoji} {region.type} **{region.name}** - {region.perc:.0%}"
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
                            planet.tracker
                            and planet.tracker.change_rate_per_hour != 0
                            and region_avail_datetime < planet.tracker.complete_time
                        ):
                            field_value += f"\n-# ↳ {region.emoji} {region.type} **{region.name}** - available <t:{int(region_avail_datetime.timestamp())}:R>"
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
                    field_value += f"Heroes: **{campaign.planet.stats.player_count:,}**"

                    for su in SpecialUnits.get_from_effects_list(
                        campaign.planet.active_effects
                    ):
                        field_value += (
                            f"\n-# {su[1]} {language_json['special_units'][su[0]]}"
                        )

                    for effect in PlanetEffects.get_from_effects_list(
                        campaign.planet.active_effects
                    ):
                        field_value += f"\n-# {effect[0]} {effect[1]}"

                    if (
                        campaign.planet.tracker
                        and campaign.planet.tracker.change_rate_per_hour > 0
                    ):
                        region_victory = False
                        for region in campaign.planet.regions.values():
                            if (
                                region.tracker
                                and region.tracker.change_rate_per_hour > 0
                                and region.tracker.complete_time
                                < campaign.planet.tracker.complete_time
                                and campaign.planet.tracker.percentage_at(
                                    region.tracker.complete_time
                                )
                                >= 1
                                - (
                                    (region.max_health * 1.5)
                                    / campaign.planet.max_health
                                )
                            ):
                                field_value += f"\nVictory **<t:{int(region.tracker.complete_time.timestamp())}:R>**\n> -# thanks to **{region.name}** {region.emoji} liberation"
                                region_victory = True
                                break
                        if not region_victory:
                            field_value += f"\nVictory **<t:{int(campaign.planet.tracker.complete_time.timestamp())}:R>**"
                    field_value += "\nPlanet liberation:"
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

                    for region in [
                        r for r in campaign.planet.regions.values() if r.is_available
                    ]:
                        field_value += f"\n-# ↳ {region.emoji} {region.type} **{region.name}** {region.perc:.2%}"
                        if region.tracker and region.tracker.change_rate_per_hour != 0:
                            field_value += (
                                f" | {region.tracker.change_rate_per_hour:+.2%}/hr"
                            )

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
                                skipped_planets_text += f"-# ↳ {getattr(getattr(Emojis.RegionIcons, region.owner.full_name), f'_{region.size}')} {region.type} **{region.name}** - {region.perc:.2%}\n"
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
