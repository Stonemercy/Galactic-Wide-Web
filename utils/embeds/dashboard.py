from datetime import datetime, timedelta
from data.lists import (
    custom_colours,
    stratagem_id_dict,
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
from utils.dataclasses import AssignmentImages, Factions, SpecialUnits
from utils.emojis import Emojis
from utils.functions import health_bar, short_format
from utils.mixins import EmbedReprMixin
from utils.trackers import BaseTracker, BaseTrackerEntry

ATTACK_EMBED_ICONS = {
    "illuminate": "https://media.discordapp.net/attachments/1212735927223590974/1414959912269643847/illuminate.png?ex=68c1779b&is=68c0261b&hm=f7f450e22f313d28b50f03c5aa9ee5c21ded41f79f5a528ec4f819f5283c479c&=&format=webp&quality=lossless",
    "automaton": "https://media.discordapp.net/attachments/1212735927223590974/1414959911728709632/automaton.png?ex=68c1779b&is=68c0261b&hm=b5a82963ba2a5010f9a8e1b1f5ea0ab15f3ca29ace1dda6922053105b122fadf&=&format=webp&quality=lossless",
    "terminids": "https://media.discordapp.net/attachments/1212735927223590974/1414959912815169636/terminids.png?ex=68c1779b&is=68c0261b&hm=3c1ad5eea04d6ca74c0a99d70244780662fa37f5e25866d4039edc921e442b0b&=&format=webp&quality=lossless",
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
                        liberation_changes_tracker=data.liberation_changes,
                        mo_task_tracker=data.major_order_changes,
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
                    liberation_changes_tracker=None,
                    mo_task_tracker=None,
                    language_json=language_json,
                    json_dict=None,
                    compact_level=False,
                )
            )

        # DSS Eembed
        if data.dss and data.dss.flags not in (0, 2):
            self.embeds.append(
                self.DSSEmbed(
                    dss=data.dss,
                    language_json=language_json,
                    planet_names_json=json_dict["planets"],
                    ta_changes=data.tactical_action_changes,
                )
            )

        # Defence embed
        if data.planet_events:
            eagle_storm = data.dss.get_ta_by_name("EAGLE STORM") if data.dss else None
            self.embeds.append(
                self.DefenceEmbed(
                    planet_events=data.planet_events,
                    liberation_changes=data.liberation_changes,
                    region_lib_changes=data.region_changes,
                    language_json=language_json,
                    planet_names=json_dict["planets"],
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
                liberation_changes=data.liberation_changes,
                region_lib_changes=data.region_changes,
                language_json=language_json,
                planet_names=json_dict["planets"],
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
                liberation_changes=data.liberation_changes,
                region_lib_changes=data.region_changes,
                language_json=language_json,
                planet_names=json_dict["planets"],
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
                liberation_changes=data.liberation_changes,
                region_lib_changes=data.region_changes,
                language_json=language_json,
                planet_names=json_dict["planets"],
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
            liberation_changes_tracker: BaseTracker,
            mo_task_tracker: BaseTracker,
            language_json: dict,
            json_dict: dict,
            compact_level: int = 0,
        ):
            self.compact_level = compact_level
            self.assignment = assignment
            self.completion_timestamps = []
            super().__init__(
                colour=Colour.from_rgb(*custom_colours["MO"]),
            )
            if not self.assignment:
                self.title = language_json["dashboard"]["MajorOrderEmbed"]["mo_missing"]
                self.add_field(
                    name="",
                    value=language_json["dashboard"]["MajorOrderEmbed"][
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
                now_timestamp = datetime.now().timestamp()
                for index, task in enumerate(assignment.tasks, start=1):
                    tracker: BaseTrackerEntry | None = mo_task_tracker.get_entry(
                        (assignment.id, index)
                    )
                    if tracker and tracker.change_rate_per_hour != 0:
                        self.completion_timestamps.append(
                            now_timestamp + tracker.seconds_until_complete
                        )
                    elif task.type in (11, 13):
                        lib_changes = liberation_changes_tracker.get_entry(
                            task.planet_index
                        )
                        if lib_changes and lib_changes.change_rate_per_hour > 0:
                            self.completion_timestamps.append(
                                now_timestamp + lib_changes.seconds_until_complete
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
                                planet_names_json=json_dict["planets"],
                                planet=planet,
                                sector_name=sector_name,
                                tracker=tracker,
                            )
                        case 3:
                            self.add_type_3(
                                task=task,
                                language_json=language_json,
                                enemy_dict=json_dict["enemies"]["enemy_ids"],
                                planet_names=json_dict["planets"],
                                tracker=tracker,
                            )
                        case 7:
                            self.add_type_7(
                                task=task,
                                language_json=language_json,
                                tracker=tracker,
                            )
                        case 9:
                            self.add_type_9(
                                task=task,
                                language_json=language_json,
                                tracker=tracker,
                            )
                        case 11:
                            self.add_type_11(
                                language_json=language_json,
                                planet=planets[task.planet_index],
                                task=task,
                                planet_names_json=json_dict["planets"],
                                liberation_changes=liberation_changes_tracker,
                            )
                        case 12:
                            self.add_type_12(
                                task=task,
                                language_json=language_json,
                                liberation_changes=liberation_changes_tracker,
                                planet_names_json=json_dict["planets"],
                                planet=planets.get(task.planet_index),
                            )
                        case 13:
                            self.add_type_13(
                                task=task,
                                language_json=language_json,
                                planet=planets[task.planet_index],
                                liberation_changes=liberation_changes_tracker,
                                planet_names_json=json_dict["planets"],
                            )
                        case 15:
                            self.add_type_15(
                                task=task,
                                language_json=language_json,
                            )
                        case _:
                            self.add_field(
                                name=language_json["dashboard"]["MajorOrderEmbed"][
                                    "tasks"
                                ]["typeNew"].format(
                                    alert_emoji=Emojis.Decoration.alert_icon
                                ),
                                value=(
                                    f"-# ||{task}||\n"
                                    f"{'|'.join(str(f'{k}:{v}') for k, v in task.values_dict.items())}"
                                ),
                                inline=False,
                            )
                    if (
                        assignment.flags == 3
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
                    assignment.flags != 3
                    and (
                        winning_all_tasks
                        and all(winning_all_tasks)
                        and len(winning_all_tasks)
                        == len([t for t in assignment.tasks if t.progress_perc != 1])
                    )
                ) or (
                    assignment.flags == 3
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
                        outlook_text += language_json["dashboard"]["MajorOrderEmbed"][
                            "ahead_of_schedule"
                        ].format(hours=hours, minutes=minutes)
                else:
                    if self.completion_timestamps != []:
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
                            outlook_text += language_json["dashboard"][
                                "MajorOrderEmbed"
                            ]["behind_schedule"].format(hours=hours, minutes=minutes)

                self.add_field(
                    "",
                    f"-# {language_json['ends']} <t:{int(assignment.ends_at_datetime.timestamp())}:R>",
                    inline=False,
                )
                if outlook_text != "":
                    self.add_field(
                        language_json["dashboard"]["outlook"],
                        f"{outlook_text}",
                        inline=False,
                    )

        def add_type_2(
            self,
            task: Assignment.Task,
            language_json: dict,
            item_names_json: dict,
            planet_names_json: dict,
            planet: Planet | None,
            sector_name: str | None,
            tracker: BaseTrackerEntry | None,
        ):
            """Successfully extract with {amount} {item}[ on {planet}][ in the __{sector}__ SECTOR][ from any {faction} controlled planet]"""
            field_name = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                "type2"
            ].format(
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
                field_name += language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type2_planet"
                ].format(
                    planet=planet_names_json[str(planet.index)]["names"][
                        language_json["code_long"]
                    ]
                )
            elif sector_name:
                # [ in the __{sector}__ SECTOR]
                field_name += language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type2_sector"
                ].format(sector=sector_name)
            elif task.faction:
                # [ from any {faction} controlled planet]
                field_name += language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type2_faction"
                ].format(faction=language_json["factions"][task.faction.full_name])
            field_value = ""
            if task.progress_perc != 1:
                field_value += f"{language_json['dashboard']['progress']}: **{task.progress:,.0f}**"
                if self.compact_level < 1:
                    if tracker and tracker.change_rate_per_hour != 0:
                        field_value += f"\n{health_bar(task.progress_perc, task.faction if task.faction else 'MO', anim=True, increasing=tracker.change_rate_per_hour > 0)}"
                    else:
                        field_value += f"\n{task.health_bar}"
                field_value += f"\n`{(task.progress_perc):^25,.2%}`"
                if tracker and tracker.change_rate_per_hour != 0:
                    rate = f"{tracker.change_rate_per_hour:+.2%}/hour"
                    field_value += f"\n`{rate:^25}`"
                    winning = (
                        tracker.change_rate_per_hour > 0
                        and datetime.now()
                        + timedelta(seconds=tracker.seconds_until_complete)
                        < self.assignment.ends_at_datetime
                    )
                    if winning:
                        outlook_text = language_json["complete"]
                    else:
                        outlook_text = language_json["failure"]
                    field_value += f"\n-# {outlook_text} <t:{int(datetime.now().timestamp() + tracker.seconds_until_complete)}:R>"

            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_3(
            self,
            task: Assignment.Task,
            language_json: dict,
            enemy_dict: dict,
            planet_names: dict,
            tracker: BaseTrackerEntry,
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
            field_name += language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                "type3"
            ].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                amount=short_format(task.target),
                target=enemy_type,
            )
            if task.item_id:
                field_name += language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type3_item"
                ].format(
                    item_to_use=stratagem_id_dict.get(
                        task.item_id, f"||UNKNOWN [{task.item_id}]||"
                    )
                )
            if task.planet_index:
                field_name += language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type3_planet"
                ].format(
                    planet=planet_names[str(task.planet_index)]["names"][
                        language_json["code_long"]
                    ]
                )
            field_value = ""
            if task.progress_perc != 1:
                field_value += f"{language_json['dashboard']['progress']}: **{(task.progress):,.0f}**"
                if self.compact_level < 1:
                    if tracker and tracker.change_rate_per_hour != 0:
                        field_value += f"\n{health_bar(task.progress_perc, task.faction if task.faction else 'MO', anim=True, increasing=tracker.change_rate_per_hour > 0)}"
                    else:
                        field_value += f"\n{task.health_bar}"
                field_value += f"\n`{(task.progress_perc):^25,.2%}`"
                if tracker and tracker.change_rate_per_hour != 0:
                    rate = f"{tracker.change_rate_per_hour:+.2%}/hour"
                    field_value += f"\n`{rate:^25}`"
                    winning = (
                        tracker.change_rate_per_hour > 0
                        and datetime.now()
                        + timedelta(seconds=tracker.seconds_until_complete)
                        < self.assignment.ends_at_datetime
                    )
                    if winning:
                        outlook_text = language_json["complete"]
                    else:
                        outlook_text = language_json["failure"]
                    field_value += f"\n-# {outlook_text} <t:{int(datetime.now().timestamp() + tracker.seconds_until_complete)}:R>"

            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_7(
            self,
            task: Assignment.Task,
            language_json: dict,
            tracker: BaseTrackerEntry,
        ):
            """Extract from a successful Mission against {faction} {number} times"""
            field_name = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                "type7"
            ].format(
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
                field_value += f"{language_json['dashboard']['progress']}: **{(task.progress):,.0f}**"
                if self.compact_level < 1:
                    if tracker and tracker.change_rate_per_hour != 0:
                        field_value += f"\n{health_bar(task.progress_perc, task.faction if task.faction else 'MO', anim=True, increasing=tracker.change_rate_per_hour > 0)}"
                    else:
                        field_value += f"\n{task.health_bar}"
                field_value += f"\n`{(task.progress_perc):^25,.2%}`"
                if tracker and tracker.change_rate_per_hour != 0:
                    rate = f"{tracker.change_rate_per_hour:+.2%}/hour"
                    field_value += f"\n`{rate:^25}`"
                    winning = (
                        tracker.change_rate_per_hour > 0
                        and datetime.now()
                        + timedelta(seconds=tracker.seconds_until_complete)
                        < self.assignment.ends_at_datetime
                    )
                    if winning:
                        outlook_text = language_json["complete"]
                    else:
                        outlook_text = language_json["failure"]
                    field_value += f"\n-# {outlook_text} <t:{int(datetime.now().timestamp() + tracker.seconds_until_complete)}:R>"

            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_9(
            self,
            task: Assignment.Task,
            language_json: dict,
            tracker: BaseTrackerEntry,
        ):
            """Complete an Operation[ against {faction}][ on {difficulty} or higher] {amount} times"""
            against_faction = ""
            on_difficulty = ""
            if task.faction:
                # [ against {faction}]
                against_faction = language_json["dashboard"]["MajorOrderEmbed"][
                    "tasks"
                ]["type9_against_faction"].format(
                    faction=language_json["factions"][task.faction.full_name]
                )
            if task.difficulty:
                # [ on {difficulty} or higher]
                on_difficulty = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type9_on_difficulty"
                ].format(difficulty=language_json["difficulty"][str(task.difficulty)])

            field_name = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                "type9"
            ].format(
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
                field_value += f"{language_json['dashboard']['progress']}: **{(task.progress):,.0f}**\n"
                if self.compact_level < 1:
                    if tracker and tracker.change_rate_per_hour != 0:
                        field_value += f"\n{health_bar(task.progress_perc, task.faction if task.faction else 'MO', anim=True, increasing=tracker.change_rate_per_hour > 0)}"
                    else:
                        field_value += f"\n{task.health_bar}\n"
                field_value += f"\n`{(task.progress_perc):^25,.2%}`"
                if tracker and tracker.change_rate_per_hour != 0:
                    rate = f"{tracker.change_rate_per_hour:+.2%}/hour"
                    field_value += f"\n`{rate:^25}`"
                    winning = (
                        tracker.change_rate_per_hour > 0
                        and datetime.now()
                        + timedelta(seconds=tracker.seconds_until_complete)
                        < self.assignment.ends_at_datetime
                    )
                    if winning:
                        field_value += f"\n-# {language_json['complete']} <t:{int(datetime.now().timestamp() + tracker.seconds_until_complete)}:R>"

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
            planet_names_json: dict,
            liberation_changes: BaseTracker,
        ):
            """Liberate a planet"""
            field_name = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                "type11"
            ].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                planet=planet_names_json[str(planet.index)]["names"][
                    language_json["code_long"]
                ],
            )
            field_value = ""
            if task.progress_perc != 1 and planet.stats.player_count > (
                self.total_players * 0.05
            ):
                field_value += language_json["dashboard"]["heroes"].format(
                    heroes=f"{planet.stats.player_count:,}"
                )
                if planet.feature:
                    field_value += f"\n{language_json['dashboard']['MajorOrderEmbed']['feature']}: **{planet.feature}**"
                planet_lib_changes = liberation_changes.get_entry(key=planet.index)
                now_seconds = int(datetime.now().timestamp())
                if planet.event:
                    winning = False
                    if (
                        planet_lib_changes
                        and planet_lib_changes.change_rate_per_hour > 0
                    ):
                        winning = (
                            now_seconds + planet_lib_changes.seconds_until_complete
                            < planet.event.end_time_datetime.timestamp()
                        )
                    field_value += f"{language_json['ends']} <t:{planet.event.end_time_datetime.timestamp():.0f}:R>"
                    if winning:
                        field_value += f"\n{language_json['dashboard']['outlook']}: **{language_json['victory']}** <t:{now_seconds + planet_lib_changes.seconds_until_complete}:R>"
                    else:
                        field_value += f"\n{language_json['dashboard']['outlook']}: **{language_json['defeat']}**"
                    field_value += f"\n{language_json['dashboard']['progress']}:"
                    if self.compact_level < 1:
                        if (
                            planet_lib_changes
                            and planet_lib_changes.change_rate_per_hour != 0
                        ):
                            field_value += f"\n{health_bar(planet.event.health_bar, planet.event.faction, anim=True, increasing=planet_lib_changes.change_rate_per_hour > 0)}"
                        else:
                            field_value += f"\n{planet.event.health_bar}"
                    field_value += f"\n`{(1-planet.event.progress):^25,.2%}`"
                else:
                    if (
                        planet_lib_changes
                        and planet_lib_changes.change_rate_per_hour > 0
                    ):
                        field_value += f"\n{language_json['dashboard']['outlook']}: **{language_json['victory']}** <t:{now_seconds + planet_lib_changes.seconds_until_complete}:R>"
                    field_value += f"\n{language_json['dashboard']['progress']}:"
                    if self.compact_level < 1:
                        if (
                            planet_lib_changes
                            and planet_lib_changes.change_rate_per_hour != 0
                        ):
                            field_value += f"\n{health_bar(planet.health_perc, 'Humans', True, anim=True, increasing=planet_lib_changes.change_rate_per_hour > 0)}"
                        else:
                            field_value += (
                                f"\n{health_bar(planet.health_perc, 'Humans', True)}"
                            )
                    field_value += f"\n`{(1-planet.health_perc):^25,.2%}`"
                if planet_lib_changes and planet_lib_changes.change_rate_per_hour > 0:
                    change = f"{planet_lib_changes.change_rate_per_hour:+.2%}/hour"
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
            liberation_changes: BaseTracker,
            planet_names_json: dict,
            planet: Planet | None,
        ):
            """Defend[ {planet}] against {amount} attacks[ from the {faction}]"""
            planet_text = ""
            if planet:
                planet_text = f"{language_json['dashboard']['MajorOrderEmbed']['tasks']['type12_planet'].format(planet=planet_names_json[str(planet.index)]['names'][language_json['code_long']])}"
            field_name = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                "type12"
            ].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                planet=planet_text,
                amount=task.target,
            )
            if task.faction:
                field_name += language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type12_faction"
                ].format(faction=language_json["factions"][task.faction.full_name])
            field_value = ""
            if task.progress_perc != 1:
                if planet:
                    if planet.feature:
                        field_value += f"{language_json['dashboard']['MajorOrderEmbed']['feature']}: **{planet.feature}**"
                    field_value += f"\n{language_json['dashboard']['heroes'].format(heroes=planet.stats.player_count)}"
                    if planet.event:
                        field_value += f"\n{language_json['ends']} <t:{planet.event.end_time_datetime.timestamp():.0f}:R>"
                        f"\n{language_json['dashboard']['DefenceEmbed']['level']} {planet.event.level}"
                    planet_lib_changes = liberation_changes.get_entry(planet.index)
                    if (
                        planet_lib_changes
                        and planet_lib_changes.change_rate_per_hour != 0
                    ):
                        now_seconds = int(datetime.now().timestamp())
                        winning = (
                            datetime.fromtimestamp(
                                now_seconds + planet_lib_changes.seconds_until_complete
                            )
                            < planet.event.end_time_datetime
                        )
                        if winning:
                            field_value += f"\n{language_json['dashboard']['outlook']}: **{language_json['victory']}** <t:{now_seconds + planet_lib_changes.seconds_until_complete}:R>"
                        else:
                            field_value += f"\n{language_json['dashboard']['outlook']}: **{language_json['defeat']}**"
                        field_value += f"\n{language_json['dashboard']['progress']}:"
                        if self.compact_level < 1:
                            if (
                                planet_lib_changes
                                and planet_lib_changes.change_rate_per_hour != 0
                            ):
                                field_value += f"\n{health_bar(planet.health_perc, planet.event.faction, anim=True, increasing=planet_lib_changes.change_rate_per_hour > 0)}"
                            else:
                                field_value += f"\n{planet.event.health_bar} 🛡️"
                        field_value += f"\n`{planet.event.progress:^25,.2%}`"
                        change = f"{planet_lib_changes.change_rate_per_hour:+.2%}/hour"
                        field_value += f"\n`{change:^25}`"
                        if planet.event.required_players != 0:
                            field_value += f"\n{language_json['dashboard']['DefenceEmbed']['players_required']}: **~{planet.event.required_players:,.0f}+**"
                else:
                    field_value += (
                        f"{language_json['dashboard']['progress']}: {int(task.progress)}/{task.target}"
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
            planet: Planet,
            liberation_changes: BaseTracker,
            planet_names_json: dict,
        ):
            """Hold {planet} when the order expires"""
            field_name = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                "type13"
            ].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                planet=planet_names_json[str(planet.index)]["names"][
                    language_json["code_long"]
                ],
            )
            field_value = ""
            if task.progress_perc != 1:
                if planet.feature:
                    field_value += f"\n{language_json['dashboard']['MajorOrderEmbed']['feature']}: **{planet.feature}**"
                for special_unit in SpecialUnits.get_from_effects_list(
                    active_effects=planet.active_effects
                ):
                    field_value += f"\n-# {language_json['special_units'][special_unit[0]]} {special_unit[1]}"
                if planet.stats.player_count > 500:
                    formatted_heroes = f"{planet.stats.player_count:,}"
                    field_value += f"\n{language_json['dashboard']['heroes'].format(heroes=formatted_heroes)}"
                if planet.event:
                    field_value += f"\n{language_json['ends']} <t:{planet.event.end_time_datetime.timestamp():.0f}:R>"
                    field_value += f"\n{language_json['dashboard']['DefenceEmbed']['level']} **{planet.event.level}**"
                    planet_lib_changes = liberation_changes.get_entry(planet.index)
                    if (
                        planet_lib_changes
                        and planet_lib_changes.change_rate_per_hour != 0
                    ):
                        now_seconds = int(datetime.now().timestamp())
                        winning = (
                            datetime.fromtimestamp(
                                now_seconds + planet_lib_changes.seconds_until_complete
                            )
                            < planet.event.end_time_datetime
                        )
                        if winning:
                            field_value += f"\n{language_json['dashboard']['outlook']}: **{language_json['victory']}** <t:{now_seconds + planet_lib_changes.seconds_until_complete}:R>"
                        else:
                            field_value += f"\n{language_json['dashboard']['outlook']}: **{language_json['defeat']}**"
                        if planet.event.required_players != 0:
                            field_value += f"\n{language_json['dashboard']['DefenceEmbed']['players_required']}: **~{planet.event.required_players:,.0f}+**"
                        field_value += f"\n{language_json['dashboard']['progress']}:"
                        if self.compact_level < 1:
                            if (
                                planet_lib_changes
                                and planet_lib_changes.change_rate_per_hour != 0
                            ):
                                field_value += f"\n{health_bar(planet.event.progress, planet.event.faction, anim=True, increasing=planet_lib_changes.change_rate_per_hour > 0)}"
                            else:
                                field_value += f"\n{planet.event.health_bar} 🛡️"
                    field_value += f"\n`{planet.event.progress:^25,.2%}`"
                    if (
                        planet_lib_changes
                        and planet_lib_changes.change_rate_per_hour != 0
                    ):
                        change = f"{planet_lib_changes.change_rate_per_hour:+.2%}/hour"
                        field_value += f"\n`{change:^25}`"
                else:
                    planet_lib_changes = liberation_changes.get_entry(planet.index)
                    if (
                        planet_lib_changes
                        and planet_lib_changes.change_rate_per_hour != 0
                    ):
                        if planet_lib_changes.change_rate_per_hour > 0:
                            now_seconds = int(datetime.now().timestamp())
                            field_value += f"\n{language_json['dashboard']['outlook']}: **{language_json['victory']}** <t:{now_seconds + planet_lib_changes.seconds_until_complete}:R>"
                        field_value += f"\n{language_json['dashboard']['progress']}:\n"
                        if self.compact_level < 1:
                            if (
                                planet_lib_changes
                                and planet_lib_changes.change_rate_per_hour != 0
                            ):
                                field_value += f"\n{health_bar(planet.health_perc, planet.current_owner, anim=True, increasing=planet_lib_changes.change_rate_per_hour > 0)}"
                            else:
                                field_value += f"{health_bar(perc=planet.health_perc, faction=planet.current_owner, reverse=True)}"
                        if (
                            planet_lib_changes
                            and planet_lib_changes.change_rate_per_hour != 0
                        ):
                            change = (
                                f"{planet_lib_changes.change_rate_per_hour:+.2%}/hour"
                            )
                            field_value += f"\n`{1 - (planet.health_perc):^25,.2%}`"
                            field_value += f"\n`{change:^25}`"
            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_type_15(self, task: Assignment.Task, language_json: dict):
            """Liberate more planets than are lost during the order duration"""
            field_name = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                "type15"
            ].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc >= 1
                    else Emojis.Icons.mo_task_incomplete
                )
            )
            field_value = ""
            if task.progress_perc != 1:
                clamped_progress = max(min(task.progress, 5), -5)
                percent = (clamped_progress + 5) / 10
                if self.compact_level < 1:
                    field_value += health_bar(
                        perc=percent,
                        faction=(
                            Factions.automaton
                            if task.progress_perc != 1
                            else Factions.humans
                        ),
                    )
                field_value += f"`{task.progress_perc:^25,}`\n"

            self.add_field(
                name=field_name,
                value=field_value,
                inline=False,
            )

        def add_description(self, assignment: Assignment, language_json: dict):
            self.add_field(
                name=assignment.briefing, value=assignment.description, inline=False
            )
            self.set_footer(
                text=language_json["dashboard"]["MajorOrderEmbed"]["assignment"].format(
                    id=assignment.id
                )
            )

        def add_rewards(self, rewards: dict, language_json: dict, reward_names: dict):
            rewards_text = ""
            for reward in rewards:
                reward_name = reward_names.get(str(reward["type"]), "Unknown Item")
                localized_name = language_json["currencies"].get(reward_name)
                rewards_text += f"{reward['amount']:,} **{language_json['dashboard']['MajorOrderEmbed']['reward_pluralized'].format(reward=localized_name)}** {getattr(Emojis.Items, reward_name.replace(' ', '_').lower(), '')}\n"
            if rewards_text != "":
                self.add_field(
                    language_json["dashboard"]["MajorOrderEmbed"]["rewards"],
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
            planet_names_json: dict,
            ta_changes: BaseTracker,
        ):
            super().__init__(
                title=language_json["dss"]["title"],
                colour=Colour.from_rgb(*custom_colours["DSS"]),
            )
            self.set_thumbnail(
                url="https://media.discordapp.net/attachments/1212735927223590974/1413612410819969114/0xfbbeedfa99b09fec.png?ex=68bc90a6&is=68bb3f26&hm=cd8bf236a355bbed28f4847d3d62b5908d050a7eeb7396bb9a891e108acc0241&=&format=webp&quality=lossless"
            )
            faction_emojis = getattr(
                Emojis.Factions, dss.planet.current_owner.full_name.lower()
            )
            for special_unit in SpecialUnits.get_from_effects_list(
                active_effects=dss.planet.active_effects
            ):
                faction_emojis += special_unit[1]
            self.description = language_json["dashboard"]["DSSEmbed"][
                "stationed_at"
            ].format(
                planet=planet_names_json[str(dss.planet.index)]["names"][
                    language_json["code_long"]
                ],
                faction_emoji=faction_emojis,
            )
            self.description += language_json["dashboard"]["DSSEmbed"][
                "next_move"
            ].format(timestamp=f"<t:{int(dss.move_timer_datetime.timestamp())}:R>")
            status_dict = {
                0: "inactive",
                1: "preparing",
                2: "active",
                3: "on_cooldown",
            }
            for tactical_action in dss.tactical_actions:
                field_name = f"{getattr(Emojis.DSS, tactical_action.name.lower().replace(' ', '_'))} {language_json['dashboard']['DSSEmbed']['tactical_actions'][tactical_action.name.upper()]['name']}"
                status = status_dict[tactical_action.status]
                field_value = f"{language_json['dashboard']['DSSEmbed']['status']}: **{language_json['dashboard']['DSSEmbed'][status]}**"
                match status:
                    case "preparing":
                        for ta_cost in tactical_action.cost:
                            field_value += f"\n{language_json['dashboard']['DSSEmbed']['max_submitable'].format(emoji=getattr(Emojis.Items,ta_cost.item.replace(' ', '_').lower()),number=f'{ta_cost.max_per_seconds[0]:,}',item=language_json['currencies'][ta_cost.item],hours=f'{ta_cost.max_per_seconds[1]/3600:.0f}')}"
                            cost_change = ta_changes.get_entry(
                                (tactical_action.id, ta_cost.item)
                            )
                            if cost_change and cost_change.change_rate_per_hour != 0:
                                field_value += f"\n{health_bar(ta_cost.progress,'MO',anim=True, increasing=cost_change.change_rate_per_hour > 0)}"
                                field_value += f"\n`{ta_cost.progress:^25.2%}`"
                                change = f"{cost_change.change_rate_per_hour:+.2%}/hr"
                                field_value += f"\n`{change:^25}`"
                                field_value += f"\n-# {language_json['dashboard']['DSSEmbed']['active']} <t:{int(datetime.now().timestamp() + cost_change.seconds_until_complete)}:R>"
                            else:
                                field_value += f"\n{health_bar(ta_cost.progress,'MO')}"
                                field_value += f"\n`{ta_cost.progress:^25.2%}`"
                    case "active":
                        field_value += f"\n{language_json['ends']} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
                        desc_fmtd = tactical_action.strategic_description.replace(
                            ". ", ".\n-# "
                        )
                        field_value += f"\n-# {desc_fmtd}"
                    case "on_cooldown":
                        field_value += f"\n-# {language_json['dashboard']['DSSEmbed']['off_cooldown']} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
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
            liberation_changes: BaseTracker,
            region_lib_changes: BaseTracker,
            language_json: dict,
            planet_names: dict,
            total_players: int,
            eagle_storm: DSS.TacticalAction | None,
            gambit_planets: dict[int, Planet],
            compact_level: int = 0,
        ):
            self.planet_names = planet_names
            self.language_json = language_json
            self.eagle_storm = eagle_storm
            self.liberation_changes = liberation_changes
            self.region_lib_changes = region_lib_changes
            self.gambit_planets = gambit_planets
            self.total_players = total_players
            self.compact_level = compact_level
            self.now = datetime.now()
            total_players_doing_defence = (
                sum(planet.stats.player_count for planet in planet_events)
                / total_players
            )
            super().__init__(
                title=f"{language_json['dashboard']['DefenceEmbed']['title']} ({total_players_doing_defence:.2%})",
                colour=Colour.blue(),
            )
            if planet_events:
                self.set_thumbnail(
                    "https://cdn.discordapp.com/attachments/1212735927223590974/1414958449967632466/0x7d2b143494a63666.png?ex=68c1763f&is=68c024bf&hm=9c1978e23c9c7991376201637f004791471d0b7e0968dfec6d1af4d4a6a9ff09&"
                )
                for planet in planet_events:
                    match planet.event.type:
                        case 1:
                            # Regular defence campaign
                            self.add_event_type_1(planet=planet)
                        case _:
                            # Unconfigured campaigns
                            self.add_unconfigured_event_type()

        def add_event_type_1(self, planet: Planet):
            feature_text = ""
            outlook_text = ""
            required_players = ""
            liberation_text = ""
            regions_text = ""
            now_seconds = int(self.now.timestamp())
            if (
                liberation_change := self.liberation_changes.get_entry(planet.index)
            ) and self.compact_level < 2:

                if planet.index in self.gambit_planets:
                    gambit_planet = self.gambit_planets[planet.index]
                    gambit_lib_change = self.liberation_changes.get_entry(
                        gambit_planet.index
                    )
                if liberation_change.change_rate_per_hour != 0:
                    win_time: datetime = datetime.fromtimestamp(
                        now_seconds + liberation_change.seconds_until_complete
                    )
                    end_time: datetime = planet.event.end_time_datetime
                    if planet.dss_in_orbit and self.eagle_storm.status == 2:
                        end_time += timedelta(
                            seconds=(
                                self.eagle_storm.status_end_datetime - self.now
                            ).total_seconds()
                        )
                    if win_time < end_time:
                        outlook_text = f"\n{self.language_json['dashboard']['outlook']}: **{self.language_json['victory']}** <t:{int(win_time.timestamp())}:R>"
                    else:
                        if (
                            planet.index in self.gambit_planets
                            and gambit_lib_change.change_rate_per_hour > 0
                            and datetime.fromtimestamp(
                                now_seconds + gambit_lib_change.seconds_until_complete
                            )
                            < planet.event.end_time_datetime
                        ):
                            outlook_text = f"\n{self.language_json['dashboard']['outlook']}: **{self.language_json['victory']}** <t:{now_seconds + gambit_lib_change.seconds_until_complete}:R>"
                            outlook_text += f"\n> -# {self.language_json['dashboard']['DefenceEmbed']['thanks_to_gambit'].format(planet=gambit_planet.name)}"
                        for region in planet.regions.values():
                            region_lib_change = self.region_lib_changes.get_entry(
                                region.settings_hash
                            )
                            if (
                                region_lib_change
                                and region_lib_change.change_rate_per_hour > 0
                            ):
                                region_lib_time = datetime.fromtimestamp(
                                    now_seconds
                                    + region_lib_change.seconds_until_complete
                                )
                                health_at_region_lib_time = (
                                    liberation_change.percentage_at(
                                        time=region_lib_time
                                    )
                                )
                                if (
                                    region_lib_time < end_time
                                    and health_at_region_lib_time
                                    >= (region.max_health * 1.5) / planet.max_health
                                ):
                                    if region_lib_time < win_time:
                                        outlook_text = f"\n{self.language_json['dashboard']['outlook']}: **{self.language_json['victory']}** <t:{int(region_lib_time.timestamp())}:R>"
                                        outlook_text += f"\n> -# Thanks to region **{region.name}** liberation"
                                        break
                        if outlook_text == "":
                            outlook_text = f"\n{self.language_json['dashboard']['outlook']}: **{self.language_json['defeat']}**"
                            if planet.index in self.gambit_planets:
                                outlook_text += f"\n> -# {self.language_json['dashboard']['DefenceEmbed']['gambit_available'].format(planet=gambit_planet.name)}"
                    change = f"{liberation_change.change_rate_per_hour:+.2%}/hour"
                    liberation_text = f"\n`{change:^25}`"
                    if (
                        self.language_json["victory"] not in outlook_text
                        and planet.event.required_players
                    ):
                        if 0 < planet.event.required_players < 2.5 * self.total_players:
                            required_players = f"\n{self.language_json['dashboard']['DefenceEmbed']['players_required']}: **~{planet.event.required_players:,.0f}+**"
                        else:
                            one_hour_ago = self.now - timedelta(hours=1)
                            if planet.event.start_time_datetime > one_hour_ago:
                                required_players = f"\n{self.language_json['dashboard']['DefenceEmbed']['players_required']}: {self.language_json['dashboard']['DefenceEmbed']['gathering_data']}"
                            else:
                                required_players = f"\n{self.language_json['dashboard']['DefenceEmbed']['players_required']}: {self.language_json['dashboard']['DefenceEmbed']['impossible']}"
            for region in planet.regions.values():
                if region.is_available:
                    region_lib_change_text = ""
                    if self.compact_level < 2 and (
                        region_lib_change := self.region_lib_changes.get_entry(
                            region.settings_hash
                        )
                    ):
                        if region_lib_change.change_rate_per_hour != 0:
                            region_lib_change_text = (
                                f"{region_lib_change.change_rate_per_hour:+.1%}/hr"
                            )
                    regions_text += f"\n-# ↳ {getattr(getattr(Emojis.RegionIcons, region.owner.full_name), f'_{region.size}')} {region.type} **{region.name}** - {region.perc:.0%} {region_lib_change_text}"
                else:
                    if (
                        region.availability_factor > planet.event.progress
                        and region.owner.full_name != "Humans"
                        and self.compact_level < 2
                    ):
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
                        if (
                            region_avail_timestamp
                            < now_seconds + liberation_change.seconds_until_complete
                        ):
                            regions_text += f"\n-# ↳ {getattr(getattr(Emojis.RegionIcons, region.owner.full_name), f'_{region.size}')} {region.type} **{region.name}** - available <t:{region_avail_timestamp}:R>"
                            break
            if planet.feature and self.compact_level < 2:
                feature_text += f"{self.language_json['dashboard']['DefenceEmbed']['feature']}: **{planet.feature}**"
            event_end_datetime = (
                planet.event.end_time_datetime
                + timedelta(
                    seconds=(
                        self.eagle_storm.status_end_datetime - self.now
                    ).total_seconds()
                )
                if planet.dss_in_orbit and self.eagle_storm.status == 2
                else planet.event.end_time_datetime
            )
            time_remaining = f"<t:{int(event_end_datetime.timestamp())}:R>"
            if planet.dss_in_orbit:
                if self.eagle_storm.status == 2:
                    time_remaining += self.language_json["dashboard"]["DefenceEmbed"][
                        "defence_held_by_dss"
                    ]
            event_health_bar = ""
            if self.compact_level < 1:
                if liberation_change and liberation_change.change_rate_per_hour != 0:
                    event_health_bar = f"\n{health_bar(perc=planet.event.progress, faction=planet.event.faction, anim=True, increasing=liberation_change.change_rate_per_hour > 0)}"
                else:
                    event_health_bar = f"\n{planet.event.health_bar}"
            player_count = f"**{planet.stats.player_count:,}**"
            self.add_field(
                f"__**{self.planet_names[str(planet.index)]['names'][self.language_json['code_long']]}**__ {planet.exclamations}",
                (
                    f"{feature_text}"
                    f"\n{self.language_json['ends']} {time_remaining}"
                    f"\n{self.language_json['dashboard']['DefenceEmbed']['level']} **{int(planet.event.max_health / 50_000)}**"
                    f"{outlook_text}"
                    f"\n{self.language_json['dashboard']['heroes'].format(heroes=player_count)}"
                    f"{required_players}"
                    f"\n{self.language_json['dashboard']['DefenceEmbed']['event_health']}:"
                    f"{event_health_bar}"
                    f"\n`{1 - (planet.event.health / planet.event.max_health):^25,.2%}`"
                    f"{liberation_text}"
                    f"{regions_text}"
                    "\u200b\n"
                ),
                inline=False,
            )

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
            liberation_changes: BaseTracker,
            region_lib_changes: BaseTracker,
            language_json: dict,
            planet_names: dict,
            faction: str,
            total_players: int,
            gambit_planets: dict[int, Planet],
            compact_level: int = 0,
        ):
            super().__init__(
                title=language_json["dashboard"]["AttackEmbed"]["title"].format(
                    faction=language_json["factions"][faction]
                ),
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
                if campaign.planet.stats.player_count < total_players * 0.05:
                    skipped_campaigns.append(campaign)
                    continue
                else:
                    time_to_complete = ""
                    change = ""
                    liberation_text = ""
                    region_text = ""
                    if (
                        liberation_change := liberation_changes.get_entry(
                            key=campaign.planet.index
                        )
                    ) and compact_level < 2:
                        if liberation_change.change_rate_per_hour > 0:
                            now_seconds = int(datetime.now().timestamp())
                            for region in campaign.planet.regions.values():
                                region_lib_change = region_lib_changes.get_entry(
                                    region.settings_hash
                                )
                                if (
                                    region_lib_change
                                    and region_lib_change.change_rate_per_hour > 0
                                    and (
                                        region_lib_change.seconds_until_complete
                                        < liberation_change.seconds_until_complete
                                        and campaign.planet.health
                                        - (region.max_health * 1.5)
                                        < 0
                                    )
                                ):
                                    time_to_complete = f"\n{language_json['dashboard']['outlook']}: **{language_json['victory']}** <t:{now_seconds + region_lib_change.seconds_until_complete}:R>\n-# thanks to {region.type} liberation"

                            if time_to_complete == "":
                                time_to_complete = f"\n{language_json['dashboard']['outlook']}: **{language_json['victory']}** <t:{now_seconds + liberation_change.seconds_until_complete}:R>"
                            change = (
                                f"{liberation_change.change_rate_per_hour:+.2%}/hour"
                            )
                            liberation_text = f"\n`{change:^25}`"
                        else:
                            skipped_campaigns.append(campaign)
                            continue

                    exclamation = campaign.planet.exclamations
                    if campaign.planet.regen_perc_per_hour <= 0.001:
                        exclamation += f":warning: {campaign.planet.regen_perc_per_hour:+.2%}/hr :warning:"
                    if campaign.planet.index in [
                        planet.index for planet in gambit_planets.values()
                    ]:
                        exclamation += ":chess_pawn:"
                    if compact_level < 1:
                        if (
                            liberation_change
                            and liberation_change.change_rate_per_hour != 0
                        ):
                            planet_health_bar = f"\n{health_bar(campaign.planet.health_perc, campaign.planet.current_owner, True, anim=True, increasing=liberation_change.change_rate_per_hour > 0)}"
                        else:
                            planet_health_bar = f"\n{health_bar(campaign.planet.health_perc, campaign.planet.current_owner, True)}"
                    else:
                        planet_health_bar = ""
                    planet_health_text = f"`{(1 - (campaign.planet.health / campaign.planet.max_health)):^25.2%}`"
                    feature_text = (
                        language_json["dashboard"]["AttackEmbed"]["feature"].format(
                            feature=campaign.planet.feature
                        )
                        if campaign.planet.feature
                        else ""
                    )
                    player_count = f"**{campaign.planet.stats.player_count:,}**"
                    for region in campaign.planet.regions.values():
                        if region.is_available:
                            region_text += f"\n-# ↳ {getattr(getattr(Emojis.RegionIcons, region.owner.full_name), f'_{region.size}')} {region.type} **{region.name}** - {region.perc:.2%}"
                    self.add_field(
                        f"{getattr(Emojis.Factions, campaign.planet.current_owner.full_name.lower())} - __**{planet_names[str(campaign.planet.index)]['names'][language_json['code_long']]}**__ {exclamation}",
                        (
                            f"{language_json['dashboard']['heroes'].format(heroes=player_count)}"
                            f"{feature_text}"
                            f"{time_to_complete}"
                            f"\n{language_json['dashboard']['AttackEmbed']['planet_health']}:"
                            f"{planet_health_bar}"
                            f"\n{planet_health_text}"
                            f"{liberation_text}"
                            f"{region_text}"
                        ),
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
                    skipped_planets_text += f"-# {planet_names[str(campaign.planet.index)]['names'][language_json['code_long']]} - **{campaign.planet.stats.player_count:,}** {exclamation}\n"
                    if compact_level < 2:
                        for region in campaign.planet.regions.values():
                            if (
                                region.is_available
                                and region.players > total_players * 0.001
                            ):
                                skipped_planets_text += f"-# ↳ {getattr(getattr(Emojis.RegionIcons, region.owner.full_name), f'_{region.size}')} {region.type} **{region.name}** - {region.perc:.2%}\n"
                if skipped_planets_text != "":
                    self.add_field(
                        f"{language_json['dashboard']['AttackEmbed']['low_impact']}",
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
                    f"-# {language_json['dashboard']['FooterEmbed']['other_updated']}\n"
                    f"-# <t:{int(now.timestamp())}:f> - <t:{int(now.timestamp())}:R>\n"
                    f"||-# Data from <t:{int(data_time.timestamp())}:R>||"
                ),
                inline=False,
            )
            self.add_field(
                "",
                (
                    f"-# {language_json['dashboard']['FooterEmbed']['total_players']}\n"
                    f"-# {Emojis.Icons.steam} {steam_players:,}\n"
                    f"-# {Emojis.Icons.playstation}/{Emojis.Icons.xbox} {total_players - steam_players:,}"
                ),
                inline=False,
            )
            special_dates = {
                "liberty_day": {
                    "dates": ["26/10"],
                    "text": language_json["dashboard"]["FooterEmbed"]["liberty_day"],
                },
                "malevelon_creek_day": {
                    "dates": ["03/04"],
                    "text": language_json["dashboard"]["FooterEmbed"][
                        "malevelon_creek_day"
                    ],
                },
                "festival_of_reckoning": {
                    "dates": ["24/12", "25/12", "26/12"],
                    "text": language_json["dashboard"]["FooterEmbed"][
                        "festival_of_reckoning"
                    ],
                },
                "new_year": {
                    "dates": ["31/12", "01/01"],
                    "text": language_json["dashboard"]["FooterEmbed"]["new_year"],
                },
            }
            for details in special_dates.values():
                if now.strftime("%d/%m") in details["dates"]:
                    self.set_footer(text=details["text"])
                    break
