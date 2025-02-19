from datetime import datetime
from math import inf
from os import getpid
from psutil import Process, cpu_percent
from data.lists import faction_colours, stratagem_image_dict, stratagem_id_dict
from disnake import Colour, Embed, OptionType
from utils.bot import GalacticWideWebBot
from utils.data import (
    DSS,
    Campaign,
    Dispatch,
    GlobalEvents,
    PersonalOrder,
    Planet,
    Planets,
    Steam,
)
from utils.emojis import Emojis
from utils.mixins import EmbedReprMixin


class APIChangesLoopEmbed(Embed, EmbedReprMixin):
    def __init__(self, total_changes: list):
        super().__init__(title="New changes in the API!", colour=Colour.brand_red())
        for change in total_changes:
            faction_emoji = (
                Emojis.factions[change.planet.current_owner]
                if not change.planet.event
                else Emojis.factions[change.planet.event.faction]
            )
            if change.statistic == "Regen %":
                self.add_field(
                    f"{faction_emoji} {change.planet.name}",
                    f"Planet Regeneration: **{change.before}**%/hr {Emojis.stratagems['right']} **{change.after}**%/hr",
                    inline=False,
                )
            elif change.statistic == "Waypoints":
                desctiption = "Waypoints:"
                waypoints_removed = [
                    waypoint
                    for waypoint in change.before
                    if waypoint not in change.after
                ]
                waypoints_added = [
                    waypoint
                    for waypoint in change.after
                    if waypoint not in change.before
                ]
                if waypoints_removed:
                    wp_list = "\n  - ".join(waypoints_removed)
                    desctiption += f"\n- Removed:\n  - {wp_list}"
                if waypoints_added:
                    wp_list = "\n  - ".join(waypoints_added)
                    desctiption += f"\n- Added:\n  - {wp_list}"
                self.add_field(
                    f"{faction_emoji} {change.planet.name}",
                    desctiption,
                    inline=False,
                )
            elif change.statistic == "Location":
                if change.planet.index == 64:
                    self.title = "Meridia has moved"
                    self.set_thumbnail(
                        url="https://cdn.discordapp.com/emojis/1331357764039086212.webp?size=96"
                    )
                description = f"Location:\n{change.before} {Emojis.stratagems['right']} {change.after}"
                description += f"\nChange: ({change.after[0] - change.before[0]:+.8f}, {change.after[1] - change.before[1]:+.8f})"
                self.add_field(
                    f"{faction_emoji} {change.planet.name}", description, inline=False
                )
            elif change.statistic == "Effects":
                removed_effects = [
                    effect for effect in change.before if effect not in change.after
                ]
                new_effects = [
                    effect for effect in change.after if effect not in change.before
                ]
                for effect in removed_effects:
                    if type(effect) == dict:
                        self.add_field(
                            "Removed effect",
                            f"**{effect['name']}**\n{effect['description']}",
                            inline=False,
                        )
                    else:
                        self.add_field("Removed effect", effect, inline=False)
                for effect in new_effects:
                    print(effect, type(effect))
                    if type(effect) == dict:
                        self.add_field(
                            "New effect",
                            f"**{effect['name']}**\n{effect['description']}",
                            inline=False,
                        )
                    else:
                        self.add_field("New effect", effect, inline=False)


class PersonalOrderLoopEmbed(Embed, EmbedReprMixin):
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
                    if enemy[-1] == "s":
                        full_objective += enemy
                    else:
                        full_objective += f"{enemy}s"
                else:
                    full_objective += (
                        language_json["factions"][str(task.values[0])]
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
            elif (
                task.type == 7
            ):  # Extract from successful mission {faction} {number} times
                faction_text = ""
                faction = {
                    1: "Humans",
                    2: "Terminids",
                    3: "Automaton",
                    4: "Illuminate",
                }.get(task.values[0], None)
                if faction:
                    faction_text = f"against {faction} "
                full_objective = f"Extract from a successful Mission {faction_text}{task.values[2]} times"
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


class BotDashboardLoopEmbed(Embed, EmbedReprMixin):
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


class DispatchesLoopEmbed(Embed, EmbedReprMixin):
    def __init__(self, language_json: dict, dispatch: Dispatch):
        super().__init__(colour=Colour.from_rgb(*faction_colours["MO"]))
        self.title, *description = dispatch.message.split("\n\n")
        self.description = "\n\n".join(description)
        self.set_footer(text=language_json["message"].format(message_id=dispatch.id))


class GlobalEventsLoopEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        planets: Planets,
        language_json: dict,
        planet_effects_json: dict,
        global_event: GlobalEvents.GlobalEvent,
    ):
        super().__init__(
            title=global_event.title, colour=Colour.from_rgb(*faction_colours["MO"])
        )
        if "OPEN LICENSE" in global_event.title:
            stratagem_name = global_event.title[15:]
            stratagem_code = [
                code
                for code, name in stratagem_id_dict.items()
                if stratagem_name.lower() in name.lower()
            ]
            if stratagem_code:
                stratagem_code = stratagem_code[0]
                stratagem_image = stratagem_image_dict.get(stratagem_code, None)
                self.set_thumbnail(url=stratagem_image)
        elif global_event.flag == 0:
            specific_planets = "\n- ".join(
                [planets[index].name for index in global_event.planet_indices]
            )
            if not specific_planets:
                specific_planets = "All"
            for effect_id in global_event.effect_ids:
                effect = planet_effects_json.get(str(effect_id))
                if not effect:
                    self.add_field(
                        "UNKNOWN effect",
                        f"-# Now active of the following planet(s):\n- {specific_planets}",
                        inline=False,
                    )
                else:
                    self.add_field(
                        effect["name"],
                        f"-# {effect['description']}\n-# Now active on the following planet(s):\n- {specific_planets}",
                        inline=False,
                    )
        else:
            for chunk in global_event.split_message:
                self.add_field("", chunk, inline=False)

        self.set_footer(
            text=language_json["message"].format(message_id=global_event.id)
        )


class SteamLoopEmbed(Embed, EmbedReprMixin):
    def __init__(self, steam: Steam, language_json: dict):
        super().__init__(title=steam.title, colour=Colour.dark_grey(), url=steam.url)
        self.set_footer(text=language_json["message"].format(message_id=steam.id))
        if len(steam.content) > 4000:
            steam.content = steam.content[:3900] + language_json["SteamEmbed"][
                "head_here"
            ].format(url=steam.url)
        self.description = steam.content


class CampaignLoopEmbed(Embed, EmbedReprMixin):
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
            def_level_exc = {0: "", 5: "!", 20: "!!", 33: "!!!", 50: " :warning:"}
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
                    "invasion_level"
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
                    "invasion_level"
                ].format(level=campaign.planet.event.level, exclamation=def_level_exc)
                potential_de = (
                    f"{(campaign.planet.event.potential_buildup / 1_000_000):.2%}"
                )
                description += self.language_json["CampaignEmbed"][
                    "potential_dark_energy"
                ].format(number=potential_de)
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
            emoji=Emojis.dss[tactical_action.name.lower().replace(" ", "_")],
            ta_name=tactical_action.name,
            status=self.language_json["dashboard"]["DSSEmbed"][
                statuses[tactical_action.status]
            ],
        )
        self.set_field_at(3, self.fields[3].name, description, inline=False)


class UsageLoopEmbed(Embed, EmbedReprMixin):
    def __init__(self, command_usage: dict, guilds_joined: int):
        super().__init__(title="Daily Usage", colour=Colour.dark_theme())
        for command_name, usage in command_usage.items():
            self.add_field(f"/{command_name}", f"Used **{usage}** times", inline=False)
        self.add_field("Guilds joined", guilds_joined, inline=False)
        self.add_field(
            "", f"-# as of <t:{int(datetime.now().timestamp())}:R>", inline=False
        )
