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
    DarkEnergy,
    Data,
    Planet,
    Planets,
    TheGreatHost,
)
from utils.emojis import Emojis
from utils.functions import health_bar, short_format
from utils.mixins import EmbedReprMixin
from utils.trackers import LiberationChangesTracker


class Dashboard:
    def __init__(
        self,
        data: Data,
        language_code: str,
        json_dict: dict,
        with_health_bars: bool = True,
    ):
        language_json = json_dict["languages"][language_code]
        self._major_order_embed = self.MajorOrderEmbed(
            assignment=data.assignment,
            planets=data.planets,
            liberation_changes=data.liberation_changes,
            language_json=language_json,
            json_dict=json_dict,
            with_health_bars=with_health_bars,
        )
        self._dss_embed = self.DSSEmbed(
            dss=data.dss,
            language_json=language_json,
            planet_names_json=json_dict["planets"],
        )
        eagle_storm = (
            data.dss.get_ta_by_name("EAGLE STORM") if data.dss != None else None
        )
        self._defence_embed = self.DefenceEmbed(
            planet_events=data.planet_events,
            liberation_changes=data.liberation_changes,
            language_json=language_json,
            planet_names=json_dict["planets"],
            total_players=data.total_players,
            eagle_storm=eagle_storm,
            with_health_bars=with_health_bars,
            gambit_planets=data.gambit_planets,
            the_great_host=data.global_resources.the_great_host,
        )
        self._illuminate_embed = self.AttackEmbed(
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
        self._automaton_embed = self.AttackEmbed(
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
        self._terminids_embed = self.AttackEmbed(
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
        self._footer_embed = self.FooterEmbed(
            language_json=language_json,
            total_players=data.total_players,
            data_time=data.fetched_at,
        )
        self.embeds = [
            self._major_order_embed,
            self._dss_embed,
            self._defence_embed,
            self._illuminate_embed,
            self._automaton_embed,
            self._terminids_embed,
            self._footer_embed,
        ]
        if data.global_resources != None:
            if data.global_resources.dark_energy:
                remaining_de = sum(
                    [
                        planet.event.remaining_dark_energy
                        for planet in data.planet_events
                        if planet.event.potential_buildup != 0
                    ]
                )
                active_invasions = len(
                    [planet for planet in data.planet_events if planet.event.type == 2]
                )
                self._dark_energy_embed = self.DarkEnergyEmbed(
                    data.global_resources.dark_energy,
                    remaining_de,
                    active_invasions,
                    data.dark_energy_changes,
                    language_json,
                )
                self.embeds.insert(2, self._dark_energy_embed)
            if data.global_resources.the_great_host:
                self._the_great_host_embed = self.TheGreatHostEmbed(
                    data.global_resources.the_great_host,
                    data.the_great_host_changes,
                    language_json,
                )
                self.embeds.insert(2, self._the_great_host_embed)

        for embed in self.embeds.copy():
            if len(embed.fields) == 0:
                self.embeds.remove(embed)
            else:
                embed.set_image(
                    "https://i.imgur.com/cThNy4f.png"
                )  # blank line (max size, dont change)
        embeds_to_skip = (self.TheGreatHostEmbed, self.DarkEnergyEmbed, self.DSSEmbed)
        if self.character_count() > 5900 or not with_health_bars:
            self.embeds = [
                embed
                for embed in self.embeds.copy()
                if type(embed) not in embeds_to_skip
            ]
            self.embeds[-1].add_field(
                "",
                "-# *Character count exceeded 6000, dashboard shrunk temporarily",
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
            planets: Planets,
            liberation_changes: LiberationChangesTracker,
            language_json: dict,
            json_dict: dict,
            with_health_bars: bool,
        ):
            self.with_health_bars = with_health_bars
            super().__init__(
                title=language_json["dashboard"]["MajorOrderEmbed"]["title"],
                colour=Colour.from_rgb(*faction_colours["MO"]),
            )
            if not assignment:
                self.add_field(
                    name="",
                    value=language_json["major_order"]["MO_unavailable"],
                )
            else:
                task_numbers = [task.type for task in assignment.tasks]
                task_for_image = max(set(task_numbers), key=task_numbers.count)
                image_link = assignment_task_images_dict.get(task_for_image, None)
                if image_link:
                    self.set_thumbnail(url=image_link)
                self.add_description(assignment=assignment, language_json=language_json)
                for task in assignment.tasks:
                    match task.type:
                        case 2:
                            self.add_type_2(
                                task=task,
                                language_json=language_json,
                                item_names_json=json_dict["items"]["item_names"],
                                planet_names_json=json_dict["planets"],
                                planet=planets[task.values[8]],
                            )
                        case 3:
                            self.add_type_3(
                                task=task,
                                language_json=language_json,
                                species_dict=json_dict["enemies"]["enemy_ids"],
                                planet_names=json_dict["planets"],
                            )
                        case 9:
                            self.add_type_9(task=task, language_json=language_json)
                        case 11:
                            self.add_type_11(
                                language_json=language_json,
                                planet=planets[task.values[2]],
                                planet_names_json=json_dict["planets"],
                                liberation_changes=liberation_changes,
                            )
                        case 12:
                            self.add_type_12(
                                task=task,
                                language_json=language_json,
                                liberation_changes=liberation_changes,
                                planet_names_json=json_dict["planets"],
                                planet=(
                                    planets[task.values[3]]
                                    if task.values[3] != 0
                                    else None
                                ),
                            )
                        case 13:
                            self.add_type_13(
                                task=task,
                                language_json=language_json,
                                planet=planets[task.values[2]],
                                liberation_changes=liberation_changes,
                                planet_names_json=json_dict["planets"],
                            )
                        case 15:
                            self.add_type_15(task=task, language_json=language_json)
                        case _:
                            self.add_field(
                                name=f"{Emojis.Decoration.alert_icon} UNRECOGNIZED TASK",
                                value=(
                                    f"-# ||{task.type}@"
                                    f"{'|'.join(str(v) for v in task.values)}-"
                                    f"{'|'.join(str(vt) for vt in task.value_types)}||"
                                ),
                                inline=False,
                            )
                    if assignment.flags == 1 and len(assignment.tasks) > 1:
                        self.add_field("or", "", inline=False)

                self.add_rewards(
                    rewards=assignment.rewards,
                    language_json=language_json,
                    reward_names=json_dict["items"]["reward_types"],
                )
                self.add_field(
                    language_json["ends"],
                    f"<t:{int(datetime.fromisoformat(assignment.ends_at).timestamp())}:R>",
                )

        def add_type_2(
            self,
            task: Assignment.Task,
            language_json: dict,
            item_names_json: dict,
            planet_names_json: dict,
            planet: Planet,
        ):
            """Extract with certain items from a certain planet"""
            name = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                "type2"
            ].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                amount=short_format(task.values[2]),
                item=item_names_json[str(task.values[4])]["name"],
                planet=planet_names_json[str(planet.index)]["names"][
                    language_json["code_long"]
                ],
            )
            if self.with_health_bars:
                task_health_bar = f"{task.health_bar}\n"
            else:
                task_health_bar = ""
            value = (
                ""
                if task.progress_perc == 1
                else (
                    f"{language_json['dashboard']['progress']}: **{task.progress:,.0f}**\n"
                    f"{task_health_bar}"
                    f"`{(task.progress_perc):^25,.2%}`\n"
                )
            )
            self.add_field(
                name=name,
                value=value,
                inline=False,
            )

        def add_type_3(
            self,
            task: Assignment.Task,
            language_json: dict,
            species_dict: dict,
            planet_names: dict,
        ):
            """Kill enemies of a type {on {planet}}"""
            species = (
                species_dict.get(str(task.values[3]), "Unknown")
                if task.values[3] != 0
                else None
            )
            target = (
                language_json["factions"][str(task.values[0])]
                if not species
                else species
            )
            full_task = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                "type3"
            ].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    else Emojis.Icons.mo_task_incomplete
                ),
                amount=short_format(task.values[2]),
                target=target,
            )
            if task.values[5] != 0:
                weapon_to_use = stratagem_id_dict.get(task.values[5], "Unknown")
                full_task += language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type3_weapon"
                ].format(weapon_to_use=weapon_to_use)
            if task.values[9] != 0:
                planet_to_use = planet_names[str(task.values[9])]["names"][
                    language_json["code_long"]
                ]
                full_task += language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type3_planet"
                ].format(planet=planet_to_use)
            if self.with_health_bars:
                task_health_bar = f"{task.health_bar}\n"
            else:
                task_health_bar = ""
            self.add_field(
                name=full_task,
                value=(
                    (
                        f"{language_json['dashboard']['progress']}: **{(task.progress):,.0f}**\n"
                        f"{task_health_bar}"
                        f"`{(task.progress_perc):^25,.2%}`"
                    )
                    if task.progress_perc != 1
                    else ""
                ),
                inline=False,
            )

        def add_type_9(self, task: Assignment.Task, language_json: dict):
            """Complete an Operation against {faction} on {difficulty} or higher {amount} times"""
            faction = language_json["factions"][str(task.values[0])]
            amount = f"{task.values[1]:,}"
            difficulty = language_json["difficulty"][str(task.values[3])]
            status_emoji = (
                Emojis.Icons.mo_task_complete
                if task.progress_perc == 1
                else Emojis.Icons.mo_task_incomplete
            )
            full_task = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                "type9"
            ].format(
                status_emoji=status_emoji,
                faction=faction,
                difficulty=difficulty,
                amount=amount,
            )
            if self.with_health_bars:
                task_health_bar = f"{task.health_bar}\n"
            else:
                task_health_bar = ""
            self.add_field(
                name=full_task,
                value=(
                    (
                        f"{language_json['dashboard']['progress']}: **{(task.progress):,.0f}**\n"
                        f"{task_health_bar}"
                        f"`{(task.progress_perc):^25,.2%}`"
                    )
                    if task.progress_perc != 1
                    else ""
                ),
                inline=False,
            )

        def add_type_11(
            self,
            language_json: dict,
            planet: Planet,
            planet_names_json: dict,
            liberation_changes: LiberationChangesTracker,
        ):
            """Liberate a planet"""
            if (planet.current_owner == "Humans" and not planet.event) or (
                planet.current_owner == "Humans"
                and planet.event
                and planet.event.type == 2
            ):
                obj_text = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type11"
                ].format(
                    status_emoji=Emojis.Icons.mo_task_complete,
                    planet=planet_names_json[str(planet.index)]["names"][
                        language_json["code_long"]
                    ],
                )
                self.add_field(name=obj_text, value="", inline=False)
            else:
                obj_text = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type11"
                ].format(
                    status_emoji=Emojis.Icons.mo_task_incomplete,
                    planet=planet_names_json[str(planet.index)]["names"][
                        language_json["code_long"]
                    ],
                )
                value_text = ""
                if planet.stats["playerCount"] > 1000:
                    value_text += language_json["dashboard"]["heroes"].format(
                        heroes=f'{planet.stats["playerCount"]:,}'
                    )
                    if planet.feature:
                        value_text += f"\n{language_json['dashboard']['MajorOrderEmbed']['feature']}: **{planet.feature}**\n"
                    planet_lib_changes = liberation_changes.get_by_index(planet.index)
                    if planet_lib_changes and planet_lib_changes.rate_per_hour > 0.01:
                        now_seconds = int(datetime.now().timestamp())
                        if planet.event:
                            winning = (
                                now_seconds + planet_lib_changes.seconds_until_complete
                                < planet.event.end_time_datetime.timestamp()
                            )
                            value_text += f"{language_json['ends']} <t:{planet.event.end_time_datetime.timestamp():.0f}:R>"
                            if winning:
                                value_text += f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + planet_lib_changes.seconds_until_complete}:R>"
                            else:
                                value_text += f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['defeat'])}"
                            value_text += f"\n{language_json['dashboard']['progress']}:"
                            value_text += f"\n{health_bar(planet.event.progress, planet.event.faction, True)}"
                            value_text += f"\n`{(1-planet.event.progress):^25,.2%}`"
                        else:
                            value_text += f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + planet_lib_changes.seconds_until_complete}:R>"
                            value_text += f"\n{language_json['dashboard']['progress']}:"
                            value_text += f"\n{health_bar(planet.health_perc, planet.current_owner, True)}"
                            value_text += f"\n`{(planet.health_perc):^25,.2%}`"
                        change = f"{planet_lib_changes.rate_per_hour:+.2f}%/hour"
                        value_text += f"\n`{change:^25}`"
                    self.add_field(
                        name=obj_text,
                        value=value_text,
                        inline=False,
                    )
                else:
                    self.add_field(
                        name=obj_text,
                        value=value_text,
                        inline=False,
                    )

        def add_type_12(
            self,
            task: Assignment.Task,
            language_json: dict,
            liberation_changes: LiberationChangesTracker,
            planet_names_json: dict,
            planet: Planet | None,
        ):
            """Succeed in defence of # <enemy> planets"""
            if planet:
                outlook_text = ""
                required_players = ""
                liberation_text = ""
                planet_lib_changes = liberation_changes.get_by_index(planet.index)
                if planet_lib_changes and planet_lib_changes.rate_per_hour != 0:
                    now_seconds = int(datetime.now().timestamp())
                    winning = (
                        datetime.fromtimestamp(
                            now_seconds + planet_lib_changes.seconds_until_complete
                        )
                        < planet.event.end_time_datetime
                    )
                    if winning:
                        outlook_text = f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + planet_lib_changes.seconds_until_complete}:R>"
                    else:
                        outlook_text = f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['defeat'])}"
                    change = f"{planet_lib_changes.rate_per_hour:+.2f}%/hour"
                    liberation_text = f"`{change:^25}`"
                    if planet.event.required_players != 0:
                        required_players = f"\n{language_json['dashboard']['DefenceEmbed']['players_required']}: **~{planet.event.required_players:,.0f}+**"
                time_remaining = (
                    f"<t:{planet.event.end_time_datetime.timestamp():.0f}:R>"
                )
                objective_text = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type12_with_planet"
                ].format(
                    status_emoji=(
                        Emojis.Icons.mo_task_complete
                        if task.progress_perc == 1
                        else Emojis.Icons.mo_task_incomplete
                    ),
                    planet=planet_names_json[str(planet.index)]["names"][
                        language_json["code_long"]
                    ],
                    number=task.values[0],
                    faction=language_json["factions"][str(task.values[1])],
                )
                feature_text = (
                    ""
                    if not planet.feature
                    else f"{language_json['dashboard']['MajorOrderEmbed']['feature']}: **{planet.feature}**"
                )
                player_count = (
                    language_json["dashboard"]["heroes"].format(
                        heroes=f"{planet.stats['playerCount']:,}"
                    )
                    if task.progress_perc != 1
                    else ""
                )
                if self.with_health_bars:
                    task_health_bar = (
                        f"\n{language_json['dashboard']['progress']}:\n"
                        f"{health_bar(perc=planet.event.progress, race=planet.event.faction, reverse=True)} 🛡️\n"
                        f"`{1 - planet.event.progress:^25,.2%}`\n"
                    )
                else:
                    task_health_bar = ""
                self.add_field(
                    objective_text,
                    (
                        f"{feature_text}"
                        f"\n{player_count}"
                        f"\n{language_json['ends']} {time_remaining}"
                        f"\n{language_json['dashboard']['DefenceEmbed']['level']} {int(planet.event.max_health / 50000)}"
                        f"{outlook_text}"
                        f"{required_players}"
                        f"{task_health_bar}"
                        f"{liberation_text}"
                    ),
                    inline=False,
                )
            else:
                objective_text = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type12_without_planet"
                ].format(
                    status_emoji=(
                        Emojis.Icons.mo_task_complete
                        if task.progress_perc == 1
                        else Emojis.Icons.mo_task_incomplete
                    ),
                    number=task.values[0],
                    faction=language_json["factions"][str(task.values[1])],
                )
                if self.with_health_bars and task.progress_perc != 1:
                    task_health_bar = (
                        f"{language_json['dashboard']['progress']}: {int(task.progress)}/{task.values[0]}\n"
                        f"{task.health_bar}\n"
                        f"`{(task.progress_perc):^25,.2%}`\n"
                    )
                else:
                    task_health_bar = ""
                self.add_field(
                    objective_text,
                    f"{task_health_bar}",
                    inline=False,
                )

        def add_type_13(
            self,
            task: Assignment.Task,
            language_json: dict,
            planet: Planet,
            liberation_changes: LiberationChangesTracker,
            planet_names_json: dict,
        ):
            """Hold a planet until the end of the MO"""
            feature_text = (
                ""
                if not planet.feature
                else f"{language_json['dashboard']['MajorOrderEmbed']['feature']}: **{planet.feature}**"
            )
            for special_unit in SpecialUnits.get_from_effects_list(
                active_effects=planet.active_effects
            ):
                feature_text += f"{special_unit[0]} {special_unit[1]}"
            obj_text = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                "type13"
            ].format(
                status_emoji=(
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc == 1
                    or (not planet.event and planet.current_owner == "Humans")
                    else Emojis.Icons.mo_task_incomplete
                ),
                planet=planet_names_json[str(planet.index)]["names"][
                    language_json["code_long"]
                ],
            )
            player_count = (
                language_json["dashboard"]["heroes"].format(
                    heroes=f"{planet.stats['playerCount']:,}"
                )
                if task.progress_perc != 1 or planet.event
                else ""
            )
            if planet.event:
                outlook_text = ""
                required_players = ""
                liberation_text = ""
                planet_lib_changes = liberation_changes.get_by_index(planet.index)
                if planet_lib_changes and planet_lib_changes.rate_per_hour != 0:
                    now_seconds = int(datetime.now().timestamp())
                    winning = (
                        datetime.fromtimestamp(
                            now_seconds + planet_lib_changes.seconds_until_complete
                        )
                        < planet.event.end_time_datetime
                    )
                    if winning:
                        outlook_text = f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + planet_lib_changes.seconds_until_complete}:R>"
                    else:
                        outlook_text = f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['defeat'])}"
                    change = f"{planet_lib_changes.rate_per_hour:+.2f}%/hour"
                    liberation_text = f"\n`{change:^25}`"
                    if planet.event.required_players != 0:
                        required_players = f"\n{language_json['dashboard']['DefenceEmbed']['players_required']}: **~{planet.event.required_players:,.0f}+**"
                time_remaining = (
                    f"<t:{planet.event.end_time_datetime.timestamp():.0f}:R>"
                )
                if self.with_health_bars:
                    task_health_bar = f"{health_bar(perc=planet.event.progress, race=planet.event.faction, reverse=True)} 🛡️"
                else:
                    task_health_bar = ""
                self.add_field(
                    obj_text,
                    (
                        f"{feature_text}"
                        f"\n{language_json['ends']} {time_remaining}"
                        f"\n{language_json['dashboard']['DefenceEmbed']['level']} **{int(planet.event.max_health / 50000)}**"
                        f"{outlook_text}"
                        f"\n{player_count}"
                        f"{required_players}"
                        f"\n{language_json['dashboard']['progress']}:\n"
                        f"{task_health_bar}"
                        f"\n`{1 - planet.event.progress:^25,.2%}`"
                        f"{liberation_text}"
                    ),
                    inline=False,
                )
            else:
                if task.progress_perc == 1 or planet.current_owner == "Humans":
                    self.add_field(obj_text, "", inline=False)
                else:
                    outlook_text = ""
                    liberation_text = ""
                    planet_lib_changes = liberation_changes.get_by_index(planet.index)
                    if planet_lib_changes and planet_lib_changes.rate_per_hour != 0:
                        if planet_lib_changes.rate_per_hour > 0:
                            now_seconds = int(datetime.now().timestamp())
                            outlook_text = f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + planet_lib_changes.seconds_until_complete}:R>"
                        change = f"{planet_lib_changes.rate_per_hour:+.2f}%/hour"
                        liberation_text = f"\n`{change:^25}`"
                    completed = (
                        f"**{language_json['dashboard']['MajorOrderEmbed']['liberated']}**"
                        if planet.current_owner == "Humans"
                        else ""
                    )
                    health_text = (
                        f"{1 - (planet.health_perc):^25,.2%}"
                        if planet.current_owner != "Humans"
                        else f"{(planet.health_perc):^25,.2%}"
                    )
                    if self.with_health_bars:
                        task_health_bar = f"{health_bar(perc=planet.health_perc,race=planet.current_owner, reverse=True if planet.current_owner != 'Humans' else False)} {completed}"
                    else:
                        task_health_bar = ""
                    self.add_field(
                        obj_text,
                        (
                            f"{feature_text}"
                            f"{outlook_text}"
                            f"\n{player_count}"
                            f"\n{language_json['dashboard']['progress']}:\n"
                            f"{task_health_bar}"
                            f"\n`{health_text}`"
                            f"{liberation_text}"
                        ),
                        inline=False,
                    )

        def add_type_15(self, task: Assignment.Task, language_json: dict):
            """Win more campaigns than lost"""
            clamped_progress = max(min(task.progress, 5), -5)
            percent = (clamped_progress + 5) / 10
            event_health_bar = (
                ""
                if not self.with_health_bars
                else health_bar(
                    perc=percent,
                    race="Humans" if task.progress_perc >= 1 else "Automaton",
                )
            )
            self.add_field(
                name=language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type15"
                ].format(
                    status_emoji=(
                        Emojis.Icons.mo_task_complete
                        if task.progress_perc >= 1
                        else Emojis.Icons.mo_task_incomplete
                    )
                ),
                value=(f"{event_health_bar}\n" f"`{task.progress_perc:^25,}`\n"),
                inline=False,
            )

        def add_description(self, assignment: Assignment, language_json: dict):
            self.add_field(
                name=assignment.title, value=assignment.description, inline=False
            )
            self.set_footer(
                text=language_json["message"].format(message_id=assignment.id)
            )

        def add_rewards(self, rewards: dict, language_json: dict, reward_names: dict):
            rewards_text = ""
            for reward in rewards:
                reward_name = reward_names.get(str(reward["type"]), "Unknown")
                rewards_text += f"{reward['amount']:,} **{reward_name}s** {getattr(Emojis.Items, reward_name.replace(' ', '_').lower(), '')}\n"
            self.add_field(
                language_json["dashboard"]["MajorOrderEmbed"]["rewards"], rewards_text
            )

    class DSSEmbed(Embed, EmbedReprMixin):
        def __init__(
            self, dss: DSS | None, language_json: dict, planet_names_json: dict
        ):
            super().__init__(
                title=language_json["dss"]["title"],
                colour=Colour.from_rgb(*faction_colours["DSS"]),
            )
            if dss != None and type(dss) != str:
                self.set_thumbnail(
                    url="https://cdn.discordapp.com/attachments/1213146233825271818/1310906165823148043/DSS.png?ex=6746ec01&is=67459a81&hm=ab1c29616fd787f727848b04e44c26cc74e045b6e725c45b9dd8a902ec300757&"
                )
                faction_emojis = getattr(
                    Emojis.Factions, dss.planet.current_owner.lower()
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

                for tactical_action in dss.tactical_actions:
                    tactical_action: DSS.TacticalAction
                    ta_health_bar = health_bar(
                        tactical_action.cost.progress,
                        "MO" if tactical_action.cost.progress != 1 else "Humans",
                    )
                    status = {1: "preparing", 2: "active", 3: "on_cooldown"}[
                        tactical_action.status
                    ]
                    if status == "preparing":
                        submittable_formatted = language_json["dashboard"]["DSSEmbed"][
                            "max_submitable"
                        ].format(
                            emoji=getattr(
                                Emojis.Items,
                                tactical_action.cost.item.replace(" ", "_").lower(),
                            ),
                            number=f"{tactical_action.cost.max_per_seconds[0]:,}",
                            item=tactical_action.cost.item,
                            hours=f"{tactical_action.cost.max_per_seconds[1]/3600:.0f}",
                        )
                        cost = (
                            f"{submittable_formatted}\n"
                            f"{ta_health_bar}\n"
                            f"`{tactical_action.cost.progress:^25.2%}`"
                        )
                    elif status == "active":
                        cost = f"{language_json['ends']} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>\n"
                        formatted_desc = tactical_action.strategic_description.replace(
                            ". ", ".\n-# "
                        )
                        cost += f"-# {formatted_desc}"
                    elif status == "on_cooldown":
                        cost = f"{language_json['dashboard']['DSSEmbed']['off_cooldown'].capitalize()} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
                    self.add_field(
                        f"{getattr(Emojis.DSS, tactical_action.name.lower().replace(' ', '_'))} {tactical_action.name.title()}",
                        (
                            f"{language_json['dashboard']['DSSEmbed']['status']}: **{language_json['dashboard']['DSSEmbed'][status].capitalize()}**\n"
                            f"{cost}"
                        ),
                        inline=False,
                    )

    class DarkEnergyEmbed(Embed, EmbedReprMixin):
        def __init__(
            self,
            dark_energy_resource: DarkEnergy,
            total_de_available: int,
            active_invasions: int,
            dark_energy_changes: dict[str:int, str:list],
            language_json: dict,
        ):
            super().__init__(
                title=language_json["dashboard"]["DarkEnergyEmbed"]["title"],
                description=language_json["dashboard"]["DarkEnergyEmbed"][
                    "description"
                ],
                colour=Colour.from_rgb(106, 76, 180),
            )
            rate_per_hour = sum(dark_energy_changes["changes"]) * 12
            rate = f"{rate_per_hour:+.2%}/hr"
            completion_timestamp = ""
            now_seconds = int(datetime.now().timestamp())
            if rate_per_hour != 0:
                seconds_until_end = (
                    int(((1 - dark_energy_changes["total"]) / rate_per_hour) * 3600)
                    if rate_per_hour > 0
                    else int((dark_energy_changes["total"] / abs(rate_per_hour)) * 3600)
                )
                completion_timestamp = language_json["dashboard"]["DarkEnergyEmbed"][
                    "reaches"
                ].format(
                    number=100 if rate_per_hour > 0 else 0,
                    timestamp=(now_seconds + seconds_until_end),
                )
                self.add_field(
                    "",
                    f"{dark_energy_resource.health_bar}\n**`{dark_energy_resource.perc:^25.3%}`**\n**`{rate:^25}`**",
                    inline=False,
                )
                warning = ""
                if (
                    (total_de_available / dark_energy_resource.max_value)
                    + dark_energy_resource.perc
                ) > 1:
                    warning = ":warning:"
                active_invasions_fmt = language_json["dashboard"]["DarkEnergyEmbed"][
                    "active_invasions"
                ].format(number=active_invasions)
                total_to_be_harvested = language_json["dashboard"]["DarkEnergyEmbed"][
                    "total_to_be_harvested"
                ].format(
                    warning=warning,
                    number=f"{(total_de_available / dark_energy_resource.max_value):.2%}",
                )
                self.add_field(
                    "",
                    (
                        f"{completion_timestamp}\n"
                        f"{active_invasions_fmt}\n"
                        f"{total_to_be_harvested}"
                    ),
                )
            else:
                self.add_field(f"**MERIDIA IS STATIONARY** {Emojis.Icons.victory}", "")
            self.set_thumbnail(
                url="https://cdn.discordapp.com/emojis/1331357764039086212.webp?size=96"
            )

    class TheGreatHostEmbed(Embed, EmbedReprMixin):
        def __init__(
            self,
            the_great_host_resource: TheGreatHost,
            the_great_host_changes: dict[str:int, str:list],
            language_json: dict,
        ):
            super().__init__(
                title="The Great Host",
                description="-# The Illuminate invasion fleet, constructed in secret behind the veil of the Meridian Wormhole. It is headed for Super Earth itself.",
                colour=Colour.from_rgb(*faction_colours["Illuminate"]),
            )
            rate_per_hour = sum(the_great_host_changes["changes"]) * 12
            rate = f"{rate_per_hour:+.2%}/hr"
            completion_timestamp = None
            now_seconds = int(datetime.now().timestamp())
            if rate_per_hour != 0:
                seconds_until_depleted = (
                    int(((1 - the_great_host_changes["total"]) / rate_per_hour) * 3600)
                    if rate_per_hour > 0
                    else int(
                        (the_great_host_changes["total"] / abs(rate_per_hour)) * 3600
                    )
                )
                completion_timestamp = language_json["dashboard"]["DarkEnergyEmbed"][
                    "reaches"
                ].format(
                    number=100 if rate_per_hour > 0 else 0,
                    timestamp=(now_seconds + seconds_until_depleted),
                )
            self.add_field(
                "",
                (
                    f"{the_great_host_resource.health_bar}\n"
                    f"**`{the_great_host_resource.perc:^25.3%}`**\n"
                    f"**`{rate:^25}`**"
                ),
                inline=False,
            )
            if completion_timestamp:
                self.add_field(
                    "",
                    (f"-# {completion_timestamp}\n"),
                )
            self.set_thumbnail(
                url="https://cdn.discordapp.com/emojis/1334887870305144883.webp?size=96"
            )

    class DefenceEmbed(Embed, EmbedReprMixin):
        def __init__(
            self,
            planet_events: list[Planet],
            liberation_changes: LiberationChangesTracker,
            language_json: dict,
            planet_names: dict,
            total_players: int,
            eagle_storm: DSS.TacticalAction | None,
            with_health_bars: bool,
            gambit_planets: dict[int, Planet],
            the_great_host: TheGreatHost | None,
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
                            # Siege campaign (?)
                            self.add_event_type_3(
                                planet=planet, the_great_host=the_great_host
                            )
                        case 4:
                            # Hold Locations campaign
                            self.add_event_type_4()
            else:
                self.add_field(
                    language_json["dashboard"]["DefenceEmbed"]["no_threats"],
                    f"||{language_json['dashboard']['DefenceEmbed']['for_now']}||",
                )

        def add_event_type_1(self, planet: Planet):
            feature_text = ""
            outlook_text = ""
            required_players = ""
            liberation_text = ""
            if self.liberation_changes.has_data:
                liberation_change = self.liberation_changes.get_by_index(planet.index)
                if planet.index in self.gambit_planets:
                    gambit_planet = self.gambit_planets[planet.index]
                    gambit_lib_change = self.liberation_changes.get_by_index(
                        gambit_planet.index
                    )
                if liberation_change and liberation_change.rate_per_hour != 0:
                    now_seconds = int(self.now.timestamp())
                    if (
                        planet.index in self.gambit_planets
                        and gambit_lib_change.rate_per_hour != 0
                    ):
                        seconds_until_gambit_complete = int(
                            (
                                (100 - gambit_lib_change.liberation)
                                / gambit_lib_change.rate_per_hour
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
                            and gambit_lib_change.rate_per_hour > 0
                            and datetime.fromtimestamp(
                                now_seconds + seconds_until_gambit_complete
                            )
                            < win_time
                        ):
                            outlook_text = f"\n{self.language_json['dashboard']['outlook'].format(outlook=self.language_json['victory'])} <t:{now_seconds + seconds_until_gambit_complete}:R>"
                            outlook_text += (
                                f"\n> -# thanks to **{gambit_planet.name}** liberation"
                            )
                        else:
                            outlook_text = f"\n{self.language_json['dashboard']['outlook'].format(outlook=self.language_json['defeat'])}"
                            if planet.index in self.gambit_planets:
                                outlook_text += f"\n> -# :chess_pawn: Can be ended by liberating **{gambit_planet.name}**"
                    change = f"{liberation_change.rate_per_hour:+.2f}%/hour"
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
                    "\u200b\n"
                ),
                inline=False,
            )

        def add_event_type_2(self, planet: Planet):
            feature_text = ""
            outlook_text = ""
            if self.liberation_changes.has_data:
                liberation_change = self.liberation_changes.get_by_index(planet.index)
                if liberation_change and liberation_change.rate_per_hour != 0:
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
                    change = f"{liberation_change.rate_per_hour:+.2f}%/hour"
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

        def add_event_type_3(self, planet: Planet, the_great_host: TheGreatHost | None):
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
                the_great_host_health_bar = f"\n{the_great_host.health_bar}"
            else:
                the_great_host_health_bar = ""
            player_count = f'**{planet.stats["playerCount"]:,}**'
            self.add_field(
                f"{getattr(Emojis.Factions, planet.event.faction.lower())} - __**{self.planet_names[str(planet.index)]['names'][self.language_json['code_long']]}**__ {planet.exclamations}",
                (
                    f"{feature_text}"
                    f"\n{self.language_json['ends']} {time_remaining}"
                    f"\n{self.language_json['dashboard']['heroes'].format(heroes=player_count)}"
                    f"\nThe Great Host strength:"
                    f"{the_great_host_health_bar}"
                    f"\n`{(the_great_host.perc):^25,.2%}`"
                    "\u200b\n"
                ),
                inline=False,
            )

        def add_event_type_3(self, planet: Planet, the_great_host: TheGreatHost | None):
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
                the_great_host_health_bar = f"\n{the_great_host.health_bar}"
            else:
                the_great_host_health_bar = ""
            player_count = f'**{planet.stats["playerCount"]:,}**'
            self.add_field(
                f"{getattr(Emojis.Factions, planet.event.faction.lower())} - __**{self.planet_names[str(planet.index)]['names'][self.language_json['code_long']]}**__ {planet.exclamations}",
                (
                    f"{feature_text}"
                    f"\n{self.language_json['ends']} {time_remaining}"
                    f"\n{self.language_json['dashboard']['heroes'].format(heroes=player_count)}"
                    f"\nThe Great Host strength:"
                    f"{the_great_host_health_bar}"
                    f"\n`{(the_great_host.perc):^25,.2%}`"
                    "\u200b\n"
                ),
                inline=False,
            )

    class AttackEmbed(Embed, EmbedReprMixin):
        def __init__(
            self,
            campaigns: list[Campaign],
            liberation_changes: LiberationChangesTracker,
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
                    if liberation_changes.has_data:
                        liberation_change = liberation_changes.get_by_index(
                            campaign.planet.index
                        )
                        if liberation_change:
                            now_seconds = int(datetime.now().timestamp())
                            if liberation_change.rate_per_hour > 0.01:
                                time_to_complete = f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + liberation_change.seconds_until_complete}:R>"
                                change = f"{liberation_change.rate_per_hour:+.2f}%/hour"
                                liberation_text = f"\n`{change:^25}`"
                            else:
                                skipped_campaigns.append(campaign)
                                continue

                    exclamation = campaign.planet.exclamations
                    if campaign.planet.regen_perc_per_hour <= 0.25:
                        exclamation += f":warning: {campaign.planet.regen_perc_per_hour:.2f}% REGEN :warning:"
                    if campaign.planet.index in [
                        planet.index for planet in gambit_planets.values()
                    ]:
                        exclamation += ":chess_pawn:"
                    if with_health_bars:
                        planet_health_bar = f"\n{health_bar(campaign.planet.health / campaign.planet.max_health, campaign.planet.current_owner, True)}"
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
                        ),
                        inline=False,
                    )

            if skipped_campaigns != []:
                skipped_planets_text = ""
                for campaign in skipped_campaigns:
                    exclamation = campaign.planet.exclamations
                    if campaign.planet.regen_perc_per_hour < 0.01:
                        exclamation += f":warning: {campaign.planet.regen_perc_per_hour:.2%} REGEN :warning:"
                    if campaign.planet.index in [
                        planet.index for planet in gambit_planets.values()
                    ]:
                        exclamation += ":chess_pawn:"
                    skipped_planets_text += f"-# {planet_names[str(campaign.planet.index)]['names'][language_json['code_long']]} - **{campaign.planet.stats['playerCount']:,}** {exclamation}\n"
                if skipped_planets_text != "":
                    self.add_field(
                        f"{language_json['dashboard']['AttackEmbed']['low_impact']}",
                        skipped_planets_text,
                        inline=False,
                    )

    class FooterEmbed(Embed, EmbedReprMixin):
        def __init__(
            self, language_json: dict, total_players: int, data_time: datetime
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
                    f"-# {total_players:,}"
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
