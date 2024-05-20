from json import load
from disnake import Embed, Colour, File
from datetime import datetime
from helpers.functions import dispatch_format, health_bar, short_format, steam_format
from data.lists import emojis_dict, warbond_images_dict, supported_languages


class Planet(Embed):
    def __init__(self, data, thumbnail_url: str, language):
        super().__init__(colour=Colour.blue())
        self.planet = data
        self.language = load(open(f"data/languages/{language}.json", encoding="UTF-8"))
        planet_health_bar = health_bar(
            self.planet["health"], self.planet["maxHealth"], self.planet["currentOwner"]
        )
        enviros_text = ""
        for i in self.planet["hazards"]:
            enviros_text += f"\n- **{i['name']}**\n - {i['description']}"
        self.add_field(
            f"__**{self.planet['name']}**__",
            (
                f"{self.language['planet.sector']}: **{self.planet['sector']}**\n"
                f"{self.language['planet.owner']}: **{self.language[self.planet['currentOwner'].lower()]}**\n\n"
                f"🏔️ {self.language['planet.biome']} \n- **{self.planet['biome']['name']}**\n - {self.planet['biome']['description']}\n\n"
                f"🌪️ {self.language['planet.environmentals']}:{enviros_text}\n\n"
                f"{self.language['planet.planet_health']}\n"
                f"{planet_health_bar}\n"
                f"`{(self.planet['health'] / self.planet['maxHealth']):^25,.2%}`\n"
                "\u200b\n"
            ),
            inline=False,
        ).add_field(
            f"📊 {self.language['planet.mission_stats']}",
            (
                f"{self.language['planet.missions_won']}: **`{short_format(self.planet['statistics']['missionsWon'])}`**\n"
                f"{self.language['planet.missions_lost']}: **`{short_format(self.planet['statistics']['missionsLost'])}`**\n"
                f"{self.language['planet.missions_winrate']}: **`{self.planet['statistics']['missionSuccessRate']}%`**\n"
                f"{self.language['planet.missions_time_spent']}: **`{self.planet['statistics']['missionTime']/31556952:.1f} years`**"
            ),
        ).add_field(
            f"📈 {self.language['planet.hero_stats']}",
            (
                f"{self.language['planet.active_heroes']}: **`{self.planet['statistics']['playerCount']:,}`**\n"
                f"{self.language['planet.heroes_lost']}: **`{short_format(self.planet['statistics']['deaths'])}`**\n"
                f"{self.language['planet.accidents']}: **`{short_format(self.planet['statistics']['friendlies'])}`**\n"
                f"{self.language['planet.shots_fired']}: **`{short_format(self.planet['statistics']['bulletsFired'])}`**\n"
                f"{self.language['planet.shots_hit']}: **`{short_format(self.planet['statistics']['bulletsHit'])}`**\n"
                f"{self.language['planet.accuracy']}: **`{self.planet['statistics']['accuracy']}%`**\n"
            ),
        )
        faction_colour = {
            "Automaton": Colour.from_rgb(r=252, g=76, b=79),
            "Terminids": Colour.from_rgb(r=253, g=165, b=58),
            "Illuminate": Colour.from_rgb(r=116, g=163, b=180),
            "Humans": Colour.from_rgb(r=36, g=205, b=76),
        }
        self.colour = faction_colour[self.planet["currentOwner"]]
        if self.planet["currentOwner"] == "Automaton":
            self.add_field(
                f"💀 {self.language['automaton']} {self.language['planet.kills']}:",
                f"**{short_format(self.planet['statistics']['automatonKills'])}**",
                inline=False,
            )
            self.set_author(
                name=self.language["planet.liberation_progress"],
                icon_url="https://cdn.discordapp.com/emojis/1215036421551685672.webp?size=44&quality=lossless",
            )
        elif self.planet["currentOwner"] == "Terminids":
            self.add_field(
                f"💀 {self.language['terminids']} {self.language['planet.kills']}:",
                f"**`{short_format(self.planet['statistics']['terminidKills'])}`**",
                inline=False,
            )
            self.set_author(
                name=self.language["planet.liberation_progress"],
                icon_url="https://cdn.discordapp.com/emojis/1215036423090999376.webp?size=44&quality=lossless",
            )
        if thumbnail_url is not None:
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
    def __init__(self, assignment, planets, language):
        self.language = load(open(f"data/languages/{language}.json", encoding="UTF-8"))
        super().__init__(
            title=f"{emojis_dict['Left Banner']} {self.language['major_order.title']} {emojis_dict['Right Banner']}",
            colour=Colour.yellow(),
        )
        reward_types = load(open("data/json/assignments/reward/type.json"))
        self.set_footer(
            text=f"{self.language['major_order.message']} #{assignment['id']}"
        )
        self.add_field(assignment["description"], assignment["briefing"])
        self.planet_names_loc = load(
            open(f"data/json/planets/planets.json", encoding="UTF-8")
        )
        for i in assignment["tasks"]:
            if i["type"] == 11 or i["type"] == 13:
                planet = planets[i["values"][2]]
                planet_health_bar = health_bar(
                    planet["health"], planet["maxHealth"], "Humans"
                )
                self.add_field(
                    self.planet_names_loc[str(planet["index"])]["names"][
                        supported_languages[language]
                    ],
                    (
                        f"{self.language['major_order.heroes']}: **{planet['statistics']['playerCount']:,}**\n"
                        f"{planet_health_bar}\n"
                        f"`{(planet['health'] / planet['maxHealth']):^25,.2%}`\n"
                    ),
                    inline=False,
                )
            elif i["type"] == 12:
                event_health_bar = health_bar(i["progress"][0], i["values"][0], "MO")
                self.add_field(
                    f"{self.language['major_order.succeed_in_defense']} {i['values'][0]} {self.language['major_order.planets']}",
                    (
                        f"{self.language['major_order.progress']}: {i['progress'][0]}/{i['values'][0]}\n"
                        f"{event_health_bar}\n"
                        f"`{(i['progress'][0] / i['values'][0]):^25,.2%}`\n"
                    ),
                    inline=False,
                )
            elif i["type"] == 3:
                faction_dict = {
                    0: "",
                    1: "<:a_:1215036421551685672>",
                    2: "<:t_:1215036423090999376>",
                    3: "<:i_:1218283483240206576>",
                }
                loc_faction = {
                    0: self.language["humans"],
                    1: self.language["automaton"],
                    2: self.language["terminids"],
                    3: self.language["illuminate"],
                }
                event_health_bar = health_bar(
                    assignment["progress"][0], i["values"][2], "MO"
                )
                self.add_field(
                    f"{self.language['major_order.kill']} {short_format(i['values'][2])} **{loc_faction}**{faction_dict[i['values'][0]]}",
                    (
                        f"{self.language['major_order.progress']}: {short_format(i['progress'][0])}/{short_format(i['values'][2])}\n"
                        f"{event_health_bar}\n"
                        f"`{(i['progress'][0] / i['values'][2]):^25,.2%}`\n"
                    ),
                    inline=False,
                )
            else:
                self.add_field(
                    self.language["major_order.new_title"],
                    self.language["major_order.new_value"],
                )
        self.add_field(
            self.language["major_order.reward"],
            f"{assignment['reward']['amount']} {self.language[reward_types[str(assignment['reward']['type'])].lower()]} <:medal:1226254158278037504>",
            inline=False,
        )
        self.add_field(
            self.language["major_order.ends"],
            f"<t:{int(datetime.fromisoformat(assignment['expiration']).timestamp())}:R>",
        )


class DispatchesEmbed(Embed):
    def __init__(self, dispatch):
        super().__init__(colour=Colour.brand_red())
        self.dispatch = dispatch
        self.set_footer(text=f"MESSAGE #{self.dispatch['id']}")
        message = self.dispatch["message"]
        message = dispatch_format(message)
        self.add_field("Message Content", message)


class SteamEmbed(Embed):
    def __init__(self, steam):
        super().__init__(
            title=steam["title"], colour=Colour.dark_grey(), url=steam["url"]
        )
        self.steam = steam
        self.set_footer(text=f"MESSAGE #{self.steam['id']}")
        content = self.steam["content"]
        content = steam_format(content)
        if len(content) > 5750:
            content = f"Please head [here](<{steam['url']}>) to see the full patch notes as they are too long for Discord."
        self.description = content


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

        self.faction_dict = {
            "Automaton": "<:a_:1215036421551685672>",
            "Terminids": "<:t_:1215036423090999376>",
            "Illuminate": "<:i_:1218283483240206576>",
        }

    def add_new_campaign(self, campaign, time_remaining):
        name = self.fields[2].name
        description = self.fields[2].value
        if time_remaining:
            description += f"🛡️ {self.language['campaigns.defend']} **{campaign['planet']['name']}**{self.faction_dict[campaign['planet']['event']['faction']]}\n> *{self.language['campaigns.ends']} {time_remaining}*\n"
        else:
            description += f"⚔️ {self.language['campaigns.liberate']} **{campaign['planet']['name']}** {self.faction_dict[campaign['planet']['currentOwner']]}\n"
        self.set_field_at(2, name, description, inline=self.fields[1].inline)

    def add_campaign_victory(self, planet, liberatee):
        liberatee_loc = self.language[liberatee.lower()]
        name = self.fields[0].name
        description = self.fields[0].value
        description += f"**<:victory:1238069280508215337> {planet['name']}** {self.language['campaigns.been_liberated']} **{liberatee_loc}** {self.faction_dict[liberatee]}!\n"
        self.set_field_at(0, name, description, inline=self.fields[0].inline)

    def add_def_victory(self, planet):
        name = self.fields[0].name
        description = self.fields[0].value
        description += f"**<:victory:1238069280508215337> {planet['name']}** {self.language['campaigns.been_defended']}!\n"
        self.set_field_at(0, name, description, inline=self.fields[0].inline)

    def add_planet_lost(self, planet):
        name = self.fields[1].name
        description = self.fields[1].value
        description += f"**💀 {planet['name']}** {self.language['campaigns.been_lost']} **{self.language[planet['currentOwner'].lower()]}** {self.faction_dict[planet['currentOwner']]}\n"
        self.set_field_at(1, name, description, inline=self.fields[1].inline)

    def remove_empty(self):
        for field in self.fields:
            if field.value == "":
                self.remove_field(self.fields.index(field))


class Dashboard:
    def __init__(self, data, language):
        self.now = datetime.now()
        self.language = load(open(f"data/languages/{language}.json", encoding="UTF-8"))
        self.planet_names_loc = load(
            open(f"data/json/planets/planets.json", encoding="UTF-8")
        )
        self.campaigns = data["campaigns"]
        self.assignment = data["assignments"]
        self.planet_events = data["planet_events"]
        self.planets = data["planets"]
        self.war = data["war_state"]
        self.faction_dict = {
            "Automaton": "<:a_:1215036421551685672>",
            "Terminids": "<:t_:1215036423090999376>",
            "Illuminate": "<:i_:1218283483240206576>",
        }
        self.MO_planets = []

        # make embeds
        self.defend_embed = Embed(
            title=self.language["dashboard.defending"], colour=Colour.blue()
        )
        self.automaton_embed = Embed(
            title=self.language["dashboard.attacking_automatons"], colour=Colour.red()
        )
        self.terminids_embed = Embed(
            title=self.language["dashboard.attacking_terminids"], colour=Colour.red()
        )
        self.major_orders_embed = Embed(
            title=self.language["dashboard.major_order"], colour=Colour.yellow()
        )

        # Major Orders
        if self.assignment not in (None, []):
            reward_types = load(open("data/json/assignments/reward/type.json"))
            self.major_orders_embed.set_thumbnail(
                "https://media.discordapp.net/attachments/1212735927223590974/1240708455040548997/MO_defend.png?ex=66478b4a&is=664639ca&hm=2593a504f96bd5e889772762c2e9790caa08fc279ca48ea0f03c70fa74efecb5&=&format=webp&quality=lossless"
            )
            self.assignment = self.assignment[0]
            self.major_orders_embed.add_field(
                f"{self.language['dashboard.major_order_message']} #{self.assignment['id']} - {self.assignment['description']}",
                f"{self.assignment['briefing']}\n\u200b\n",
                inline=False,
            )
            for i in self.assignment["tasks"]:
                if i["type"] == 11 or i["type"] == 13:
                    planet = self.planets[i["values"][2]]
                    self.MO_planets.append(planet["name"])
                    if planet["event"] != None:
                        planet_health_bar = health_bar(
                            planet["event"]["health"],
                            planet["event"]["maxHealth"],
                            "MO",
                            True,
                        )
                        completed = f"🛡️ {self.faction_dict[planet['event']['faction']]}"
                        health_text = f"{1 - (planet['event']['health'] / planet['event']['maxHealth']):^25,.2%}"
                    else:
                        planet_health_bar = health_bar(
                            planet["health"],
                            planet["maxHealth"],
                            "MO" if planet["currentOwner"] != "Humans" else "Humans",
                            True if planet["currentOwner"] != "Humans" else False,
                        )
                        completed = (
                            self.language["dashboard.major_order_liberated"]
                            if planet["currentOwner"] == "Humans"
                            else ""
                        )
                        health_text = (
                            f"{(planet['health'] / planet['maxHealth']):^25,.2%}"
                        )
                    progress_made = 0
                    for progress in self.assignment["progress"]:
                        if progress == 1:
                            progress_made += 1
                    self.major_orders_embed.add_field(
                        self.planet_names_loc[str(planet["index"])]["names"][
                            supported_languages[language]
                        ],
                        (
                            f"{self.language['dashboard.heroes']}: **{planet['statistics']['playerCount']:,}**\n"
                            f"{self.language['dashboard.major_order_occupied_by']}: **{planet['currentOwner']}**\n"
                            f"{self.language['dashboard.major_order_event_health']}:\n"
                            f"{planet_health_bar} {completed}\n"
                            f"`{health_text}`\n"
                        ),
                        inline=False,
                    )
                    self.major_orders_embed.add_field(
                        "Progress",
                        f"{progress_made} / {len(self.assignment['progress'])}",
                    )
                elif i["type"] == 12:
                    event_health_bar = health_bar(
                        self.assignment["progress"][0], i["values"][0], "MO"
                    )
                    self.major_orders_embed.add_field(
                        f"{self.language['dashboard.major_order_succeed_in_defense']} {i['values'][0]} {self.language['dashboard.planets']}",
                        (
                            f"{self.language['dashboard.major_order_progress']}: {self.assignment['progress'][0]}/{i['values'][0]}\n"
                            f"{event_health_bar}\n"
                            f"`{(self.assignment['progress'][0] / i['values'][0]):^25,.2%}`\n"
                        ),
                        inline=False,
                    )
                elif i["type"] == 3:
                    self.major_orders_embed.set_thumbnail(
                        "https://media.discordapp.net/attachments/1212735927223590974/1240708455250133142/MO_exterminate.png?ex=66478b4a&is=664639ca&hm=301a0766d3bf6e48c335a7dbafec801ecbe176d65624e69a63cb030dad9b4d82&=&format=webp&quality=lossless"
                    )
                    faction_dict = {
                        0: "",
                        1: "",
                        2: "<:t_:1215036423090999376>",
                        3: "<:a_:1215036421551685672>",
                        4: "<:i_:1218283483240206576>",
                    }
                    loc_faction = {
                        0: self.language["enemies_of_freedom"],
                        1: self.language["humans"],
                        2: self.language["terminids"],
                        3: self.language["automaton"],
                        4: self.language["illuminate"],
                    }
                    event_health_bar = health_bar(
                        self.assignment["progress"][0], i["values"][2], "MO"
                    )
                    self.major_orders_embed.add_field(
                        f"{self.language['dashboard.major_order_kill']} {short_format(i['values'][2])} {loc_faction[i['values'][0]]} {faction_dict[i['values'][0]]}",
                        (
                            f"{self.language['major_order.progress']}: **{short_format(self.assignment['progress'][0])}**/**{short_format(i['values'][2])}**\n"
                            f"{event_health_bar}\n"
                            f"`{(self.assignment['progress'][0] / i['values'][2]):^25,.2%}`\n"
                        ),
                        inline=False,
                    )
                else:
                    self.major_orders_embed.add_field(
                        self.language["dashboard_major_order_new_title"],
                        self.language["major_order_new_value"],
                    )
            self.major_orders_embed.add_field(
                self.language["dashboard.major_order_reward"],
                f"{self.assignment['reward']['amount']} {self.language[reward_types[str(self.assignment['reward']['type'])].lower()]} <:medal:1226254158278037504>",
                inline=False,
            )
            self.major_orders_embed.add_field(
                self.language["dashboard.major_order_ends"],
                f"<t:{int(datetime.fromisoformat(self.assignment['expiration']).timestamp())}:R>",
            )
        if len(self.major_orders_embed.fields) < 1:
            self.major_orders_embed.add_field(
                self.language["dashboard.major_order_none"], "\u200b"
            )

        # Defending
        if self.planet_events != None:
            self.defend_embed.set_thumbnail("https://helldivers.io/img/defense.png")
            for i in self.planet_events:
                faction_icon = self.faction_dict[i["event"]["faction"]]
                time_remaining = f"<t:{datetime.fromisoformat(i['event']['endTime']).timestamp():.0f}:R>"
                event_health_bar = health_bar(
                    i["event"]["health"], i["event"]["maxHealth"], "Humans", True
                )
                exclamation = (
                    "<:MO:1240706769043456031>" if i["name"] in self.MO_planets else ""
                )
                self.defend_embed.add_field(
                    f"{faction_icon} - __**{self.planet_names_loc[str(i['index'])]['names'][supported_languages[language]]}**__ {exclamation}",
                    (
                        f"{self.language['dashboard.defend_embed_ends']}: {time_remaining}\n"
                        f"{self.language['dashboard.heroes']}: **{i['statistics']['playerCount']:,}**\n"
                        f"{self.language['dashboard.defend_embed_event_health']}:\n"
                        f"{event_health_bar}\n"
                        f"`{(1 - (i['event']['health'] / i['event']['maxHealth'])):^25,.2%}`\n"
                        "\u200b\n"
                    ),
                    inline=False,
                )

        if len(self.defend_embed.fields) < 1:
            self.defend_embed.add_field(
                self.language["dashboard.defend_embed_no_threats"],
                f"||{self.language['dashboard.defend_embed_for_now']}||",
            )

        # Attacking
        self.terminids_embed.set_thumbnail("https://helldivers.io/img/attack.png")
        self.automaton_embed.set_thumbnail("https://helldivers.io/img/attack.png")

        if self.campaigns != None:
            skipped_t_planets = {
                str(i["planet"]["index"]): i["planet"]["currentOwner"]
                for i in self.campaigns
                if i["planet"]["statistics"]["playerCount"] <= 500
                and i["planet"]["currentOwner"] == "Terminids"
            }
            skipped_a_planets = {
                str(i["planet"]["index"]): i["planet"]["currentOwner"]
                for i in self.campaigns
                if i["planet"]["statistics"]["playerCount"] <= 500
                and i["planet"]["currentOwner"] == "Automaton"
            }
            self.campaigns = [
                i
                for i in self.campaigns
                if i["planet"]["statistics"]["playerCount"] > 500
            ]
            for i in self.campaigns:
                if i["planet"]["event"] != None:
                    continue
                faction_icon = self.faction_dict[i["planet"]["currentOwner"]]
                if len(self.campaigns) < 10:
                    planet_health_bar = health_bar(
                        i["planet"]["health"],
                        i["planet"]["maxHealth"],
                        i["planet"]["currentOwner"],
                        True,
                    )
                    planet_health_text = f"\n`{(1 - (i['planet']['health'] / i['planet']['maxHealth'])):^25.2%}`"
                else:
                    planet_health_bar = ""
                    planet_health_text = f"**`{(1 - (i['planet']['health'] / i['planet']['maxHealth'])):^15.2%}`**"
                if i["planet"]["currentOwner"] == "Automaton":
                    self.automaton_embed.add_field(
                        f"{faction_icon} - __**{self.planet_names_loc[str(i['planet']['index'])]['names'][supported_languages[language]]}**__",
                        (
                            f"{self.language['dashboard.heroes']}: **{i['planet']['statistics']['playerCount']:,}**\n"
                            f"{self.language['dashboard.attack_embed_planet_health']}:\n"
                            f"{planet_health_bar}"
                            f"{planet_health_text}"
                            "\n\u200b\n"
                        ),
                        inline=False,
                    )
                else:
                    self.terminids_embed.add_field(
                        f"{faction_icon} - __**{self.planet_names_loc[str(i['planet']['index'])]['names'][supported_languages[language]]}**__",
                        (
                            f"{self.language['dashboard.heroes']}: **{i['planet']['statistics']['playerCount']:,}**\n"
                            f"{self.language['dashboard.attack_embed_planet_health']}:\n"
                            f"{planet_health_bar}"
                            f"{planet_health_text}"
                            "\n\u200b\n"
                        ),
                        inline=False,
                    )

        # Other
        self.timestamp = int(self.now.timestamp())
        s_t_p_string = ""
        for planet, owner in skipped_t_planets.items():
            s_t_p_string += f"{self.planet_names_loc[planet]['names'][supported_languages[language]]} - {self.faction_dict[owner]}\n"
        if s_t_p_string != "":
            self.terminids_embed.add_field(
                "Empty/low-pop planets",
                s_t_p_string,
                inline=False,
            )
        s_a_p_string = ""
        for planet, owner in skipped_a_planets.items():
            s_a_p_string += f"{self.planet_names_loc[planet]['names'][supported_languages[language]]} - {self.faction_dict[owner]}\n"
        if s_a_p_string != "":
            self.automaton_embed.add_field(
                "Empty/low-pop planets",
                s_a_p_string,
                inline=False,
            )
        self.terminids_embed.add_field(
            "\u200b",
            f"{self.language['dashboard.other_updated']} <t:{self.timestamp}:f> - <t:{self.timestamp}:R>",
            inline=False,
        )
        if len(self.campaigns) >= 10:
            self.terminids_embed.add_field(
                "",
                f"*{self.language['dashboard.lite_mode']}*",
            )
        if self.now.strftime("%d/%m") == "26/10":
            self.major_orders_embed.set_footer(self.language["dashboard.liberty_day"])
        if self.now.strftime("%d/%m") == "03/04":
            self.major_orders_embed.set_footer(
                self.language["dashboard.malevelon_creek_day"]
            )
        self.automaton_embed.set_image("https://i.imgur.com/cThNy4f.png")
        self.terminids_embed.set_image("https://i.imgur.com/cThNy4f.png")
        self.defend_embed.set_image("https://i.imgur.com/cThNy4f.png")
        self.major_orders_embed.set_image("https://i.imgur.com/cThNy4f.png")
        self.embeds = [
            self.major_orders_embed,
            self.defend_embed,
            self.automaton_embed,
            self.terminids_embed,
        ]


class Items:
    class Weapons:
        class Primary(Embed):
            def __init__(
                self,
                primary: dict,
                types: dict,
                fire_modes: dict,
                traits: dict,
                language,
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
                            f"\n- {traits[str(i)]} {emojis_dict[traits[str(i)]]}"
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
                        f"{language['weapons.fire_modes']}:**{gun_fire_modes}**"
                        f"{language['weapons.features']}:**{features}**"
                    ),
                )
                try:
                    self.set_thumbnail(
                        file=File(
                            f"resources/weapons/{primary['name'].replace(' ', '-')}.png"
                        )
                    )
                except:
                    pass

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
                            f"\n- {traits[str(i)]} {emojis_dict[traits[str(i)]]}"
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
                except:
                    pass

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
                except:
                    pass

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
                self.set_thumbnail(file=File(f"resources/boosters/booster.png"))
            except:
                pass

    class Warbond(Embed):
        def __init__(
            self,
            warbond: dict,
            warbond_json: str,
            item_names: dict,
            page,
        ):
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
                self.add_field(
                    f"{item_names[str(item['item_id'])]['name']}",
                    f"Medal cost: **{item['medal_cost']} <:medal:1226254158278037504>**",
                )
                if item_number % 2 == 0:
                    self.add_field("", "")
                item_number += 1


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
            6: ":extreme:1219232490288451595>",
            7: "<:suicide_mission:1219239152332312696>",
            8: "<:impossible:1219234932145131570>",
            9: "<:helldive:1219238179551318067>",
            "?": "?",
        }
        file_name = species_name.replace(" ", "-")
        self.add_field(
            language["enemy.introduced"],
            f"{language['enemy.difficulty']} {species_data['start']} {difficulty_dict[species_data['start']]}",
            inline=False,
        ).add_field(
            language["enemy.tactics"], species_data["tactics"], inline=False
        ).add_field(
            language["enemy.weak_spots"], species_data["weak spots"], inline=False
        )
        variations = []
        if variation == False and species_data["variations"] != None:
            for i in species_data["variations"]:
                variations.append(i)
            self.add_field(language["enemy.variations"], ", ".join(variations))
        try:
            self.set_thumbnail(
                file=File(f"resources/enemies/terminids/{file_name}.png")
            )
        except:
            pass


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
            6: ":extreme:1219232490288451595>",
            7: "<:suicide_mission:1219239152332312696>",
            8: "<:impossible:1219234932145131570>",
            9: "<:helldive:1219238179551318067>",
            "?": "?",
        }
        file_name = bot_name.replace(" ", "-")
        self.add_field(
            language["enemy.introduced"],
            f"{language['enemy.difficulty']} {bot_data['start']} {difficulty_dict[bot_data['start']]}",
            inline=False,
        ).add_field(
            language["enemy.tactics"], bot_data["tactics"], inline=False
        ).add_field(
            language["enemy.weak_spots"], bot_data["weak spots"], inline=False
        )
        variations = []
        if variation == False and bot_data["variations"] != None:
            for i in bot_data["variations"]:
                variations.append(i)
            self.add_field(language["enemy.variations"], ", ".join(variations))
        try:
            self.set_thumbnail(
                file=File(f"resources/enemies/automatons/{file_name}.png")
            )
        except:
            pass


class ReactRoleDashboard(Embed):
    def __init__(self):
        super().__init__(title="Roles", colour=Colour.dark_theme())
        self.add_field(
            "Select the buttons below to be given specific roles.",
            "These buttons only give roles in this server.",
        )
