from datetime import datetime, timedelta
from random import choice
from data.lists import (
    CUSTOM_COLOURS,
    ATTACK_EMBED_ICONS,
    DEFENCE_EMBED_ICONS,
    HOMEWORLD_ICONS,
)
from disnake import Colour, Embed
from utils.api_wrapper.models import (
    Assignment,
    Campaign,
    DSS,
    GlobalEvent,
    GlobalResource,
    Planet,
)
from utils.api_wrapper.formatters.data_formatter import FormattedData
from utils.dataclasses import AssignmentImages, Factions, SpecialUnits, PlanetFeatures
from utils.dataclasses.factions import Faction
from utils.emojis import Emojis
from utils.functions import get_end_time, health_bar, short_format
from utils.mixins import EmbedReprMixin

STATUS_DICT = {
    0: "inactive",
    1: "preparing",
    2: "active",
    3: "on_cooldown",
}


class Dashboard:
    def __init__(
        self,
        data: FormattedData,
        language_code: str,
        json_dict: dict,
        compact_level: int = 0,
    ):
        language_json = json_dict["languages"][language_code]
        self.embeds: list[Embed] = []
        self.compact_level = compact_level

        # Homeworld Campaigns
        homeworld_campaigns = [c for c in data.campaigns if c.planet.homeworld]
        if homeworld_campaigns:
            for c in homeworld_campaigns:
                self.embeds.append(
                    self.HomeworldCampaignEmbed(
                        campaign=c,
                        language_json=language_json,
                        compact_level=self.compact_level,
                    )
                )

        # Major Order Embeds
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

        # DSS Embed
        if data.dss and data.dss.flags not in (0, 2):
            self.embeds.append(
                self.DSSEmbed(
                    dss=data.dss,
                    language_json=language_json,
                    gambit_planets=data.gambit_planets,
                )
            )

        # Global Resources
        for gr in data.global_resources:
            self.embeds.append(self.GlobalResourceEmbed(global_resource=gr))

        # Defence Embed
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

        # Attack Embeds
        faction_campaigns = [
            (
                f,
                [
                    c
                    for c in data.campaigns
                    if c.faction.full_name == f
                    and not c.planet.event
                    and not c.planet.homeworld
                ],
            )
            for f in ["Illuminate", "Terminids", "Automaton"]
        ]
        sorted_campaigns = sorted(
            faction_campaigns,
            key=lambda x: sum([c.planet.stats.player_count for c in x[1]]),
            reverse=True,
        )
        for faction, campaigns in sorted_campaigns:
            self.embeds.append(
                self.AttackEmbed(
                    campaigns=campaigns,
                    language_json=language_json,
                    faction=faction,
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
                steam_players=data.steam_player_count,
                data_time=data.formatted_at,
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

    class HomeworldCampaignEmbed(Embed, EmbedReprMixin):
        def __init__(
            self,
            campaign: Campaign,
            language_json: dict,
            compact_level: int = 0,
        ):
            super().__init__(
                title=f"BATTLE FOR {campaign.planet.loc_names.get(language_json['code_long'], campaign.planet.name).upper()}",
                colour=Colour.from_rgb(*campaign.planet.homeworld.colour),
            )
            if homeworld_icon := HOMEWORLD_ICONS.get(
                campaign.faction.full_name.lower()
            ):
                self.set_thumbnail(homeworld_icon)
            if compact_level == 0:
                self.description = f"-# Carve a path through the Megafactories towards the Cyborg Capital—the largest Megafactory and nexus of the Cyborg resistance.\n-# Destroy it before our **Forces in Reserve** are depleted to liberate **CYBERSTAN**"

            for region in campaign.planet.regions.values():
                field_name = ""
                field_value = ""
                if region.is_available:
                    field_name += f"{region.emoji} {region.names.get(language_json['code_long'], region.name)}"
                    if compact_level < 2:
                        field_value += f"-# {region.descriptions.get(language_json['code_long'], region.description)}"
                    if region.tracker and region.tracker.change_rate_per_hour > 0:
                        field_value += f"\n-# Victory <t:{int(region.tracker.complete_time.timestamp())}:R>"
                    field_value += f"\n{region.health_bar}"
                    field_value += f"\n`{region.perc:^25,.1%}`"
                    if region.tracker and region.tracker.change_rate_per_hour != 0:
                        change = f"{region.tracker.change_rate_per_hour:+.1%}/hr"
                        field_value += f"\n`{change:^25}`"
                else:
                    field_value += f"-# {region.emoji} {region.names.get(language_json['code_long'], region.name)}"

                self.add_field(field_name, field_value, inline=False)

    class MajorOrderEmbed(Embed, EmbedReprMixin):
        def __init__(
            self,
            assignment: Assignment,
            planets: dict[int, Planet],
            gambit_planets: dict[int, Planet],
            language_json: dict,
            json_dict: dict,
            compact_level: int = 0,
        ) -> None:
            self.assignment = assignment
            self.planets = planets
            self.gambit_planets = gambit_planets
            self.language_json = language_json
            self.json_dict = json_dict
            self.compact_level = compact_level
            self.completion_timestamps: list[int] = []
            self.task_tags = [
                "{ext_pre}",
                "{ext}",
                "{ext_post}",
                "{item_pre}",
                "{item}",
                "{item_post}",
                "{count_pre}",
                "{count}",
                "{count_post}",
                "{diff_pre}",
                "{diff}",
                "{diff_post}",
                "{multi}",
                "{type}",
                "{mtype}",
            ]
            super().__init__(
                title=self.assignment.title,
                colour=Colour.from_rgb(*CUSTOM_COLOURS["MO"]),
            )

            self._set_thumbnail()

            if self.compact_level < 2:
                self._add_description()

            self._collect_completion_timestamps()

            task_handlers = {
                1: self._add_type_1,
                2: self._add_type_2,
                3: self._add_type_3,
                4: self._add_type_4,
                5: self._add_type_5,
                6: self._add_type_6,
                7: self._add_type_7,
                9: self._add_type_9,
                10: self._add_type_10,
                11: self._add_type_11,
                12: self._add_type_12,
                13: self._add_type_13,
                14: self._add_type_14,
                15: self._add_type_15,
            }

            for task in self.assignment.tasks:
                handler = task_handlers.get(task.type, self._add_type_UNK)
                handler(task=task)

            self._add_rewards()

            self.add_field(
                name=f"{self.language_json['ends']}",
                value=f"-# <t:{int(self.assignment.ends_at_datetime.timestamp())}:R>",
            )

            if self.assignment.starts_at_datetime < datetime.now() - timedelta(hours=1):
                self._add_outlook_text()

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

        def _collect_completion_timestamps(self) -> None:
            """Fills `self.completion_timestamps` with estimated timestamps for each task (if possible)"""
            for task in self.assignment.tasks:
                if task.tracker and task.tracker.change_rate_per_hour > 0:
                    self.completion_timestamps.append(
                        task.tracker.complete_time.timestamp()
                    )
                else:
                    match task.type:
                        case 11:
                            if task.planet_index:
                                planet = self.planets.get(task.planet_index)
                                if not planet:
                                    continue
                                end_time_info = get_end_time(
                                    source_planet=planet,
                                    gambit_planets=self.gambit_planets,
                                )
                                if end_time_info.end_time:
                                    self.completion_timestamps.append(
                                        end_time_info.end_time.timestamp()
                                    )
                            elif task.sector_index:
                                sector: str = self.json_dict["sectors"][
                                    str(task.sector_index)
                                ]
                                sector_timestamps = []
                                for planet in [
                                    p
                                    for p in self.planets.values()
                                    if p.sector.lower() == sector.lower()
                                ]:
                                    if (
                                        planet.faction.full_name == "Humans"
                                        and not planet.event
                                    ):
                                        continue
                                    else:
                                        end_time_info = get_end_time(
                                            source_planet=planet,
                                            gambit_planets=self.gambit_planets,
                                        )
                                        if end_time_info.end_time:
                                            sector_timestamps.append(
                                                end_time_info.end_time.timestamp()
                                            )
                                if sector_timestamps:
                                    self.completion_timestamps.append(
                                        max(sector_timestamps)
                                    )
                        case 12:
                            if task.target - task.progress == 1:
                                for planet in [
                                    p for p in self.planets.values() if p.event
                                ]:
                                    end_time_info = get_end_time(
                                        source_planet=planet,
                                        gambit_planets=self.gambit_planets,
                                    )
                                    if (
                                        end_time_info.end_time
                                        and end_time_info.end_time
                                        < self.assignment.ends_at_datetime
                                    ):
                                        self.completion_timestamps.append(
                                            end_time_info.end_time.timestamp()
                                        )
                        case 13:
                            if task.planet_index:
                                planet = self.planets.get(task.planet_index)
                                if not planet:
                                    continue
                                if planet.event and (
                                    planet.event.end_time_datetime
                                    < self.assignment.ends_at_datetime
                                ):
                                    end_time_info = get_end_time(
                                        source_planet=planet,
                                        gambit_planets=self.gambit_planets,
                                    )
                                    if end_time_info.end_time:
                                        self.completion_timestamps.append(
                                            end_time_info.end_time.timestamp()
                                        )
                            elif task.sector_index:
                                sector: str = self.json_dict["sectors"][
                                    str(task.sector_index)
                                ]
                                sector_timestamps = []
                                for planet in [
                                    p
                                    for p in self.planets.values()
                                    if p.sector.lower() == sector.lower()
                                ]:
                                    if (
                                        planet.faction.full_name == "Humans"
                                        and not planet.event
                                    ):
                                        continue
                                    else:
                                        end_time_info = get_end_time(
                                            source_planet=planet,
                                            gambit_planets=self.gambit_planets,
                                        )
                                        if end_time_info.end_time:
                                            sector_timestamps.append(
                                                end_time_info.end_time.timestamp()
                                            )
                                if sector_timestamps:
                                    self.completion_timestamps.append(
                                        max(sector_timestamps)
                                    )

        def _add_progress_emoji(self, text: str, task: Assignment.Task):
            if task.type == 13 and task.progress_perc != 1:
                if task.planet_index:
                    planet = self.planets.get(task.planet_index)
                    if planet and planet.faction == Factions.humans:
                        return text.replace("{emoji}", Emojis.Icons.mo_task_complete)
            return text.replace(
                "{emoji}",
                (
                    Emojis.Icons.mo_task_complete
                    if task.progress_perc >= 1
                    else Emojis.Icons.mo_task_incomplete
                ),
            )

        def _get_faction_name(self, faction: Faction, plural: bool = False) -> str:
            """Get localized and pluralized (if requested) faction name"""
            names: dict = self.language_json["factions"]
            name_to_get = (
                faction.full_name if not plural else faction.full_name + "_plural"
            )
            name = names.get(name_to_get, "Unknown Faction")
            return name

        def _add_location_info(self, text: str, task: Assignment.Task) -> None:
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]

            if task.planet_index:
                planet = self.planets.get(task.planet_index)
                from_the_planet = tasks_json["loc_from_planet"]
                text = text.replace("{ext_pre}", f" {from_the_planet} **")
                if planet:
                    text = text.replace(
                        "{ext}", planet.loc_names[self.language_json["code_long"]]
                    )
                else:
                    text = text.replace("{ext}", "UNKNOWN PLANET")
                text = text.replace("{ext_post}", "**")
            elif task.sector_index:
                in_the = tasks_json["loc_in_the"]
                sector_name = self.json_dict["sectors"][str(task.sector_index)]
                sector = tasks_json["loc_sector"]
                text = text.replace("{ext_pre}", f" {in_the} **")
                text = text.replace("{ext}", sector_name)
                text = text.replace("{ext_post}", f"** {sector}")
            elif task.faction:
                from_any = tasks_json["loc_from_any"]
                controlled_planet = tasks_json["loc_controlled"]
                faction = self._get_faction_name(task.faction)
                text = text.replace("{ext_pre}", f" {from_any} **")
                text = text.replace("{ext}", faction)
                text = text.replace("{ext_post}", f"** {controlled_planet}")
            return text

        def _add_location_info_enemies(self, text: str, task: Assignment.Task) -> None:
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]

            if task.planet_index:
                planet = self.planets.get(task.planet_index)
                on = tasks_json["loc_on_planet"]
                text = text.replace("{ext_pre}", f" {on} **")
                if planet:
                    text = text.replace(
                        "{ext}", planet.loc_names[self.language_json["code_long"]]
                    )
                else:
                    text = text.replace("{ext}", "UNKNOWN PLANET")
                text = text.replace("{ext_post}", "**")
            elif task.sector_index:
                in_the = tasks_json["loc_in_the"]
                sector_name = self.json_dict["sectors"][str(task.sector_index)]
                sector = tasks_json["loc_sector"]
                text = text.replace("{ext_pre}", f" {in_the} **")
                text = text.replace("{ext}", sector_name)
                text = text.replace("{ext_post}", f"** {sector}")
            elif task.faction:
                on_any = tasks_json["loc_on_any"]
                controlled_planet = tasks_json["loc_controlled"]
                faction = self._get_faction_name(task.faction)
                text = text.replace("{ext_pre}", f" {on_any} **")
                text = text.replace("{ext}", faction)
                text = text.replace("{ext_post}", f"** {controlled_planet}")
            return text

        def _add_multiplayer_info(self, text: str, task: Assignment.Task):
            in_multiplayer = self.language_json["embeds"]["Dashboard"][
                "MajorOrderEmbed"
            ]["tasks"]["in_mp"]
            if task.min_players and task.min_players > 1:
                text = text.replace("{multi}", in_multiplayer)
            return text

        def _add_difficulty_info(self, text: str, task: Assignment.Task):
            if task.difficulty:
                tasks_json = self.language_json["embeds"]["Dashboard"][
                    "MajorOrderEmbed"
                ]["tasks"]
                on = tasks_json["diff_on"]
                or_higher = tasks_json["diff_or_higher"]
                difficulty = self.language_json["difficulty"].get(
                    str(task.difficulty), "UNKNOWN"
                )
                text = text.replace("{diff_pre}", f" {on} **")
                text = text.replace("{diff}", difficulty)
                text = text.replace("{diff_post}", f" {or_higher}**")
            return text

        def _remove_empty_tags(self, text: str):
            for tag in (t for t in self.task_tags if t in text):
                text = text.replace(tag, "")
            return text

        def _add_race_planet_info(self, text: str, task: Assignment.Task):
            """Add race or planet information"""
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]
            if task.planet_index:
                on = tasks_json["on_the_planet"]
                planet = self.planets.get(task.planet_index)
                text = text.replace("{race_pre}", f" {on} **")
                if planet:
                    text = text.replace(
                        "{race}", planet.loc_names[self.language_json["code_long"]]
                    )
                else:
                    text = text.replace("{race}", "UNKNOWN PLANET")
                text = text.replace("{race_post}", "**")
            else:
                on_a_planet_controlled_by_the = tasks_json["on_faction_planet"]
                race_name = self._get_faction_name(task.faction, plural=True)
                text = text.replace(
                    "{race_pre}", f" {on_a_planet_controlled_by_the} **"
                )
                text = text.replace("{race}", race_name)
                text = text.replace("{race_post}", "**")
            return text

        def _add_option_number(self, text: str, task_index: int):
            text = (
                f"{self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['tasks']['option']} {task_index + 1}\n"
                + text
            )
            return text

        def _add_type_UNK(self, task: Assignment.Task) -> None:
            """Type UNK: UNKNOWN"""
            tasks_json: dict[str, str] = self.language_json["embeds"]["Dashboard"][
                "MajorOrderEmbed"
            ]["tasks"]
            text: str = tasks_json["typeUNK"]
            text = self._add_progress_emoji(text=text, task=task)

            self.add_field(text, "", inline=False)

        def _add_type_1(self, task: Assignment.Task) -> None:
            """Type 1: Extract from locations"""
            tasks_json: dict[str, str] = self.language_json["embeds"]["Dashboard"][
                "MajorOrderEmbed"
            ]["tasks"]
            field_name: str = tasks_json["type1"]
            field_name = self._add_progress_emoji(text=field_name, task=task)
            field_name = self._add_location_info(text=field_name, task=task)
            if task.target:
                if task.target > 1:
                    times = tasks_json["times"]
                    field_name = field_name.replace("{count_pre}", " **")
                    field_name = field_name.replace("{count}", f"{task.target:,}")
                    field_name = field_name.replace("{count_post}", f"** {times}")
                else:
                    field_name = field_name.replace(
                        "{count_pre}{count}{count_post}", ""
                    )
            field_name = self._add_multiplayer_info(text=field_name, task=task)
            field_name = self._add_difficulty_info(text=field_name, task=task)
            field_name = self._remove_empty_tags(text=field_name)

            field_value = ""
            if task.progress_perc < 1:
                if task.target > 1:
                    progress = ""
                    if task.tracker and task.tracker.change_rate_per_hour > 0.1:
                        progress = f"`+{task.tracker.change_rate_per_hour:^25,.1%}/hr`"
                    field_value += (
                        f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{short_format(task.progress)}/{short_format(task.target)}**"
                        f"\n{task.health_bar}"
                        f"\n`{task.progress_perc:^25,.1%}`"
                        f"{progress}"
                    )
                else:
                    field_value += f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{task.progress}/{task.target}**"

            if self.assignment.flags in (2, 3):
                task_index = self.assignment.tasks.index(task)
                field_name = self._add_option_number(
                    text=field_name, task_index=task_index
                )

            self.add_field(field_name, field_value, inline=False)

        def _add_type_2(self, task: Assignment.Task) -> None:
            """Type 2: Extract with specific items"""
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]
            field_name: str = tasks_json["type2"]
            field_name = self._add_progress_emoji(text=field_name, task=task)
            field_name = field_name.replace("{count}", f"{task.target:,}")
            match task.item_type:
                case 1:
                    item_name: str = self.json_dict["items"]["item_names"].get(
                        str(task.item_id), {"name": "UNKNOWN ITEM"}
                    )["name"]
                    emoji = getattr(
                        Emojis.Items, item_name.lower().replace(" ", "_"), ""
                    )
                    field_name = field_name.replace("{item_pre}", "**")
                    field_name = field_name.replace("{item}", f"{emoji} {item_name}")
                    field_name = field_name.replace("{item_post}", "**")
                case 3:
                    item_name = (
                        tasks_json["type2_sample"]
                        if task.target == 1
                        else tasks_json["type2_samples"]
                    )
                    field_name = field_name.replace("{item}", item_name)
                case 4:
                    field_name = field_name.replace("{item}", "Secret Item")
            field_name = self._add_location_info(text=field_name, task=task)
            field_name = self._add_multiplayer_info(text=field_name, task=task)
            field_name = self._add_difficulty_info(text=field_name, task=task)
            field_name = self._remove_empty_tags(text=field_name)

            field_value = ""
            if task.progress_perc < 1:
                if task.target > 1:
                    progress = ""
                    if task.tracker and task.tracker.change_rate_per_hour > 0.1:
                        progress = f"`+{task.tracker.change_rate_per_hour:^25,.1%}/hr`"
                    field_value += (
                        f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{short_format(task.progress)}/{short_format(task.target)}**"
                        f"\n{task.health_bar}"
                        f"\n`{task.progress_perc:^25,.1%}`"
                        f"{progress}"
                    )
                else:
                    field_value += f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{task.progress}/{task.target}**"

            if self.assignment.flags in (2, 3):
                task_index = self.assignment.tasks.index(task)
                field_name = self._add_option_number(
                    text=field_name, task_index=task_index
                )

            self.add_field(field_name, field_value, inline=False)

        def _add_type_3(self, task: Assignment.Task) -> None:
            """Type 3: Kill specific enemies"""
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]
            field_name: str = tasks_json["type3"]
            field_name = self._add_progress_emoji(text=field_name, task=task)
            field_name = field_name.replace("{count}", f"{task.target:,}")
            if task.enemy_id:
                enemy = self.json_dict["enemy_ids"].get(
                    str(task.enemy_id), "UNKNOWN ENEMIES"
                )
            elif task.faction:
                enemy = self.language_json["factions"][task.faction.full_name]
            field_name = field_name.replace("{enemy}", enemy)
            if task.item_id:
                strat_list = [
                    name
                    for stratagems in self.json_dict["stratagems"].values()
                    for name, strat_info in stratagems.items()
                    if strat_info["id"] == task.item_id
                ]
                if strat_list:
                    using_the = tasks_json["type3_using_the"]
                    field_name = field_name.replace("{item_pre}", f" {using_the} **")
                    field_name = field_name.replace("{item}", strat_list[0])
                    field_name = field_name.replace("{item_post}", "**")
            field_name = self._add_location_info_enemies(text=field_name, task=task)
            field_name = self._add_multiplayer_info(text=field_name, task=task)
            field_name = self._add_difficulty_info(text=field_name, task=task)
            field_name = self._remove_empty_tags(text=field_name)

            field_value = ""
            if task.progress_perc < 1:
                if task.target > 1:
                    progress = ""
                    if task.tracker and task.tracker.change_rate_per_hour > 0:
                        progress = f"{task.tracker.change_rate_per_hour:+,.1%}/hr"
                        progress = f"\n`{progress:^25}`"
                        if task.tracker.complete_time < max(
                            self.assignment.ends_at_datetime,
                            datetime.now() + timedelta(weeks=2),
                        ):
                            progress += f"\n-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['complete']} <t:{int(task.tracker.complete_time.timestamp())}:R>"
                    field_value += (
                        f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{short_format(task.progress)}/{short_format(task.target)}**"
                        f"\n{task.health_bar}"
                        f"\n`{task.progress_perc:^25,.1%}`"
                        f"{progress}"
                    )
                else:
                    field_value += f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{task.progress}/{task.target}**"

            if self.assignment.flags in (2, 3):
                task_index = self.assignment.tasks.index(task)
                field_name = self._add_option_number(
                    text=field_name, task_index=task_index
                )

            self.add_field(field_name, field_value, inline=False)

        def _add_type_4(self, task: Assignment.Task) -> None:
            """Type 4: Complete objectives"""
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]
            if task.objective:
                field_name: str = tasks_json["type4"]
                objective = self.json_dict.get("objectives", {}).get(
                    str(task.objective), "UNKNOWN"
                )
                field_name = field_name.replace("{obj}", objective)
                if task.target > 1:
                    times = tasks_json["times"]
                    field_name = field_name.replace("{COUNT_PRE}", " **")
                    field_name = field_name.replace("{COUNT}", f"{task.target:,}")
                    field_name = field_name.replace("{COUNT_POST}", f"** {times}")
            else:
                # idk how they are going to put this through atm
                objective_verb = choice(["activate", "destroy", "primary", "secondary"])
                match objective_verb:
                    case "activate":
                        field_name = "{emoji} Activate **{count} {obj}**{race_pre}{race}{race_post}{multi}."
                        obj_name = (
                            "Secret Objective"
                            if task.target == 1
                            else "Secret Objectives"
                        )
                    case "destroy":
                        field_name = "{emoji} Destroy **{count} {obj}**{race_pre}{race}{race_post}{multi}."
                        obj_name = (
                            "Secret Objective"
                            if task.target == 1
                            else "Secret Objectives"
                        )
                    case _:
                        field_name = "{emoji} Complete **{count}{type} {obj}**{race_pre}{race}{race_post}{multi}."
                        obj_name = (
                            "Secret Objective"
                            if task.target == 1
                            else "Secret Objectives"
                        )
                        if objective_verb == "primary":
                            field_name = field_name.replace("{type}", " Primary")
                        elif objective_verb == "secondary":
                            field_name = field_name.replace("{type}", " Secondary")
                field_name = field_name.replace("{obj}", obj_name)
                field_name = field_name.replace("{count}", f"{task.target:,}")
            field_name = self._add_progress_emoji(text=field_name, task=task)
            field_name = self._add_race_planet_info(text=field_name, task=task)
            field_name = self._add_multiplayer_info(text=field_name, task=task)
            field_name = self._add_difficulty_info(text=field_name, task=task)
            field_name = self._remove_empty_tags(text=field_name)

            field_value = ""
            if task.progress_perc < 1:
                if task.target > 1:
                    progress = ""
                    if task.tracker and task.tracker.change_rate_per_hour > 0.1:
                        progress = f"`+{task.tracker.change_rate_per_hour:^25,.1%}/hr`"
                    field_value += (
                        f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{short_format(task.progress)}/{short_format(task.target)}**"
                        f"\n{task.health_bar}"
                        f"\n`{task.progress_perc:^25,.1%}`"
                        f"{progress}"
                    )
                else:
                    field_value += f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{task.progress}/{task.target}**"

            if self.assignment.flags in (2, 3):
                task_index = self.assignment.tasks.index(task)
                field_name = self._add_option_number(
                    text=field_name, task_index=task_index
                )

            self.add_field(field_name, field_value, inline=False)

        def _add_type_5(self, task: Assignment.Task) -> None:
            """Type 5: Play missions"""
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]
            field_name: str = tasks_json["type5"]
            field_name = self._add_progress_emoji(text=field_name, task=task)
            field_name = field_name.replace("{count}", f"{task.target:,}")
            mission_word = (
                tasks_json["mission"] if task.target == 1 else tasks_json["missions"]
            )
            field_name = field_name.replace("{obj}", mission_word)
            field_name = self._add_race_planet_info(text=field_name, task=task)
            field_name = self._add_multiplayer_info(text=field_name, task=task)
            field_name = self._add_difficulty_info(text=field_name, task=task)
            field_name = self._remove_empty_tags(text=field_name)

            field_value = ""
            if task.progress_perc < 1:
                if task.target > 1:
                    progress = ""
                    if task.tracker and task.tracker.change_rate_per_hour > 0.1:
                        progress = f"`+{task.tracker.change_rate_per_hour:^25,.1%}/hr`"
                    field_value += (
                        f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{short_format(task.progress)}/{short_format(task.target)}**"
                        f"\n{task.health_bar}"
                        f"\n`{task.progress_perc:^25,.1%}`"
                        f"{progress}"
                    )
                else:
                    field_value += f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{task.progress}/{task.target}**"

            if self.assignment.flags in (2, 3):
                task_index = self.assignment.tasks.index(task)
                field_name = self._add_option_number(
                    text=field_name, task_index=task_index
                )

            self.add_field(field_name, field_value, inline=False)

        def _add_type_6(self, task: Assignment.Task) -> None:
            """Type 6: Use specific stratagem"""
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]
            field_name: str = tasks_json["type6"]
            field_name = self._add_progress_emoji(text=field_name, task=task)
            if task.target > 1:
                times = tasks_json["times"]
                field_name = field_name.replace("{count_pre}", " **")
                field_name = field_name.replace("{count}", f"{task.target:,}")
                field_name = field_name.replace("{count_post}", f"** {times}")
            if task.item_id:
                strat_list = [
                    name
                    for stratagems in self.json_dict["stratagems"].values()
                    for name, strat_info in stratagems.items()
                    if strat_info["id"] == task.item_id
                ]
                if strat_list:
                    field_name = field_name.replace("{item}", strat_list[0])
            if task.faction:
                against = tasks_json["against"]
                race_name = self._get_faction_name(task.faction, plural=True)
                field_name = field_name.replace("{race_pre}", f" {against} **")
                field_name = field_name.replace("{race}", race_name)
                field_name = field_name.replace("{race_post}", "**")
            field_name = self._add_multiplayer_info(text=field_name, task=task)
            field_name = self._add_difficulty_info(text=field_name, task=task)
            field_name = self._remove_empty_tags(text=field_name)

            field_value = ""
            if task.progress_perc < 1:
                if task.target > 1:
                    progress = ""
                    if task.tracker and task.tracker.change_rate_per_hour > 0.1:
                        progress = f"`+{task.tracker.change_rate_per_hour:^25,.1%}/hr`"
                    field_value += (
                        f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{short_format(task.progress)}/{short_format(task.target)}**"
                        f"\n{task.health_bar}"
                        f"\n`{task.progress_perc:^25,.1%}`"
                        f"{progress}"
                    )
                else:
                    field_value += f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{task.progress}/{task.target}**"

            if self.assignment.flags in (2, 3):
                task_index = self.assignment.tasks.index(task)
                field_name = self._add_option_number(
                    text=field_name, task_index=task_index
                )

            self.add_field(field_name, field_value, inline=False)

        def _add_type_7(self, task: Assignment.Task) -> None:
            """Type 7: Extract from successful mission"""
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]
            if task.faction or task.planet_index:
                field_name = tasks_json["type7_f_p"]
            else:
                field_name = tasks_json["type7_r"]
            field_name = self._add_progress_emoji(text=field_name, task=task)
            if task.mission_type == 2:
                field_name = field_name.replace("{mtype}", "Opportunity Mission")
            elif task.mission_type == 3:
                field_name = field_name.replace("{mtype}", "Community-Target Mission")
            else:
                field_name = field_name.replace("{mtype}", tasks_json["mission"])
            if task.faction:
                against = tasks_json["against"]
                race_name = self._get_faction_name(task.faction, plural=True)
                field_name = field_name.replace("{race_pre}", f" {against} **")
                field_name = field_name.replace("{race}", race_name)
                field_name = field_name.replace("{race_post}", "**")
            if task.target > 1:
                times = tasks_json["times"]
                field_name = field_name.replace("{count_pre}", " **")
                field_name = field_name.replace("{count}", f"{task.target:,}")
                field_name = field_name.replace("{count_post}", f"** {times}")
            field_name = self._add_location_info_enemies(text=field_name, task=task)
            field_name = self._add_multiplayer_info(text=field_name, task=task)
            field_name = self._add_difficulty_info(text=field_name, task=task)
            field_name = self._remove_empty_tags(text=field_name)

            if self.assignment.flags in (2, 3):
                task_index = self.assignment.tasks.index(task)
                field_name = self._add_option_number(
                    text=field_name, task_index=task_index
                )

            field_value = ""
            if task.progress_perc < 1:
                if task.target > 1:
                    progress = ""
                    if task.tracker and task.tracker.change_rate_per_hour > 0.001:
                        progress = (
                            f"\n`{f'{task.tracker.change_rate_per_hour:+.1%}/hr':^25}`"
                        )
                        if task.tracker.complete_time < max(
                            self.assignment.ends_at_datetime,
                            datetime.now() + timedelta(weeks=2),
                        ):
                            progress += f"\n-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['complete']} <t:{int(task.tracker.complete_time.timestamp())}:R>"

                    field_value += (
                        f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{short_format(task.progress)}/{short_format(task.target)}**"
                        f"\n{task.health_bar}"
                        f"\n`{task.progress_perc:^25,.1%}`"
                        f"{progress}"
                    )
                else:
                    field_value += f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{task.progress}/{task.target}**"

            self.add_field(field_name, field_value, inline=False)

        def _add_type_9(self, task: Assignment.Task) -> None:
            """Type 9: Complete operations"""
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]
            if task.faction or task.planet_index:
                field_name = tasks_json["type9_f_p"]
            else:
                field_name = tasks_json["type9_r"]
            field_name = self._add_progress_emoji(text=field_name, task=task)
            if task.faction:
                against = tasks_json["against"]
                race_name = self._get_faction_name(task.faction, plural=True)
                field_name = field_name.replace("{race_pre}", f" {against} **")
                field_name = field_name.replace("{race}", race_name)
                field_name = field_name.replace("{race_post}", "**")
            if task.target > 1:
                times = tasks_json["times"]
                field_name = field_name.replace("{count_pre}", " **")
                field_name = field_name.replace("{count}", f"{task.target:,}")
                field_name = field_name.replace("{count_post}", f"** {times}")
            field_name = self._add_location_info_enemies(text=field_name, task=task)
            field_name = self._add_multiplayer_info(text=field_name, task=task)
            field_name = self._add_difficulty_info(text=field_name, task=task)
            field_name = self._remove_empty_tags(text=field_name)

            field_value = ""
            if task.progress_perc < 1:
                if task.target > 1:
                    progress = ""
                    if task.tracker and task.tracker.change_rate_per_hour > 0.0001:
                        progress = (
                            f"\n`{f'{task.tracker.change_rate_per_hour:+.1%}/hr':^25}`"
                        )
                    field_value += (
                        f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{short_format(task.progress)}/{short_format(task.target)}**"
                        f"\n{task.health_bar}"
                        f"\n`{task.progress_perc:^25,.1%}`"
                        f"{progress}"
                    )
                else:
                    field_value += f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{task.progress}/{task.target}**"

            if self.assignment.flags in (2, 3):
                task_index = self.assignment.tasks.index(task)
                field_name = self._add_option_number(
                    text=field_name, task_index=task_index
                )

            self.add_field(field_name, field_value, inline=False)

        def _add_type_10(self, task: Assignment.Task) -> None:
            """Type 10: Donate items"""
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]
            field_name = tasks_json["type10"]
            field_name = self._add_progress_emoji(text=field_name, task=task)
            field_name = field_name.replace("{count}", f"{task.target:,}")
            if task.item_id:
                # unsure how they get the items for this
                item_name, item_type = ("item_name", "item_type")
                item_name = self.json_dict["items"]["item_names"].get(
                    str(task.item_id), {"name": "item_name"}
                )[
                    "name"
                ]  # temp patch
                field_name = field_name.replace("{item}", item_name)
                field_name = field_name.replace("{item_type}", item_type)
            field_name = self._remove_empty_tags(text=field_name)

            field_value = ""
            if task.progress_perc < 1:
                if task.target > 1:
                    progress = ""
                    if task.tracker and task.tracker.change_rate_per_hour > 0.1:
                        progress = f"`+{task.tracker.change_rate_per_hour:^25,.1%}/hr`"
                    field_value += (
                        f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{short_format(task.progress)}/{short_format(task.target)}**"
                        f"\n{task.health_bar}"
                        f"\n`{task.progress_perc:^25,.1%}`"
                        f"{progress}"
                    )
                else:
                    field_value += f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{task.progress}/{task.target}**"

            if self.assignment.flags in (2, 3):
                task_index = self.assignment.tasks.index(task)
                field_name = self._add_option_number(
                    text=field_name, task_index=task_index
                )

            self.add_field(field_name, field_value, inline=False)

        def _add_type_11(self, task: Assignment.Task) -> None:
            """Type 11: Liberate planet or sector"""
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]
            field_name = tasks_json["type11"]
            field_name = self._add_progress_emoji(text=field_name, task=task)

            if task.planet_index:
                planet = self.planets.get(task.planet_index)
                if not planet:
                    location_name = "Unknown Location"
                else:
                    location_name = planet.loc_names.get(
                        self.language_json["code_long"], "UNKNOWN PLANET"
                    )
            elif task.sector_index:
                location_name = self.json_dict["sectors"].get(str(task.sector_index))
            else:
                location_name = "Unknown Location"
            field_name = field_name.replace("{location}", location_name)

            field_value = ""
            if task.progress_perc != 1:
                if task.planet_index:
                    planet = self.planets.get(task.planet_index)
                    if planet:
                        if not planet.active_campaign:
                            waypoint_timestamps: list[tuple[str, int]] = []
                            for waypoint in planet.waypoints:
                                way_planet = self.planets.get(waypoint)
                                if way_planet and way_planet.active_campaign:
                                    end_time_info = get_end_time(
                                        source_planet=way_planet,
                                        gambit_planets=self.gambit_planets,
                                    )
                                    if end_time_info.end_time:
                                        waypoint_timestamps.append(
                                            (
                                                way_planet.loc_names[
                                                    self.language_json["code_long"]
                                                ],
                                                int(end_time_info.end_time.timestamp()),
                                            )
                                        )
                            if waypoint_timestamps != []:
                                earliest_timestamp = sorted(
                                    waypoint_timestamps, key=lambda x: x[1]
                                )[0]
                                field_value += self.language_json["embeds"][
                                    "Dashboard"
                                ]["MajorOrderEmbed"]["avail_thanks_to_wp"].format(
                                    timestamp=earliest_timestamp[1],
                                    planet_name=earliest_timestamp[0],
                                )
                        field_value += (
                            f"\n{planet.health_bar}"
                            f"\n`{1 - planet.health_perc:^25,.1%}`"
                        )
                elif task.sector_index:
                    sector_name: str = self.json_dict["sectors"].get(
                        str(task.sector_index), "Unknown"
                    )
                    planets_in_sector = [
                        p
                        for p in self.planets.values()
                        if p.sector.lower() == sector_name.lower()
                    ]
                    perc_owned = len(planets_in_sector) / len(
                        [
                            p
                            for p in planets_in_sector
                            if p.faction.full_name == "Humans"
                        ]
                    )
                    field_value += (
                        f"{health_bar(perc=perc_owned, faction='Humans')}"
                        f"\n`{perc_owned:^25,.2%}`"
                    )

            if self.assignment.flags in (2, 3):
                task_index = self.assignment.tasks.index(task)
                field_name = self._add_option_number(
                    text=field_name, task_index=task_index
                )

            self.add_field(field_name, field_value, inline=False)

        def _add_type_12(self, task: Assignment.Task) -> None:
            """Type 12: Defend against attacks"""
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]
            if task.sector_index:
                if task.faction:
                    field_name: str = tasks_json["type12_s_f"]
                    race_name = self._get_faction_name(task.faction, plural=True)
                    field_name = field_name.replace("{race}", race_name)
                else:
                    field_name: str = tasks_json["type12_s_r"]
                sector_name = self.json_dict["sectors"].get(str(task.sector_index))
                field_name = field_name.replace("{sector}", sector_name)
            elif task.planet_index:
                if task.faction:
                    field_name: str = tasks_json["type12_p_f"]
                    race_name = self._get_faction_name(task.faction, plural=True)
                    field_name = field_name.replace("{race}", race_name)
                else:
                    field_name: str = tasks_json["type12_p_r"]
                planet = self.planets.get(task.planet_index)
                if planet:
                    field_name = field_name.replace(
                        "{planet}", planet.loc_names[self.language_json["code_long"]]
                    )
                else:
                    field_name = field_name.replace("{planet}", "UNKNOWN PLANET")
            else:
                if task.faction:
                    field_name: str = tasks_json["type12_r_f"]
                    race_name = self._get_faction_name(task.faction, plural=True)
                    field_name = field_name.replace("{race}", race_name)
                else:
                    field_name: str = tasks_json["type12_r_r"]
            field_name = field_name.replace("{count}", f"{task.target:,}")
            field_name = self._add_progress_emoji(text=field_name, task=task)

            field_value = (
                f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{task.progress}/{task.target:,}**"
                f"\n{task.health_bar}"
                f"\n`{task.progress_perc:^25.1%}`"
            )

            if self.assignment.flags in (2, 3):
                task_index = self.assignment.tasks.index(task)
                field_name = self._add_option_number(
                    text=field_name, task_index=task_index
                )

            self.add_field(field_name, field_value, inline=False)

        def _add_type_13(self, task: Assignment.Task) -> None:
            """Type 13: Hold location when order expires"""
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]
            if task.target > 1 and task.sector_index:
                field_name = tasks_json["type13_c_s"]
            elif task.target == 1 and any([task.planet_index, task.sector_index]):
                field_name = tasks_json["type13_r"]
            else:
                return  # invalid config
            field_name = self._add_progress_emoji(text=field_name, task=task)
            if task.target > 0:
                field_name = field_name.replace("{count}", f"{task.target:,}")
            if task.target == 1:
                if task.planet_index:
                    planet = self.planets.get(task.planet_index)
                    if planet:
                        location_name = planet.loc_names[
                            self.language_json["code_long"]
                        ]
                    else:
                        location_name = "UNKNOWN PLANET"
                elif task.sector_index:
                    location_name = self.json_dict["sectors"].get(
                        str(task.sector_index), "UNKNOWN"
                    )
                else:
                    return
                field_name = field_name.replace("{location}", location_name)
            elif task.target > 1 and task.sector_index:
                sector_name = self.json_dict["sectors"].get(
                    str(task.sector_index), "UNKNOWN"
                )
                field_name = field_name.replace("{sector}", sector_name)

            field_value = ""
            if task.progress_perc != 1:
                if task.planet_index:
                    planet = self.planets.get(task.planet_index)
                    if planet and planet.faction != Factions.humans:
                        field_value += (
                            planet.health_bar + f"\n`{1 - planet.health_perc:^25,.2%}`"
                        )
                elif task.target > 1 and task.sector_index:
                    field_value += (
                        f"{self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{task.progress}/{task.target}**"
                        f"\n{task.health_bar}"
                        f"\n`{task.progress_perc:^25,.2%}`"
                    )
            elif task.planet_index:
                planet = self.planets.get(task.planet_index)
                if planet:
                    if planet.event:
                        field_value += (
                            f"{planet.health_bar}:shield:"
                            f"\n`{planet.event.progress:^25,.2%}`"
                        )

            if self.assignment.flags in (2, 3):
                task_index = self.assignment.tasks.index(task)
                field_name = self._add_option_number(
                    text=field_name, task_index=task_index
                )

            self.add_field(field_name, field_value, inline=False)

        def _add_type_14(self, task: Assignment.Task) -> None:
            """Type 14: Liberate X planets"""
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]
            if task.faction:
                field_name = tasks_json["type14_f"]
            else:
                field_name = tasks_json["type14_r"]
            field_name = self._add_progress_emoji(text=field_name, task=task)
            if task.faction:
                race_name = self._get_faction_name(task.faction, plural=True)
                field_name = field_name.replace("{race}", race_name)
            field_name = field_name.replace("{count}", f"{task.target:,}")

            field_value = ""
            if task.progress_perc < 1:
                if task.target > 1:
                    progress = ""
                    if task.tracker and task.tracker.change_rate_per_hour > 0.1:
                        progress = f"`+{task.tracker.change_rate_per_hour:^25,.1%}/hr`"
                    field_value += (
                        f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{short_format(task.progress)}/{short_format(task.target)}**"
                        f"\n{task.health_bar}"
                        f"\n`{task.progress_perc:^25,.1%}`"
                        f"{progress}"
                    )
                else:
                    field_value += f"-# {self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['progress']}: **{task.progress}/{task.target}**"

            if self.assignment.flags in (2, 3):
                task_index = self.assignment.tasks.index(task)
                field_name = self._add_option_number(
                    text=field_name, task_index=task_index
                )

            self.add_field(field_name, field_value, inline=False)

        def _add_type_15(self, task: Assignment.Task) -> None:
            """Type 15: Net liberation (liberate more than lost)"""
            # TASK TITLE
            tasks_json = self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                "tasks"
            ]
            if task.faction:
                field_name = tasks_json["type15_f"]
            else:
                field_name = tasks_json["type15_r"]
            field_name = self._add_progress_emoji(text=field_name, task=task)
            if task.faction:
                race_name = self._get_faction_name(task.faction, plural=True)
                field_name = field_name.replace("{race}", race_name)
            if self.assignment.flags in (2, 3):
                task_index = self.assignment.tasks.index(task)
                field_name = self._add_option_number(
                    text=field_name, task_index=task_index
                )

            # TASK INFO
            field_value = ""
            if self.compact_level < 1:
                field_value += f"\n{task.health_bar}"
                percent = {i: (i + 5) / 10 for i in range(-5, 6)}[
                    [
                        key
                        for key in range(-5, 6)
                        if key <= min(max(-5, task.progress), 5)
                    ][-1]
                ]
                progress = f"{task.progress:+}"
                left_buffer = " " * min(int(percent * 25), (25 - len(progress) - 1))
                right_buffer = " " * (25 - len(left_buffer) - len(progress) - 1)
                arrow = "↑"
                if task.progress > 4:
                    pointer_text = f"{progress}{arrow}"
                else:
                    pointer_text = f"{arrow}{progress}"
                field_value += f"\n`{left_buffer}{pointer_text}{right_buffer}`"
                for planet in (
                    p for p in self.planets.values() if p.stats.player_count > 200
                ):
                    if task.faction:
                        if (planet.event and planet.event.faction != task.faction) or (
                            not planet.event and planet.faction != task.faction
                        ):
                            continue
                    end_time_info = get_end_time(planet, self.gambit_planets)
                    if end_time_info.end_time:
                        if planet.event:
                            if (
                                planet.event.end_time_datetime < end_time_info.end_time
                                and planet.event.end_time_datetime
                                < self.assignment.ends_at_datetime
                            ):
                                field_value += self.language_json["embeds"][
                                    "Dashboard"
                                ]["MajorOrderEmbed"]["tasks"][
                                    "type15_from_loss"
                                ].format(
                                    planet=planet.loc_names[
                                        self.language_json["code_long"]
                                    ],
                                    timestamp=f"<t:{int(planet.event.end_time_datetime.timestamp())}:R>",
                                )
                        else:
                            if (
                                end_time_info.end_time
                                < self.assignment.ends_at_datetime
                            ):
                                field_value += self.language_json["embeds"][
                                    "Dashboard"
                                ]["MajorOrderEmbed"]["tasks"]["type15_from_lib"].format(
                                    planet=planet.loc_names[
                                        self.language_json["code_long"]
                                    ],
                                    timestamp=f"<t:{int(end_time_info.end_time.timestamp())}:R>",
                                )
                    elif planet.event:
                        field_value += self.language_json["embeds"]["Dashboard"][
                            "MajorOrderEmbed"
                        ]["tasks"]["type15_from_loss"].format(
                            planet=planet.loc_names[self.language_json["code_long"]],
                            timestamp=f"<t:{int(planet.event.end_time_datetime.timestamp())}:R>",
                        )

            self.add_field(field_name, field_value, inline=False)

        def _add_rewards(self) -> None:
            rewards_text = ""
            for reward in self.assignment.rewards:
                reward_name: str = self.json_dict["items"]["reward_types"].get(
                    str(reward["type"]), "Unknown Item"
                )
                localized_name = self.language_json["currencies"].get(reward_name)
                rewards_text += f"{reward['amount']:,} "
                if reward["amount"] > 1:
                    rewards_text += f"**{self.language_json['embeds']['Dashboard']['MajorOrderEmbed']['reward_pluralized'].format(reward=localized_name)}** "
                else:
                    rewards_text += f"**{localized_name}**"
                rewards_text += f"{getattr(Emojis.Items, reward_name.replace(' ', '_').lower(), '')}\n"
            if rewards_text != "":
                self.add_field(
                    self.language_json["embeds"]["Dashboard"]["MajorOrderEmbed"][
                        "rewards"
                    ],
                    rewards_text,
                )

        def _add_outlook_text(self) -> None:

            if (
                datetime.now() < self.assignment.ends_at_datetime - timedelta(days=2)
                and {13, 15} & self.assignment.unique_task_types
            ):
                # return if assignments that last the full assignment duration are present
                # and we are not within 2 days of assignment end
                return

            winning_all_unfinished_tasks = [
                ts < self.assignment.ends_at_datetime.timestamp()
                for ts in self.completion_timestamps
            ]

            complete_type_15s = []
            for task in (t for t in self.assignment.tasks if t.type == 15):
                progress = int(task.progress)
                for planet in (
                    p for p in self.planets.values() if p.stats.player_count > 200
                ):
                    end_time_info = get_end_time(planet, self.gambit_planets)
                    if end_time_info.end_time:
                        if (
                            not planet.event
                            and end_time_info.end_time
                            < self.assignment.ends_at_datetime
                        ):
                            progress += 1
                        elif planet.event:
                            if (
                                planet.event.end_time_datetime
                                > self.assignment.ends_at_datetime
                            ):
                                continue
                            elif (
                                end_time_info.end_time > planet.event.end_time_datetime
                            ):
                                progress -= 1
                if progress >= task.target:
                    complete_type_15s.append(True)

            complete_type_13s = []
            for task in (t for t in self.assignment.tasks if t.type == 13):
                if task.planet_index:
                    planet = self.planets.get(task.planet_index)
                    if planet:
                        if planet.faction.full_name == "Humans" and not planet.event:
                            complete_type_13s.append(True)
                        elif planet.faction.full_name != "Humans":
                            end_time_info = get_end_time(
                                source_planet=planet, gambit_planets=self.gambit_planets
                            )
                            if (
                                end_time_info.end_time
                                and end_time_info.end_time
                                < self.assignment.ends_at_datetime
                            ):
                                complete_type_13s.append(True)
                elif task.sector_index:
                    sector = self.json_dict["sectors"][task.sector_index]
                    sector_wins = []
                    for planet in [
                        p
                        for p in self.planets.values()
                        if p.sector.lower() == sector.lower()
                    ]:
                        if planet.faction.full_name == "Humans" and not planet.event:
                            sector_wins.append(True)
                        else:
                            sector_wins.append(False)
                    complete_type_13s.append(
                        all(sector_wins)
                        if task.target == 1
                        else len([t for t in sector_wins if t]) > task.target
                    )

            complete_tasks = (
                [
                    True
                    for t in self.assignment.tasks
                    if t.progress_perc >= 1 and t.type not in [13, 15]
                ]
                + [b for b in winning_all_unfinished_tasks if b]
                + complete_type_13s
                + complete_type_15s
            )

            outlook_text = ""
            match self.assignment.flags:
                case 0 | 1:  # complete all tasks
                    if len(complete_tasks) == len(self.assignment.tasks):
                        outlook_text = self.language_json["complete"]
                        if {13, 15} & self.assignment.unique_task_types:
                            outlook_text += f" <t:{int(self.assignment.ends_at_datetime.timestamp())}:R>"
                        else:
                            time_to_use: datetime = sorted(
                                self.completion_timestamps, reverse=True
                            )[0]
                            outlook_text += f" <t:{int(time_to_use)}:R>"
                            time_diff = (
                                self.assignment.ends_at_datetime.timestamp()
                                - time_to_use
                            )
                            hours = f"{time_diff // 3600:.0f}"
                            minutes = f"{(time_diff % 3600) // 60:.0f}"
                            outlook_text += self.language_json["embeds"]["Dashboard"][
                                "MajorOrderEmbed"
                            ]["ahead_of_schedule"].format(hours=hours, minutes=minutes)
                    else:
                        outlook_text += f"{self.language_json['failure']} <t:{int(self.assignment.ends_at_datetime.timestamp())}:R>"
                        if self.completion_timestamps != [] and len(
                            self.completion_timestamps
                        ) == len([t.progress_perc < 1 for t in self.assignment.tasks]):
                            oldest_timestamp: int = sorted(
                                self.completion_timestamps, reverse=True
                            )[0]
                            time_diff = (
                                oldest_timestamp
                                - self.assignment.ends_at_datetime.timestamp()
                            )
                            hours = f"{time_diff // 3600:.0f}"
                            minutes = f"{(time_diff % 3600) // 60:.0f}"
                            if 0 < time_diff // 3600 < 250:
                                outlook_text += self.language_json["embeds"][
                                    "Dashboard"
                                ]["MajorOrderEmbed"]["behind_schedule"].format(
                                    hours=hours, minutes=minutes
                                )
                case 2 | 3:  # complete any task
                    if any(complete_tasks):
                        outlook_text = self.language_json["complete"]
                        if {13, 15} & self.assignment.unique_task_types:
                            outlook_text += f" <t:{int(self.assignment.ends_at_datetime.timestamp())}:R>"
                        else:
                            time_to_use: datetime = sorted(self.completion_timestamps)[
                                0
                            ]
                            outlook_text += f" <t:{int(time_to_use)}:R>"
                            time_diff = (
                                self.assignment.ends_at_datetime.timestamp()
                                - time_to_use
                            )
                            hours = f"{time_diff // 3600:.0f}"
                            minutes = f"{(time_diff % 3600) // 60:.0f}"
                            outlook_text += self.language_json["embeds"]["Dashboard"][
                                "MajorOrderEmbed"
                            ]["ahead_of_schedule"].format(hours=hours, minutes=minutes)
                    else:
                        outlook_text += f"{self.language_json['failure']} <t:{int(self.assignment.ends_at_datetime.timestamp())}:R>"
                        if self.completion_timestamps != []:
                            newest_timestamp: int = sorted(self.completion_timestamps)[
                                0
                            ]
                            time_diff = (
                                newest_timestamp
                                - self.assignment.ends_at_datetime.timestamp()
                            )
                            hours = f"{time_diff // 3600:.0f}"
                            minutes = f"{(time_diff % 3600) // 60:.0f}"
                            if 0 < time_diff // 3600 < 250:
                                outlook_text += self.language_json["embeds"][
                                    "Dashboard"
                                ]["MajorOrderEmbed"]["behind_schedule"].format(
                                    hours=hours, minutes=minutes
                                )

            if outlook_text != "":
                self.add_field(
                    self.language_json["embeds"]["Dashboard"]["outlook"],
                    f"-# {outlook_text}",
                    inline=False,
                )

        def _add_briefing(self, briefing: GlobalEvent) -> None:
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
                title=language_json["embeds"]["Dashboard"]["DSSEmbed"]["title"],
                colour=Colour.from_rgb(*CUSTOM_COLOURS["DSS"]),
            )
            self.set_thumbnail(
                url="https://media.discordapp.net/attachments/1212735927223590974/1413612410819969114/0xfbbeedfa99b09fec.png?ex=68bc90a6&is=68bb3f26&hm=cd8bf236a355bbed28f4847d3d62b5908d050a7eeb7396bb9a891e108acc0241&=&format=webp&quality=lossless"
            )
            move_datetime = dss.move_timer_datetime
            because_of_planet = False
            end_time_info = get_end_time(dss.planet, gambit_planets)
            if end_time_info.end_time and end_time_info.end_time < move_datetime:
                move_datetime = end_time_info.end_time
                because_of_planet = True
            self.description = (
                f"-# {language_json['embeds']['Dashboard']['DSSEmbed']['station_moves']} **<t:{int(move_datetime.timestamp())}:R>**"
                f"\n-# {language_json['embeds']['Dashboard']['DSSEmbed']['current_location']}: {dss.planet.faction.emoji} **{dss.planet.loc_names.get(language_json['code_long'], dss.planet.name)}**"
            )
            if dss.votes:
                sorted_planets: list[tuple[Planet, int]] = sorted(
                    dss.votes.available_planets,
                    key=lambda x: x[1],
                    reverse=True,
                )
                next_planet = sorted_planets[0]
                if (
                    because_of_planet
                    and dss.planet == next_planet[0]
                    and len(dss.votes.available_planets) == 8
                ):
                    next_planet = sorted_planets[1]
                self.description += f"\n-# {language_json['embeds']['Dashboard']['DSSEmbed']['next_location']}: {next_planet[0].faction.emoji} **{next_planet[0].loc_names.get(language_json['code_long'], next_planet[0].name)}**"

            if move_datetime < datetime.now() + timedelta(minutes=15):
                self.description += f"\n-# {Emojis.Decoration.alert_icon} {language_json['embeds']['Dashboard']['DSSEmbed']['vote_reminder']} {Emojis.Decoration.alert_icon}"
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
                            cost_change = tactical_action.cost_changes.get(ta_cost.item)
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
                        field_value += f" :green_circle:\n{language_json['ends']} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
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

            if (
                all([ta.status == 0 for ta in dss.tactical_actions])
                and dss.planet.index == 0
            ):
                self.add_field(
                    f"{Emojis.Decoration.alert_icon} {language_json['embeds']['Dashboard']['DSSEmbed']['voting_mode']} {Emojis.Decoration.alert_icon}",
                    language_json["embeds"]["Dashboard"]["DSSEmbed"]["select"],
                    inline=False,
                )
                if dss.votes:
                    field_value = ""
                    for index, (planet, votes) in enumerate(
                        sorted(
                            dss.votes.available_planets,
                            key=lambda x: x[1],
                            reverse=True,
                        ),
                        start=1,
                    ):
                        field_value += f"\n-# #{index} - {planet.faction.emoji} {planet.loc_names[language_json['code_long']]} - {votes/dss.votes.total_votes:.1%}"
                    self.add_field(
                        language_json["embeds"]["Dashboard"]["DSSEmbed"]["votes"],
                        field_value,
                    )

    class GlobalResourceEmbed(Embed, EmbedReprMixin):
        def __init__(self, global_resource: GlobalResource):
            super().__init__(
                title=global_resource.name or "Unknown Resource",
                description=global_resource.description,
                colour=global_resource.embed_colour,
            )

            field_value = global_resource.get_health_bar
            field_value += f"\n`{f'{global_resource.perc:.2%}':^25}`"
            if (
                global_resource.tracker
                and global_resource.tracker.change_rate_per_hour != 0
            ):
                field_value += f"\n`{f'{global_resource.tracker.change_rate_per_hour:+.2%}/hr':^25}`"
                if global_resource.tracker.change_rate_per_hour > 0:
                    field_value += f"\n-# 100% <t:{int(datetime.now().timestamp() + global_resource.tracker.seconds_until_complete)}:R>"
                else:
                    field_value += f"\n-# 0% <t:{int(datetime.now().timestamp() + global_resource.tracker.seconds_until_complete)}:R>"
            self.add_field("", field_value)

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
            if total_players != 0:
                total_players_doing_defence = f" ({(sum(planet.stats.player_count for planet in planet_events)/total_players):.2%})"
            else:
                total_players_doing_defence = ""
            super().__init__(
                title=f"{language_json['embeds']['Dashboard']['DefenceEmbed']['title']}{total_players_doing_defence}",
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
                field_value += f"\n-# {planet_feature[1]} {planet_feature[0]}"

            if (
                planet.dss_in_orbit
                and self.eagle_storm
                and self.eagle_storm.status == 2
            ):
                field_value += self.language_json["embeds"]["Dashboard"][
                    "DefenceEmbed"
                ]["defence_held_by_dss"]

            field_value += f"\n{self.language_json['ends']} **<t:{int(planet.event.end_time_datetime.timestamp())}:R>**"
            field_value += f"\n{self.language_json['embeds']['Dashboard']['DefenceEmbed']['invasion_level']} **{planet.event.level}**{planet.event.level_exclamation}"

            calculated_end_time = get_end_time(planet, self.gambit_planets)
            if calculated_end_time.end_time and (
                self.now < calculated_end_time.end_time < planet.event.end_time_datetime
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
                    field_value += f"\n-# :chess_pawn: **{gambit_planet.loc_names[self.language_json['code_long']]}** {self.language_json['embeds']['Dashboard']['DefenceEmbed']['gambit']}"

            field_value += f"\n{self.language_json['embeds']['Dashboard']['DefenceEmbed']['heroes']}: **{planet.stats.player_count:,}**"
            if self.compact_level < 1:
                field_value += f"\n{planet.health_bar}"
            field_value += f"\n`{planet.event.progress:^25.2%}`"
            if planet.tracker and planet.tracker.change_rate_per_hour > 0:
                change = f"{planet.tracker.change_rate_per_hour:+.2%}/hr"
                field_value += f"\n`{change:^25}`"

            for region in sorted(
                planet.regions.values(), key=lambda x: x.availability_factor
            ):
                if region.is_available:
                    field_value += f"\n-# ↳ {region.emoji} {self.language_json['regions'][str(region.type.value)]} **{region.names[self.language_json['code_long']]}** - {region.perc:.0%}"
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
                            field_value += f"\n-# ↳ {region.emoji} {self.language_json['regions'][str(region.type.value)]} **{region.names[self.language_json['code_long']]}** - {self.language_json['embeds']['Dashboard']['DefenceEmbed']['available']} <t:{int(region_avail_datetime.timestamp())}:R>"
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
            planets: dict[int, Planet],
            compact_level: int = 0,
        ):
            super().__init__(
                title=language_json["embeds"]["Dashboard"]["AttackEmbed"][
                    "title"
                ].format(faction=language_json["factions"][f"{faction}_plural"]),
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
                    field_name += f"{campaign.faction.emoji} - **{campaign.planet.loc_names.get(language_json['code_long'], campaign.planet.name)}** {campaign.planet.exclamations}"
                    if campaign.type == 2:
                        field_name += Emojis.Icons.high_prio_campaign
                    field_value += f"{language_json['embeds']['Dashboard']['AttackEmbed']['heroes']}: **{campaign.planet.stats.player_count:,}**"

                    for su in SpecialUnits.get_from_effects_list(
                        campaign.planet.active_effects
                    ):
                        field_value += f"\n-# {su[1]} {language_json['special_units'].get(su[0], su[0])}"

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
                        gambit_planet = planets.get(
                            {v.index: k for k, v in gambit_planets.items()}[
                                campaign.planet.index
                            ]
                        )
                        if gambit_planet:
                            field_value += f"\n-# :chess_pawn: {language_json['embeds']['Dashboard']['AttackEmbed']['gambit_for']} {gambit_planet.loc_names.get(language_json['code_long'], gambit_planet.name)}"
                    if compact_level < 1:
                        if campaign.type == 1:
                            field_value += f"\n**`{language_json['embeds']['Dashboard']['AttackEmbed']['recon_campaign']:^25}`**"
                        else:
                            field_value += f"\n{campaign.planet.health_bar}"
                    if campaign.type != 1:
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
                            field_value += f"\n-# ↳ {region.emoji} {language_json['regions'][str(region.type.value)]} **{region.names[language_json['code_long']]}** {region.perc:.2%}"
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
                            if (
                                region.availability_factor == 0
                                and not region.is_available
                            ):
                                break
                            field_value += f"\n-# ↳ {region.emoji} {language_json['regions'][str(region.type.value)]} **{region.names[language_json['code_long']]}** {language_json['embeds']['Dashboard']['AttackEmbed']['reg_avail_at']} **{region.availability_factor:.2%}**"
                            break

                    self.add_field(
                        field_name,
                        field_value,
                        inline=False,
                    )

            if skipped_campaigns != []:
                skipped_planets_text = ""
                for campaign in skipped_campaigns[:10]:
                    exclamation = campaign.planet.exclamations
                    if campaign.planet.regen_perc_per_hour < 0.001:
                        exclamation += f":warning: {campaign.planet.regen_perc_per_hour:+.2%}/hr :warning:"
                    if campaign.planet.index in [
                        planet.index for planet in gambit_planets.values()
                    ]:
                        exclamation += ":chess_pawn:"
                    if campaign.type == 2:
                        field_name += Emojis.Icons.high_prio_campaign
                    skipped_planets_text += f"-# {campaign.planet.loc_names.get(language_json['code_long'], campaign.planet.name)} - **{campaign.planet.stats.player_count:,}** {exclamation}\n"
                    if compact_level < 2 and len(skipped_campaigns) < 10:
                        for region in campaign.planet.regions.values():
                            if (
                                region.is_available
                                and region.players > total_players * 0.001
                            ):
                                skipped_planets_text += f"-# ↳ {region.emoji} {language_json['regions'][str(region.type.value)]} **{region.names[language_json['code_long']]}** - {region.perc:.2%}\n"
                if len(skipped_campaigns) > 10:
                    other_count = sum(
                        [c.planet.stats.player_count for c in skipped_campaigns[10:]]
                    )
                    skipped_planets_text += f"-# Other Planets: {other_count:,}"
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
