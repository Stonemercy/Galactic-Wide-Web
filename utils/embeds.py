from json import load
from disnake import Embed, Colour, File, ModalInteraction
from datetime import datetime
from utils.functions import health_bar, short_format, skipped_planets
from utils.api import Assignment, Campaign, Data, Dispatch, Steam, Tasks, Planet
from data.lists import (
    emojis_dict,
    warbond_images_dict,
    supported_languages,
    emotes_list,
    victory_poses_list,
    player_cards_list,
    titles_list,
    stratagem_permit_list,
)


class PlanetEmbed(Embed):
    def __init__(self, planet: Planet, thumbnail_url: str, language):
        super().__init__(colour=Colour.blue())
        if planet.current_owner == "Humans":
            if not planet.event:
                planet_health_bar = health_bar(
                    planet.health / planet.max_health, "Humans", False
                )
                health_text = f"{(planet.health / planet.max_health):^25,.2%}"
            else:
                planet_health_bar = health_bar(
                    planet.event.progress,
                    planet.event.faction,
                    True,
                )
                health_text = f"{1 - planet.event.progress:^25,.2%}"
        else:
            planet_health_bar = health_bar(
                planet.health / planet.max_health,
                planet.current_owner,
                True,
            )
            health_text = f"{1 - (planet.health / planet.max_health):^25,.2%}"
        enviros_text = ""
        for hazard in planet.hazards:
            enviros_text += f"\n- **{hazard['name']}**\n - {hazard['description']}"
        self.add_field(
            f"__**{planet.name}**__",
            (
                f"{language['planet.sector']}: **{planet.sector}**\n"
                f"{language['planet.owner']}: **{language[planet.current_owner.lower()]}**\n\n"
                f"🏔️ {language['planet.biome']} \n- **{planet.biome['name']}**\n - {planet.biome['description']}\n\n"
                f"🌪️ {language['planet.environmentals']}:{enviros_text}\n\n"
                f"{language['planet.planet_health']}\n"
                f"{planet_health_bar}{' 🛡️' if planet.event else ''}\n"
                f"`{health_text}`\n"
                "\u200b\n"
            ),
            inline=False,
        ).add_field(
            f"📊 {language['planet.mission_stats']}",
            (
                f"{language['planet.missions_won']}: **`{short_format(planet.stats['missionsWon'])}`**\n"
                f"{language['planet.missions_lost']}: **`{short_format(planet.stats['missionsLost'])}`**\n"
                f"{language['planet.missions_winrate']}: **`{planet.stats['missionSuccessRate']}%`**\n"
                f"{language['planet.missions_time_spent']}: **`{planet.stats['missionTime']/31556952:.1f} years`**"
            ),
        ).add_field(
            f"📈 {language['planet.hero_stats']}",
            (
                f"{language['planet.active_heroes']}: **`{planet.stats['playerCount']:,}`**\n"
                f"{language['planet.heroes_lost']}: **`{short_format(planet.stats['deaths'])}`**\n"
                f"{language['planet.accidents']}: **`{short_format(planet.stats['friendlies'])}`**\n"
                f"{language['planet.shots_fired']}: **`{short_format(planet.stats['bulletsFired'])}`**\n"
                f"{language['planet.shots_hit']}: **`{short_format(planet.stats['bulletsHit'])}`**\n"
                f"{language['planet.accuracy']}: **`{planet.stats['accuracy']}%`**\n"
            ),
        )
        faction_colour = {
            "Automaton": Colour.from_rgb(r=252, g=76, b=79),
            "Terminids": Colour.from_rgb(r=253, g=165, b=58),
            "Illuminate": Colour.from_rgb(r=116, g=163, b=180),
            "Humans": Colour.from_rgb(r=36, g=205, b=76),
        }
        self.colour = faction_colour[planet.current_owner]
        if planet.current_owner == "Automaton":
            self.add_field(
                f"💀 {language['automaton']} {language['planet.kills']}:",
                f"**{short_format(planet.stats['automatonKills'])}**",
                inline=False,
            )
            self.set_author(
                name=language["planet.liberation_progress"],
                icon_url="https://cdn.discordapp.com/emojis/1215036421551685672.webp?size=44&quality=lossless",
            )
        elif planet.current_owner == "Terminids":
            self.add_field(
                f"💀 {language['terminids']} {language['planet.kills']}:",
                f"**`{short_format(planet.stats['terminidKills'])}`**",
                inline=False,
            )
            self.set_author(
                name=language["planet.liberation_progress"],
                icon_url="https://cdn.discordapp.com/emojis/1215036423090999376.webp?size=44&quality=lossless",
            )
        if thumbnail_url:
            self.set_thumbnail(url=thumbnail_url)


class HelpEmbed(Embed):
    def __init__(self):
        super().__init__(colour=Colour.green(), title="Help")


class BotDashboardEmbed(Embed):
    def __init__(self, dt: datetime):
        super().__init__(colour=Colour.green(), title="GWW Overview")
        self.description = (
            "This is the dashboard for all information about the GWW itself"
        )
        self.set_footer(text=f"Updated at {dt.strftime('%H:%M')}BST")


class MajorOrderEmbed(Embed):
    def __init__(
        self,
        assignment: Assignment,
        planets: dict[int, Planet],
        language,
        with_health_bars: bool = False,
    ):
        language_json = load(open(f"data/languages/{language}.json", encoding="UTF-8"))
        super().__init__(
            title=f"{emojis_dict['Left Banner']} {language_json['major_order.title']} {emojis_dict['Right Banner']}",
            colour=Colour.yellow(),
        )
        reward_types = load(open("data/json/assignments/reward/type.json"))
        self.add_field(
            f"{language_json['major_order.message']} #{assignment.id}",
            f"{assignment.title}\n{assignment.description}",
        )
        self.planet_names_loc = load(
            open(f"data/json/planets/planets.json", encoding="UTF-8")
        )
        for task in assignment.tasks:
            task: Tasks.Task
            if task.type in (11, 13):
                planet: Planet = planets[task.values[2]]
                text = f"{language_json['major_order.heroes']}: **{planet.stats['playerCount']:,}**\n"
                if with_health_bars:
                    health = (
                        1 - planet.event.progress if planet.event else task.progress
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
                text += f"{language_json['dashboard.major_order_occupied_by']}: **{language_json[planet.current_owner.lower()]}**\n"
                self.add_field(
                    self.planet_names_loc[str(planet.index)]["names"][
                        supported_languages[language]
                    ],
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
                    f"{language_json['major_order.succeed_in_defense']} {task.values[0]} {language_json['dashboard.planets']} {language_json[factions[task.values[1]].lower()]} {emojis_dict[factions[task.values[1]]]}",
                    (
                        f"{language_json['major_order.progress']}: {int(task.progress * task.values[0])}/{task.values[0]}\n"
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
                    0: language_json["enemies_of_freedom"],
                    2: language_json["terminids"],
                    3: language_json["automaton"],
                    4: language_json["illuminate"],
                }
                species_dict = {
                    2514244534: "Bile Titan",
                    1379865898: "Bile Spewer",
                    2058088313: "Warrior",
                }
                if task.values[3] in species_dict:
                    species = (
                        species_dict[task.values[3]] if task.values[3] != 0 else None
                    )
                event_health_bar = health_bar(
                    task.progress, en_faction_dict[task.values[0]]
                )
                target = loc_faction_dict[task.values[0]] if not species else species
                self.add_field(
                    f"{language_json['major_order.kill']} {short_format(task.values[2])} **{target}s** {emojis_dict[en_faction_dict[task.values[0]]]}",
                    (
                        f"{language_json['major_order.progress']}: {task.progress * task.values[2]}\n"
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
                    language_json["dashboard.victory"]
                    if percent > 0.5
                    else language_json["dashboard.defeat"]
                )
                event_health_bar = health_bar(
                    percent,
                    "Humans" if victory == ["dashboard.victory"] else "Automaton",
                )
                self.add_field(
                    f"{language_json['major_order.liberate_more_than_them']} ",
                    (
                        f"{language_json['dashboard.outlook']}: {victory.upper()}\n"
                        f"{event_health_bar}\n"
                        f"`{task.progress:^25,}`\n"
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    language_json["major_order.new_title"],
                    language_json["major_order.new_value"],
                )
        self.add_field(
            language_json["major_order.reward"],
            f"{assignment.reward['amount']} {language_json[reward_types[str(assignment.reward['type'])].lower()]} <:medal:1226254158278037504>",
        )
        self.add_field(
            language_json["major_order.ends"],
            f"<t:{int(datetime.fromisoformat(assignment.ends_at).timestamp())}:R>",
        )


class DispatchesEmbed(Embed):
    def __init__(self, dispatch: Dispatch):
        super().__init__(colour=Colour.brand_red())
        self.set_footer(text=f"MESSAGE #{dispatch.id}")
        self.add_field("Message Content", dispatch.message)


class SteamEmbed(Embed):
    def __init__(self, steam: Steam):
        super().__init__(title=steam.title, colour=Colour.dark_grey(), url=steam.url)
        self.set_footer(text=f"MESSAGE #{steam.id}")
        if len(steam.content) > 4000:
            steam.content = f"Please head [here](<{steam.url}>) to see the full patch notes as they are too long for Discord."
        self.description = steam.content
        self.author.name = steam.author
        self.author.url = f"https://steamcommunity.com/id/{steam.author}"


class CampaignEmbed(Embed):
    def __init__(self, language):
        self.language = load(open(f"data/languages/{language}.json", encoding="UTF-8"))
        super().__init__(
            title=f"{emojis_dict['Left Banner']} {self.language['campaigns.critical_war_updates']} {emojis_dict['Right Banner']}",
            colour=Colour.brand_red(),
        )

        self.add_field(self.language["campaigns.victories"], "", inline=False)
        self.add_field(self.language["campaigns.planets_lost"], "", inline=False)
        self.add_field(self.language["campaigns.new_battles"], "", inline=False)

    def add_new_campaign(self, campaign: Campaign, time_remaining):
        description = self.fields[2].value
        description += (
            (
                f"🛡️ {self.language['campaigns.defend']} **{campaign.planet.name}** "
                f"{emojis_dict[campaign.faction]}\n> *{self.language['campaigns.ends']} {time_remaining}*\n"
            )
            if time_remaining
            else (
                f"⚔️ {self.language['campaigns.liberate']} **{campaign.planet.name}** "
                f"{emojis_dict[campaign.faction]}\n"
            )
        )
        self.set_field_at(2, self.fields[2].name, description, inline=False)

    def add_campaign_victory(self, planet: Planet, liberatee: str):
        liberatee_loc = self.language[liberatee.lower()]
        name = self.fields[0].name
        description = self.fields[0].value
        description += f"**{emojis_dict['victory']} {planet.name}** {self.language['campaigns.been_liberated']} **{liberatee_loc}** {emojis_dict[liberatee]}!\n"
        self.set_field_at(0, name, description, inline=False)

    def add_def_victory(self, planet: Planet):
        name = self.fields[0].name
        description = self.fields[0].value
        description += f"**{emojis_dict['victory']} {planet.name}** {self.language['campaigns.been_defended']}!\n"
        self.set_field_at(0, name, description, inline=False)

    def add_planet_lost(self, planet: Planet):
        name = self.fields[1].name
        description = self.fields[1].value
        description += f"**💀 {planet.name}** {self.language['campaigns.been_lost']} **{self.language[planet.current_owner.lower()]}** {emojis_dict[planet.current_owner]}\n"
        self.set_field_at(1, name, description, inline=False)

    def remove_empty(self):
        for field in self.fields:
            if field.value == "":
                self.remove_field(self.fields.index(field))


class Dashboard:
    def __init__(self, data: Data, language_code: str, liberation_changes: dict):
        now = datetime.now()
        language = load(open(f"data/languages/{language_code}.json", encoding="UTF-8"))
        planet_names_loc = load(
            open(f"data/json/planets/planets.json", encoding="UTF-8")
        )
        skipped_terminid_campaigns = []
        skipped_automaton_campaigns = []
        skipped_illuminate_campaigns = []

        # make embeds
        major_orders_embed = Embed(
            title=language["dashboard.major_order"], colour=Colour.yellow()
        )
        defend_embed = Embed(
            title=language["dashboard.defending"], colour=Colour.blue()
        )
        automaton_embed = Embed(
            title=language["dashboard.attacking_automatons"], colour=Colour.red()
        )
        terminids_embed = Embed(
            title=language["dashboard.attacking_terminids"], colour=Colour.red()
        )
        illuminate_embed = Embed(
            title=language["dashboard.attacking_illuminate"], colour=Colour.red()
        )
        updated_embed = Embed(colour=Colour.dark_theme())

        # Major Orders
        if data.assignment:
            reward_types = load(open("data/json/assignments/reward/type.json"))
            major_orders_embed.set_thumbnail(
                "https://media.discordapp.net/attachments/1212735927223590974/1240708455040548997/MO_defend.png?ex=66478b4a&is=664639ca&hm=2593a504f96bd5e889772762c2e9790caa08fc279ca48ea0f03c70fa74efecb5&=&format=webp&quality=lossless"
            )
            major_orders_embed.add_field(
                f"{language['dashboard.major_order_message']} #{data.assignment.id}",
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
                        health_text = f"{1 - (planet.event.progress):^25,.2%}"
                    else:
                        task.health_bar = health_bar(
                            planet.health / planet.max_health,
                            ("MO" if planet.current_owner != "Humans" else "Humans"),
                            True if planet.current_owner != "Humans" else False,
                        )
                        completed = (
                            f"**{language['dashboard.major_order_liberated']}**"
                            if planet.current_owner == "Humans"
                            else ""
                        )
                        health_text = (
                            f"{1 - (planet.health / planet.max_health):^25,.2%}"
                            if planet.current_owner != "Humans"
                            else f"{(planet.health / planet.max_health):^25,.2%}"
                        )
                    major_orders_embed.add_field(
                        planet_names_loc[str(planet.index)]["names"][
                            supported_languages[language_code]
                        ],
                        (
                            f"{language['dashboard.heroes']}: **{planet.stats['playerCount']:,}**\n"
                            f"{language['dashboard.major_order_occupied_by']}: **{planet.current_owner}**\n"
                            f"{language['dashboard.major_order_event_health']}:\n"
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
                        f"{language['dashboard.major_order_succeed_in_defense']} {task.values[0]} {language['dashboard.planets']} {language[factions[task.values[1]].lower()]} {emojis_dict[factions[task.values[1]]]}",
                        (
                            f"{language['dashboard.major_order_progress']}: {int(task.progress*task.values[0])}/{task.values[0]}\n"
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
                    if task.values[3] in species_dict:
                        species = (
                            species_dict[task.values[3]]
                            if task.values[3] != 0
                            else None
                        )
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
                    major_orders_embed.add_field(
                        f"{language['dashboard.major_order_kill']} {short_format(task.values[2])} **{target}s** {emojis_dict[en_faction_dict[task.values[0]]]}",
                        (
                            f"{language['major_order.progress']}: **{(task.values[2]*task.progress):,.0f}**\n"
                            f"{task.health_bar}\n"
                            f"`{(task.progress):^25,.2%}`\n"
                        ),
                        inline=False,
                    )
                elif task.type == 2:  # Extract with items from a planet
                    items_dict = load(
                        open(f"data/json/items/item_names.json", encoding="UTF-8")
                    )
                    task.health_bar = health_bar(
                        task.progress,
                        "MO",
                    )
                    major_orders_embed.add_field(
                        f"{language['dashboard.major_order_extract_items']} {short_format(task.values[2])} {items_dict[str(task.values[4])]} on {data.planets[task.values[8]].name}",
                        (
                            f"{language['major_order.progress']}: **{task.values[2]*task.progress:,.0f}**\n"
                            f"{task.health_bar}\n"
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
                        language["dashboard.victory"]
                        if percent > 0.5
                        else language["dashboard.defeat"]
                    )
                    event_health_bar = health_bar(
                        percent,
                        (
                            "Humans"
                            if victory == language["dashboard.victory"]
                            else "Automaton"
                        ),
                    )
                    major_orders_embed.add_field(
                        f"{language['major_order.liberate_more_than_them']} ",
                        (
                            f"{language['dashboard.outlook']}: {victory.upper()}\n"
                            f"{event_health_bar}\n"
                            f"`{task.progress:^25,}`\n"
                        ),
                        inline=False,
                    )
                else:
                    major_orders_embed.add_field(
                        language["dashboard.major_order_new_title"],
                        language["dashboard.major_order_new_value"],
                    )
            major_orders_embed.add_field(
                language["dashboard.major_order_reward"],
                f"{data.assignment.reward['amount']} {language[reward_types[str(data.assignment.reward['type'])].lower()]} {emojis_dict['medal']}",
            )
            major_orders_embed.add_field(
                language["dashboard.major_order_ends"],
                f"<t:{int(datetime.fromisoformat(data.assignment.ends_at).timestamp())}:R>",
            )
        else:
            major_orders_embed.add_field(
                language["dashboard.major_order_none"], "\u200b"
            )

        # Defending
        if data.planet_events:
            defend_embed.set_thumbnail("https://helldivers.io/img/defense.png")
            for planet in data.planet_events:
                planet: Planet
                liberation_text = ""
                time_to_complete = ""
                outlook_text = ""
                winning = ""
                if liberation_changes != {}:
                    liberation_change = liberation_changes.get(planet.name, None)
                    if (
                        liberation_change
                        and len(liberation_change["liberation_changes"]) > 0
                        and sum(liberation_change["liberation_changes"]) != 0
                    ):
                        above_zero = (
                            "+"
                            if sum(liberation_change["liberation_changes"]) > 0
                            else ""
                        )
                        now_seconds = int(datetime.now().timestamp())
                        seconds_to_complete = int(
                            (
                                (100 - liberation_change["liberation"])
                                / sum(liberation_change["liberation_changes"])
                            )
                            * 3600
                        )
                        winning = {
                            True: f"**{language['dashboard.victory']}**",
                            False: f"**{language['dashboard.defeat']}**",
                        }[
                            datetime.fromtimestamp(now_seconds + seconds_to_complete)
                            < planet.event.end_time_datetime
                        ]
                        time_to_complete = (
                            f"<t:{now_seconds + seconds_to_complete}:R>"
                            if winning == f"**{language['dashboard.victory']}**"
                            else ""
                        )
                        change = (
                            f"{(sum(liberation_change['liberation_changes'])):.2}%/hour"
                        )
                        liberation_text = f"\n`{(above_zero + change):^25}` "
                        outlook_text = f"\n{language['dashboard.outlook']}: **{winning}** {time_to_complete}"
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
                    "<:MO:1240706769043456031>"
                    if data.assignment_planets
                    and planet.index in data.assignment_planets
                    else ""
                )
                defend_embed.add_field(
                    f"{faction_icon} - __**{planet_names_loc[str(planet.index)]['names'][supported_languages[language_code]]}**__ {exclamation}",
                    (
                        f"{language['dashboard.defend_embed_ends']}: {time_remaining}"
                        f"\n{language['dashboard.heroes']}: **{planet.stats['playerCount']:,}**"
                        f"{outlook_text}"
                        f"\n{language['dashboard.defend_embed_event_health']}:"
                        f"\n{event_health_bar}"
                        f"\n`{1 - (planet.event.health / planet.event.max_health):^25,.2%}`"
                        f"{liberation_text}"
                        "\u200b\n"
                    ),
                    inline=False,
                )
        else:
            defend_embed.add_field(
                language["dashboard.defend_embed_no_threats"],
                f"||{language['dashboard.defend_embed_for_now']}||",
            )

        # Attacking
        if data.campaigns:
            for embed in (
                terminids_embed,
                automaton_embed,
                illuminate_embed,
            ):
                embed.set_thumbnail("https://helldivers.io/img/attack.png")
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
                if liberation_changes != {}:
                    liberation_change = liberation_changes.get(
                        campaign.planet.name, None
                    )
                    if (
                        liberation_change
                        and len(liberation_change["liberation_changes"]) > 0
                    ):
                        above_zero = (
                            "+"
                            if sum(liberation_change["liberation_changes"]) > 0
                            else ""
                        )
                        if above_zero == "+":
                            now_seconds = int(datetime.now().timestamp())
                            seconds_to_complete = int(
                                (
                                    (100 - liberation_change["liberation"])
                                    / sum(liberation_change["liberation_changes"])
                                )
                                * 3600
                            )
                            time_to_complete = f"\n{language['dashboard.outlook']}: **{language['dashboard.victory']}** <t:{now_seconds + seconds_to_complete}:R>"
                        change = (
                            f"{(sum(liberation_change['liberation_changes'])):.2}%/hour"
                        )
                        liberation_text = f"\n`{(above_zero + change):^25}`"
                exclamation = (
                    emojis_dict["MO"]
                    if data.assignment_planets
                    and campaign.planet.index in data.assignment_planets
                    else ""
                )
                faction_icon = emojis_dict[campaign.planet.current_owner]
                if len(non_skipped_campaigns) < 9:
                    planet_health_bar = health_bar(
                        campaign.planet.health / campaign.planet.max_health,
                        campaign.planet.current_owner,
                        True,
                    )
                    planet_health_text = f"`{(1 - (campaign.planet.health / campaign.planet.max_health)):^25.2%}`"
                else:
                    planet_health_bar = ""
                    planet_health_text = f"**`{(1 - (campaign.planet.health / campaign.planet.max_health)):^15.2%}`**"
                if campaign.planet.current_owner == "Automaton":
                    automaton_embed.add_field(
                        f"{faction_icon} - __**{planet_names_loc[str(campaign.planet.index)]['names'][supported_languages[language_code]]}**__ {exclamation}",
                        (
                            f"{language['dashboard.heroes']}: **{campaign.planet.stats['playerCount']:,}**"
                            f"{time_to_complete}"
                            f"\n{language['dashboard.attack_embed_planet_health']}:"
                            f"\n{planet_health_bar}"
                            f"\n{planet_health_text}"
                            f"{liberation_text}"
                        ),
                        inline=False,
                    )
                elif campaign.planet.current_owner == "Terminids":
                    terminids_embed.add_field(
                        f"{faction_icon} - __**{planet_names_loc[str(campaign.planet.index)]['names'][supported_languages[language_code]]}**__ {exclamation}",
                        (
                            f"{language['dashboard.heroes']}: **{campaign.planet.stats['playerCount']:,}**"
                            f"{time_to_complete}"
                            f"\n{language['dashboard.attack_embed_planet_health']}:"
                            f"\n{planet_health_bar}"
                            f"\n{planet_health_text}"
                            f"{liberation_text}"
                        ),
                        inline=False,
                    )
                elif campaign.planet.current_owner == "Illuminate":
                    illuminate_embed.add_field(
                        f"{faction_icon} - __**{planet_names_loc[str(campaign.planet.index)]['names'][supported_languages[language_code]]}**__ {exclamation}",
                        (
                            f"{language['dashboard.heroes']}: **{campaign.planet.stats['playerCount']:,}**"
                            f"{time_to_complete}"
                            f"\n{language['dashboard.attack_embed_planet_health']}:"
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
                values[
                    "string"
                ] += f"-# {planet_names_loc[str(campaign.planet.index)]['names'][supported_languages[language_code]]} - {emojis_dict[campaign.planet.current_owner]} - {campaign.planet.stats['playerCount']} {exclamation}\n"
            if values["string"] != "":
                values["embed"].add_field(
                    f"{language['dashboard.low_impact']}",
                    values["string"],
                    inline=False,
                )

        updated_embed.add_field(
            "",
            (
                f"-# {language['dashboard.other_updated']}\n"
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
                f"*{language['dashboard.lite_mode']}*",
            )
        if now.strftime("%d/%m") == "26/10":
            major_orders_embed.set_footer(text=language["dashboard.liberty_day"])
        if now.strftime("%d/%m") == "03/04":
            major_orders_embed.set_footer(
                text=language["dashboard.malevelon_creek_day"]
            )
        self.embeds = []
        for embed in (
            major_orders_embed,
            defend_embed,
            automaton_embed,
            terminids_embed,
            illuminate_embed,
            updated_embed,
        ):
            embed.set_image("https://i.imgur.com/cThNy4f.png")
            if len(embed.fields) != 0:
                self.embeds.append(embed)


class Items:
    class Weapons:
        class Primary(Embed):
            def __init__(
                self,
                primary: dict,
                types: dict,
                fire_modes: dict,
                traits: dict,
                language: dict,
            ):
                super().__init__(
                    colour=Colour.blue(),
                    title=primary["name"],
                    description=primary["description"],
                )
                gun_fire_modes = ""
                features = ""
                for i in primary["fire_mode"]:
                    gun_fire_modes += (
                        f"\n- {fire_modes[str(i)]} {emojis_dict[fire_modes[str(i)]]}"
                    )
                for i in primary["traits"]:
                    if i != 0:
                        features += (
                            f"\n- **{traits[str(i)]} {emojis_dict[traits[str(i)]]}**"
                        )
                    else:
                        features = "\n- None"
                if 9 in primary["traits"]:
                    primary["capacity"] = (
                        f"{primary['capacity']} {language['weapons.constant_fire']}"
                    )
                    primary["fire_rate"] = 60
                if primary["capacity"] == 999:
                    primary["capacity"] = "♾️"
                self.add_field(
                    language["weapons.information"],
                    (
                        f"{language['weapons.type']}: **`{types[str(primary['type'])]}`**\n"
                        f"{language['weapons.damage']}: **`{primary['damage']}`**\n"
                        f"{language['weapons.fire_rate']}: **`{primary['fire_rate']}rpm`**\n"
                        f"{language['weapons.dps']}: **`{(primary['damage']*primary['fire_rate'])/60:.2f}/s`**\n"
                        f"{language['weapons.capacity']}: **`{primary['capacity']}`** {emojis_dict['Capacity'] if primary['fire_rate'] != 0 else ''}\n"
                        f"{language['weapons.fire_modes']}:**{gun_fire_modes}**\n"
                        f"{language['weapons.features']}:{features}"
                    ),
                )
                try:
                    self.set_thumbnail(
                        file=File(
                            f"resources/weapons/{primary['name'].replace(' ', '-').replace('&', 'n')}.png"
                        )
                    )
                    self.image_set = True
                except:
                    self.image_set = False

        class Secondary(Embed):
            def __init__(
                self, secondary: dict, fire_modes: dict, traits: dict, language
            ):
                super().__init__(
                    colour=Colour.blue(),
                    title=secondary["name"],
                    description=secondary["description"],
                )
                gun_fire_modes = ""
                features = ""
                for i in secondary["fire_mode"]:
                    gun_fire_modes += (
                        f"\n- {fire_modes[str(i)]} {emojis_dict[fire_modes[str(i)]]}"
                    )
                for i in secondary["traits"]:
                    if i != 0:
                        features += (
                            f"\n- **{traits[str(i)]} {emojis_dict[traits[str(i)]]}**"
                        )
                    else:
                        features = "\n- None"
                if 9 in secondary["traits"]:
                    secondary["capacity"] = (
                        f"{secondary['capacity']} {language['weapons.constant_fire']}"
                    )
                    secondary["fire_rate"] = 60
                if secondary["capacity"] == 999:
                    secondary["capacity"] = "♾️"
                self.add_field(
                    language["weapons.information"],
                    (
                        f"{language['weapons.damage']}: **`{secondary['damage']}`**\n"
                        f"{language['weapons.fire_rate']}: **`{secondary['fire_rate']}rpm`**\n"
                        f"{language['weapons.dps']}: **`{(secondary['damage']*secondary['fire_rate'])/60:.2f}/s`**\n"
                        f"{language['weapons.capacity']}: **`{secondary['capacity']}`** {emojis_dict['Capacity'] if secondary['fire_rate'] != 0 else ''}\n"
                        f"{language['weapons.fire_modes']}:**{gun_fire_modes}**"
                        f"{language['weapons.features']}:**{features}**"
                    ),
                )
                try:
                    self.set_thumbnail(
                        file=File(
                            f"resources/weapons/{secondary['name'].replace(' ', '-')}.png"
                        )
                    )
                    self.image_set = True
                except:
                    self.image_set = False

        class Grenade(Embed):
            def __init__(self, grenade: dict, language):
                super().__init__(
                    colour=Colour.blue(),
                    title=grenade["name"],
                    description=grenade["description"],
                )
                self.add_field(
                    language["weapons.information"],
                    (
                        f"{language['weapons.damage']}: **{grenade['damage']}**\n"
                        f"{language['weapons.fuse_time']}: **{grenade['fuse_time']} seconds**\n"
                        f"{language['weapons.penetration']}: **{grenade['penetration']}**\n"
                        f"{language['weapons.radius']}: **{grenade['outer_radius']}**"
                    ),
                )
                try:
                    self.set_thumbnail(
                        file=File(
                            f"resources/weapons/{grenade['name'].replace(' ', '-')}.png"
                        )
                    )
                    self.image_set = True
                except:
                    self.image_set = False

    class Armour(Embed):
        def __init__(self, armour: dict, passives: dict, slots: dict):
            super().__init__(
                colour=Colour.blue(),
                title=armour["name"],
                description=armour["description"],
            )
            self.add_field(
                "Information",
                (
                    f"Slot: **{slots[str(armour['slot'])]}**\n"
                    f"Armour Rating: **{armour['armor_rating']}**\n"
                    f"Speed: **{armour['speed']}**\n"
                    f"Stamina Regen: **{armour['stamina_regen']}**\n"
                    f"Passive effect:\n"
                    f"- {passives[str(armour['passive'])]}"
                ),
            )
            try:
                self.set_thumbnail(
                    file=File(
                        f"resources/armour/{armour['name'].replace(' ', '-')}.png"
                    )
                )
            except:
                pass

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
        def __init__(
            self,
            warbond: dict,
            warbond_json: str,
            item_names: dict,
            page,
            armor_json: dict,
            armor_perks_json: dict,
            primary_json: dict,
            secondary_json: dict,
            grenade_json: dict,
            weapon_types: dict,
            boosters_list: dict,
        ):
            slots = {"0": "Head", "1": "Cloak", "2": "Body"}
            warbond_page = warbond[str(page)]
            cost = warbond_json["credits_to_unlock"]
            super().__init__(
                colour=Colour.blue(),
                title=warbond_json["name"],
                description=(
                    f"Page {page}/{[i for i in warbond][-1]}\n"
                    f"Cost to unlock warbond: **{cost}** {emojis_dict['Super Credits']}\n"
                    f"Medals to unlock page: **{warbond_page['medals_to_unlock'] }** <:medal:1226254158278037504>\n"
                ),
            )
            self.set_image(warbond_images_dict[warbond_json["name"]])
            item_number = 1
            for item in warbond_page["items"]:
                item_json = None
                item_type = None
                for item_key, item_value in armor_json.items():
                    if int(item_key) == item["item_id"]:
                        item_json = item_value
                        item_type = "armor"
                        break
                for item_key, item_value in primary_json.items():
                    if item_type != None:
                        break
                    if int(item_key) == item["item_id"]:
                        item_json = item_value
                        item_type = "primary"
                        break
                for item_key, item_value in secondary_json.items():
                    if item_type != None:
                        break
                    if int(item_key) == item["item_id"]:
                        item_json = item_value
                        item_type = "secondary"
                        break
                for item_key, item_value in grenade_json.items():
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
                                f"Slot: **{slots[str(item_json['slot'])]}** {emojis_dict[slots[str(item_json['slot'])]]}\n"
                                f"Armor Rating: **{item_json['armor_rating']}**\n"
                                f"Speed: **{item_json['speed']}**\n"
                                f"Stamina Regen: **{item_json['stamina_regen']}**\n"
                                f"Passive: **{armor_perks_json[str(item_json['passive'])]['name']}**\n"
                                f"Medal Cost: **{item.get('medal_cost', None)} <:medal:1226254158278037504>**\n\n"
                            ),
                        )
                    elif item_type == "primary":
                        self.add_field(
                            f"{item_json['name']} {emojis_dict['Primary']}",
                            (
                                "Type: **Primary**\n"
                                f"Weapon type: **{weapon_types[str(item_json['type'])]}**\n"
                                f"Damage: **{item_json['damage']}**\n"
                                f"Capacity: **{item_json['capacity']}** {emojis_dict['Capacity']}\n"
                                f"Recoil: **{item_json['recoil']}**\n"
                                f"Fire Rate: **{item_json['fire_rate']}**\n"
                                f"Medal Cost: **{item['medal_cost']} <:medal:1226254158278037504>**\n\n"
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
                                f"Medal Cost: **{item['medal_cost']} <:medal:1226254158278037504>**\n\n"
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
                                f"Medal Cost: **{item['medal_cost']} <:medal:1226254158278037504>**\n\n"
                            ),
                        )
                elif "Super Credits" in item_names[str(item["item_id"])]["name"]:
                    self.add_field(
                        f"{item_names[str(item['item_id'])]['name']} {emojis_dict['Super Credits']}",
                        f"Medal cost: **{item['medal_cost']} <:medal:1226254158278037504>**",
                    )
                elif item_names[str(item["item_id"])]["name"] in emotes_list:
                    self.add_field(
                        f"{item_names[str(item['item_id'])]['name']}",
                        (
                            "Type: Emote\n"
                            f"Medal cost: **{item['medal_cost']} <:medal:1226254158278037504>**"
                        ),
                    )
                elif item_names[str(item["item_id"])]["name"] in victory_poses_list:
                    self.add_field(
                        f"{item_names[str(item['item_id'])]['name']}",
                        (
                            "Type: Victory Pose\n"
                            f"Medal cost: **{item['medal_cost']} <:medal:1226254158278037504>**"
                        ),
                    )
                elif item_names[str(item["item_id"])]["name"] in player_cards_list:
                    self.add_field(
                        f"{item_names[str(item['item_id'])]['name']}",
                        (
                            "Type: Player Card\n"
                            f"Medal cost: **{item['medal_cost']} <:medal:1226254158278037504>**"
                        ),
                    )
                elif item_names[str(item["item_id"])]["name"] in boosters_list:
                    self.add_field(
                        f"{item_names[str(item['item_id'])]['name']}",
                        (
                            "Type: Booster\n"
                            f"Medal cost: **{item['medal_cost']} <:medal:1226254158278037504>**"
                        ),
                    )
                elif item_names[str(item["item_id"])]["name"] in titles_list:
                    self.add_field(
                        f"{item_names[str(item['item_id'])]['name']}",
                        (
                            "Type: Title\n"
                            f"Medal cost: **{item['medal_cost']} <:medal:1226254158278037504>**"
                        ),
                    )
                elif item_names[str(item["item_id"])]["name"] in stratagem_permit_list:
                    self.add_field(
                        f"{item_names[str(item['item_id'])]['name']}",
                        (
                            "Type: Stratagem Permit\n"
                            f"Medal cost: **{item['medal_cost']} <:medal:1226254158278037504>**"
                        ),
                    )
                else:
                    self.add_field(
                        f"{item_names[str(item['item_id'])]['name']}",
                        f"Medal cost: **{item['medal_cost']} <:medal:1226254158278037504>**",
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


class Terminid(Embed):
    def __init__(
        self, species_name: str, species_data: dict, language, variation: bool = False
    ):
        super().__init__(
            colour=Colour.dark_gold(),
            title=species_name,
            description=species_data["desc"],
        )
        difficulty_dict = {
            1: "<:trivial:1219233272987648070>",
            2: "<:easy:1219232432671428608>",
            3: "<:medium:1219232485536432138>",
            4: "<:challenging:1219232486693928970>",
            5: "<:hard:1219232488602337291>",
            6: "<:extreme:1219232490288451595>",
            7: "<:suicide_mission:1219239152332312696>",
            8: "<:impossible:1219234932145131570>",
            9: "<:helldive:1219238179551318067>",
            "?": "?",
        }
        file_name = species_name.replace(" ", "_")
        self.add_field(
            language["enemy.introduced"],
            f"{language['enemy.difficulty']} {species_data['start']} {difficulty_dict[species_data['start']]}",
            inline=False,
        ).add_field(
            language["enemy.tactics"], species_data["tactics"], inline=False
        ).add_field(
            language["enemy.weak_spots"], species_data["weak spots"], inline=False
        )
        variations = ""
        if not variation and species_data["variations"] != None:
            for i in species_data["variations"]:
                variations += f"\n- {i}"
            self.add_field(language["enemy.variations"], variations)
        try:
            self.set_thumbnail(
                file=File(f"resources/enemies/terminids/{file_name}.png")
            )
            self.image_set = True
        except:
            self.image_set = False


class Automaton(Embed):
    def __init__(
        self, bot_name: str, bot_data: dict, language, variation: bool = False
    ):
        super().__init__(
            colour=Colour.brand_red(),
            title=bot_name,
            description=bot_data["desc"],
        )
        difficulty_dict = {
            1: "<:trivial:1219233272987648070>",
            2: "<:easy:1219232432671428608>",
            3: "<:medium:1219232485536432138>",
            4: "<:challenging:1219232486693928970>",
            5: "<:hard:1219232488602337291>",
            6: "<:extreme:1219232490288451595>",
            7: "<:suicide_mission:1219239152332312696>",
            8: "<:impossible:1219234932145131570>",
            9: "<:helldive:1219238179551318067>",
            "?": "?",
        }
        file_name = bot_name.replace(" ", "_")
        self.add_field(
            language["enemy.introduced"],
            f"{language['enemy.difficulty']} {bot_data['start']} {difficulty_dict[bot_data['start']]}",
            inline=False,
        ).add_field(
            language["enemy.tactics"], bot_data["tactics"], inline=False
        ).add_field(
            language["enemy.weak_spots"], bot_data["weak spots"], inline=False
        )
        variations = ""
        if not variation and bot_data["variations"] != None:
            for i in bot_data["variations"]:
                variations += f"\n- {i}"
            self.add_field(language["enemy.variations"], variations)
        try:
            self.set_thumbnail(
                file=File(f"resources/enemies/automatons/{file_name}.png")
            )
            self.image_set = True
        except:
            self.image_set = False


class Illuminate(Embed):
    def __init__(
        self,
        illuminate_name: str,
        illuminate_data: dict,
        language,
        variation: bool = False,
    ):
        super().__init__(
            colour=Colour.blue(),
            title=illuminate_name,
            description=illuminate_data["desc"],
        )
        difficulty_dict = {
            1: "<:trivial:1219233272987648070>",
            2: "<:easy:1219232432671428608>",
            3: "<:medium:1219232485536432138>",
            4: "<:challenging:1219232486693928970>",
            5: "<:hard:1219232488602337291>",
            6: "<:extreme:1219232490288451595>",
            7: "<:suicide_mission:1219239152332312696>",
            8: "<:impossible:1219234932145131570>",
            9: "<:helldive:1219238179551318067>",
            "?": "?",
        }
        file_name = illuminate_name.replace(" ", "_")
        self.add_field(
            language["enemy.introduced"],
            f"{language['enemy.difficulty']} {illuminate_data['start']} {difficulty_dict[illuminate_data['start']]}",
            inline=False,
        ).add_field(
            language["enemy.tactics"], illuminate_data["tactics"], inline=False
        ).add_field(
            language["enemy.weak_spots"], illuminate_data["weak spots"], inline=False
        )
        variations = ""
        if not variation and illuminate_data["variations"] != None:
            for i in illuminate_data["variations"]:
                variations += f"\n- {i}"
            self.add_field(language["enemy.variations"], variations)
        try:
            self.set_thumbnail(
                file=File(f"resources/enemies/automatons/{file_name}.png")
            )
            self.image_set = True
        except:
            self.image_set = False


class ReactRoleDashboard(Embed):
    def __init__(self):
        super().__init__(title="Roles", colour=Colour.dark_theme())
        self.add_field(
            "Select the buttons below to be given specific roles.",
            "These buttons only give roles in this server.",
        )


class AnnouncementEmbed(Embed):
    def __init__(self):
        super().__init__(
            title="Galactic Wide Web Update",
            description="An update has been released!",
            colour=Colour.blue(),
        )
        self.add_field(
            "Direct Feedback",
            (
                "Fancy giving me some feedback but don't want to join the support server? Well now you can!\n"
                "- </feedback:1253094891513184356>\n"
                "Using this command gives you a text box to let me know if something isnt working for you or provide feedback about the bot\n"
                "-# This gets sent to a channel that only I can read."
            ),
            inline=False,
        )
        self.add_field(
            "Liberation rate",
            (
                "I have also been working on the liberation rate for planets that are active\n"
                "This is based off a 4-point rolling average over the last hour so I *think* it's pretty accurate\n"
                "I'll be working on time-to-victory/defeat soon!"
            ),
        )


class SetupEmbed(Embed):
    def __init__(self):
        super().__init__(colour=Colour.brand_green())


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
