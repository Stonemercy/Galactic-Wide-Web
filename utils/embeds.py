from data.lists import (
    warbond_images_dict,
    emotes_list,
    victory_poses_list,
    player_cards_list,
    titles_list,
    stratagem_permit_list,
    help_dict,
    faction_colours,
    stratagem_id_dict,
    assignment_task_images_dict,
    task_type_15_progress_dict,
    stratagem_image_dict,
)
from datetime import datetime, timedelta
from disnake import APISlashCommand, Embed, Colour, File, ModalInteraction, OptionType
from main import GalacticWideWebBot
from math import inf
from os import getpid
from psutil import Process, cpu_percent
from utils.db import GWWGuild
from utils.functions import health_bar, short_format
from utils.data import (
    DSS,
    Assignment,
    Campaign,
    Data,
    Dispatch,
    PersonalOrder,
    PlanetEvents,
    Planets,
    Steam,
    Superstore,
    Tasks,
    Planet,
    GlobalEvents,
)
from utils.emojis import Emojis


class PlanetEmbed(Embed):
    def __init__(self, planet_names: dict, planet: Planet, language_json: dict):
        super().__init__(colour=Colour.from_rgb(*faction_colours[planet.current_owner]))
        self.planet_names = planet_names
        self.planet = planet
        self.language_json = language_json
        self.add_planet_info()
        self.add_mission_stats()
        self.add_hero_stats()
        self.add_misc_stats()

    def add_planet_info(self):
        sector = self.language_json["PlanetEmbed"]["sector"].format(
            sector=self.planet.sector
        )
        owner = self.language_json["PlanetEmbed"]["owner"].format(
            faction=self.language_json["factions"][self.planet.current_owner],
            faction_emoji=Emojis.factions[self.planet.current_owner],
        )
        biome = self.language_json["PlanetEmbed"]["biome"].format(
            biome_name=self.planet.biome["name"],
            biome_description=self.planet.biome["description"],
        )
        environmentals = self.language_json["PlanetEmbed"]["environmentals"].format(
            environmentals="".join(
                [
                    f"\n- **{hazard['name']}**\n  - -# {hazard['description']}"
                    for hazard in self.planet.hazards
                ]
            )
        )
        title_exclamation = ""
        if self.planet.dss:
            title_exclamation += Emojis.dss["dss"]
        if self.planet.in_assignment:
            title_exclamation += Emojis.icons["MO"]
        planet_health_bar = health_bar(
            (
                self.planet.event.progress
                if self.planet.event
                else self.planet.health_perc
            ),
            (
                self.planet.event.faction
                if self.planet.event
                else self.planet.current_owner
            ),
            True if self.planet.event else False,
        )
        if self.planet.event:
            planet_health_bar += f" 🛡️ {Emojis.factions[self.planet.event.faction]}"
        if self.planet.current_owner == "Humans":
            health_text = (
                f"{1 - self.planet.event.progress:^25,.2%}"
                if self.planet.event
                else f"{(self.planet.health_perc):^25,.2%}"
            )
        else:
            health_text = f"{1 - (self.planet.health_perc):^25,.2%}"
        self.add_field(
            f"__**{self.planet_names['names'][self.language_json['code_long']]}**__ {title_exclamation}",
            (
                f"{sector}"
                f"{owner}"
                f"{biome}"
                f"{environmentals}"
                f"{self.language_json['PlanetEmbed']['liberation_progress']}\n"
                f"{planet_health_bar}\n"
                f"`{health_text}`\n"
                "\u200b\n"
            ),
            inline=False,
        )

    def add_mission_stats(self):
        self.add_field(
            self.language_json["PlanetEmbed"]["mission_stats"],
            (
                f"{self.language_json['PlanetEmbed']['missions_won']}: **`{short_format(self.planet.stats['missionsWon'])}`**\n"
                f"{self.language_json['PlanetEmbed']['missions_lost']}: **`{short_format(self.planet.stats['missionsLost'])}`**\n"
                f"{self.language_json['PlanetEmbed']['missions_winrate']}: **`{self.planet.stats['missionSuccessRate']}%`**\n"
                f"{self.language_json['PlanetEmbed']['missions_time_spent']}: **`{self.planet.stats['missionTime']/31556952:.1f} years`**"
            ),
        )

    def add_hero_stats(self):
        self.add_field(
            self.language_json["PlanetEmbed"]["hero_stats"],
            (
                f"{self.language_json['PlanetEmbed']['active_heroes']}: **`{self.planet.stats['playerCount']:,}`**\n"
                f"{self.language_json['PlanetEmbed']['heroes_lost']}: **`{short_format(self.planet.stats['deaths'])}`**\n"
                f"{self.language_json['PlanetEmbed']['accidentals']}: **`{short_format(self.planet.stats['friendlies'])}`**\n"
                f"{self.language_json['PlanetEmbed']['shots_fired']}: **`{short_format(self.planet.stats['bulletsFired'])}`**\n"
                f"{self.language_json['PlanetEmbed']['shots_hit']}: **`{short_format(self.planet.stats['bulletsHit'])}`**\n"
                f"{self.language_json['PlanetEmbed']['accuracy']}: **`{self.planet.stats['accuracy']}%`**\n"
            ),
        )

    def add_misc_stats(self):
        faction = (
            self.planet.current_owner
            if not self.planet.event
            else self.planet.event.faction
        )
        if faction != "Humans":
            faction_kills = {
                "Automaton": "automatonKills",
                "Terminids": "terminidKills",
                "Illuminate": "illuminateKills",
            }[(faction)]
            self.add_field(
                f"💀 {self.language_json['factions'][faction]} {self.language_json['PlanetEmbed']['killed']}:",
                f"**{short_format(self.planet.stats[faction_kills])}**",
                inline=False,
            ).set_author(
                name=self.language_json["PlanetEmbed"]["liberation_progress"],
                icon_url={
                    "Automaton": "https://cdn.discordapp.com/emojis/1215036421551685672.webp?size=44&quality=lossless",
                    "Terminids": "https://cdn.discordapp.com/emojis/1215036423090999376.webp?size=44&quality=lossless",
                    "Illuminate": "https://cdn.discordapp.com/emojis/1317057914145603635.webp?size=44&quality=lossless",
                }.get(
                    faction,
                    None,
                ),
            )
        if self.planet.feature:
            self.add_field("Feature", self.planet.feature)
        if self.planet.thumbnail:
            self.set_thumbnail(url=self.planet.thumbnail)
        try:
            self.set_image(
                file=File(
                    f"resources/biomes/{self.planet.biome['name'].lower().replace(' ', '_')}.png"
                )
            )
            self.image_set = True
        except:
            self.image_set = False


class HelpEmbed(Embed):
    def __init__(self, commands: list[APISlashCommand], command_name: str):
        super().__init__(colour=Colour.green(), title="Help")
        if command_name == "all":
            for global_command in commands:
                options = "*Options:*\n" if global_command.options != [] else ""
                for option in global_command.options:
                    if option.type == OptionType.sub_command:
                        options += f"- </{global_command.name} {option.name}:{global_command.id}>\n"
                        for sub_option in option.options:
                            options += f" - **`{sub_option.name}`**: `{sub_option.type.name}` {'**[Required]**' if sub_option.required else '**<Optional>**'}- {sub_option.description} \n"
                    else:
                        options += f"- **`{option.name}`**: `{option.type.name}` {'**[Required]**' if option.required else '**<Optional>**'} - {option.description}\n"
                self.add_field(
                    f"</{global_command.name}:{global_command.id}>",
                    (f"-# {global_command.description}\n" f"{options}\n"),
                    inline=False,
                )
        else:
            command_help = list(
                filter(
                    lambda cmd: cmd.name == command_name,
                    commands,
                )
            )[0]
            options = "" if command_help.options == [] else "**Options:**\n"
            for option in command_help.options:
                if option.type == OptionType.sub_command:
                    options += (
                        f"- </{command_help.name} {option.name}:{command_help.id}>\n"
                    )
                    for sub_option in option.options:
                        options += f" - **`{sub_option.name}`** {'**[Required]**' if sub_option.required else '**<Optional>**'}- {sub_option.description}\n"
                else:
                    options += f"- **`{option.name}`** {'**[Required]**' if option.required else '**<Optional>**'} - {option.description}\n"
            self.add_field(
                f"</{command_help.name}:{command_help.id}>",
                (
                    f"{help_dict[command_name]['long_description']}\n\n"
                    f"{options}"
                    f"**Example usage:**\n- {help_dict[command_name]['example_usage']}\n"
                ),
                inline=False,
            )


class BotDashboardEmbed(Embed):
    def __init__(self, bot: GalacticWideWebBot, user_installs: int):
        super().__init__(colour=Colour.green(), title="GWW Overview")
        now = datetime.now()
        self.description = (
            "This is the dashboard for all information about the GWW itself"
        )
        commands = ""
        for global_command in bot.global_slash_commands:
            for option in global_command.options:
                if option.type == OptionType.sub_command:
                    commands += (
                        f"</{global_command.name} {option.name}:{global_command.id}> "
                    )
            if global_command.name != "weapons":
                commands += f"</{global_command.name}:{global_command.id}> "

        member_count = sum([guild.member_count for guild in bot.guilds])
        self.add_field(
            "The GWW has",
            f"{len(bot.global_slash_commands)} commands available:\n{commands}",
            inline=False,
        ).add_field("Currently in", f"{len(bot.guilds)} discord servers").add_field(
            "Members of Democracy", f"{member_count:,}"
        ).add_field(
            "Approx. user installs", user_installs
        )

        memory_used = Process(getpid()).memory_info().rss / 1024**2
        latency = 9999.999 if bot.latency == float(inf) else bot.latency
        self.add_field(
            "Hardware Info",
            (
                f"**CPU**: {cpu_percent()}%\n"
                f"**RAM**: {memory_used:.2f}MB\n"
                f"**Last restart**: <t:{int(bot.startup_time.timestamp())}:R>\n"
                f"**Latency**: {int(latency * 1000)}ms"
            ),
            inline=True,
        )
        cogs = {
            "This Dashboard": ("GuildManagementCog", "bot_dashboard"),
            "All Dashboards": ("DashboardCog", "dashboard_poster"),
            "All Maps": ("MapCog", "map_poster"),
            "Update data": ("DataManagementCog", "pull_from_api"),
            "Major Order Update": ("AnnouncementsCog", "major_order_updates"),
            "Personal Order Update": ("PersonalOrderCog", "personal_order_update"),
        }
        update_times = {}
        for label, (cog_name, attribute_name) in cogs.items():
            next_iteration = getattr(
                bot.get_cog(cog_name), attribute_name
            ).next_iteration
            update_times[label] = (
                f"<t:{int(next_iteration.timestamp())}:R>"
                if next_iteration
                else "**__ERROR__**:warning:"
            )
        self.add_field(
            "Update Timers",
            "\n".join(f"{label}: {time}" for label, time in update_times.items()),
        )
        self.add_field("", "", inline=False)
        self.add_field(
            "Credits",
            (
                "https://helldivers.wiki.gg/ - Most of my enemy information is from them, as well as a lot of the enemy images.\n\n"
                "https://helldivers.news/ - Planet images are from them, their website is also amazing.\n\n"
                "https://github.com/helldivers-2/ - The people over here are kind and helpful, great work too!\n\n"
                "and **You**\n"
            ),
            inline=False,
        )

        self.add_field("", f"-# Updated <t:{int(now.timestamp())}:R>")


class DispatchesEmbed(Embed):
    def __init__(self, language_json: dict, dispatch: Dispatch):
        super().__init__(colour=Colour.yellow())
        self.add_field("", dispatch.message)
        self.set_footer(text=language_json["message"].format(message_id=dispatch.id))


class GlobalEventsEmbed(Embed):
    def __init__(self, language_json: dict, global_event: GlobalEvents.GlobalEvent):
        super().__init__(
            title=global_event.title, colour=Colour.from_rgb(*faction_colours["MO"])
        )
        for chunk in global_event.split_message:
            self.add_field("", chunk, inline=False)
        self.set_footer(
            text=language_json["message"].format(message_id=global_event.id)
        )


class SteamEmbed(Embed):
    def __init__(self, steam: Steam, language_json: dict):
        super().__init__(title=steam.title, colour=Colour.dark_grey(), url=steam.url)
        self.set_footer(text=language_json["message"].format(message_id=steam.id))
        if len(steam.content) > 4000:
            steam.content = steam.content[:3900] + language_json["SteamEmbed"][
                "head_here"
            ].format(url=steam.url)
        self.description = steam.content


class CampaignEmbed(Embed):
    def __init__(self, language_json: dict, planet_names_json: dict):
        self.language_json = language_json
        self.planet_names_json = planet_names_json
        super().__init__(
            title=f"{Emojis.decoration['left_banner']} {self.language_json['CampaignEmbed']['title']} {Emojis.decoration['right_banner']}",
            colour=Colour.brand_red(),
        )
        self.add_field(
            self.language_json["CampaignEmbed"]["victories"], "", inline=False
        )
        self.add_field(
            self.language_json["CampaignEmbed"]["planets_lost"], "", inline=False
        )
        self.add_field(
            self.language_json["CampaignEmbed"]["new_battles"], "", inline=False
        )
        self.add_field(
            self.language_json["dss"]["title"] + " " + Emojis.dss["dss"],
            "",
            inline=False,
        )
        self.add_field(
            self.language_json["CampaignEmbed"]["invasions"], "", inline=False
        )

    def add_new_campaign(self, campaign: Campaign, time_remaining: str | None):
        description = self.fields[2].value
        exclamation = ""
        if campaign.planet.dss:
            exclamation += Emojis.dss["dss"]
        if campaign.planet.in_assignment:
            exclamation += Emojis.icons["MO"]
        if campaign.planet.event and time_remaining:
            def_level_exc = {0: "", 5: "!", 20: "!!", 33: "!!!", 50: ":warning:"}
            key = [
                key
                for key in def_level_exc.keys()
                if key <= campaign.planet.event.level
            ][-1]
            def_level_exc = def_level_exc[key]
            if campaign.planet.event.type != 2:
                description += self.language_json["CampaignEmbed"][
                    "defend_planet"
                ].format(
                    planet=self.planet_names_json[str(campaign.planet.index)]["names"][
                        self.language_json["code_long"]
                    ],
                    faction_emoji=Emojis.factions[campaign.faction],
                    exclamation=exclamation,
                )
                description += self.language_json["CampaignEmbed"][
                    "defence_level"
                ].format(level=campaign.planet.event.level, exclamation=def_level_exc)
                description += f"\n> *{self.language_json['ends']} {time_remaining}*\n"
            else:
                description += self.language_json["CampaignEmbed"][
                    "repel_invasion"
                ].format(
                    planet=self.planet_names_json[str(campaign.planet.index)]["names"][
                        self.language_json["code_long"]
                    ],
                    faction_emoji=Emojis.factions[campaign.faction],
                    exclamation=exclamation,
                )
                description += self.language_json["CampaignEmbed"][
                    "defence_level"
                ].format(level=campaign.planet.event.level, exclamation=def_level_exc)
                description += f"\n> *{self.language_json['ends']} {time_remaining}*\n"
        else:
            description += self.language_json["CampaignEmbed"]["liberate"].format(
                planet=self.planet_names_json[str(campaign.planet.index)]["names"][
                    self.language_json["code_long"]
                ],
                faction_emoji=Emojis.factions[campaign.faction],
                exclamation=exclamation,
            )
        self.set_field_at(2, self.fields[2].name, description, inline=False)

    def add_campaign_victory(self, planet: Planet, taken_from: str):
        description = self.fields[0].value
        exclamation = ""
        if planet.dss:
            exclamation += Emojis.dss["dss"]
        if planet.in_assignment:
            exclamation += Emojis.icons["MO"]
        description += self.language_json["CampaignEmbed"]["been_liberated"].format(
            emoji=Emojis.icons["victory"],
            planet=self.planet_names_json[str(planet.index)]["names"][
                self.language_json["code_long"]
            ],
            faction=self.language_json["factions"][taken_from],
            faction_emoji=Emojis.factions[taken_from],
            exclamation=exclamation,
        )
        self.set_field_at(0, self.fields[0].name, description, inline=False)

    def add_def_victory(self, planet: Planet):
        description = self.fields[0].value
        exclamation = ""
        if planet.dss:
            exclamation += Emojis.dss["dss"]
        if planet.in_assignment:
            exclamation += Emojis.icons["MO"]
        description += self.language_json["CampaignEmbed"]["been_defended"].format(
            emoji=Emojis.icons["victory"],
            planet=self.planet_names_json[str(planet.index)]["names"][
                self.language_json["code_long"]
            ],
            exclamation=exclamation,
        )
        self.set_field_at(0, self.fields[0].name, description, inline=False)

    def add_planet_lost(self, planet: Planet):
        description = self.fields[1].value
        exclamation = ""
        if planet.dss:
            exclamation += Emojis.dss["dss"]
        if planet.in_assignment:
            exclamation += Emojis.icons["MO"]
        description += self.language_json["CampaignEmbed"]["been_lost"].format(
            planet=self.planet_names_json[str(planet.index)]["names"][
                self.language_json["code_long"]
            ],
            faction=planet.current_owner,
            faction_emoji=Emojis.factions[planet.current_owner],
            exclamation=exclamation,
        )
        self.set_field_at(1, self.fields[1].name, description, inline=False)

    def add_invasion_over(self, planet: Planet, faction: str):
        name = self.fields[4].name
        description = self.fields[4].value
        exclamation = ""
        if planet.dss:
            exclamation += Emojis.dss["dss"]
        if planet.in_assignment:
            exclamation += Emojis.icons["MO"]
        description += self.language_json["CampaignEmbed"]["invasion_over"].format(
            planet=self.planet_names_json[str(planet.index)]["names"][
                self.language_json["code_long"]
            ],
            faction_emoji=Emojis.factions[planet.current_owner],
            exclamation=exclamation,
        )
        description += self.language_json["CampaignEmbed"][
            "no_territory_change"
        ].format(
            faction=faction,
            faction_emoji=Emojis.factions[faction],
        )
        self.set_field_at(4, name, description, inline=False)

    def remove_empty(self):
        for field in self.fields.copy():
            if field.value == "":
                self.remove_field(self.fields.index(field))

    def dss_moved(self, before_planet: Planet, after_planet: Planet):
        description = self.fields[3].value
        exclamation = ""
        if after_planet.in_assignment:
            exclamation += Emojis.icons["MO"]
        if after_planet.event:
            exclamation += f" 🛡️ {Emojis.factions[after_planet.event.faction]}"
        description += self.language_json["CampaignEmbed"]["dss"]["has_moved"].format(
            planet1=self.planet_names_json[str(before_planet.index)]["names"][
                self.language_json["code_long"]
            ],
            faction_emoji1=Emojis.factions[before_planet.current_owner],
            planet2=self.planet_names_json[str(after_planet.index)]["names"][
                self.language_json["code_long"]
            ],
            faction_emoji2=Emojis.factions[after_planet.current_owner],
            exclamation=exclamation,
        )
        self.set_field_at(3, self.fields[3].name, description, inline=False)

    def ta_status_changed(self, tactical_action: DSS.TacticalAction):
        statuses = {1: "preparing", 2: "active", 3: "on_cooldown"}
        description = self.fields[3].value
        description += self.language_json["CampaignEmbed"]["dss"][
            "ta_status_change"
        ].format(
            ta_name=tactical_action.name,
            status=self.language_json["dashboard"]["DSSEmbed"][
                statuses[tactical_action.status]
            ],
        )
        self.set_field_at(3, self.fields[3].name, description, inline=False)


class Dashboard:
    def __init__(self, data: Data, language_code: str, json_dict: dict):
        language_json = json_dict["languages"][language_code]
        self._major_order_embed = self.MajorOrderEmbed(
            assignment=data.assignment,
            planets=data.planets,
            liberation_changes=data.liberation_changes,
            player_requirements=data.planets_with_player_reqs,
            language_json=language_json,
            json_dict=json_dict,
        )
        self._dss_embed = self.DSSEmbed(dss=data.dss, language_json=language_json)
        self._defence_embed = self.DefenceEmbed(
            planet_events=data.planet_events,
            liberation_changes=data.liberation_changes,
            player_requirements=data.planets_with_player_reqs,
            language_json=language_json,
            planet_names=json_dict["planets"],
            total_players=data.total_players,
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
        )
        self._footer_embed = self.FooterEmbed(
            language_json=language_json, total_players=data.total_players
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
        for embed in self.embeds.copy():
            if len(embed.fields) == 0:
                self.embeds.remove(embed)
            else:
                embed.set_image(
                    "https://i.imgur.com/cThNy4f.png"
                )  # blank line (max size, dont change)

    class MajorOrderEmbed(Embed):
        def __init__(
            self,
            assignment: Assignment | None,
            planets: Planets,
            liberation_changes: dict,
            player_requirements: dict,
            language_json: dict,
            json_dict: dict,
        ):
            super().__init__(
                title=language_json["dashboard"]["MajorOrderEmbed"]["title"],
                colour=Colour.from_rgb(r=255, g=220, b=0),
            )
            if not assignment:
                self.add_field(
                    name="",
                    value=language_json["major_order"]["MO_unavailable"],
                )
                return
            else:
                task_numbers = [task.type for task in assignment.tasks]
                task_for_image = max(set(task_numbers), key=task_numbers.count)
                image_link = assignment_task_images_dict.get(task_for_image, None)
                if image_link:
                    self.set_thumbnail(url=image_link)
                self.add_description(assignment=assignment, language_json=language_json)
                for task in assignment.tasks:
                    task: Tasks.Task
                    if task.type == 2:
                        self.add_type_2(
                            task=task,
                            language_json=language_json,
                            item_names_json=json_dict["items"]["item_names"],
                            planet_names_json=json_dict["planets"],
                            planet=planets[task.values[8]],
                        )
                    elif task.type == 3:
                        self.add_type_3(
                            task=task,
                            language_json=language_json,
                            species_dict=json_dict["enemies"]["enemy_ids"],
                        )
                    elif task.type == 11:
                        self.add_type_11(
                            task=task,
                            language_json=language_json,
                            planet=planets[task.values[2]],
                            planet_names_json=json_dict["planets"],
                        )
                    elif task.type == 12:
                        self.add_type_12(
                            task=task,
                            language_json=language_json,
                            liberation_changes=liberation_changes,
                            player_requirements=player_requirements,
                            planet_names_json=json_dict["planets"],
                            planet=(
                                planets[task.values[3]] if task.values[3] != 0 else None
                            ),
                        )
                    elif task.type == 13:
                        self.add_type_13(
                            task=task,
                            language_json=language_json,
                            planet=planets[task.values[2]],
                            liberation_changes=liberation_changes,
                            player_requirements=player_requirements,
                            planet_names_json=json_dict["planets"],
                        )
                    elif task.type == 15:
                        self.add_type_15(task=task, language_json=language_json)
                    else:
                        self.add_field("", "Calibrating...")
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
            task: Tasks.Task,
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
                    Emojis.icons["MO_task_complete"]
                    if task.progress == 1
                    else Emojis.icons["MO_task_incomplete"]
                ),
                amount=short_format(task.values[2]),
                item=item_names_json[str(task.values[4])]["name"],
                planet=planet_names_json[str(planet.index)]["names"][
                    language_json["code_long"]
                ],
            )
            value = (
                ""
                if task.progress == 1
                else (
                    f"{language_json['dashboard']['progress']}: **{task.values[2]*task.progress:,.0f}**\n"
                    f"{task.health_bar}\n"
                    f"`{(task.progress):^25,.2%}`\n"
                )
            )
            self.add_field(
                name=name,
                value=value,
                inline=False,
            )

        def add_type_3(self, task: Tasks.Task, language_json: dict, species_dict: dict):
            """Kill enemies of a type"""
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
                    Emojis.icons["MO_task_complete"]
                    if task.progress == 1
                    else Emojis.icons["MO_task_incomplete"]
                ),
                amount=short_format(task.values[2]),
                target=target,
            )
            if task.values[5] != 0:
                weapon_to_use = stratagem_id_dict.get(task.values[5], "Unknown")
                full_task += language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type3.5"
                ].format(weapon_to_use=weapon_to_use)
            self.add_field(
                name=full_task,
                value=(
                    f"{language_json['dashboard']['progress']}: **{(task.values[2]*task.progress):,.0f}**\n"
                    f"{task.health_bar}\n"
                    f"`{(task.progress):^25,.2%}`"
                ),
                inline=False,
            )

        def add_type_11(
            self,
            task: Tasks.Task,
            language_json: dict,
            planet: Planet,
            planet_names_json: dict,
        ):
            """Liberate a planet"""
            if planet.event:
                task.health_bar = health_bar(
                    planet.event.progress,
                    planet.event.faction,
                    True,
                )
                completed = f"🛡️ {Emojis.factions[planet.event.faction]}"
                health_text = f"{1 - planet.event.progress:^25,.2%}"
            else:
                task.health_bar = health_bar(
                    planet.health_perc,
                    planet.current_owner,
                    True if planet.current_owner != "Humans" else False,
                )
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
            feature_text = "" if not planet.feature else f"Feature: {planet.feature}\n"
            obj_text = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                "type11"
            ].format(
                status_emoji=(
                    Emojis.icons["MO_task_complete"]
                    if task.progress == 1
                    else Emojis.icons["MO_task_incomplete"]
                ),
                planet=planet_names_json[str(planet.index)]["names"][
                    language_json["code_long"]
                ],
            )
            player_count = language_json["dashboard"]["heroes"].format(
                heroes=f'{planet.stats["playerCount"]:,}'
            )
            self.add_field(
                name=obj_text,
                value=(
                    f"{player_count}\n"
                    f"{feature_text}"
                    f"{language_json['dashboard']['progress']}:\n"
                    f"{task.health_bar} {completed}\n"
                    f"`{health_text}`\n"
                ),
                inline=False,
            )

        def add_type_12(
            self,
            task: Tasks.Task,
            language_json: dict,
            liberation_changes: dict,
            player_requirements: dict,
            planet_names_json: dict,
            planet: Planet | None,
        ):
            """Succeed in defence of # <enemy> planets"""
            if planet:
                outlook_text = ""
                required_players = ""
                liberation_text = ""
                planet_lib_changes = liberation_changes.get(planet.index, None)
                if (
                    planet_lib_changes
                    and len(planet_lib_changes["liberation_changes"]) > 0
                    and sum(planet_lib_changes["liberation_changes"]) != 0
                ):
                    now_seconds = int(datetime.now().timestamp())
                    seconds_until_complete = int(
                        (
                            (100 - planet_lib_changes["liberation"])
                            / sum(planet_lib_changes["liberation_changes"])
                        )
                        * 3600
                    )
                    winning = (
                        datetime.fromtimestamp(now_seconds + seconds_until_complete)
                        < planet.event.end_time_datetime
                    )
                    if winning:
                        outlook_text = f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + seconds_until_complete}:R>"
                    else:
                        outlook_text = f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['defeat'])}"
                    change = (
                        f"{(sum(planet_lib_changes['liberation_changes'])):+.2f}%/hour"
                    )
                    liberation_text = f"\n`{change:^25}`"
                    if player_requirements and planet.index in player_requirements:
                        required_players = f"\n{language_json['dashboard']['DefenceEmbed']['players_required']}: **~{player_requirements[planet.index]:,.0f}+**"
                time_remaining = (
                    f"<t:{planet.event.end_time_datetime.timestamp():.0f}:R>"
                )
                objective_text = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type12_with_planet"
                ].format(
                    status_emoji=(
                        Emojis.icons["MO_task_complete"]
                        if task.progress == 1
                        else Emojis.icons["MO_task_incomplete"]
                    ),
                    planet=planet_names_json[str(planet.index)]["names"][
                        language_json["code_long"]
                    ],
                    number=task.values[0],
                    faction=language_json["factions"][str(task.values[1])],
                )
                feature_text = (
                    "" if not planet.feature else f"Feature: {planet.feature}"
                )
                player_count = (
                    language_json["dashboard"]["heroes"].format(
                        heroes=f"{planet.stats['playerCount']:,}"
                    )
                    if task.progress != 1
                    else ""
                )
                self.add_field(
                    objective_text,
                    (
                        f"{feature_text}"
                        f"\n{player_count}"
                        f"\n{language_json['ends']} {time_remaining}"
                        f"\n{language_json['dashboard']['DefenceEmbed']['level']} {int(planet.event.max_health / 50000)}"
                        f"{outlook_text}"
                        f"{required_players}"
                        f"\n{language_json['dashboard']['progress']}:\n"
                        f"{health_bar(perc=planet.event.progress, race=planet.event.faction, reverse=True)} 🛡️"
                        f"\n`{1 - planet.event.progress:^25,.2%}`"
                        f"{liberation_text}"
                    ),
                    inline=False,
                )
            else:
                objective_text = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type12_without_planet"
                ].format(
                    status_emoji=(
                        Emojis.icons["MO_task_complete"]
                        if task.progress == 1
                        else Emojis.icons["MO_task_incomplete"]
                    ),
                    number=task.values[0],
                    faction=language_json["factions"][str(task.values[1])],
                )
                self.add_field(
                    objective_text,
                    (
                        f"{language_json['dashboard']['progress']}: {int(task.progress*task.values[0])}/{task.values[0]}\n"
                        f"{task.health_bar}\n"
                        f"`{(task.progress):^25,.2%}`\n"
                    ),
                    inline=False,
                )

        def add_type_13(
            self,
            task: Tasks.Task,
            language_json: dict,
            planet: Planet,
            liberation_changes: dict,
            player_requirements: dict,
            planet_names_json: dict,
        ):
            """Hold a planet until the end of the MO"""
            feature_text = "" if not planet.feature else f"Feature: {planet.feature}"
            obj_text = language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                "type13"
            ].format(
                status_emoji=(
                    Emojis.icons["MO_task_complete"]
                    if task.progress == 1
                    else Emojis.icons["MO_task_incomplete"]
                ),
                planet=planet_names_json[str(planet.index)]["names"][
                    language_json["code_long"]
                ],
            )
            player_count = (
                language_json["dashboard"]["heroes"].format(
                    heroes=f"{planet.stats['playerCount']:,}"
                )
                if task.progress != 1 or planet.event
                else ""
            )
            if planet.event:
                outlook_text = ""
                required_players = ""
                liberation_text = ""
                planet_lib_changes = liberation_changes.get(planet.index, None)
                if (
                    planet_lib_changes
                    and len(planet_lib_changes["liberation_changes"]) > 0
                    and sum(planet_lib_changes["liberation_changes"]) != 0
                ):
                    now_seconds = int(datetime.now().timestamp())
                    seconds_until_complete = int(
                        (
                            (100 - planet_lib_changes["liberation"])
                            / sum(planet_lib_changes["liberation_changes"])
                        )
                        * 3600
                    )
                    winning = (
                        datetime.fromtimestamp(now_seconds + seconds_until_complete)
                        < planet.event.end_time_datetime
                    )
                    if winning:
                        outlook_text = f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + seconds_until_complete}:R>"
                    else:
                        outlook_text = f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['defeat'])}"
                    change = (
                        f"{(sum(planet_lib_changes['liberation_changes'])):+.2f}%/hour"
                    )
                    liberation_text = f"\n`{change:^25}`"
                    if player_requirements and planet.index in player_requirements:
                        required_players = f"\n{language_json['dashboard']['DefenceEmbed']['players_required']}: **~{player_requirements[planet.index]:,.0f}+**"
                time_remaining = (
                    f"<t:{planet.event.end_time_datetime.timestamp():.0f}:R>"
                )
                self.add_field(
                    obj_text,
                    (
                        f"{feature_text}"
                        f"\n{player_count}"
                        f"\n{language_json['ends']} {time_remaining}"
                        f"\n{language_json['dashboard']['DefenceEmbed']['level']} {int(planet.event.max_health / 50000)}"
                        f"{outlook_text}"
                        f"{required_players}"
                        f"\n{language_json['dashboard']['progress']}:\n"
                        f"{health_bar(perc=planet.event.progress, race=planet.event.faction, reverse=True)} 🛡️"
                        f"\n`{1 - planet.event.progress:^25,.2%}`"
                        f"{liberation_text}"
                    ),
                    inline=False,
                )
            else:
                if task.progress == 1:
                    self.add_field(obj_text, "", inline=False)
                else:
                    planet_health_bar = health_bar(
                        perc=planet.health_perc,
                        race=planet.current_owner,
                        reverse=True if planet.current_owner != "Humans" else False,
                    )
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
                    self.add_field(
                        obj_text,
                        (
                            f"{player_count}\n"
                            f"{feature_text}"
                            f"{language_json['dashboard']['progress']}:\n"
                            f"{planet_health_bar} {completed}\n"
                            f"`{health_text}`\n"
                        ),
                        inline=False,
                    )

        def add_type_15(self, task: Tasks.Task, language_json: dict):
            """Win more campaigns than lost"""
            percent = task_type_15_progress_dict[
                [
                    key
                    for key in task_type_15_progress_dict.keys()
                    if key <= task.progress
                ][-1]
            ]
            if percent > 0.5:
                outlook = language_json["victory"]
                event_health_bar = health_bar(
                    perc=percent,
                    race="Humans",
                )
            else:
                outlook = language_json["defeat"]
                event_health_bar = health_bar(perc=percent, race="Automaton")
            self.add_field(
                name=language_json["dashboard"]["MajorOrderEmbed"]["tasks"][
                    "type15"
                ].format(
                    status_emoji=(
                        Emojis.icons["MO_task_complete"]
                        if task.progress >= 1
                        else Emojis.icons["MO_task_incomplete"]
                    )
                ),
                value=(
                    f"{language_json['dashboard']['outlook'].format(outlook=outlook)}\n"
                    f"{event_health_bar}\n"
                    f"`{task.progress:^25,}`\n"
                ),
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
                rewards_text += f"{reward['amount']:,} **{reward_name}s** {Emojis.items.get(reward_name, '')}\n"
            self.add_field(
                language_json["dashboard"]["MajorOrderEmbed"]["rewards"], rewards_text
            )

    class DSSEmbed(Embed):
        def __init__(self, dss: DSS, language_json: dict):
            super().__init__(
                title=language_json["dss"]["title"],
                colour=Colour.from_rgb(*faction_colours["DSS"]),
            )
            if dss not in ("Error", None):
                self.set_thumbnail(
                    url="https://cdn.discordapp.com/attachments/1213146233825271818/1310906165823148043/DSS.png?ex=6746ec01&is=67459a81&hm=ab1c29616fd787f727848b04e44c26cc74e045b6e725c45b9dd8a902ec300757&"
                )
                self.description = language_json["dashboard"]["DSSEmbed"][
                    "stationed_at"
                ].format(
                    planet=dss.planet.name,
                    faction_emoji=Emojis.factions[dss.planet.current_owner],
                )
                self.description += language_json["dashboard"]["DSSEmbed"][
                    "next_move"
                ].format(timestamp=f"<t:{int(dss.election_date_time.timestamp())}:R>")

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
                        cost_formatted = language_json["dashboard"]["DSSEmbed"][
                            "cost"
                        ].format(
                            amount=f"{tactical_action.cost.target:,}",
                            emoji=Emojis.items[tactical_action.cost.item],
                            item=tactical_action.cost.item,
                        )
                        submittable_formatted = language_json["dashboard"]["DSSEmbed"][
                            "max_submitable"
                        ].format(
                            number=f"{tactical_action.cost.max_per_seconds[0]:,}",
                            hours=f"{tactical_action.cost.max_per_seconds[1]/3600:.0f}",
                        )
                        cost = (
                            f"{cost_formatted}\n"
                            f"{language_json['dashboard']['progress']}: **{tactical_action.cost.current:,.0f}**\n"
                            f"{submittable_formatted}\n"
                            f"{ta_health_bar}\n"
                            f"`{tactical_action.cost.progress:^25.2%}`"
                        )
                    elif status == "active":
                        cost = f"{language_json['ends']} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>\n"
                        cost += tactical_action.strategic_description
                    elif status == "on_cooldown":
                        cost = f"{language_json['dashboard']['DSSEmbed']['off_cooldown'].capitalize()} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
                    self.add_field(
                        f"{Emojis.dss[tactical_action.name.lower().replace(' ', '_')]} {tactical_action.name.title()}",
                        (
                            f"{language_json['dashboard']['DSSEmbed']['status']}: **{language_json['dashboard']['DSSEmbed'][status]}**\n"
                            f"{cost}"
                        ),
                        inline=False,
                    )

    class DefenceEmbed(Embed):
        def __init__(
            self,
            planet_events: PlanetEvents,
            liberation_changes: dict,
            player_requirements: dict,
            language_json: dict,
            planet_names: dict,
            total_players: int,
        ):
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
                    outlook_text = ""
                    required_players = ""
                    liberation_text = ""
                    if liberation_changes != {}:
                        liberation_change = liberation_changes.get(planet.index, None)
                        if (
                            liberation_change
                            and len(liberation_change["liberation_changes"]) > 0
                            and sum(liberation_change["liberation_changes"]) != 0
                        ):
                            now_seconds = int(datetime.now().timestamp())
                            seconds_until_complete = int(
                                (
                                    (100 - liberation_change["liberation"])
                                    / sum(liberation_change["liberation_changes"])
                                )
                                * 3600
                            )
                            winning = (
                                datetime.fromtimestamp(
                                    now_seconds + seconds_until_complete
                                )
                                < planet.event.end_time_datetime
                            )
                            if winning:
                                outlook_text = f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + seconds_until_complete}:R>"
                            else:
                                outlook_text = f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['defeat'])}"
                            change = f"{(sum(liberation_change['liberation_changes'])):+.2f}%/hour"
                            liberation_text = f"\n`{change:^25}`"
                            if (
                                player_requirements
                                and planet.index in player_requirements
                            ):
                                required_players = f"\n{language_json['dashboard']['DefenceEmbed']['players_required']}: **~{player_requirements[planet.index]:,.0f}+**"
                    time_remaining = (
                        f"<t:{planet.event.end_time_datetime.timestamp():.0f}:R>"
                    )
                    exclamation = Emojis.icons["MO"] if planet.in_assignment else ""
                    feature_text = (
                        "" if not planet.feature else f"\nFeature: {planet.feature}"
                    )
                    if planet.dss:
                        exclamation += Emojis.dss["dss"]
                    player_count = f'**{planet.stats["playerCount"]:,}**'
                    self.add_field(
                        f"{Emojis.factions[planet.event.faction]} - __**{planet_names[str(planet.index)]['names'][language_json['code_long']]}**__ {exclamation}",
                        (
                            f"{language_json['ends']} {time_remaining}"
                            f"\n{language_json['dashboard']['DefenceEmbed']['level']} {int(planet.event.max_health / 50000)}"
                            f"{outlook_text}"
                            f"\n{language_json['dashboard']['heroes'].format(heroes=player_count)}"
                            f"{feature_text}"
                            f"{required_players}"
                            f"\n{language_json['dashboard']['DefenceEmbed']['event_health']}:"
                            f"\n{planet.event.health_bar}"
                            f"\n`{1 - (planet.event.health / planet.event.max_health):^25,.2%}`"
                            f"{liberation_text}"
                            "\u200b\n"
                        ),
                        inline=False,
                    )
            else:
                self.add_field(
                    language_json["dashboard"]["DefenceEmbed"]["no_threats"],
                    f"||{language_json['dashboard']['DefenceEmbed']['for_now']}||",
                )

    class AttackEmbed(Embed):
        def __init__(
            self,
            campaigns: list[Campaign],
            liberation_changes: dict,
            language_json: dict,
            planet_names: dict,
            faction: str,
            total_players: int,
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
            skipped_campaigns = []
            for campaign in campaigns:
                if campaign.planet.stats["playerCount"] < total_players * 0.05:
                    skipped_campaigns.append(campaign)
                    continue
                else:
                    time_to_complete = ""
                    liberation_text = ""
                    if liberation_changes != {}:
                        liberation_change = liberation_changes.get(
                            campaign.planet.index, None
                        )
                        if (
                            liberation_change
                            and len(liberation_change["liberation_changes"]) > 0
                        ):
                            lib_per_hour = sum(liberation_change["liberation_changes"])
                            if lib_per_hour > 0.05:
                                now_seconds = int(datetime.now().timestamp())
                                seconds_to_complete = int(
                                    (
                                        (100 - liberation_change["liberation"])
                                        / sum(liberation_change["liberation_changes"])
                                    )
                                    * 3600
                                )
                                time_to_complete = f"\n{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + seconds_to_complete}:R>"
                                change = f"{(sum(liberation_change['liberation_changes'])):+.2f}%/hour"
                                liberation_text = f"\n`{change:^25}`"
                            else:
                                skipped_campaigns.append(campaign)
                                continue

                    exclamation = (
                        Emojis.icons["MO"] if campaign.planet.in_assignment else ""
                    )
                    if campaign.planet.dss:
                        exclamation += Emojis.dss["dss"]
                    if campaign.planet.regen_perc_per_hour <= 0.25:
                        exclamation += f" :warning: {campaign.planet.regen_perc_per_hour:.2f}% REGEN :warning:"
                    planet_health_bar = health_bar(
                        campaign.planet.health / campaign.planet.max_health,
                        campaign.planet.current_owner,
                        True,
                    )
                    planet_health_text = f"`{(1 - (campaign.planet.health / campaign.planet.max_health)):^25.2%}`"
                    feature_text = (
                        f"\nFeature: {campaign.planet.feature}"
                        if campaign.planet.feature
                        else ""
                    )
                    player_count = f'**{campaign.planet.stats["playerCount"]:,}**'
                    self.add_field(
                        f"{Emojis.factions[campaign.planet.current_owner]} - __**{planet_names[str(campaign.planet.index)]['names'][language_json['code_long']]}**__ {exclamation}",
                        (
                            f"{language_json['dashboard']['heroes'].format(heroes=player_count)}"
                            f"{feature_text}"
                            f"{time_to_complete}"
                            f"\n{language_json['dashboard']['AttackEmbed']['planet_health']}:"
                            f"\n{planet_health_bar}"
                            f"\n{planet_health_text}"
                            f"{liberation_text}"
                        ),
                        inline=False,
                    )

            if skipped_campaigns != []:
                skipped_planets_text = ""
                for campaign in skipped_campaigns:
                    campaign: Campaign
                    exclamation = (
                        Emojis.icons["MO"] if campaign.planet.in_assignment else ""
                    )
                    if campaign.planet.dss:
                        exclamation += f" {Emojis.dss['dss']}"
                    if campaign.planet.regen < 1:
                        exclamation += " :warning: 0% REGEN :warning:"
                    skipped_planets_text += f"-# {Emojis.factions[campaign.planet.current_owner]} - {planet_names[str(campaign.planet.index)]['names'][language_json['code_long']]} - **{campaign.planet.stats['playerCount']:,}** {exclamation}\n"
                if skipped_planets_text != "":
                    self.add_field(
                        f"{language_json['dashboard']['AttackEmbed']['low_impact']}",
                        skipped_planets_text,
                        inline=False,
                    )

    class FooterEmbed(Embed):
        def __init__(self, language_json: dict, total_players: int):
            super().__init__(colour=Colour.dark_embed())
            now = datetime.now()
            self.add_field(
                "",
                (
                    f"-# {language_json['dashboard']['FooterEmbed']['other_updated']}\n"
                    f"-# <t:{int(now.timestamp())}:f> - <t:{int(now.timestamp())}:R>"
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


class Items:
    class Weapons:
        class Primary(Embed):
            def __init__(
                self,
                weapon_json: dict,
                json_dict: dict,
                language_json: dict,
            ):
                super().__init__(
                    colour=Colour.blue(),
                    title=weapon_json["name"],
                    description=weapon_json["description"],
                )
                gun_fire_modes = ""
                for i in weapon_json["fire_mode"]:
                    gun_fire_modes += f"\n- **{json_dict['items']['fire_modes'][str(i)]} {Emojis.weapons[json_dict['items']['fire_modes'][str(i)]]}**"

                features = ""
                for i in weapon_json["traits"]:
                    if i != 0:
                        features += f"\n- **{json_dict['items']['weapon_traits'][str(i)]} {Emojis.weapons[json_dict['items']['weapon_traits'][str(i)]]}**"
                    else:
                        features = "\n- None"

                if 9 in weapon_json["traits"]:
                    weapon_json["capacity"] = language_json["WeaponEmbed"][
                        "constant_fire"
                    ].format(number=weapon_json["capacity"])
                    weapon_json["fire_rate"] = 60
                if weapon_json["capacity"] == 999:
                    weapon_json["capacity"] = "**∞**"
                information = ""
                information += language_json["WeaponEmbed"]["type"].format(
                    type=json_dict["items"]["weapon_types"][str(weapon_json["type"])]
                )
                information += language_json["WeaponEmbed"]["damage"].format(
                    damage=weapon_json["damage"]
                )
                information += language_json["WeaponEmbed"]["fire_rate"].format(
                    fire_rate=weapon_json["fire_rate"]
                )
                information += language_json["WeaponEmbed"]["dps"].format(
                    dps=f'{((weapon_json["damage"] * weapon_json["fire_rate"]) / 60):.2f}'
                )
                information += language_json["WeaponEmbed"]["capacity"].format(
                    capacity=weapon_json["capacity"],
                    emoji=(
                        Emojis.weapons["Capacity"]
                        if weapon_json["fire_rate"] != 0
                        else ""
                    ),
                )
                information += language_json["WeaponEmbed"]["fire_modes"].format(
                    fire_modes=gun_fire_modes
                )
                information += language_json["WeaponEmbed"]["features"].format(
                    features=features
                )
                self.add_field(
                    language_json["WeaponEmbed"]["information_title"],
                    information,
                )
                try:
                    self.set_thumbnail(
                        file=File(
                            f"resources/weapons/{weapon_json['name'].replace(' ', '-').replace('&', 'n')}.png"
                        )
                    )
                    self.image_set = True
                except:
                    self.image_set = False

        class Secondary(Embed):
            def __init__(
                self,
                weapon_json: dict,
                json_dict: dict,
                language_json: dict,
            ):
                super().__init__(
                    colour=Colour.blue(),
                    title=weapon_json["name"],
                    description=weapon_json["description"],
                )
                gun_fire_modes = ""
                for i in weapon_json["fire_mode"]:
                    gun_fire_modes += f"\n- **{json_dict['items']['fire_modes'][str(i)]} {Emojis.weapons[json_dict['items']['fire_modes'][str(i)]]}**"

                features = ""
                for i in weapon_json["traits"]:
                    if i != 0:
                        features += f"\n- **{json_dict['items']['weapon_traits'][str(i)]} {Emojis.weapons[json_dict['items']['weapon_traits'][str(i)]]}**"
                    else:
                        features = "\n- None"

                if 9 in weapon_json["traits"]:
                    weapon_json["capacity"] = language_json["WeaponEmbed"][
                        "constant_fire"
                    ].format(number=weapon_json["capacity"])
                    weapon_json["fire_rate"] = 60
                if weapon_json["capacity"] == 999:
                    weapon_json["capacity"] = "**∞**"
                information = ""
                information += language_json["WeaponEmbed"]["damage"].format(
                    damage=weapon_json["damage"]
                )
                information += language_json["WeaponEmbed"]["fire_rate"].format(
                    fire_rate=weapon_json["fire_rate"]
                )
                information += language_json["WeaponEmbed"]["dps"].format(
                    dps=f'{((weapon_json["damage"] * weapon_json["fire_rate"]) / 60):.2f}'
                )
                information += language_json["WeaponEmbed"]["capacity"].format(
                    capacity=weapon_json["capacity"],
                    emoji=(
                        Emojis.weapons["Capacity"]
                        if weapon_json["fire_rate"] != 0
                        else ""
                    ),
                )
                information += language_json["WeaponEmbed"]["fire_modes"].format(
                    fire_modes=gun_fire_modes
                )
                information += language_json["WeaponEmbed"]["features"].format(
                    features=features
                )
                self.add_field(
                    language_json["WeaponEmbed"]["information_title"],
                    information,
                )
                try:
                    self.set_thumbnail(
                        file=File(
                            f"resources/weapons/{weapon_json['name'].replace(' ', '-')}.png"
                        )
                    )
                    self.image_set = True
                except:
                    self.image_set = False

        class Grenade(Embed):
            def __init__(self, grenade_json: dict, language_json: dict):
                super().__init__(
                    colour=Colour.blue(),
                    title=grenade_json["name"],
                    description=grenade_json["description"],
                )
                information = ""
                information += language_json["WeaponEmbed"]["damage"].format(
                    damage=grenade_json["damage"]
                )
                information += language_json["WeaponEmbed"]["fuse_time"].format(
                    fuse_time=grenade_json["fuse_time"]
                )
                information += language_json["WeaponEmbed"]["penetration"].format(
                    penetration=grenade_json["penetration"]
                )
                information += language_json["WeaponEmbed"]["radius"].format(
                    radius=grenade_json["outer_radius"]
                )

                self.add_field(
                    language_json["WeaponEmbed"]["information_title"],
                    information,
                )
                try:
                    self.set_thumbnail(
                        file=File(
                            f"resources/weapons/{grenade_json['name'].replace(' ', '-')}.png"
                        )
                    )
                    self.image_set = True
                except:
                    self.image_set = False

    class Booster(Embed):
        def __init__(self, booster: dict):
            super().__init__(
                colour=Colour.blue(),
                title=booster["name"],
                description=booster["description"],
            )
            try:
                self.set_thumbnail(
                    file=File(
                        f"resources/boosters/{booster['name'].replace(' ', '_')}.png"
                    )
                )
                self.image_set = True
            except:
                self.image_set = False

    class Warbond(Embed):
        def __init__(self, warbond_json: dict, json_dict: dict, page: int):
            warbond_page = warbond_json["json"][str(page)]
            formatted_index = {
                warbond["name"]: warbond
                for warbond in json_dict["warbonds"]["index"].values()
            }
            cost = formatted_index[warbond_json["name"]]["credits_to_unlock"]
            super().__init__(
                colour=Colour.blue(),
                title=warbond_json["name"],
                description=(
                    f"Page {page}/{list(warbond_json['json'].keys())[-1]}\n"
                    f"Cost to unlock warbond: **{cost}** {Emojis.items['Super Credits']}\n"
                    f"Medals to unlock page: **{warbond_page['medals_to_unlock'] }** {Emojis.items['Medal']}\n"
                ),
            )
            self.set_image(warbond_images_dict[warbond_json["name"]])
            item_number = 1
            for item in warbond_page["items"]:
                item_json = None
                item_type = None
                for item_key, item_value in json_dict["items"]["armor"].items():
                    if int(item_key) == item["item_id"]:
                        item_json = item_value
                        item_type = "armor"
                        break
                for item_key, item_value in json_dict["items"][
                    "primary_weapons"
                ].items():
                    if item_type != None:
                        break
                    if int(item_key) == item["item_id"]:
                        item_json = item_value
                        item_type = "primary"
                        break
                for item_key, item_value in json_dict["items"][
                    "secondary_weapons"
                ].items():
                    if item_type != None:
                        break
                    if int(item_key) == item["item_id"]:
                        item_json = item_value
                        item_type = "secondary"
                        break
                for item_key, item_value in json_dict["items"]["grenades"].items():
                    if item_type != None:
                        break
                    if int(item_key) == item["item_id"]:
                        item_json = item_value
                        item_type = "grenade"
                        break

                if item_json != None:
                    if item_type == "armor":
                        self.add_field(
                            f"{item_json['name']}",
                            (
                                "Type: **Armor**\n"
                                f"Slot: **{json_dict['items']['armor_slots'][str(item_json['slot'])]}** {Emojis.armour[json_dict['items']['armor_slots'][str(item_json['slot'])]]}\n"
                                f"Armor Rating: **{item_json['armor_rating']}**\n"
                                f"Speed: **{item_json['speed']}**\n"
                                f"Stamina Regen: **{item_json['stamina_regen']}**\n"
                                f"Passive: **{json_dict['items']['armor_perks'][str(item_json['passive'])]['name']}**\n"
                                f"Medal Cost: **{item.get('medal_cost', None)} {Emojis.items['Medal']}**\n\n"
                            ),
                        )
                    elif item_type == "primary":
                        self.add_field(
                            f"{item_json['name']} {Emojis.weapons['Primary']}",
                            (
                                "Type: **Primary**\n"
                                f"Weapon type: **{json_dict['items']['weapon_types'][str(item_json['type'])]}**\n"
                                f"Damage: **{item_json['damage']}**\n"
                                f"Capacity: **{item_json['capacity']}** {Emojis.weapons['Capacity']}\n"
                                f"Recoil: **{item_json['recoil']}**\n"
                                f"Fire Rate: **{item_json['fire_rate']}**\n"
                                f"Medal Cost: **{item['medal_cost']} {Emojis.items['Medal']}**\n\n"
                            ),
                        )
                    elif item_type == "secondary":
                        self.add_field(
                            f"{item_json['name']} {Emojis.weapons['Secondary']}",
                            (
                                "Type: **Secondary**\n"
                                f"Damage: **{item_json['damage']}**\n"
                                f"Capacity: **{item_json['capacity']}** {Emojis.weapons['Capacity']}\n"
                                f"Recoil: **{item_json['recoil']}**\n"
                                f"Fire Rate: **{item_json['fire_rate']}**\n"
                                f"Medal Cost: **{item['medal_cost']} {Emojis.items['Medal']}**\n\n"
                            ),
                        )
                    elif item_type == "grenade":
                        self.add_field(
                            f"{item_json['name']} {Emojis.weapons['Grenade']}",
                            (
                                "Type: **Grenade**\n"
                                f"Damage: **{item_json['damage']}**\n"
                                f"Penetration: **{item_json['penetration']}**\n"
                                f"Outer Radius: **{item_json['outer_radius']}**\n"
                                f"Fuse Time: **{item_json['fuse_time']}**\n"
                                f"Medal Cost: **{item['medal_cost']} {Emojis.items['Medal']}**\n\n"
                            ),
                        )
                elif (
                    "Super Credits"
                    in json_dict["items"]["item_names"][str(item["item_id"])]["name"]
                ):
                    self.add_field(
                        f"{json_dict['items']['item_names'][str(item['item_id'])]['name']} {Emojis.items['Super Credits']}",
                        f"Medal cost: **{item['medal_cost']} {Emojis.items['Medal']}**",
                    )
                elif (
                    json_dict["items"]["item_names"][str(item["item_id"])]["name"]
                    in emotes_list
                ):
                    self.add_field(
                        f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                        (
                            "Type: Emote\n"
                            f"Medal cost: **{item['medal_cost']} {Emojis.items['Medal']}**"
                        ),
                    )
                elif (
                    json_dict["items"]["item_names"][str(item["item_id"])]["name"]
                    in victory_poses_list
                ):
                    self.add_field(
                        f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                        (
                            "Type: Victory Pose\n"
                            f"Medal cost: **{item['medal_cost']} {Emojis.items['Medal']}**"
                        ),
                    )
                elif (
                    json_dict["items"]["item_names"][str(item["item_id"])]["name"]
                    in player_cards_list
                ):
                    self.add_field(
                        f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                        (
                            "Type: Player Card\n"
                            f"Medal cost: **{item['medal_cost']} {Emojis.items['Medal']}**"
                        ),
                    )
                elif str(item["item_id"]) in json_dict["items"]["boosters"]:
                    self.add_field(
                        f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                        (
                            "Type: Booster\n"
                            f"Medal cost: **{item['medal_cost']} {Emojis.items['Medal']}**"
                        ),
                    )
                elif (
                    json_dict["items"]["item_names"][str(item["item_id"])]["name"]
                    in titles_list
                ):
                    self.add_field(
                        f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                        (
                            "Type: Title\n"
                            f"Medal cost: **{item['medal_cost']} {Emojis.items['Medal']}**"
                        ),
                    )
                elif (
                    json_dict["items"]["item_names"][str(item["item_id"])]["name"]
                    in stratagem_permit_list
                ):
                    self.add_field(
                        f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                        (
                            "Type: Stratagem Permit\n"
                            f"Medal cost: **{item['medal_cost']} {Emojis.items['Medal']}**"
                        ),
                    )
                else:
                    self.add_field(
                        f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                        f"Medal cost: **{item['medal_cost']} {Emojis.items['Medal']}**",
                    )
                if item_number % 2 == 0:
                    self.add_field("", "")
                item_number += 1


class StratagemEmbed(Embed):
    def __init__(self, stratagem_name: str, stratagem_stats: dict, language_json: dict):
        super().__init__(title=stratagem_name, colour=Colour.brand_green())
        key_inputs = ""
        for key in stratagem_stats["keys"]:
            key_inputs += Emojis.stratagems[key]
        self.add_field(
            language_json["StratagemEmbed"]["key_input"], key_inputs, inline=False
        )
        self.add_field(
            language_json["StratagemEmbed"]["uses"],
            stratagem_stats["uses"],
            inline=False,
        )
        self.add_field(
            language_json["StratagemEmbed"]["cooldown"],
            f"{stratagem_stats['cooldown']} seconds ({(stratagem_stats['cooldown']/60):.2f} minutes)",
        )
        try:
            self.set_thumbnail(
                file=File(
                    f"resources/stratagems/{stratagem_name.replace('/', '_').replace(' ', '_')}.png"
                )
            )
            self.image_set = True
        except:
            self.image_set = False


class EnemyEmbed(Embed):
    def __init__(
        self,
        faction: str,
        species_info: dict,
        language_json: dict,
        variation: bool = False,
    ):
        super().__init__(
            colour=Colour.from_rgb(*faction_colours[faction]),
            title=species_info["name"],
            description=species_info["info"]["desc"],
        )
        file_name = species_info["name"].replace(" ", "_")
        start_emoji = Emojis.difficulty[f"difficulty{species_info['info']['start']}"]
        self.add_field(
            language_json["EnemyEmbed"]["introduced"],
            f"{language_json['EnemyEmbed']['difficulty']} {species_info['info']['start']} {start_emoji}",
            inline=False,
        ).add_field(
            language_json["EnemyEmbed"]["tactics"],
            species_info["info"]["tactics"],
            inline=False,
        ).add_field(
            language_json["EnemyEmbed"]["weak_spots"],
            species_info["info"]["weak spots"],
            inline=False,
        )
        variations = ""
        if not variation and species_info["info"]["variations"] != None:
            for i in species_info["info"]["variations"]:
                variations += f"\n- {i}"
            self.add_field(language_json["EnemyEmbed"]["variations"], variations)
        try:
            self.set_thumbnail(
                file=File(f"resources/enemies/{faction.lower()}/{file_name}.png")
            )
            self.image_set = True
        except Exception as e:
            self.image_set = False
            self.error = e


class SetupEmbed(Embed):
    def __init__(self, guild: GWWGuild, language_json: dict):
        super().__init__(
            title=language_json["SetupEmbed"]["title"], colour=Colour.og_blurple()
        )

        # dashboard
        dashboard_text = f"{language_json['SetupEmbed']['dashboard_desc']}"
        if 0 not in (
            guild.dashboard_channel_id,
            guild.dashboard_message_id,
        ):
            dashboard_text += (
                f"{language_json['SetupEmbed']['dashboard_channel']}: <#{guild.dashboard_channel_id}>\n"
                f"{language_json['SetupEmbed']['dashboard_message']}: https://discord.com/channels/{guild.id}/{guild.dashboard_channel_id}/{guild.dashboard_message_id}"
            )
        else:
            dashboard_text += language_json["SetupEmbed"]["not_set"]
        self.add_field(
            language_json["SetupEmbed"]["dashboard"],
            dashboard_text,
            inline=False,
        )

        # announcements
        announcements_text = f"{language_json['SetupEmbed']['announcements_desc']}"
        if guild.announcement_channel_id != 0:
            announcements_text += f"{language_json['SetupEmbed']['announcement_channel']}: <#{guild.announcement_channel_id}>"
        else:
            announcements_text += language_json["SetupEmbed"]["not_set"]
        self.add_field(
            language_json["SetupEmbed"]["announcements"],
            announcements_text,
            inline=False,
        )

        # map
        map_text = f"{language_json['SetupEmbed']['map_desc']}"
        if 0 not in (guild.map_channel_id, guild.map_message_id):
            map_text += (
                f"{language_json['SetupEmbed']['map_channel']}: <#{guild.map_channel_id}>\n"
                f"{language_json['SetupEmbed']['map_message']}: https://discord.com/channels/{guild.id}/{guild.map_channel_id}/{guild.map_message_id}"
            )
        else:
            map_text += language_json["SetupEmbed"]["not_set"]
        self.add_field(
            language_json["SetupEmbed"]["map"],
            map_text,
            inline=False,
        )

        # patch notes
        patch_notes_enabled = {True: ":white_check_mark:", False: ":x:"}[
            guild.patch_notes
        ]
        self.add_field(
            f"{language_json['SetupEmbed']['patch_notes']}*",
            (
                f"{language_json['SetupEmbed']['patch_notes_desc']}"
                f"{patch_notes_enabled}"
            ),
        )

        # mo updates
        mo_enabled = {True: ":white_check_mark:", False: ":x:"}[
            guild.major_order_updates
        ]
        self.add_field(
            f"{language_json['SetupEmbed']['mo_updates']}*",
            (f"{language_json['SetupEmbed']['mo_updates_desc']}" f"{mo_enabled}"),
        )

        # po updates
        po_updates = {True: ":white_check_mark:", False: ":x:"}[
            guild.personal_order_updates
        ]
        self.add_field(
            f"{language_json['SetupEmbed']['po_updates']}*",
            (f"{language_json['SetupEmbed']['po_updates_desc']}" f"{po_updates}"),
        )

        # detailed dispatches
        detailed_dispatches = {True: ":white_check_mark:", False: ":x:"}[
            guild.detailed_dispatches
        ]
        self.add_field(
            f"{language_json['SetupEmbed']['detailed_dispatches']}*",
            (
                f"{language_json['SetupEmbed']['detailed_dispatches_desc']}"
                f"{detailed_dispatches}"
            ),
        )

        # language
        flag_dict = {
            "en": ":flag_gb:",
            "fr": ":flag_fr:",
            "de": ":flag_de:",
            "it": ":flag_it:",
        }
        self.add_field(
            language_json["SetupEmbed"]["language"].format(
                flag_emoji=flag_dict[guild.language]
            ),
            guild.language_long,
        )

        # extra
        self.add_field(
            "", language_json["SetupEmbed"]["footer_message_not_set"], inline=False
        )
        self.add_field(
            "",
            language_json["SetupEmbed"]["footer_message_announcements_asterisk"],
            inline=False,
        )


class FeedbackEmbed(Embed):
    def __init__(self, inter: ModalInteraction):
        super().__init__(
            title=inter.text_values["title"],
            description=inter.text_values["description"],
            colour=Colour.og_blurple(),
        )
        self.set_author(
            name=inter.author.id,
            icon_url=inter.author.avatar.url if inter.author.avatar != None else None,
        )


class SuperstoreEmbed(Embed):
    def __init__(self, superstore: Superstore):
        super().__init__(title=f"Superstore Rotation", colour=Colour.blue())
        now = datetime.now()
        expiration = datetime.strptime(superstore.expiration, "%d-%b-%Y %H:%M")
        warning = " :warning:" if expiration < now + timedelta(days=1) else ""
        self.description = f"Rotates <t:{int(expiration.timestamp())}:R>{warning}"
        for item in superstore.items:
            if "unmapped" in item["name"].lower():
                self.add_field("Item is new", "Try again later")
                continue
            passives = ""
            item_type = f"Type: **{item['type']}**\n" if item["slot"] == "Body" else ""
            if item["slot"] == "Body":
                passives_list = item["passive"]["description"].splitlines()
                passives = f"**{item['passive']['name']}**\n"
                for passive in passives_list:
                    passives += f"-# - {passive}\n"
            self.add_field(
                f"{item['name']} - {item['store_cost']} {Emojis.items['Super Credits']}",
                (
                    f"{item_type}"
                    f"Slot: **{item['slot']}** {Emojis.armour[item['slot']]}\n"
                    f"Armor: **{item['armor_rating']}**\n"
                    f"Speed: **{item['speed']}**\n"
                    f"Stamina Regen: **{item['stamina_regen']}**\n"
                    f"{passives}"
                ),
            )
        self.insert_field_at(1, "", "").insert_field_at(4, "", "")


class UsageEmbed(Embed):
    def __init__(self, command_usage: dict, guilds_joined: int):
        super().__init__(title="Daily Usage", colour=Colour.dark_theme())
        for command_name, usage in command_usage.items():
            self.add_field(f"/{command_name}", f"Used **{usage}** times", inline=False)
        self.add_field("Guilds joined", guilds_joined, inline=False)
        self.add_field(
            "", f"-# as of <t:{int(datetime.now().timestamp())}:R>", inline=False
        )


class DSSEmbed(Embed):
    def __init__(self, dss_data: DSS, language_json: dict):
        super().__init__(
            title=language_json["dss"]["title"],
            colour=Colour.from_rgb(r=38, g=156, b=182),
        )
        self.description = language_json["dashboard"]["DSSEmbed"][
            "stationed_at"
        ].format(
            planet=dss_data.planet.name,
            faction_emoji=Emojis.factions[dss_data.planet.current_owner],
        )
        self.description += language_json["dashboard"]["DSSEmbed"]["next_move"].format(
            timestamp=f"<t:{int(dss_data.election_date_time.timestamp())}:R>"
        )
        self.set_thumbnail(
            "https://cdn.discordapp.com/attachments/1212735927223590974/1312446626975187065/DSS.png?ex=674c86ab&is=674b352b&hm=3184fde3e8eece703b0e996501de23c89dc085999ebff1a77009fbee2b09ccad&"
        ).set_image(
            "https://cdn.discordapp.com/attachments/1212735927223590974/1312448218398986331/dss.jpg?ex=674c8827&is=674b36a7&hm=def01cbdf1920b85617b1028a95ec982484c70a5cf9bed14b9072319fd018246&"
        )
        for tactical_action in dss_data.tactical_actions:
            tactical_action: DSS.TacticalAction
            ta_health_bar = health_bar(tactical_action.cost.progress, "MO")
            status = {1: "preparing", 2: "active", 3: "on_cooldown"}[
                tactical_action.status
            ]
            if status == "preparing":
                cost_formatted = language_json["dashboard"]["DSSEmbed"]["cost"].format(
                    amount=f"{tactical_action.cost.target:,}",
                    emoji=Emojis.items[tactical_action.cost.item],
                    item=tactical_action.cost.item,
                )
                submittable_formatted = language_json["dashboard"]["DSSEmbed"][
                    "max_submitable"
                ].format(
                    number=f"{tactical_action.cost.max_per_seconds[0]:,}",
                    hours=f"{tactical_action.cost.max_per_seconds[1]/3600:.0f}",
                )
                cost = (
                    f"{cost_formatted}\n"
                    f"{language_json['dashboard']['progress']}: **{tactical_action.cost.current:,.0f}**\n"
                    f"{submittable_formatted}\n"
                    f"{ta_health_bar}\n"
                    f"`{tactical_action.cost.progress:^25.2%}`"
                )
            elif status == "active":
                cost = f"{language_json['ends']} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
            elif status == "on_cooldown":
                cost = f"{language_json['dashboard']['DSSEmbed']['off_cooldown'].capitalize()} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
            ta_long_description = tactical_action.strategic_description.replace(
                ". ", ".\n- "
            )
            self.add_field(
                f"{Emojis.dss[tactical_action.name.lower().replace(' ', '_')]} {tactical_action.name.title()}",
                (
                    f"{language_json['dashboard']['DSSEmbed']['status']}: **{language_json['dashboard']['DSSEmbed'][status]}**\n"
                    f"- {ta_long_description}\n"
                    f"{cost}\n\u200b\n"
                ),
                inline=False,
            )


class PersonalOrderEmbed(Embed):
    def __init__(
        self,
        personal_order: PersonalOrder,
        language_json: dict,
        reward_types: dict,
        item_names_json: dict,
        enemy_ids_json: dict,
    ):
        super().__init__(
            description=f"Personal order ends <t:{int(personal_order.expiration_datetime.timestamp())}:R>",
            colour=Colour.from_rgb(*faction_colours["MO"]),
        )
        self.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1212735927223590974/1329395683861594132/personal_order_icon.png?ex=678a2fb6&is=6788de36&hm=2f38b1b89aa5475862c8fdbde8d8fdbd003b39e8a4591d868a51814d57882da2&"
        )

        for task in personal_order.setting.tasks:
            task: PersonalOrder.Setting.Tasks.Task
            if task.type == 2:  # Extract with {number} {items}
                item = item_names_json.get(str(task.values[5]), None)
                if item:
                    item = item["name"]
                    full_objective = f"Successfully extract with {task.values[2]} {item}s {Emojis.items[item]}"
                else:
                    full_objective = (
                        f"Successfully extract from with {task.values[2]} **UNMAPPED**s"
                    )
                self.add_field(full_objective, "", inline=False)
            elif task.type == 3:  # Kill {number} {species} {stratagem}
                full_objective = f"Kill {task.values[2]} "
                if task.values[3] != 0:
                    enemy = enemy_ids_json.get(str(task.values[3]), "Unknown")
                    full_objective += f"{enemy}s"
                else:
                    full_objective += (
                        language_json["factions"][str(task.values[0] + 1)]
                        if task.values[0]
                        else "Enemies"
                    )
                stratagem = stratagem_id_dict.get(task.values[5], None)
                if stratagem:
                    self.set_thumbnail(url=stratagem_image_dict[task.values[5]])
                    full_objective += (
                        f" with the {stratagem_id_dict[task.values[5]]}"
                        if task.values[5]
                        else ""
                    )
                self.add_field(
                    full_objective,
                    "",
                    inline=False,
                )
            elif task.type == 4:  # Complete {number} {tier} objectives
                objective_type = {1: "primary", 2: "secondary"}[task.values[3]]
                full_objective = (
                    f"Complete {task.values[2]} {objective_type} objectives"
                )
                self.add_field(
                    full_objective,
                    "",
                    inline=False,
                )
            elif task.type == 7:  # Extract from {faction} {number} times
                faction = {
                    1: "Humans",
                    2: "Terminids",
                    3: "Automaton",
                    4: "Illuminate",
                }[task.values[0]]
                full_objective = f"Extract from a successful Mission against {faction} {task.values[2]} times"
                self.add_field(
                    full_objective,
                    "",
                    inline=False,
                )

        for reward in personal_order.setting.rewards:
            reward: PersonalOrder.Setting.Rewards.Reward
            reward_name = reward_types[str(reward.type)]
            self.add_field(
                "Reward",
                f"{reward.amount} {reward_name}s {Emojis.items[reward_name]}",
                inline=False,
            )
