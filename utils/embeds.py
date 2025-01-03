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
)
from datetime import datetime, timedelta
from disnake import APISlashCommand, Embed, Colour, File, ModalInteraction, OptionType
from main import GalacticWideWebBot
from math import inf
from os import getpid
from psutil import Process, cpu_percent
from utils.db import GWWGuild
from utils.functions import health_bar, short_format, skipped_planets
from utils.data import DSS, Campaign, Data, Dispatch, Steam, Superstore, Tasks, Planet
from utils.emojis import Emojis


class PlanetEmbed(Embed):
    def __init__(self, planet_names: dict, planet: Planet, language: dict):
        super().__init__(colour=Colour.blue())
        if planet.current_owner == "Humans":
            planet_health_bar = health_bar(
                planet.event.progress if planet.event else planet.health_perc,
                planet.event.faction if planet.event else planet.current_owner,
                True if planet.event else False,
            )
            health_text = (
                f"{1 - planet.event.progress:^25,.2%}"
                if planet.event
                else f"{(planet.health_perc):^25,.2%}"
            )
        else:
            planet_health_bar = health_bar(
                planet.health_perc,
                planet.current_owner,
                True,
            )
            health_text = f"{1 - (planet.health_perc):^25,.2%}"
        enviros_text = ""
        for hazard in planet.hazards:
            enviros_text += f"\n- **{hazard['name']}**\n  - -# {hazard['description']}"
        dss_icon = Emojis.dss["dss"] if planet.dss else ""
        MO_icon = Emojis.icons["MO"] if planet.in_assignment else ""
        self.add_field(
            f"__**{planet_names['names'][language['code_long']]}**__ {dss_icon}{MO_icon}",
            (
                f"{language['sector']}: **{planet.sector}**\n"
                f"{language['planet']['owner']}: **{language[planet.current_owner.lower()]}** {Emojis.factions[planet.current_owner]}\n\n"
                f"🏔️ {language['planet']['biome']} \n- **{planet.biome['name']}**\n  - -# {planet.biome['description']}\n\n"
                f"🌪️ {language['planet']['environmentals']}:{enviros_text}\n\n"
                f"{language['planet']['planet_health']}\n"
                f"{planet_health_bar}{f' 🛡️{Emojis.factions[planet.event.faction]}' if planet.event else ''}\n"
                f"`{health_text}`\n"
                "\u200b\n"
            ),
            inline=False,
        ).add_field(
            f"📊 {language['planet']['mission_stats']}",
            (
                f"{language['planet']['missions_won']}: **`{short_format(planet.stats['missionsWon'])}`**\n"
                f"{language['planet']['missions_lost']}: **`{short_format(planet.stats['missionsLost'])}`**\n"
                f"{language['planet']['missions_winrate']}: **`{planet.stats['missionSuccessRate']}%`**\n"
                f"{language['planet']['missions_time_spent']}: **`{planet.stats['missionTime']/31556952:.1f} years`**"
            ),
        ).add_field(
            f"📈 {language['planet']['hero_stats']}",
            (
                f"{language['planet']['active_heroes']}: **`{planet.stats['playerCount']:,}`**\n"
                f"{language['planet']['heroes_lost']}: **`{short_format(planet.stats['deaths'])}`**\n"
                f"{language['planet']['accidents']}: **`{short_format(planet.stats['friendlies'])}`**\n"
                f"{language['planet']['shots_fired']}: **`{short_format(planet.stats['bulletsFired'])}`**\n"
                f"{language['planet']['shots_hit']}: **`{short_format(planet.stats['bulletsHit'])}`**\n"
                f"{language['planet']['accuracy']}: **`{planet.stats['accuracy']}%`**\n"
            ),
        )
        self.colour = Colour.from_rgb(*faction_colours[planet.current_owner])
        if planet.current_owner != "Humans":
            faction_kills = {
                "Automaton": "automatonKills",
                "Terminids": "terminidKills",
                "Illuminate": "illuminateKills",
            }[planet.current_owner if not planet.event else planet.event.faction]
            self.add_field(
                f"💀 {language[planet.current_owner.lower()]} {language['planet']['killed']}:",
                f"**{short_format(planet.stats[faction_kills])}**",
                inline=False,
            ).set_author(
                name=language["planet"]["liberation_progress"],
                icon_url={
                    "Automaton": "https://cdn.discordapp.com/emojis/1215036421551685672.webp?size=44&quality=lossless",
                    "Terminids": "https://cdn.discordapp.com/emojis/1215036423090999376.webp?size=44&quality=lossless",
                    "Illuminate": "https://cdn.discordapp.com/emojis/1317057914145603635.webp?size=44&quality=lossless",
                }.get(
                    planet.current_owner if not planet.event else planet.event.faction,
                    None,
                ),
            )
        if planet.feature:
            self.add_field("Feature", planet.feature)
        if planet.thumbnail:
            self.set_thumbnail(url=planet.thumbnail)
        try:
            self.set_image(
                file=File(
                    f"resources/biomes/{planet.biome['name'].lower().replace(' ', '_')}.png"
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
            "All Dashboards": ("DashboardCog", "dashboard"),
            "All Maps": ("MapCog", "map_poster"),
            "Update data": ("DataManagementCog", "pull_from_api"),
            "Major Order Update": ("AnnouncementsCog", "major_order_updates"),
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


class MajorOrderEmbed(Embed):
    def __init__(
        self,
        data: Data,
        language: dict,
        planet_names: dict,
        reward_types: dict,
        with_health_bars: bool = False,
    ):
        super().__init__(
            title=f"{Emojis.decoration['left_banner']} {language['major_order']['title']} {Emojis.decoration['right_banner']}",
            colour=Colour.yellow(),
        )
        self.add_field(
            f"{language['message']} #{data.assignment.id}",
            f"{data.assignment.title}\n{data.assignment.description}",
        )
        for task in data.assignment.tasks:
            task: Tasks.Task
            if task.type in (11, 13):
                planet: Planet = data.planets[task.values[2]]
                text = f"{language['heroes']}: **{planet.stats['playerCount']:,}**\n"
                if with_health_bars:
                    health = (
                        1 - planet.event.progress
                        if planet.event
                        else (
                            (1 - (planet.health / planet.max_health))
                            if planet.current_owner != "Humans"
                            else (planet.health / planet.max_health)
                        )
                    )
                    if planet.event:
                        planet_health_bar = health_bar(
                            planet.event.progress,
                            "MO",
                            True,
                        )
                    else:
                        planet_health_bar = health_bar(
                            planet.health / planet.max_health,
                            ("MO" if planet.current_owner != "Humans" else "Humans"),
                            True if planet.current_owner != "Humans" else False,
                        )
                    text += f"{planet_health_bar}\n"
                    text += f"`{(health):^25,.2%}`\n"
                text += f"{language['dashboard']['major_order']['occupied_by']}: **{language[planet.current_owner.lower()]}**\n"
                if planet.feature:
                    text += f"Feature: {planet.feature}"
                if task.type == 11:
                    obj_text = f"{language['dashboard']['major_order']['liberate']} {planet_names[str(planet.index)]['names'][language['code_long']]}"
                else:
                    obj_text = f"{language['dashboard']['major_order']['hold']} {planet_names[str(planet.index)]['names'][language['code_long']]} {language['dashboard']['major_order']['when_the_order_expires']}"

                self.add_field(
                    obj_text,
                    text,
                    inline=False,
                )
            elif task.type == 12:
                factions = {
                    1: "Humans",
                    2: "Terminids",
                    3: "Automaton",
                    4: "Illuminate",
                }
                task_health_bar = health_bar(task.progress, "MO")
                self.add_field(
                    f"{language['major_order']['succeed_in_defense']} {task.values[0]} {language['dashboard']['planets']} {language[factions[task.values[1]].lower()]} {Emojis.factions[factions[task.values[1]]]}",
                    (
                        f"{language['major_order']['progress']}: {int(task.progress * task.values[0])}/{task.values[0]}\n"
                        f"{task_health_bar}\n"
                        f"`{(task.progress):^25,.2%}`\n"
                    ),
                    inline=False,
                )
            elif task.type == 3:
                en_faction_dict = {
                    0: "",
                    2: "Terminids",
                    3: "Automaton",
                    4: "Illuminate",
                }
                loc_faction_dict = {
                    0: language["enemies_of_freedom"],
                    2: language["terminids"],
                    3: language["automaton"],
                    4: language["illuminate"],
                }
                species_dict = {
                    2514244534: "Bile Titan",
                    1379865898: "Bile Spewer",
                    2058088313: "Warrior",
                }
                species = (
                    species_dict.get(task.values[3], None)
                    if task.values[3] != 0
                    else None
                )
                weapon_to_use = stratagem_id_dict.get(task.values[5], None)
                event_health_bar = health_bar(
                    task.progress,
                    en_faction_dict[task.values[0]] if task.progress != 1 else "MO",
                )
                target = loc_faction_dict[task.values[0]] if not species else species
                if weapon_to_use:
                    target += f" using the __{weapon_to_use}__"
                self.add_field(
                    f"{language['kill']} {short_format(task.values[2])} **{target}** {Emojis.factions[en_faction_dict[task.values[0]]]}",
                    (
                        f"{language['major_order']['progress']}: {(task.progress * task.values[2]):,.0f}\n"
                        f"{event_health_bar}\n"
                        f"`{(task.progress):^25,.2%}`\n"
                    ),
                    inline=False,
                )
            elif task.type == 15:
                progress_dict = {
                    -10: 0,
                    -8: 0.1,
                    -6: 0.2,
                    -4: 0.3,
                    -2: 0.4,
                    0: 0.5,
                    2: 0.6,
                    4: 0.7,
                    6: 0.8,
                    8: 0.9,
                    10: 1,
                }
                percent = 0
                for progress, perc in progress_dict.items():
                    if task.progress <= progress:
                        percent = perc
                        break
                victory = (
                    language["dashboard"]["victory"]
                    if percent > 0.5
                    else language["dashboard"]["defeat"]
                )
                event_health_bar = health_bar(
                    percent,
                    (
                        "Humans"
                        if victory == language["dashboard"]["victory"]
                        else "Automaton"
                    ),
                )
                self.add_field(
                    f"{language['major_order']['liberate_more_than_them']} ",
                    (
                        f"{language['dashboard']['outlook']}: {victory.upper()}\n"
                        f"{event_health_bar}\n"
                        f"`{task.progress:^25,}`\n"
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    language["major_order"]["new_title"],
                    language["major_order"]["new_value"],
                )
        rewards_text = ""
        for reward in data.assignment.rewards:
            reward_type = reward_types.get(str(reward["type"]), "Unknown")
            rewards_text += (
                f"{reward['amount']} {reward_type}s {Emojis.items.get(reward_type, '')}"
            )
        self.add_field(
            language["rewards"],
            rewards_text,
        )
        self.add_field(
            language["ends"],
            f"<t:{int(datetime.fromisoformat(data.assignment.ends_at).timestamp())}:R>",
        )


class DispatchesEmbed(Embed):
    def __init__(self, language: dict, dispatch: Dispatch):
        super().__init__(colour=Colour.yellow())
        self.add_field("", dispatch.message)
        self.set_footer(text=f"{language['message'].upper()} #{dispatch.id}")


class SteamEmbed(Embed):
    def __init__(self, steam: Steam, language: dict):
        super().__init__(title=steam.title, colour=Colour.dark_grey(), url=steam.url)
        self.set_footer(text=f"{language['message']} #{steam.id}")
        if len(steam.content) > 4000:
            steam.content = f"{steam.content[:3900]}...\n# {language['steam']['head_here']}(<{steam.url}>) {language['steam']['to_see_full']}"
        self.description = steam.content


class CampaignEmbed(Embed):
    def __init__(self, language: dict):
        self.language = language
        super().__init__(
            title=f"{Emojis.decoration['left_banner']} {self.language['campaigns']['critical_war_updates']} {Emojis.decoration['right_banner']}",
            colour=Colour.brand_red(),
        )
        self.add_field(self.language["campaigns"]["victories"], "", inline=False)
        self.add_field(self.language["campaigns"]["planets_lost"], "", inline=False)
        self.add_field(self.language["campaigns"]["new_battles"], "", inline=False)
        self.add_field(
            self.language["dss"]["name"] + " " + Emojis.dss["dss"], "", inline=False
        )
        self.add_field(self.language["campaigns"]["invasions"], "", inline=False)

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
                description += (
                    f"🛡️ {self.language['defend']['defend']} **{campaign.planet.name}** {Emojis.factions[campaign.faction]}{exclamation}\n"
                    f"> -# {self.language['dashboard']['defend_embed']['level']} {campaign.planet.event.level}{def_level_exc}\n"
                    f"> *{self.language['ends']} {time_remaining}*\n"
                )
            else:
                description += (
                    f"🛡️ {self.language['campaigns']['repel_invasion']} **{campaign.planet.name}** {Emojis.factions[campaign.faction]}{exclamation}\n"
                    f"> -# {self.language['dashboard']['defend_embed']['level']} {campaign.planet.event.level}{def_level_exc}\n"
                    f"> *{self.language['ends']} {time_remaining}*\n"
                )
        else:
            description += f"⚔️ {self.language['campaigns']['liberate']} **{campaign.planet.name}** {Emojis.factions[campaign.faction]}{exclamation}\n"
        self.set_field_at(2, self.fields[2].name, description, inline=False)

    def add_campaign_victory(self, planet: Planet, liberatee: str):
        liberatee_loc = self.language[liberatee.lower()]
        name = self.fields[0].name
        description = self.fields[0].value
        exclamation = ""
        if planet.dss:
            exclamation += Emojis.dss["dss"]
        if planet.in_assignment:
            exclamation += Emojis.icons["MO"]
        description += f"**{Emojis.icons['victory']} {planet.name}** {self.language['campaigns']['been_liberated']} **{liberatee_loc}** {Emojis.factions[liberatee]}!{exclamation}\n"
        self.set_field_at(0, name, description, inline=False)

    def add_def_victory(self, planet: Planet):
        name = self.fields[0].name
        description = self.fields[0].value
        exclamation = ""
        if planet.dss:
            exclamation += Emojis.dss["dss"]
        if planet.in_assignment:
            exclamation += Emojis.icons["MO"]
        description += f"**{Emojis.icons['victory']} {planet.name}** {self.language['campaigns']['been_defended']}! {exclamation}\n"
        self.set_field_at(0, name, description, inline=False)

    def add_planet_lost(self, planet: Planet):
        name = self.fields[1].name
        description = self.fields[1].value
        exclamation = ""
        if planet.dss:
            exclamation += Emojis.dss["dss"]
        if planet.in_assignment:
            exclamation += Emojis.icons["MO"]
        description += f"**💀 {planet.name}** {self.language['campaigns']['been_lost']} **{self.language[planet.current_owner.lower()]}** {Emojis.factions[planet.current_owner]}{exclamation}\n"
        self.set_field_at(1, name, description, inline=False)

    def add_invasion_over(self, planet: Planet, faction: str):
        name = self.fields[4].name
        description = self.fields[4].value
        exclamation = ""
        if planet.dss:
            exclamation += Emojis.dss["dss"]
        if planet.in_assignment:
            exclamation += Emojis.icons["MO"]
        description += f"{self.language['campaigns']['invasion_of']} **{planet.name}** {self.language['campaigns']['has_ended']} {Emojis.factions[planet.current_owner]}{exclamation}\n"
        description += f"-# **{self.language[faction.lower()]}** {self.language['campaigns']['no_changes']} {Emojis.factions[faction]}"
        self.set_field_at(4, name, description, inline=False)

    def remove_empty(self):
        for field in self.fields:
            if field.value == "":
                self.remove_field(self.fields.index(field))

    def dss_moved(self, before_planet: Planet, after_planet: Planet):
        description = (
            self.fields[3].value
            + f"{self.language['dss']['has_moved']} **{before_planet.name}** {Emojis.factions[before_planet.current_owner]} {self.language['dss']['to']} **{after_planet.name}** {Emojis.factions[after_planet.current_owner]} {Emojis.icons['MO'] if after_planet.in_assignment else ''}\n"
        )
        self.set_field_at(3, self.fields[3].name, description, inline=False)

    def ta_status_changed(self, tactical_action: DSS.TacticalAction):
        statuses = {1: "preparing", 2: "active", 3: "on_cooldown"}
        description = (
            self.fields[3].value
            + f"**{tactical_action.name}** {self.language['dss']['is_now']} **{self.language['dss'][statuses[tactical_action.status]]}**\n"
        )
        self.set_field_at(3, self.fields[3].name, description, inline=False)


class Dashboard:
    def __init__(
        self,
        data: Data,
        language: dict,
        json_dict: dict,
    ):
        now = datetime.now()
        planet_names = json_dict["planets"]

        # make embeds
        major_orders_embed = Embed(
            title=language["dashboard"]["major_order"]["major_order"],
            colour=Colour.yellow(),
        )
        dss_embed = Embed(title=language["dss"]["name"], colour=Colour.teal())
        defend_embed = Embed(
            title=language["dashboard"]["defending"], colour=Colour.blue()
        )
        automaton_embed = Embed(
            title=language["dashboard"]["attacking_automatons"], colour=Colour.red()
        )
        terminids_embed = Embed(
            title=language["dashboard"]["attacking_terminids"], colour=Colour.red()
        )
        illuminate_embed = Embed(
            title=language["dashboard"]["attacking_illuminate"], colour=Colour.red()
        )
        updated_embed = Embed(colour=Colour.dark_embed())

        # DSS
        if data.dss != "Error":
            dss_embed.set_thumbnail(
                url="https://cdn.discordapp.com/attachments/1213146233825271818/1310906165823148043/DSS.png?ex=6746ec01&is=67459a81&hm=ab1c29616fd787f727848b04e44c26cc74e045b6e725c45b9dd8a902ec300757&"
            )
            dss_embed.description = (
                f"{language['dashboard']['dss_embed']['stationed_at']}: **{data.dss.planet.name}** {Emojis.factions[data.dss.planet.current_owner]}\n"
                f"Next location move <t:{data.war_time + data.dss.election_war_time}:R>"
            )
            for tactical_action in data.dss.tactical_actions:
                tactical_action: DSS.TacticalAction
                ta_health_bar = health_bar(tactical_action.cost.progress, "MO")
                status = {1: "preparing", 2: "active", 3: "on_cooldown"}[
                    tactical_action.status
                ]
                cost = (
                    (
                        f"{language['dashboard']['dss_embed']['cost']}: {tactical_action.cost.target:,} {Emojis.dss[tactical_action.cost.item]} **{tactical_action.cost.item}s**\n"
                        f"{language['dashboard']['dss_embed']['progress']}: **{tactical_action.cost.current:,.0f}**\n"
                        f"{ta_health_bar}\n"
                        f"`{tactical_action.cost.progress:^25.2%}`\n"
                        f"{language['dashboard']['dss_embed']['max_submitable']}: **{tactical_action.cost.max_per_seconds[0]:,}** every **{tactical_action.cost.max_per_seconds[1] /3600:.0f}** hours\n"
                    )
                    if status == "preparing"
                    else ""
                )
                if cost == "":
                    if status == "active":
                        cost = (
                            f"Ends <t:{data.war_time + tactical_action.status_end}:R>\n"
                        )
                    elif status == "on_cooldown":
                        cost = f"Off cooldown <t:{data.war_time + tactical_action.status_end}:R>\n"

                dss_embed.add_field(
                    tactical_action.name.title(),
                    (
                        f"{language['dashboard']['dss_embed']['status']}: **{language['dashboard']['dss_embed'][status]}**\n"
                        f"{cost}"
                    ),
                    inline=False,
                )

        # Major Orders
        if data.assignment:
            reward_types = json_dict["items"]["reward_types"]
            major_orders_embed.set_thumbnail(
                "https://media.discordapp.net/attachments/1212735927223590974/1240708455040548997/MO_defend.png?ex=66478b4a&is=664639ca&hm=2593a504f96bd5e889772762c2e9790caa08fc279ca48ea0f03c70fa74efecb5&=&format=webp&quality=lossless"
            )
            description = (
                f"\n{data.assignment.description}\n\u200b\n"
                if data.assignment.description != ""
                else ""
            )
            major_orders_embed.add_field(
                f"{language['message']} #{data.assignment.id}",
                f"{data.assignment.title}{description}",
                inline=False,
            )
            for task in data.assignment.tasks:
                task: Tasks.Task
                if task.type in (11, 13):
                    planet: Planet = data.planets[task.values[2]]
                    if planet.event:
                        task.health_bar = health_bar(
                            planet.event.progress,
                            "MO",
                            True,
                        )
                        completed = f"🛡️ {Emojis.factions[planet.event.faction]}"
                        health_text = f"{1 - planet.event.progress:^25,.2%}"
                    else:
                        task.health_bar = health_bar(
                            planet.health / planet.max_health,
                            ("MO" if planet.current_owner != "Humans" else "Humans"),
                            True if planet.current_owner != "Humans" else False,
                        )
                        completed = (
                            f"**{language['dashboard']['major_order']['liberated']}**"
                            if planet.current_owner == "Humans"
                            else ""
                        )
                        health_text = (
                            f"{1 - (planet.health / planet.max_health):^25,.2%}"
                            if planet.current_owner != "Humans"
                            else f"{(planet.health / planet.max_health):^25,.2%}"
                        )
                    feature_text = (
                        "" if not planet.feature else f"Feature: {planet.feature}\n"
                    )
                    dss_text = ""
                    if planet.dss:
                        dss_text = Emojis.dss["dss"]
                    if task.type == 11:
                        obj_text = f"{language['dashboard']['major_order']['liberate']} {planet_names[str(planet.index)]['names'][language['code_long']]}"
                    else:
                        obj_text = f"{language['dashboard']['major_order']['hold']} {planet_names[str(planet.index)]['names'][language['code_long']]} {language['dashboard']['major_order']['when_the_order_expires']}"
                    major_orders_embed.add_field(
                        obj_text,
                        (
                            f"{language['heroes']}: **{planet.stats['playerCount']:,}**\n"
                            f"{language['dashboard']['major_order']['occupied_by']}: **{planet.current_owner}** {Emojis.factions[planet.current_owner]}{dss_text}\n"
                            f"{feature_text}"
                            f"{language['dashboard']['major_order']['event_health']}:\n"
                            f"{task.health_bar} {completed}\n"
                            f"`{health_text}`\n"
                        ),
                        inline=False,
                    )
                elif task.type == 12:  # Succeed in defence of # <enemy> planets
                    factions = {
                        1: "Humans",
                        2: "Terminids",
                        3: "Automaton",
                        4: "Illuminate",
                    }
                    task.health_bar = health_bar(
                        task.progress,
                        "MO" if task.progress < 1 else "Humans",
                    )
                    specific_planet = (
                        data.planets[task.values[3]] if task.values[3] != 0 else None
                    )
                    if specific_planet:
                        objective_text = f"{language['defend']['defend']} {specific_planet.name} {language['dashboard']['major_order']['against']} {task.values[0]} {language['dashboard']['major_order']['attacks_from']} {language[factions[task.values[1]].lower()]} {Emojis.factions[factions[task.values[1]]]}"
                    else:
                        objective_text = f"{language['dashboard']['major_order']['defend_against']} {task.values[0]} {language['dashboard']['major_order']['attacks_from']} {language[factions[task.values[1]].lower()]} {Emojis.factions[factions[task.values[1]]]}"

                    major_orders_embed.add_field(
                        objective_text,
                        (
                            f"{language['dashboard']['major_order']['progress']}: {int(task.progress*task.values[0])}/{task.values[0]}\n"
                            f"{task.health_bar}\n"
                            f"`{(task.progress):^25,.2%}`\n"
                        ),
                        inline=False,
                    )
                elif task.type == 3:  # Kill enemies of a type
                    major_orders_embed.set_thumbnail(
                        "https://media.discordapp.net/attachments/1212735927223590974/1240708455250133142/MO_exterminate.png?ex=66478b4a&is=664639ca&hm=301a0766d3bf6e48c335a7dbafec801ecbe176d65624e69a63cb030dad9b4d82&=&format=webp&quality=lossless"
                    )
                    en_faction_dict = {
                        2: "Terminids",
                        3: "Automaton",
                        4: "Illuminate",
                    }
                    loc_faction_dict = {
                        0: language["enemies_of_freedom"],
                        2: language["terminids"],
                        3: language["automaton"],
                        4: language["illuminate"],
                    }
                    species_dict = {
                        878778730: "Trooper",
                        20706814: "Scout Strider",
                        4276710272: "Devastator",
                        2664856027: "Shredder Tank",
                        471929602: "Hulk",
                        3330362068: "Hunter",
                        2058088313: "Warrior",
                        1379865898: "Bile Spewer",
                        2387277009: "Stalker",
                        2651633799: "Charger",
                        2514244534: "Bile Titan",
                        4211847317: "Voteless",
                        1405979473: "Harvester",
                    }
                    species = (
                        species_dict.get(task.values[3], "Unknown")
                        if task.values[3] != 0
                        else None
                    )
                    weapon_to_use = stratagem_id_dict.get(task.values[5], None)
                    task.health_bar = health_bar(
                        task.progress,
                        (
                            en_faction_dict[task.values[0]]
                            if task.progress != 1.00
                            else "Humans"
                        ),
                    )
                    if task.progress == 1.0:
                        task.health_bar += " COMPLETED"
                    target = (
                        loc_faction_dict[task.values[0]] if not species else species
                    )
                    if weapon_to_use:
                        target += f" using the __{weapon_to_use}__"
                    major_orders_embed.add_field(
                        f"{language['kill']} {short_format(task.values[2])} **{target}** {Emojis.factions[en_faction_dict[task.values[0]]]}",
                        (
                            f"{language['major_order']['progress']}: **{(task.values[2]*task.progress):,.0f}**\n"
                            f"{task.health_bar}\n"
                            f"`{(task.progress):^25,.2%}`\n"
                        ),
                        inline=False,
                    )
                elif task.type == 2:  # Extract with items from a planet
                    items_dict = json_dict["items"]["item_names"]
                    task.health_bar = health_bar(
                        task.progress,
                        "MO",
                    )
                    major_orders_embed.add_field(
                        f"{language['dashboard']['major_order']['extract_items']} {short_format(task.values[2])} {items_dict[str(task.values[4])]} on {data.planets[task.values[8]].name}",
                        (
                            f"{language['major_order']['progress']}: **{task.values[2]*task.progress:,.0f}**\n"
                            f"{task.health_bar}\n"
                            f"`{(task.progress):^25,.2%}`\n"
                        ),
                        inline=False,
                    )
                elif task.type == 15:  # win more than lost
                    progress_dict = {
                        -10: 0,
                        -8: 0.1,
                        -6: 0.2,
                        -4: 0.3,
                        -2: 0.4,
                        0: 0.5,
                        2: 0.6,
                        4: 0.7,
                        6: 0.8,
                        8: 0.9,
                        10: 1,
                    }
                    percent = 0
                    for progress, perc in progress_dict.items():
                        if task.progress <= progress:
                            percent = perc
                            break
                    victory = (
                        language["dashboard"]["victory"]
                        if percent > 0.5
                        else language["dashboard"]["defeat"]
                    )
                    event_health_bar = health_bar(
                        percent,
                        (
                            "Humans"
                            if victory == language["dashboard"]["victory"]
                            else "Automaton"
                        ),
                    )
                    major_orders_embed.add_field(
                        f"{language['major_order']['liberate_more_than_them']} ",
                        (
                            f"{language['dashboard']['outlook']}: {victory.upper()}\n"
                            f"{event_health_bar}\n"
                            f"`{task.progress:^25,}`\n"
                        ),
                        inline=False,
                    )
                else:
                    major_orders_embed.add_field(
                        language["dashboard"]["major_order"]["new_title"],
                        language["dashboard"]["major_order"]["new_value"],
                    )
            rewards_text = ""
            for reward in data.assignment.rewards:
                reward_type = reward_types.get(str(reward["type"]), "Unknown")
                rewards_text += f"{reward['amount']} {reward_type}s {Emojis.items.get(reward_type, '')}"
            major_orders_embed.add_field(language["rewards"], rewards_text)
            major_orders_embed.add_field(
                language["ends"],
                f"<t:{int(datetime.fromisoformat(data.assignment.ends_at).timestamp())}:R>",
            )
        else:
            major_orders_embed.add_field(
                language["dashboard"]["major_order"]["none"], "\u200b"
            )

        # Defending
        if data.planet_events:
            defend_embed.set_thumbnail("https://helldivers.io/img/defense.png")
            for planet in data.planet_events:
                planet: Planet
                liberation_text = ""
                time_to_complete = ""
                outlook_text = ""
                required_players_text = ""
                winning = ""
                if data.liberation_changes != {}:
                    liberation_change = data.liberation_changes.get(planet.index, None)
                    if (
                        liberation_change
                        and len(liberation_change["liberation_changes"]) > 0
                        and sum(liberation_change["liberation_changes"]) != 0
                    ):
                        now_seconds = int(datetime.now().timestamp())
                        seconds_to_complete = int(
                            (
                                (100 - liberation_change["liberation"])
                                / sum(liberation_change["liberation_changes"])
                            )
                            * 3600
                        )
                        winning = (
                            f"**{language['dashboard']['victory']}**"
                            if datetime.fromtimestamp(now_seconds + seconds_to_complete)
                            < planet.event.end_time_datetime
                            else f"**{language['dashboard']['defeat']}**"
                        )
                        time_to_complete = (
                            f"<t:{now_seconds + seconds_to_complete}:R>"
                            if winning == f"**{language['dashboard']['victory']}**"
                            else ""
                        )
                        change = f"{(sum(liberation_change['liberation_changes'])):+.2f}%/hour"
                        liberation_text = f"\n`{change:^25}` "
                        outlook_text = f"\n{language['dashboard']['outlook']}: **{winning}** {time_to_complete}"
                        if (
                            data.planets_with_player_reqs
                            and planet.index in data.planets_with_player_reqs
                        ):
                            required_players_text = f"\n{language['dashboard']['defend_embed']['players_required']}: **~{data.planets_with_player_reqs[planet.index]:,.0f}+**"
                faction_icon = Emojis.factions[planet.event.faction]
                time_remaining = (
                    f"<t:{planet.event.end_time_datetime.timestamp():.0f}:R>"
                )
                event_health_bar = health_bar(
                    planet.event.progress,
                    "Humans",
                    True,
                )
                exclamation = Emojis.icons["MO"] if planet.in_assignment else ""
                feature_text = (
                    "" if not planet.feature else f"\nFeature: {planet.feature}"
                )
                if planet.dss:
                    exclamation += Emojis.dss["dss"]
                defend_embed.add_field(
                    f"{faction_icon} - __**{planet_names[str(planet.index)]['names'][language['code_long']]}**__ {exclamation}",
                    (
                        f"{language['ends']}: {time_remaining}"
                        f"\n{language['dashboard']['defend_embed']['level']} {int(planet.event.max_health / 50000)}"
                        f"{outlook_text}"
                        f"\n{language['heroes']}: **{planet.stats['playerCount']:,}**"
                        f"{feature_text}"
                        f"{required_players_text}"
                        f"\n{language['dashboard']['defend_embed']['event_health']}:"
                        f"\n{event_health_bar}"
                        f"\n`{1 - (planet.event.health / planet.event.max_health):^25,.2%}`"
                        f"{liberation_text}"
                        "\u200b\n"
                    ),
                    inline=False,
                )
        else:
            defend_embed.add_field(
                language["dashboard"]["defend_embed"]["no_threats"],
                f"||{language['dashboard']['defend_embed']['for_now']}||",
            )

        # Attacking
        if data.campaigns:
            skipped_terminid_campaigns = []
            skipped_automaton_campaigns = []
            skipped_illuminate_campaigns = []
            for embed in (
                terminids_embed,
                automaton_embed,
                illuminate_embed,
            ):
                embed.set_thumbnail("https://helldivers.io/img/attack.png")
            defend_embed.title += f" ({(sum([campaign.planet.stats['playerCount'] for campaign in data.campaigns if campaign.planet.event]) / data.total_players):.0%})"
            terminids_embed.title += f" ({(sum([campaign.planet.stats['playerCount'] for campaign in data.campaigns if campaign.planet.current_owner == 'Terminids']) / data.total_players):.0%})"
            automaton_embed.title += f" ({(sum([campaign.planet.stats['playerCount'] for campaign in data.campaigns if campaign.planet.current_owner == 'Automaton']) / data.total_players):.0%})"
            illuminate_embed.title += f" ({(sum([campaign.planet.stats['playerCount'] for campaign in data.campaigns if campaign.planet.current_owner == 'Illuminate']) / data.total_players):.0%})"
            (
                skipped_terminid_campaigns,
                skipped_automaton_campaigns,
                skipped_illuminate_campaigns,
                non_skipped_campaigns,
            ) = skipped_planets(data.campaigns, data.total_players)
            for campaign in non_skipped_campaigns:
                campaign: Campaign
                if campaign.planet.event != None:
                    continue
                time_to_complete = ""
                liberation_text = ""
                if data.liberation_changes != {}:
                    liberation_change = data.liberation_changes.get(
                        campaign.planet.index, None
                    )
                    if (
                        liberation_change
                        and len(liberation_change["liberation_changes"]) > 0
                    ):
                        lib_per_hour = sum(liberation_change["liberation_changes"]) > 0
                        if lib_per_hour > 0:
                            now_seconds = int(datetime.now().timestamp())
                            seconds_to_complete = int(
                                (
                                    (100 - liberation_change["liberation"])
                                    / sum(liberation_change["liberation_changes"])
                                )
                                * 3600
                            )
                            time_to_complete = f"\n{language['dashboard']['outlook']}: **{language['dashboard']['victory']}** <t:{now_seconds + seconds_to_complete}:R>"
                        change = f"{(sum(liberation_change['liberation_changes'])):+.2f}%/hour"
                        liberation_text = f"\n`{change:^25}`"

                exclamation = (
                    Emojis.icons["MO"] if campaign.planet.in_assignment else ""
                )
                if campaign.planet.dss:
                    exclamation += Emojis.dss["dss"]
                faction_icon = Emojis.factions[campaign.planet.current_owner]
                if len(non_skipped_campaigns) < 9:
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
                else:
                    planet_health_bar = ""
                    planet_health_text = f"**`{(1 - (campaign.planet.health / campaign.planet.max_health)):^15.2%}`**"
                    feature_text = ""
                embeds_dict = {
                    "Automaton": automaton_embed,
                    "Terminids": terminids_embed,
                    "Illuminate": illuminate_embed,
                }
                embeds_dict[campaign.planet.current_owner].add_field(
                    f"{faction_icon} - __**{planet_names[str(campaign.planet.index)]['names'][language['code_long']]}**__ {exclamation}",
                    (
                        f"{language['heroes']}: **{campaign.planet.stats['playerCount']:,}**"
                        f"{feature_text}"
                        f"{time_to_complete}"
                        f"\n{language['dashboard']['attack_embed']['planet_health']}:"
                        f"\n{planet_health_bar}"
                        f"\n{planet_health_text}"
                        f"{liberation_text}"
                    ),
                    inline=False,
                )

        # Other
        timestamp = int(now.timestamp())
        skipped_dict = {
            "terminid": {
                "string": "",
                "campaigns": skipped_terminid_campaigns,
                "embed": terminids_embed,
            },
            "automaton": {
                "string": "",
                "campaigns": skipped_automaton_campaigns,
                "embed": automaton_embed,
            },
            "illuminate": {
                "string": "",
                "campaigns": skipped_illuminate_campaigns,
                "embed": illuminate_embed,
            },
        }
        for values in skipped_dict.values():
            for campaign in values["campaigns"]:
                campaign: Campaign
                exclamation = (
                    Emojis.icons["MO"] if campaign.planet.in_assignment else ""
                )
                if campaign.planet.dss:
                    exclamation += Emojis.dss["dss"]
                values[
                    "string"
                ] += f"-# {planet_names[str(campaign.planet.index)]['names'][language['code_long']]} - {Emojis.factions[campaign.planet.current_owner]} - {campaign.planet.stats['playerCount']} {exclamation}\n"
            if values["string"] != "":
                values["embed"].add_field(
                    f"{language['dashboard']['low_impact']}",
                    values["string"],
                    inline=False,
                )

        updated_embed.add_field(
            "",
            (
                f"-# {language['dashboard']['other_updated']}\n"
                f"-# <t:{timestamp}:f> - <t:{timestamp}:R>"
            ),
            inline=False,
        )
        updated_embed.add_field(
            "", ("-# Total Players\n" f"-# {data.total_players:,}"), inline=False
        )
        if len(non_skipped_campaigns) >= 10:
            updated_embed.add_field(
                "",
                f"*{language['dashboard']['lite_mode']}*",
            )
        special_dates = {
            "26/10": language["dashboard"]["liberty_day"],
            "03/04": language["dashboard"]["malevelon_creek_day"],
            "24/12": "Happy Festival of Reckoning!",
            "25/12": "Happy Festival of Reckoning!",
            "26/12": "Happy Festival of Reckoning!",
            "31/12": "Happy New Year!",
            "01/01": "Happy New Year!",
        }
        if now.strftime("%d/%m") in special_dates:
            updated_embed.set_footer(text=special_dates[now.strftime("%d/%m")])

        self.embeds = []
        for embed in (
            major_orders_embed,
            dss_embed,
            defend_embed,
            automaton_embed,
            terminids_embed,
            illuminate_embed,
            updated_embed,
        ):
            embed.set_image(
                "https://i.imgur.com/cThNy4f.png"
            )  # blank bar to unify width
            if len(embed.fields) != 0:
                self.embeds.append(embed)


class Items:
    class Weapons:
        class Primary(Embed):
            def __init__(
                self,
                weapon_json: dict,
                json_dict: dict,
                language: dict,
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
                    weapon_json["capacity"] = (
                        f"{weapon_json['capacity']} {language['weapons']['constant_fire']}"
                    )
                    weapon_json["fire_rate"] = 60
                if weapon_json["capacity"] == 999:
                    weapon_json["capacity"] = "**∞**"
                self.add_field(
                    language["weapons"]["information"],
                    (
                        f"{language['weapons']['type']}: **`{json_dict['items']['weapon_types'][str(weapon_json['type'])]}`**\n"
                        f"{language['weapons']['damage']}: **`{weapon_json['damage']}`**\n"
                        f"{language['weapons']['fire_rate']}: **`{weapon_json['fire_rate']}rpm`**\n"
                        f"{language['weapons']['dps']}: **`{(weapon_json['damage']*weapon_json['fire_rate'])/60:.2f}/s`**\n"
                        f"{language['weapons']['capacity']}: **`{weapon_json['capacity']}`** {Emojis.weapons['Capacity'] if weapon_json['fire_rate'] != 0 else ''}\n"
                        f"{language['weapons']['fire_modes']}:{gun_fire_modes}\n"
                        f"{language['weapons']['features']}:{features}"
                    ),
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
                language: dict,
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
                    weapon_json["capacity"] = (
                        f"{weapon_json['capacity']} {language['weapons']['constant_fire']}"
                    )
                    weapon_json["fire_rate"] = 60
                if weapon_json["capacity"] == 999:
                    weapon_json["capacity"] = "**∞**"
                self.add_field(
                    language["weapons"]["information"],
                    (
                        f"{language['weapons']['damage']}: **`{weapon_json['damage']}`**\n"
                        f"{language['weapons']['fire_rate']}: **`{weapon_json['fire_rate']}rpm`**\n"
                        f"{language['weapons']['dps']}: **`{(weapon_json['damage']*weapon_json['fire_rate'])/60:.2f}/s`**\n"
                        f"{language['weapons']['capacity']}: **`{weapon_json['capacity']}`** {Emojis.weapons['Capacity'] if weapon_json['fire_rate'] != 0 else ''}\n"
                        f"{language['weapons']['fire_modes']}:{gun_fire_modes}\n"
                        f"{language['weapons']['features']}:{features}"
                    ),
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
            def __init__(self, grenade_json: dict, language: dict):
                super().__init__(
                    colour=Colour.blue(),
                    title=grenade_json["name"],
                    description=grenade_json["description"],
                )
                self.add_field(
                    language["weapons"]["information"],
                    (
                        f"{language['weapons']['damage']}: **{grenade_json['damage']}**\n"
                        f"{language['weapons']['fuse_time']}: **{grenade_json['fuse_time']} seconds**\n"
                        f"{language['weapons']['penetration']}: **{grenade_json['penetration']}**\n"
                        f"{language['weapons']['radius']}: **{grenade_json['outer_radius']}**"
                    ),
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
    def __init__(self, stratagem_name: str, stratagem_stats: dict):
        super().__init__(title=stratagem_name, colour=Colour.brand_green())
        key_inputs = ""
        for key in stratagem_stats["keys"]:
            key_inputs += Emojis.stratagems[key]
        self.add_field("Key input", key_inputs, inline=False)
        self.add_field("Uses", stratagem_stats["uses"], inline=False)
        self.add_field(
            "Cooldown",
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
        self, faction: str, species_info: dict, language: dict, variation: bool = False
    ):
        super().__init__(
            colour=Colour.from_rgb(*faction_colours[faction]),
            title=species_info["name"],
            description=species_info["info"]["desc"],
        )
        file_name = species_info["name"].replace(" ", "_")
        start_emoji = Emojis.difficulty[f"difficulty{species_info['info']['start']}"]
        self.add_field(
            language["enemy"]["introduced"],
            f"{language['enemy']['difficulty']} {species_info['info']['start']} {start_emoji}",
            inline=False,
        ).add_field(
            language["enemy"]["tactics"], species_info["info"]["tactics"], inline=False
        ).add_field(
            language["enemy"]["weak_spots"],
            species_info["info"]["weak spots"],
            inline=False,
        )
        variations = ""
        if not variation and species_info["info"]["variations"] != None:
            for i in species_info["info"]["variations"]:
                variations += f"\n- {i}"
            self.add_field(language["enemy"]["variations"], variations)
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
        super().__init__(title="Setup", colour=Colour.og_blurple())

        # dashboard
        if 0 not in (
            guild.dashboard_channel_id,
            guild.dashboard_message_id,
        ):
            dashboard_text = (
                f"{language_json['setup']['dashboard_channel']}: <#{guild.dashboard_channel_id}>\n"
                f"{language_json['setup']['dashboard_message']}: https://discord.com/channels/{guild.id}/{guild.dashboard_channel_id}/{guild.dashboard_message_id}"
            )
        else:
            dashboard_text = language_json["setup"]["not_set"]
        self.add_field(
            language_json["setup"]["dashboard"],
            dashboard_text,
            inline=False,
        )

        # announcements
        if guild.announcement_channel_id != 0:
            announcements_text = f"{language_json['setup']['announcement_channel']}: <#{guild.announcement_channel_id}>"
        else:
            announcements_text = language_json["setup"]["not_set"]
        self.add_field(
            language_json["setup"]["announcements"],
            announcements_text,
            inline=False,
        )

        # map
        if 0 not in (guild.map_channel_id, guild.map_message_id):
            map_text = (
                f"{language_json['setup']['map']['channel']}: <#{guild.map_channel_id}>\n"
                f"{language_json['setup']['map']['message']}: https://discord.com/channels/{guild.id}/{guild.map_channel_id}/{guild.map_message_id}"
            )
        else:
            map_text = language_json["setup"]["not_set"]
        self.add_field(
            language_json["setup"]["map"]["map"],
            map_text,
            inline=False,
        )

        # language
        self.add_field(
            language_json["setup"]["language"]["language"],
            guild.language_long,
        )

        # patch notes
        self.add_field(
            f"{language_json['setup']['patch_notes']['name']}*",
            {True: ":white_check_mark:", False: ":x:"}[guild.patch_notes],
        )

        # mo updates
        self.add_field(
            f"{language_json['setup']['mo_updates']['name']}*",
            {True: ":white_check_mark:", False: ":x:"}[guild.major_order_updates],
        )

        # extra
        self.add_field("", language_json["setup"]["message"], inline=False)
        self.add_field("", "-# \* to set this up, Announcements must be configured")


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
            item["type"] = f"Type: {item['type']}\n" if item["slot"] == "Body" else ""
            if item["slot"] == "Body":
                passives_list = item["passive"]["description"].splitlines()
                passives = f"**{item['passive']['name']}**\n"
                for passive in passives_list:
                    passives += f"-# - {passive}\n"
            self.add_field(
                f"{item['name']} - {item['store_cost']} {Emojis.items['Super Credits']}",
                (
                    f"{item['type']}"
                    f"Slot: **{item['slot']}** {Emojis.armour[item['slot']]}\n"
                    f"Armor: **{item['armor_rating']}**\n"
                    f"Speed: **{item['speed']}**\n"
                    f"Stamina Regen: **{item['stamina_regen']}**\n"
                    f"{passives}"
                ),
            )
        self.insert_field_at(1, "", "").insert_field_at(4, "", "")


class CommandUsageEmbed(Embed):
    def __init__(self, command_usage: dict):
        super().__init__(title="Daily Command Usage", colour=Colour.dark_theme())
        for command_name, usage in command_usage.items():
            self.add_field(f"/{command_name}", f"Used **{usage}** times", inline=False)
        self.add_field(
            "", f"-# as of <t:{int(datetime.now().timestamp())}:R>", inline=False
        )


class DSSEmbed(Embed):
    def __init__(self, dss_data: DSS, language_json: dict):
        super().__init__(
            title=language_json["dss"]["name"],
            description=f"{language_json['dss']['stationed_at']}: **{dss_data.planet.name}** {Emojis.factions[dss_data.planet.current_owner]}",
            colour=Colour.teal(),
        )
        self.set_thumbnail(
            "https://cdn.discordapp.com/attachments/1212735927223590974/1312446626975187065/DSS.png?ex=674c86ab&is=674b352b&hm=3184fde3e8eece703b0e996501de23c89dc085999ebff1a77009fbee2b09ccad&"
        ).set_image(
            "https://cdn.discordapp.com/attachments/1212735927223590974/1312448218398986331/dss.jpg?ex=674c8827&is=674b36a7&hm=def01cbdf1920b85617b1028a95ec982484c70a5cf9bed14b9072319fd018246&"
        )
        for tactical_action in dss_data.tactical_actions:
            tactical_action: DSS.TacticalAction
            ta_health_bar = health_bar(tactical_action.cost.progress, "MO")
            spacer = (
                "\n\u200b\n\u200b\n"
                if tactical_action != dss_data.tactical_actions[-1]
                else ""
            )
            cost = (
                (
                    f"{language_json['dss']['cost']}: **{tactical_action.cost.target:,}** {Emojis.dss[tactical_action.cost.item]} **{tactical_action.cost.item}s**\n"
                    f"{language_json['dss']['progress']}: **{tactical_action.cost.current:,.0f}**\n"
                    f"{ta_health_bar}\n"
                    f"`{tactical_action.cost.progress:^25.2%}`\n"
                    f"{language_json['dss']['max_submitable']}: **{tactical_action.cost.max_per_seconds[0]}** every **{(tactical_action.cost.max_per_seconds[1]/3600):,.2f}** hours\n"
                )
                if tactical_action.status == 1
                else ""
            )
            status = language_json["dss"][
                {1: "preparing", 2: "active", 3: "on_cooldown"}[tactical_action.status]
            ]
            self.add_field(
                f"{Emojis.dss[tactical_action.name.replace(' ', '_').lower()]} {tactical_action.name.title()}",
                (
                    f"{language_json['dss']['description']}:\n-# {tactical_action.description}\n"
                    f"{language_json['dss']['strategic_description']}:\n-# {tactical_action.strategic_description}\n"
                    f"{cost}"
                    f"{language_json['dss']['status']}: **{status}**\n"
                    # f"Status Expiration: <t:{int((datetime.now() + timedelta(seconds=tactical_action.status_end)).timestamp())}:R>\n"
                    f"{spacer}"
                ),
                inline=False,
            )


class WarfrontEmbed(Embed):
    def __init__(
        self,
        faction: str,
        data: Data,
        language_json: dict,
        planet_names: dict,
    ):
        campaigns = [
            campaign for campaign in data.campaigns if campaign.faction == faction
        ]
        cut_campaigns = None
        if len(campaigns) > 15:
            campaigns, cut_campaigns = campaigns[:15], campaigns[15:]
        super().__init__(
            title=f"{language_json['warfront']['warfront_for']} {language_json[faction.lower()]}",
            description=f"{language_json['warfront']['there_are']} **{len(campaigns)}** {language_json['warfront']['available_campaigns']}",
            colour=Colour.from_rgb(*faction_colours[faction]),
        )
        self.set_thumbnail(
            (
                {
                    "Automaton": "https://cdn.discordapp.com/emojis/1215036421551685672.webp?size=44&quality=lossless",
                    "Terminids": "https://cdn.discordapp.com/emojis/1215036423090999376.webp?size=44&quality=lossless",
                    "Illuminate": "https://cdn.discordapp.com/emojis/1317057914145603635.webp?size=44&quality=lossless",
                }[faction]
            ),
        )
        defence_campaigns = [
            campaign for campaign in campaigns if campaign.planet.event
        ]
        attack_campaigns = [
            campaign for campaign in campaigns if not campaign.planet.event
        ]
        if len(defence_campaigns) > 0:
            self.add_field(
                "", f"```{language_json['dashboard']['defending']:^50}```", inline=False
            )
        for index, campaign in enumerate(defence_campaigns, 1):
            liberation_text = ""
            time_to_complete = ""
            outlook_text = ""
            required_players_text = ""
            winning = ""
            if data.liberation_changes != {}:
                liberation_change = data.liberation_changes.get(
                    campaign.planet.index, None
                )
                if (
                    liberation_change
                    and len(liberation_change["liberation_changes"]) > 0
                    and sum(liberation_change["liberation_changes"]) != 0
                ):
                    now_seconds = int(datetime.now().timestamp())
                    seconds_to_complete = int(
                        (
                            (100 - liberation_change["liberation"])
                            / sum(liberation_change["liberation_changes"])
                        )
                        * 3600
                    )
                    winning = (
                        f"**{language_json['dashboard']['victory']}**"
                        if datetime.fromtimestamp(now_seconds + seconds_to_complete)
                        < campaign.planet.event.end_time_datetime
                        else f"**{language_json['dashboard']['defeat']}**"
                    )
                    time_to_complete = (
                        f"<t:{now_seconds + seconds_to_complete}:R>"
                        if winning == f"**{language_json['dashboard']['victory']}**"
                        else ""
                    )
                    change = (
                        f"{(sum(liberation_change['liberation_changes'])):+.2f}%/hour"
                    )
                    liberation_text = f"\n`{change:^25}` "
                    outlook_text = f"\n{language_json['dashboard']['outlook']}: **{winning}** {time_to_complete}"
                    if (
                        data.planets_with_player_reqs
                        and campaign.planet.index in data.planets_with_player_reqs
                    ):
                        required_players_text = f"\n{language_json['dashboard']['defend_embed']['players_required']}: **~{data.planets_with_player_reqs[campaign.planet.index]:,.0f}+**"
            exclamation = Emojis.icons["MO"] if campaign.planet.in_assignment else ""
            if campaign.planet.dss:
                exclamation += Emojis.dss["dss"]
            feature_text = (
                ""
                if not campaign.planet.feature
                else f"\nFeature: {campaign.planet.feature}"
            )
            event_health_bar = health_bar(
                campaign.planet.event.progress,
                "Humans",
                True,
            )
            self.add_field(
                f"{Emojis.factions[campaign.planet.event.faction]} - __**{planet_names[str(campaign.planet.index)]['names'][language_json['code_long']]}**__ {exclamation}",
                (
                    f"{language_json['ends']}: {f'<t:{campaign.planet.event.end_time_datetime.timestamp():.0f}:R>'}"
                    f"\n{language_json['dashboard']['defend_embed']['level']} {int(campaign.planet.event.max_health / 50000)}"
                    f"{outlook_text}"
                    f"\n{language_json['heroes']}: **{campaign.planet.stats['playerCount']:,}**"
                    f"{feature_text}"
                    f"{required_players_text}"
                    f"\n{language_json['dashboard']['defend_embed']['event_health']}:"
                    f"\n{event_health_bar}"
                    f"\n`{1 - (campaign.planet.event.health / campaign.planet.event.max_health):^25,.2%}`"
                    f"{liberation_text}"
                    "\u200b\n"
                ),
            )
            if index % 2 == 0:
                self.add_field("", "")

        if len(attack_campaigns) > 0:
            self.add_field(
                "", f"```{language_json['dashboard']['attacking']:^50}```", inline=False
            )
        for index, campaign in enumerate(attack_campaigns, 1):
            time_to_complete = ""
            liberation_text = ""
            if data.liberation_changes != {}:
                liberation_change = data.liberation_changes.get(
                    campaign.planet.index, None
                )
                if (
                    liberation_change
                    and len(liberation_change["liberation_changes"]) > 0
                ):
                    lib_per_hour = sum(liberation_change["liberation_changes"]) > 0
                    if lib_per_hour > 0:
                        now_seconds = int(datetime.now().timestamp())
                        seconds_to_complete = int(
                            (
                                (100 - liberation_change["liberation"])
                                / sum(liberation_change["liberation_changes"])
                            )
                            * 3600
                        )
                        time_to_complete = f"\n{language_json['dashboard']['outlook']}: **{language_json['dashboard']['victory']}** <t:{now_seconds + seconds_to_complete}:R>"
                        change = f"{(sum(liberation_change['liberation_changes'])):+.2f}%/hour"
                        liberation_text = f"\n`{change:^25}`"
            exclamation = Emojis.icons["MO"] if campaign.planet.in_assignment else ""
            if campaign.planet.dss:
                exclamation += Emojis.dss["dss"]
            faction_icon = Emojis.factions[campaign.planet.current_owner]
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
            self.add_field(
                f"{faction_icon} - __**{planet_names[str(campaign.planet.index)]['names'][language_json['code_long']]}**__ {exclamation}",
                (
                    f"{language_json['heroes']}: **{campaign.planet.stats['playerCount']:,}**"
                    f"{feature_text}"
                    f"{time_to_complete}"
                    f"\n{language_json['dashboard']['attack_embed']['planet_health']}:"
                    f"\n{planet_health_bar}"
                    f"\n{planet_health_text}"
                    f"{liberation_text}"
                ),
            )
            if index % 2 == 0:
                self.add_field("", "")

        if cut_campaigns:
            self.set_footer(
                text=f"Also there are these planets: {' - '.join([campaign.planet.name for campaign in cut_campaigns])}",
            )
