from math import inf
from os import getpid
from disnake import APISlashCommand, Embed, Colour, File, ModalInteraction, OptionType
from datetime import datetime, timedelta
from psutil import Process, cpu_percent
from main import GalacticWideWebBot
from utils.db import GuildRecord, GuildsDB
from utils.functions import health_bar, short_format, skipped_planets
from utils.data import DSS, Campaign, Data, Dispatch, Steam, Superstore, Tasks, Planet
from data.lists import (
    emojis_dict,
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


class PlanetEmbed(Embed):
    def __init__(self, planet_names: dict, planet_data: Planet, language: dict):
        super().__init__(colour=Colour.blue())
        if planet_data.current_owner == "Humans":
            planet_health_bar = health_bar(
                (
                    planet_data.event.progress
                    if planet_data.event
                    else (planet_data.health / planet_data.max_health)
                ),
                planet_data.event.faction if planet_data.event else "Humans",
                True if planet_data.event else False,
            )
            health_text = (
                f"{1 - planet_data.event.progress:^25,.2%}"
                if planet_data.event
                else f"{(planet_data.health / planet_data.max_health):^25,.2%}"
            )
        else:
            planet_health_bar = health_bar(
                planet_data.health / planet_data.max_health,
                planet_data.current_owner,
                True,
            )
            health_text = f"{1 - (planet_data.health / planet_data.max_health):^25,.2%}"
        enviros_text = ""
        for hazard in planet_data.hazards:
            enviros_text += f"\n- **{hazard['name']}**\n  - {hazard['description']}"
        self.add_field(
            f"__**{planet_names['names'][language['code_long']]}**__",
            (
                f"{language['sector']}: **{planet_data.sector}**\n"
                f"{language['planet']['owner']}: **{language[planet_data.current_owner.lower()]}**\n\n"
                f"🏔️ {language['planet']['biome']} \n- **{planet_data.biome['name']}**\n  - {planet_data.biome['description']}\n\n"
                f"🌪️ {language['planet']['environmentals']}:{enviros_text}\n\n"
                f"{language['planet']['planet_health']}\n"
                f"{planet_health_bar}{' 🛡️' if planet_data.event else ''}\n"
                f"`{health_text}`\n"
                "\u200b\n"
            ),
            inline=False,
        ).add_field(
            f"📊 {language['planet']['mission_stats']}",
            (
                f"{language['planet']['missions_won']}: **`{short_format(planet_data.stats['missionsWon'])}`**\n"
                f"{language['planet']['missions_lost']}: **`{short_format(planet_data.stats['missionsLost'])}`**\n"
                f"{language['planet']['missions_winrate']}: **`{planet_data.stats['missionSuccessRate']}%`**\n"
                f"{language['planet']['missions_time_spent']}: **`{planet_data.stats['missionTime']/31556952:.1f} years`**"
            ),
        ).add_field(
            f"📈 {language['planet']['hero_stats']}",
            (
                f"{language['planet']['active_heroes']}: **`{planet_data.stats['playerCount']:,}`**\n"
                f"{language['planet']['heroes_lost']}: **`{short_format(planet_data.stats['deaths'])}`**\n"
                f"{language['planet']['accidents']}: **`{short_format(planet_data.stats['friendlies'])}`**\n"
                f"{language['planet']['shots_fired']}: **`{short_format(planet_data.stats['bulletsFired'])}`**\n"
                f"{language['planet']['shots_hit']}: **`{short_format(planet_data.stats['bulletsHit'])}`**\n"
                f"{language['planet']['accuracy']}: **`{planet_data.stats['accuracy']}%`**\n"
            ),
        )
        self.colour = Colour.from_rgb(*faction_colours[planet_data.current_owner])
        if planet_data.current_owner != "Humans":
            faction = (
                planet_data.current_owner.lower()[:-1]
                if planet_data.current_owner.lower() == "terminids"
                else planet_data.current_owner.lower()
            )
            self.add_field(
                f"💀 {language[planet_data.current_owner.lower()]} {language['planet']['killed']}:",
                f"**{short_format(planet_data.stats[f'{faction}Kills'])}**",
                inline=False,
            ).set_author(
                name=language["planet"]["liberation_progress"],
                icon_url=(
                    "https://cdn.discordapp.com/emojis/1215036421551685672.webp?size=44&quality=lossless"
                    if planet_data.current_owner == "Automaton"
                    else "https://cdn.discordapp.com/emojis/1215036423090999376.webp?size=44&quality=lossless"
                ),
            )
        if planet_data.feature:
            self.add_field("Feature", planet_data.feature)
        if planet_data.thumbnail:
            self.set_thumbnail(url=planet_data.thumbnail)
        try:
            self.set_image(
                file=File(
                    f"resources/biomes/{planet_data.biome['name'].lower().replace(' ', '_')}.png"
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
                        options += f" - **`{sub_option.name}`** `{sub_option.type.name}` {'**[Required]**' if sub_option.required else '**<Optional>**'}- {sub_option.description} \n"
                else:
                    options += f"- **`{option.name}`**: `{option.type.name}` {'**[Required]**' if option.required else '**<Optional>**'} - {option.description}\n"
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
    def __init__(self, bot: GalacticWideWebBot):
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
        ).add_field("Currently in", f"{len(bot.guilds)} discord servers").add_field(
            "Members of Democracy", f"{member_count:,}"
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
        stats_dict = {
            "Dashboard Setup": GuildsDB.dashboard_not_setup(),
            "Announcements Setup": GuildsDB.feed_not_setup(),
            None: None,
            "Maps Setup": GuildsDB.maps_not_setup(),
            "Patch Notes Enabled": GuildsDB.patch_notes_not_setup(),
        }
        for title, amount in stats_dict.items():
            if not title:
                self.add_field("", "", inline=False)
                continue
            healthbar = health_bar(
                (len(bot.guilds) - amount) / len(bot.guilds),
                "Humans",
            )
            self.add_field(
                title,
                (
                    f"**Setup**: {len(bot.guilds) - amount}\n"
                    f"**Not Setup**: {amount}\n"
                    f"{healthbar}"
                ),
            )
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
            title=f"{emojis_dict['Left Banner']} {language['major_order']['title']} {emojis_dict['Right Banner']}",
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
                    f"{language['major_order']['succeed_in_defense']} {task.values[0]} {language['dashboard']['planets']} {language[factions[task.values[1]].lower()]} {emojis_dict[factions[task.values[1]]]}",
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
                    task.progress, en_faction_dict[task.values[0]]
                )
                target = loc_faction_dict[task.values[0]] if not species else species
                if weapon_to_use:
                    target += f" using the __{weapon_to_use}__"
                self.add_field(
                    f"{language['kill']} {short_format(task.values[2])} **{target}** {emojis_dict[en_faction_dict[task.values[0]]]}",
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
        self.add_field(
            language["reward"],
            f"{data.assignment.reward['amount']} {language[reward_types[str(data.assignment.reward['type'])].lower()]} {emojis_dict['medal']}",
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
            title=f"{emojis_dict['Left Banner']} {self.language['campaigns']['critical_war_updates']} {emojis_dict['Right Banner']}",
            colour=Colour.brand_red(),
        )
        self.add_field(self.language["campaigns"]["victories"], "", inline=False)
        self.add_field(self.language["campaigns"]["planets_lost"], "", inline=False)
        self.add_field(self.language["campaigns"]["new_battles"], "", inline=False)
        self.add_field(
            self.language["dss"]["name"] + " " + emojis_dict["dss"], "", inline=False
        )

    def add_new_campaign(self, campaign: Campaign, time_remaining):
        description = self.fields[2].value
        description += (
            (
                f"🛡️ {self.language['campaigns']['defend']} **{campaign.planet.name}** "
                f"{emojis_dict[campaign.faction]}\n> *{self.language['ends']} {time_remaining}*\n"
            )
            if time_remaining
            else (
                f"⚔️ {self.language['campaigns']['liberate']} **{campaign.planet.name}** "
                f"{emojis_dict[campaign.faction]}\n"
            )
        )
        self.set_field_at(2, self.fields[2].name, description, inline=False)

    def add_campaign_victory(self, planet: Planet, liberatee: str):
        liberatee_loc = self.language[liberatee.lower()]
        name = self.fields[0].name
        description = self.fields[0].value
        description += f"**{emojis_dict['victory']} {planet.name}** {self.language['campaigns']['been_liberated']} **{liberatee_loc}** {emojis_dict[liberatee]}!\n"
        self.set_field_at(0, name, description, inline=False)

    def add_def_victory(self, planet: Planet):
        name = self.fields[0].name
        description = self.fields[0].value
        description += f"**{emojis_dict['victory']} {planet.name}** {self.language['campaigns']['been_defended']}!\n"
        self.set_field_at(0, name, description, inline=False)

    def add_planet_lost(self, planet: Planet):
        name = self.fields[1].name
        description = self.fields[1].value
        description += f"**💀 {planet.name}** {self.language['campaigns']['been_lost']} **{self.language[planet.current_owner.lower()]}** {emojis_dict[planet.current_owner]}\n"
        self.set_field_at(1, name, description, inline=False)

    def remove_empty(self):
        for field in self.fields:
            if field.value == "":
                self.remove_field(self.fields.index(field))

    def dss_moved(self, before_planet: Planet, after_planet: Planet):
        description = (
            self.fields[3].value
            + f"{self.language['dss']['has_moved']} **{before_planet.name}** {emojis_dict[before_planet.current_owner]} {self.language['dss']['to']} **{after_planet.name}** {emojis_dict[after_planet.current_owner]}\n"
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
        updated_embed = Embed(colour=Colour.dark_theme())

        # DSS
        dss_embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1213146233825271818/1310906165823148043/DSS.png?ex=6746ec01&is=67459a81&hm=ab1c29616fd787f727848b04e44c26cc74e045b6e725c45b9dd8a902ec300757&"
        )
        dss_embed.description = f"{language['dashboard']['dss_embed']['stationed_at']}: **{data.dss.planet.name}** {emojis_dict[data.dss.planet.current_owner]}"
        for tactical_action in data.dss.tactical_actions:
            tactical_action: DSS.TacticalAction
            ta_health_bar = health_bar(tactical_action.cost.progress, "MO")
            cost = (
                (
                    f"{language['dashboard']['dss_embed']['cost']}: {tactical_action.cost.target:,} {emojis_dict[tactical_action.cost.item]} **{tactical_action.cost.item}s**\n"
                    f"{language['dashboard']['dss_embed']['progress']}: **{tactical_action.cost.current:,.0f}**\n"
                    f"{ta_health_bar}\n"
                    f"`{tactical_action.cost.progress:^25.2%}`\n"
                    f"{language['dashboard']['dss_embed']['max_submitable']}: **{tactical_action.cost.max_per_seconds[0]:,}** every **{tactical_action.cost.max_per_seconds[1] /3600:.0f}** hours\n"
                )
                if tactical_action.status == 1
                else ""
            )
            status = language["dashboard"]["dss_embed"][
                {1: "preparing", 2: "active", 3: "on_cooldown"}[tactical_action.status]
            ]
            dss_embed.add_field(
                tactical_action.name.title(),
                (
                    f"{cost}"
                    f"{language['dashboard']['dss_embed']['status']}: **{status}**\n"
                    # f"Status Expiration: <t:{int((datetime.now() + timedelta(seconds=tactical_action.status_end)).timestamp())}:R>\n"
                ),
                inline=False,
            )

        # Major Orders
        if data.assignment:
            reward_types = json_dict["items"]["reward_types"]
            major_orders_embed.set_thumbnail(
                "https://media.discordapp.net/attachments/1212735927223590974/1240708455040548997/MO_defend.png?ex=66478b4a&is=664639ca&hm=2593a504f96bd5e889772762c2e9790caa08fc279ca48ea0f03c70fa74efecb5&=&format=webp&quality=lossless"
            )
            major_orders_embed.add_field(
                f"{language['message']} #{data.assignment.id}",
                f"{data.assignment.title}\n{data.assignment.description}\n\u200b\n",
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
                        completed = f"🛡️ {emojis_dict[planet.event.faction]}"
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
                        dss_text = emojis_dict["dss"]
                    if task.type == 11:
                        obj_text = f"{language['dashboard']['major_order']['liberate']} {planet_names[str(planet.index)]['names'][language['code_long']]}"
                    else:
                        obj_text = f"{language['dashboard']['major_order']['hold']} {planet_names[str(planet.index)]['names'][language['code_long']]} {language['dashboard']['major_order']['when_the_order_expires']}"
                    major_orders_embed.add_field(
                        obj_text,
                        (
                            f"{language['heroes']}: **{planet.stats['playerCount']:,}**\n"
                            f"{language['dashboard']['major_order']['occupied_by']}: **{planet.current_owner}** {emojis_dict[planet.current_owner]} {dss_text}\n"
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
                    major_orders_embed.add_field(
                        f"{language['dashboard']['major_order']['succeed_in_defense']} {task.values[0]} {language['dashboard']['planets']} {language[factions[task.values[1]].lower()]} {emojis_dict[factions[task.values[1]]]}",
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
                        f"{language['kill']} {short_format(task.values[2])} **{target}** {emojis_dict[en_faction_dict[task.values[0]]]}",
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
            major_orders_embed.add_field(
                language["reward"],
                f"{data.assignment.reward['amount']} {language[reward_types[str(data.assignment.reward['type'])].lower()]} {emojis_dict['medal']}",
            )
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
                faction_icon = emojis_dict[planet.event.faction]
                time_remaining = (
                    f"<t:{planet.event.end_time_datetime.timestamp():.0f}:R>"
                )
                event_health_bar = health_bar(
                    planet.event.progress,
                    "Humans",
                    True,
                )
                exclamation = (
                    emojis_dict["MO"]
                    if data.assignment_planets
                    and planet.index in data.assignment_planets
                    else ""
                )
                feature_text = (
                    "" if not planet.feature else f"\nFeature: {planet.feature}"
                )
                if planet.dss:
                    feature_text += emojis_dict["dss"]
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
                    emojis_dict["MO"]
                    if data.assignment_planets
                    and campaign.planet.index in data.assignment_planets
                    else ""
                )
                if campaign.planet.dss:
                    exclamation += emojis_dict["dss"]
                faction_icon = emojis_dict[campaign.planet.current_owner]
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
                    emojis_dict["MO"]
                    if data.assignment_planets
                    and campaign.planet.index in data.assignment_planets
                    else ""
                )
                if campaign.planet.dss:
                    exclamation += emojis_dict["dss"]
                values[
                    "string"
                ] += f"-# {planet_names[str(campaign.planet.index)]['names'][language['code_long']]} - {emojis_dict[campaign.planet.current_owner]} - {campaign.planet.stats['playerCount']} {exclamation}\n"
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
        if now.strftime("%d/%m") == "26/10":
            major_orders_embed.set_footer(text=language["dashboard"]["liberty_day"])
        if now.strftime("%d/%m") == "03/04":
            major_orders_embed.set_footer(
                text=language["dashboard"]["malevelon_creek_day"]
            )
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
                    gun_fire_modes += f"\n- **{json_dict['items']['fire_modes'][str(i)]} {emojis_dict[json_dict['items']['fire_modes'][str(i)]]}**"

                features = ""
                for i in weapon_json["traits"]:
                    if i != 0:
                        features += f"\n- **{json_dict['items']['weapon_traits'][str(i)]} {emojis_dict[json_dict['items']['weapon_traits'][str(i)]]}**"
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
                        f"{language['weapons']['capacity']}: **`{weapon_json['capacity']}`** {emojis_dict['Capacity'] if weapon_json['fire_rate'] != 0 else ''}\n"
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
                    gun_fire_modes += f"\n- **{json_dict['items']['fire_modes'][str(i)]} {emojis_dict[json_dict['items']['fire_modes'][str(i)]]}**"

                features = ""
                for i in weapon_json["traits"]:
                    if i != 0:
                        features += f"\n- **{json_dict['items']['weapon_traits'][str(i)]} {emojis_dict[json_dict['items']['weapon_traits'][str(i)]]}**"
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
                        f"{language['weapons']['capacity']}: **`{weapon_json['capacity']}`** {emojis_dict['Capacity'] if weapon_json['fire_rate'] != 0 else ''}\n"
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
                    f"Cost to unlock warbond: **{cost}** {emojis_dict['Super Credits']}\n"
                    f"Medals to unlock page: **{warbond_page['medals_to_unlock'] }** {emojis_dict['medal']}\n"
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
                                f"Slot: **{json_dict['items']['armor_slots'][str(item_json['slot'])]}** {emojis_dict[json_dict['items']['armor_slots'][str(item_json['slot'])]]}\n"
                                f"Armor Rating: **{item_json['armor_rating']}**\n"
                                f"Speed: **{item_json['speed']}**\n"
                                f"Stamina Regen: **{item_json['stamina_regen']}**\n"
                                f"Passive: **{json_dict['items']['armor_perks'][str(item_json['passive'])]['name']}**\n"
                                f"Medal Cost: **{item.get('medal_cost', None)} {emojis_dict['medal']}**\n\n"
                            ),
                        )
                    elif item_type == "primary":
                        self.add_field(
                            f"{item_json['name']} {emojis_dict['Primary']}",
                            (
                                "Type: **Primary**\n"
                                f"Weapon type: **{json_dict['items']['weapon_types'][str(item_json['type'])]}**\n"
                                f"Damage: **{item_json['damage']}**\n"
                                f"Capacity: **{item_json['capacity']}** {emojis_dict['Capacity']}\n"
                                f"Recoil: **{item_json['recoil']}**\n"
                                f"Fire Rate: **{item_json['fire_rate']}**\n"
                                f"Medal Cost: **{item['medal_cost']} {emojis_dict['medal']}**\n\n"
                            ),
                        )
                    elif item_type == "secondary":
                        self.add_field(
                            f"{item_json['name']} {emojis_dict['Secondary']}",
                            (
                                "Type: **Secondary**\n"
                                f"Damage: **{item_json['damage']}**\n"
                                f"Capacity: **{item_json['capacity']}** {emojis_dict['Capacity']}\n"
                                f"Recoil: **{item_json['recoil']}**\n"
                                f"Fire Rate: **{item_json['fire_rate']}**\n"
                                f"Medal Cost: **{item['medal_cost']} {emojis_dict['medal']}**\n\n"
                            ),
                        )
                    elif item_type == "grenade":
                        self.add_field(
                            f"{item_json['name']} {emojis_dict['Grenade']}",
                            (
                                "Type: **Grenade**\n"
                                f"Damage: **{item_json['damage']}**\n"
                                f"Penetration: **{item_json['penetration']}**\n"
                                f"Outer Radius: **{item_json['outer_radius']}**\n"
                                f"Fuse Time: **{item_json['fuse_time']}**\n"
                                f"Medal Cost: **{item['medal_cost']} {emojis_dict['medal']}**\n\n"
                            ),
                        )
                elif (
                    json_dict["items"]["item_names"][str(item["item_id"])]["name"]
                    == "Super Credits"
                ):
                    self.add_field(
                        f"{json_dict['items']['item_names'][str(item['item_id'])]['name']} {emojis_dict['Super Credits']}",
                        f"Medal cost: **{item['medal_cost']} {emojis_dict['medal']}**",
                    )
                elif (
                    json_dict["items"]["item_names"][str(item["item_id"])]["name"]
                    in emotes_list
                ):
                    self.add_field(
                        f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                        (
                            "Type: Emote\n"
                            f"Medal cost: **{item['medal_cost']} {emojis_dict['medal']}**"
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
                            f"Medal cost: **{item['medal_cost']} {emojis_dict['medal']}**"
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
                            f"Medal cost: **{item['medal_cost']} {emojis_dict['medal']}**"
                        ),
                    )
                elif str(item["item_id"]) in json_dict["items"]["boosters"]:
                    self.add_field(
                        f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                        (
                            "Type: Booster\n"
                            f"Medal cost: **{item['medal_cost']} {emojis_dict['medal']}**"
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
                            f"Medal cost: **{item['medal_cost']} {emojis_dict['medal']}**"
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
                            f"Medal cost: **{item['medal_cost']} {emojis_dict['medal']}**"
                        ),
                    )
                else:
                    self.add_field(
                        f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                        f"Medal cost: **{item['medal_cost']} {emojis_dict['medal']}**",
                    )
                if item_number % 2 == 0:
                    self.add_field("", "")
                item_number += 1


class StratagemEmbed(Embed):
    def __init__(self, stratagem_name: str, stratagem_stats: dict):
        super().__init__(title=stratagem_name, colour=Colour.brand_green())
        key_inputs = ""
        for key in stratagem_stats["keys"]:
            key_inputs += emojis_dict[key]
        self.add_field("Key input", key_inputs, inline=False)
        self.add_field("Uses", stratagem_stats["uses"], inline=False)
        self.add_field(
            "Cooldown",
            f"{stratagem_stats['cooldown']} seconds ({(stratagem_stats['cooldown']/60):.2f} minutes)",
        )
        self.add_field(
            "Activation time", f"{stratagem_stats['activation']} seconds", inline=False
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
        start_emoji = emojis_dict[f"difficulty{species_info['info']['start']}"]
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


class AnnouncementEmbed(Embed):
    def __init__(self):
        super().__init__(
            title="Galactic Wide Web Update",
            colour=Colour.blue(),
        )
        self.add_field(
            "Lots of updates!",
            "It's been a while since I've given one of these but lots has changed with the bot and I figured yous should know about it.",
            inline=False,
        )
        self.add_field(
            "Whats changed?",
            (
                "- Required players for victory:\n  - Still in early stages but it's doing *okay*\n"
                "- Added </stratagem:1277911286021095484> for basic stratagem info\n"
                "- Also added </major_order:1284164484423876640> to get current progress on the current MO\n"
                "- Most informative commands now have links directly to the [Helldivers 2 wiki.gg](<https://helldivers.wiki.gg/wiki/Helldivers_Wiki>)\n"
                "- Made Meridia *purple* on maps\n"
                "- Lots of new images\n"
            ),
        )
        self.add_field(
            "As always...",
            "</feedback:1253094891513184356> if you want to let me know how I'm doing or if you want more features.",
            inline=False,
        )


class SetupEmbed(Embed):
    def __init__(self, guild_record: GuildRecord, language_json: dict):
        super().__init__(title="Setup", colour=Colour.og_blurple())

        # dashboard
        if 0 not in (
            guild_record.dashboard_channel_id,
            guild_record.dashboard_message_id,
        ):
            dashboard_text = (
                f"{language_json['setup']['dashboard_channel']}: <#{guild_record.dashboard_channel_id}>\n"
                f"{language_json['setup']['dashboard_message']}: https://discord.com/channels/{guild_record.guild_id}/{guild_record.dashboard_channel_id}/{guild_record.dashboard_message_id}"
            )
        else:
            dashboard_text = language_json["setup"]["not_set"]
        self.add_field(
            language_json["setup"]["dashboard"],
            dashboard_text,
            inline=False,
        )

        # announcements
        if guild_record.announcement_channel_id != 0:
            announcements_text = f"{language_json['setup']['announcement_channel']}: <#{guild_record.announcement_channel_id}>"
        else:
            announcements_text = language_json["setup"]["not_set"]
        self.add_field(
            language_json["setup"]["announcements"],
            announcements_text,
            inline=False,
        )

        # map
        if 0 not in (guild_record.map_channel_id, guild_record.map_message_id):
            map_text = (
                f"{language_json['setup']['map']['channel']}: <#{guild_record.map_channel_id}>\n"
                f"{language_json['setup']['map']['message']}: https://discord.com/channels/{guild_record.guild_id}/{guild_record.map_channel_id}/{guild_record.map_message_id}"
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
            guild_record.language_long,
        )

        # patch notes
        self.add_field(
            f"{language_json['setup']['patch_notes']['name']}*",
            {True: ":white_check_mark:", False: ":x:"}[guild_record.patch_notes],
        )

        # mo updates
        self.add_field(
            f"{language_json['setup']['mo_updates']['name']}*",
            {True: ":white_check_mark:", False: ":x:"}[
                guild_record.major_order_updates
            ],
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
            name=inter.author.name,
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
                f"{item['name']} - {item['store_cost']} {emojis_dict['Super Credits']}",
                (
                    f"{item['type']}"
                    f"Slot: **{item['slot']}** {emojis_dict[item['slot']]}\n"
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
            description=f"{language_json['dss']['stationed_at']}: **{dss_data.planet.name}** {emojis_dict[dss_data.planet.current_owner]}",
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
                    f"{language_json['dss']['cost']}: **{tactical_action.cost.target:,}** {emojis_dict[tactical_action.cost.item]} **{tactical_action.cost.item}s**\n"
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
                tactical_action.name.title(),
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
