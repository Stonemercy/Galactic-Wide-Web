from datetime import datetime, timedelta
from data.lists import (
    SpecialUnits,
    assignment_task_images_dict,
    stratagem_id_dict,
    faction_colours,
)
from disnake import Colour, Embed
from utils.data import (
    DSS,
    Assignment,
    Campaign,
    Data,
    Planet,
    Planets,
)
from utils.emojis import Emojis
from utils.functions import health_bar, short_format
from utils.mixins import EmbedReprMixin
from utils.trackers import BaseTracker, BaseTrackerEntry


class Dashboard:
    def __init__(
        self,
        data: Data,
        language_code: str,
        json_dict: dict,
        with_health_bars: bool = True,
    ):
        language_json = json_dict["languages"][language_code]
        self.embeds: list[Embed] = []

        # Major Order embeds
        if data.assignments:
            for assignment in data.assignments:
                self.embeds.append(
                    self.MajorOrderEmbed(
                        assignment=assignment,
                        planets=data.planets,
                        liberation_changes_tracker=data.liberation_changes,
                        mo_task_tracker=data.major_order_changes,
                        language_json=language_json,
                        json_dict=json_dict,
                        with_health_bars=with_health_bars,
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
                    with_health_bars=False,
                )
            )

        # DSS Eembed
        if data.dss and data.dss.flags not in (0, 2):
            self.embeds.append(
                self.DSSEmbed(
                    dss=data.dss,
                    language_json=language_json,
                    planet_names_json=json_dict["planets"],
                )
            )

        # Defence embed
        if data.planet_events:
            eagle_storm = data.dss.get_ta_by_name("EAGLE STORM") if data.dss else None
            self.embeds.append(
                self.DefenceEmbed(
                    planet_events=data.planet_events,
                    liberation_changes=data.liberation_changes,
                    language_json=language_json,
                    planet_names=json_dict["planets"],
                    total_players=data.total_players,
                    eagle_storm=eagle_storm,
                    with_health_bars=with_health_bars,
                    gambit_planets=data.gambit_planets,
                )
            )

        # Attack embeds
        self.embeds.append(
            self.AttackEmbed(
                campaigns=[
                    campaign
                    for campaign in data.campaigns
                    if campaign.faction == "Illuminate" and not campaign.planet.event
                ],
                liberation_changes=data.liberation_changes,
                language_json=language_json,
                planet_names=json_dict["planets"],
                faction="Illuminate",
                total_players=data.total_players,
                gambit_planets=data.gambit_planets,
                with_health_bars=with_health_bars,
            )
        )
        self.embeds.append(
            self.AttackEmbed(
                campaigns=[
                    campaign
                    for campaign in data.campaigns
                    if campaign.faction == "Automaton" and not campaign.planet.event
                ],
                liberation_changes=data.liberation_changes,
                language_json=language_json,
                planet_names=json_dict["planets"],
                faction="Automaton",
                total_players=data.total_players,
                gambit_planets=data.gambit_planets,
                with_health_bars=with_health_bars,
            )
        )
        self.embeds.append(
            self.AttackEmbed(
                campaigns=[
                    campaign
                    for campaign in data.campaigns
                    if campaign.faction == "Terminids" and not campaign.planet.event
                ],
                liberation_changes=data.liberation_changes,
                language_json=language_json,
                planet_names=json_dict["planets"],
                faction="Terminids",
                total_players=data.total_players,
                gambit_planets=data.gambit_planets,
                with_health_bars=with_health_bars,
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

        if self.character_count() > 5900 or not with_health_bars:
            self.embeds = [
                embed
                for embed in self.embeds.copy()
                if type(embed) not in embeds_to_skip
            ]
            self.embeds[-1].add_field(
                "",
                f"-# *{language_json['dashboard']['shrunk_temporarily']}",
            )

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
            with_health_bars: bool,
        ):
            self.with_health_bars = with_health_bars
            self.assignment = assignment
            self.completion_timestamps = []
            super().__init__(
                colour=Colour.from_rgb(*faction_colours["MO"]),
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
                    [p.stats["playerCount"] for p in planets.values()]
                )
                task_numbers = [task.type for task in assignment.tasks]
                task_for_image = max(set(task_numbers), key=task_numbers.count)
                image_link = assignment_task_images_dict.get(
                    task_for_image,
                    "https://cdn.discordapp.com/attachments/1212735927223590974/1338186496967966720/mo_icon_liberate.png?ex=67aa2acb&is=67a8d94b&hm=aa64d3140e3d0e84f1e471906dca59c193e3db72cca0fb9ee1069740a776359a&",
                )
                if image_link:
                    self.set_thumbnail(url=image_link)
                self.add_description(assignment=assignment, language_json=language_json)
                now_timestamp = datetime.now().timestamp()
                for index, task in enumerate(assignment.tasks, start=1):
                    tracker: BaseTrackerEntry | None = mo_task_tracker.get_entry(
                        (assignment.id, index)
                    )
                    if tracker and tracker.change_rate_per_hour != 0:
                        self.completion_timestamps.append(
                            now_timestamp + tracker.seconds_until_complete
                        )
                    elif task.type == 11:
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
                        assignment.flags == 2
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
                    winning_all_tasks
                    and all(winning_all_tasks)
                    and len(winning_all_tasks)
                    == len([t for t in assignment.tasks if t.progress_perc != 1])
                ):
                    outlook_text = "Winning"
                    if {13, 15} & set([t.type for t in assignment.tasks]):
                        outlook_text += (
                            f" <t:{int(assignment.ends_at_datetime.timestamp())}:R>"
                        )
                    else:
                        oldest_time = sorted(self.completion_timestamps, reverse=True)[
                            0
                        ]
                        outlook_text += f" <t:{int(oldest_time)}:R>"

                self.add_field(
                    "",
                    f"-# {language_json['ends']} <t:{int(assignment.ends_at_datetime.timestamp())}:R>",
                    inline=False,
                )
                if outlook_text != "":
                    self.add_field("Outlook", f"{outlook_text}", inline=False)

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
                item=item_names_json[str(task.item_id)]["name"],
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
                ].format(faction=language_json["factions"][task.faction])
            field_value = ""
            if task.progress_perc != 1:
                field_value += f"{language_json['dashboard']['progress']}: **{task.progress:,.0f}**"
                if self.with_health_bars:
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
            enemy_type = enemy_dict.get(
                str(task.enemy_id), f"||UNKNOWN [{task.enemy_id}]||"
            )
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
                if self.with_health_bars:
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
                faction=language_json["factions"][task.faction],
                amount=f"{task.target:,}",
            )
            field_value = ""
            if task.progress_perc != 1:
                field_value += f"{language_json['dashboard']['progress']}: **{(task.progress):,.0f}**"
                if self.with_health_bars:
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
                    faction=language_json["factions"][task.faction]
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
                if self.with_health_bars:
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
            if task.progress_perc != 1 and planet.stats["playerCount"] > (
                self.total_players * 0.05
            ):
                field_value += language_json["dashboard"]["heroes"].format(
                    heroes=f'{planet.stats["playerCount"]:,}'
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
                        field_value += f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + planet_lib_changes.seconds_until_complete}:R>"
                    else:
                        field_value += f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['defeat'])}"
                    field_value += f"\n{language_json['dashboard']['progress']}:"
                    if self.with_health_bars:
                        field_value += f"\n{planet.event.health_bar}"
                    field_value += f"\n`{(1-planet.event.progress):^25,.2%}`"
                else:
                    if (
                        planet_lib_changes
                        and planet_lib_changes.change_rate_per_hour > 0
                    ):
                        field_value += f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + planet_lib_changes.seconds_until_complete}:R>"
                    field_value += f"\n{language_json['dashboard']['progress']}:"
                    field_value += f"\n{health_bar(planet.health_perc, 'Humans', True)}"
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
                planet_text = f" {planet_names_json[str(planet.index)]['names'][language_json['code_long']]}"
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
                ].format(faction=language_json["factions"][task.faction])
            field_value = ""
            if task.progress_perc != 1:
                if planet:
                    if planet.feature:
                        field_value += f"{language_json['dashboard']['MajorOrderEmbed']['feature']}: **{planet.feature}**"
                    field_value += f"\n{language_json['dashboard']['heroes'].format(heroes=planet.stats['playerCount'])}"
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
                            field_value += f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + planet_lib_changes.seconds_until_complete}:R>"
                        else:
                            field_value += f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['defeat'])}"
                        field_value += f"\n{language_json['dashboard']['progress']}:"
                        if self.with_health_bars:
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
                    field_value += f"\n-# {special_unit[0]} {special_unit[1]}"
                field_value += f"{language_json['dashboard']['heroes'].format(heroes=planet.stats['playerCount'])}"
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
                            field_value += f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + planet_lib_changes.seconds_until_complete}:R>"
                        else:
                            field_value += f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['defeat'])}"
                        if planet.event.required_players != 0:
                            field_value += f"\n{language_json['dashboard']['DefenceEmbed']['players_required']}: **~{planet.event.required_players:,.0f}+**"
                        field_value += f"\n{language_json['dashboard']['progress']}:"
                        if self.with_health_bars:
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
                            field_value += f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + planet_lib_changes.seconds_until_complete}:R>"
                        field_value += f"\n{language_json['dashboard']['progress']}:\n"
                        if self.with_health_bars:
                            field_value += f"{health_bar(perc=planet.health_perc, race=planet.current_owner, reverse=True)}"
                        if (
                            planet_lib_changes
                            and planet_lib_changes.change_rate_per_hour != 0
                        ):
                            change = (
                                f"{planet_lib_changes.change_rate_per_hour:+.2%}/hour"
                            )
                            field_value += f"\n`{change:^25}`"
                        field_value += f"{1 - (planet.health_perc):^25,.2%}"
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
                if self.with_health_bars:
                    field_value += health_bar(
                        perc=percent,
                        race="Automaton" if task.progress_perc != 1 else "Humans",
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
                reward_name = reward_names.get(str(reward["type"]), "Unknown")
                rewards_text += f"{reward['amount']:,} **{reward_name}s** {getattr(Emojis.Items, reward_name.replace(' ', '_').lower(), '')}\n"
            if rewards_text != "":
                self.add_field(
                    language_json["dashboard"]["MajorOrderEmbed"]["rewards"],
                    rewards_text,
                )

    class DSSEmbed(Embed, EmbedReprMixin):
        def __init__(
            self, dss: DSS | None, language_json: dict, planet_names_json: dict
        ):
            super().__init__(
                title=language_json["dss"]["title"],
                colour=Colour.from_rgb(*faction_colours["DSS"]),
            )
            self.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/1213146233825271818/1310906165823148043/DSS.png?ex=6746ec01&is=67459a81&hm=ab1c29616fd787f727848b04e44c26cc74e045b6e725c45b9dd8a902ec300757&"
            )
            faction_emojis = getattr(Emojis.Factions, dss.planet.current_owner.lower())
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
                field_name = f"{getattr(Emojis.DSS, tactical_action.name.lower().replace(' ', '_'))} {tactical_action.name.upper()}"
                status = status_dict[tactical_action.status]
                field_value = f"{language_json['dashboard']['DSSEmbed']['status']}: **{language_json['dashboard']['DSSEmbed'][status]}**"
                match status:
                    case "preparing":
                        for ta_cost in tactical_action.cost:
                            field_value += f"\n{language_json['dashboard']['DSSEmbed']['max_submitable'].format(emoji=getattr(Emojis.Items,ta_cost.item.replace(' ', '_').lower()),number=f'{ta_cost.max_per_seconds[0]:,}',item=ta_cost.item,hours=f'{ta_cost.max_per_seconds[1]/3600:.0f}')}"
                            field_value += f"\n{health_bar(ta_cost.progress,'MO')}"
                            field_value += f"\n`{ta_cost.progress:^25.2%}`"
                    case "active":
                        field_value += f"\n{language_json['ends']} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
                        desc_fmtd = tactical_action.strategic_description.replace(
                            ". ", ".\n-# "
                        )
                        field_value += f"\n-# {desc_fmtd}"
                    case "on_cooldown":
                        field_value += f"\n{language_json['dashboard']['DSSEmbed']['off_cooldown']} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
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
            language_json: dict,
            planet_names: dict,
            total_players: int,
            eagle_storm: DSS.TacticalAction | None,
            with_health_bars: bool,
            gambit_planets: dict[int, Planet],
        ):
            self.planet_names = planet_names
            self.language_json = language_json
            self.eagle_storm = eagle_storm
            self.liberation_changes = liberation_changes
            self.gambit_planets = gambit_planets
            self.total_players = total_players
            self.with_health_bars = with_health_bars
            self.now = datetime.now()
            total_players_doing_defence = (
                sum(planet.stats["playerCount"] for planet in planet_events)
                / total_players
            )
            super().__init__(
                title=f"{language_json['dashboard']['DefenceEmbed']['title']} ({total_players_doing_defence:.2%})",
                colour=Colour.blue(),
            )
            if planet_events:
                self.set_thumbnail("https://helldivers.io/img/defense.png")
                for planet in planet_events:
                    match planet.event.type:
                        case 1:
                            # Regular defence campaign
                            self.add_event_type_1(planet=planet)
                        case 2:
                            # Invasion campaign
                            self.add_event_type_2(planet=planet)
                        case 3:
                            # Siege campaign
                            self.add_event_type_3(planet=planet)
                        case _:
                            # Unknown campaigns
                            self.add_unknown_event_type()

        def add_event_type_1(self, planet: Planet):
            feature_text = ""
            outlook_text = ""
            required_players = ""
            liberation_text = ""
            regions_text = ""
            if liberation_change := self.liberation_changes.get_entry(planet.index):
                if planet.index in self.gambit_planets:
                    gambit_planet = self.gambit_planets[planet.index]
                    gambit_lib_change = self.liberation_changes.get_entry(
                        gambit_planet.index
                    )
                if liberation_change.change_rate_per_hour != 0:
                    now_seconds = int(self.now.timestamp())
                    if (
                        planet.index in self.gambit_planets
                        and gambit_lib_change.change_rate_per_hour != 0
                    ):
                        seconds_until_gambit_complete = int(
                            (
                                (100 - gambit_lib_change.value)
                                / gambit_lib_change.change_rate_per_hour
                            )
                            * 3600
                        )
                    win_time = planet.event.end_time_datetime
                    if planet.dss_in_orbit and self.eagle_storm.status == 2:
                        win_time += timedelta(
                            seconds=(
                                self.eagle_storm.status_end_datetime - self.now
                            ).total_seconds()
                        )
                    winning = (
                        datetime.fromtimestamp(
                            now_seconds + liberation_change.seconds_until_complete
                        )
                        < win_time
                    )
                    if winning:
                        outlook_text = f"\n{self.language_json['dashboard']['outlook'].format(outlook=self.language_json['victory'])} <t:{now_seconds + liberation_change.seconds_until_complete}:R>"
                    else:
                        if (
                            planet.index in self.gambit_planets
                            and gambit_lib_change.change_rate_per_hour > 0
                            and datetime.fromtimestamp(
                                now_seconds + seconds_until_gambit_complete
                            )
                            < win_time
                        ):
                            outlook_text = f"\n{self.language_json['dashboard']['outlook'].format(outlook=self.language_json['victory'])} <t:{now_seconds + seconds_until_gambit_complete}:R>"
                            outlook_text += f"\n> -# {self.language_json['dashboard']['DefenceEmbed']['thanks_to_gambit'].format(planet=gambit_planet.name)}"
                        else:
                            outlook_text = f"\n{self.language_json['dashboard']['outlook'].format(outlook=self.language_json['defeat'])}"
                            if planet.index in self.gambit_planets:
                                outlook_text += f"\n> -# {self.language_json['dashboard']['DefenceEmbed']['gambit_available'].format(planet=gambit_planet.name)}"
                    change = f"{liberation_change.change_rate_per_hour:+.2%}/hour"
                    liberation_text = f"\n`{change:^25}`"
                    if planet.event.required_players:
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
                    regions_text += f"\n-# ↳ {getattr(getattr(Emojis.RegionIcons, region.owner), f'_{region.size}')} {region.type} **{region.name}** - {region.perc:.2%}"
            if planet.feature:
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
            if self.with_health_bars:
                event_health_bar = f"\n{planet.event.health_bar}"
            else:
                event_health_bar = ""
            player_count = f'**{planet.stats["playerCount"]:,}**'
            self.add_field(
                f"{getattr(Emojis.Factions, planet.event.faction.lower())} - __**{self.planet_names[str(planet.index)]['names'][self.language_json['code_long']]}**__ {planet.exclamations}",
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

        def add_event_type_2(self, planet: Planet):
            feature_text = ""
            outlook_text = ""
            if liberation_change := self.liberation_changes.get_entry(planet.index):
                if liberation_change.change_rate_per_hour != 0:
                    now_seconds = int(self.now.timestamp())
                    win_time = planet.event.end_time_datetime
                    winning = (
                        datetime.fromtimestamp(
                            now_seconds + liberation_change.seconds_until_complete
                        )
                        < win_time
                    )
                    if winning:
                        outlook_text = f"\n{self.language_json['dashboard']['outlook'].format(outlook=self.language_json['victory'])} <t:{now_seconds + liberation_change.seconds_until_complete}:R>"
                    else:
                        outlook_text = f"\n{self.language_json['dashboard']['outlook'].format(outlook=self.language_json['defeat'])}"
                    change = f"{liberation_change.change_rate_per_hour:+.2%}/hour"
                    liberation_text = f"\n`{change:^25}`"
                    if planet.event.required_players:
                        if 0 < planet.event.required_players < 2.5 * self.total_players:
                            required_players = f"\n{self.language_json['dashboard']['DefenceEmbed']['players_required']}: **~{planet.event.required_players:,.0f}+**"
                        else:
                            one_hour_ago = self.now - timedelta(hours=1)
                            if planet.event.start_time_datetime > one_hour_ago:
                                required_players = f"\n{self.language_json['dashboard']['DefenceEmbed']['players_required']}: *Gathering Data*"
                            else:
                                required_players = f"\n{self.language_json['dashboard']['DefenceEmbed']['players_required']}: **IMPOSSIBLE**"
            if planet.feature:
                feature_text += f"{self.language_json['dashboard']['DefenceEmbed']['feature']}: **{planet.feature}**"
            if planet.event.potential_buildup != 0:
                feature_text += self.language_json["dashboard"]["DefenceEmbed"][
                    "dark_energy_remaining"
                ].format(
                    number=f"{(planet.event.remaining_dark_energy / 1_000_000):.2%}"
                )
            time_remaining = f"<t:{int(planet.event.end_time_datetime.timestamp())}:R>"
            if self.with_health_bars:
                event_health_bar = f"\n{planet.event.health_bar}"
            else:
                event_health_bar = ""
            player_count = f'**{planet.stats["playerCount"]:,}**'
            self.add_field(
                f"{getattr(Emojis.Factions, planet.event.faction.lower())} - __**{self.planet_names[str(planet.index)]['names'][self.language_json['code_long']]}**__ {planet.exclamations}",
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
                    "\u200b\n"
                ),
                inline=False,
            )

        def add_event_type_3(self, planet: Planet):
            feature_text = ""
            if planet.feature:
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
            if self.with_health_bars:
                siege_fleet_health_bar = f"\n{planet.event.siege_fleet.health_bar}"
            else:
                siege_fleet_health_bar = ""
            player_count = f'**{planet.stats["playerCount"]:,}**'
            self.add_field(
                f"{getattr(Emojis.Factions, planet.event.faction.lower())} - __**{self.planet_names[str(planet.index)]['names'][self.language_json['code_long']]}**__ {planet.exclamations}",
                (
                    f"{feature_text}"
                    f"\n{self.language_json['ends']} {time_remaining}"
                    f"\n{self.language_json['dashboard']['heroes'].format(heroes=player_count)}"
                    f"\n-# {planet.event.siege_fleet.name} strength:"
                    f"{siege_fleet_health_bar}"
                    f"\n`{(planet.event.siege_fleet.perc):^25,.2%}`"
                    "\u200b\n"
                ),
                inline=False,
            )

        def add_unknown_event_type(self, planet: Planet):
            self.add_field(
                f"{Emojis.Decoration.alert_icon} NEW DEFENCE TYPE",
                (
                    f"-# {planet.event.type}|{planet.event.health}/{planet.event.max_health}\n"
                    f"{planet.event.siege_fleet or ''}"
                ),
                inline=False,
            )

    class AttackEmbed(Embed, EmbedReprMixin):
        def __init__(
            self,
            campaigns: list[Campaign],
            liberation_changes: BaseTracker,
            language_json: dict,
            planet_names: dict,
            faction: str,
            total_players: int,
            gambit_planets: dict[int, Planet],
            with_health_bars: bool,
        ):
            super().__init__(
                title=language_json["dashboard"]["AttackEmbed"]["title"].format(
                    faction=language_json["factions"][faction]
                ),
                colour=Colour.from_rgb(*faction_colours[faction]),
            )
            self.set_thumbnail("https://helldivers.io/img/attack.png")
            total_players_doing_faction = (
                sum(campaign.planet.stats["playerCount"] for campaign in campaigns)
                / total_players
            )
            self.title += f" ({total_players_doing_faction:.2%})"
            skipped_campaigns: list[Campaign] = []
            for campaign in campaigns:
                if campaign.planet.stats["playerCount"] < total_players * 0.05:
                    skipped_campaigns.append(campaign)
                    continue
                else:
                    time_to_complete = ""
                    change = ""
                    liberation_text = ""
                    region_text = ""
                    if liberation_change := liberation_changes.get_entry(
                        key=campaign.planet.index
                    ):
                        if liberation_change.change_rate_per_hour > 0:
                            now_seconds = int(datetime.now().timestamp())
                            time_to_complete = f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + liberation_change.seconds_until_complete}:R>"
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
                    if with_health_bars:
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
                    player_count = f'**{campaign.planet.stats["playerCount"]:,}**'
                    for region in campaign.planet.regions.values():
                        if region.is_available:
                            region_text += f"\n-# ↳ {getattr(getattr(Emojis.RegionIcons, region.owner), f'_{region.size}')} {region.type} **{region.name}** - {region.perc:.2%}"
                    self.add_field(
                        f"{getattr(Emojis.Factions, campaign.planet.current_owner.lower())} - __**{planet_names[str(campaign.planet.index)]['names'][language_json['code_long']]}**__ {exclamation}",
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
                    skipped_planets_text += f"-# {planet_names[str(campaign.planet.index)]['names'][language_json['code_long']]} - **{campaign.planet.stats['playerCount']:,}** {exclamation}\n"
                    for region in campaign.planet.regions.values():
                        if region.is_available:
                            skipped_planets_text += f"-# ↳ {getattr(getattr(Emojis.RegionIcons, region.owner), f'_{region.size}')} {region.type} **{region.name}** - {region.perc:.2%}\n"
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
                    f"-# {Emojis.Icons.playstation} {total_players - steam_players:,}"
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
