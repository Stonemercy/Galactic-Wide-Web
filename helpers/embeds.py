from json import load
from disnake import Embed, Colour, File, ModalInteraction
from datetime import datetime
from helpers.functions import (
    dispatch_format,
    health_bar,
    short_format,
    skipped_planets,
    steam_format,
)
from data.lists import (
    emojis_dict,
    warbond_images_dict,
    supported_languages,
    emotes_list,
    victory_poses_list,
    player_cards_list,
    titles_list,
)


class Planet(Embed):
    def __init__(self, data, thumbnail_url: str, language):
        super().__init__(colour=Colour.blue())
        self.planet = data
        self.language = load(open(f"data/languages/{language}.json", encoding="UTF-8"))
        if self.planet["event"] != None:
            planet_health_bar = health_bar(
                self.planet["health"],
                self.planet["maxHealth"],
                self.planet["currentOwner"],
                True,
            )
            health_text = f"{1 - (self.planet['event']['health'] / self.planet['event']['maxHealth']):^25,.2%}"
        else:
            planet_health_bar = health_bar(
                (
                    self.planet["health"]
                    if self.planet["event"] == None
                    else self.planet["event"]["health"]
                ),
                (
                    self.planet["maxHealth"]
                    if self.planet["event"] == None
                    else self.planet["event"]["maxHealth"]
                ),
                self.planet["currentOwner"],
                True if self.planet["currentOwner"] != "Humans" else False,
            )
            health_text = (
                f"{1 - (self.planet['health'] / self.planet['maxHealth']):^25,.2%}"
                if self.planet["currentOwner"] != "Humans"
                else f"{(self.planet['health'] / self.planet['maxHealth']):^25,.2%}"
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
                f"`{health_text}`\n"
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
                self.add_field(
                    self.planet_names_loc[str(planet["index"])]["names"][
                        supported_languages[language]
                    ],
                    (
                        f"{self.language['major_order.heroes']}: **{planet['statistics']['playerCount']:,}**\n"
                        f"{self.language['dashboard.major_order_occupied_by']}: **{self.language[planet['currentOwner'].lower()]}**\n"
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
        if len(content) > 4000:
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
            description += f"🛡️ {self.language['campaigns.defend']} **{campaign['planet']['name']}** {self.faction_dict[campaign['planet']['event']['faction']]}\n> *{self.language['campaigns.ends']} {time_remaining}*\n"
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
    def __init__(self, data, language, liberation_changes):
        self.now = datetime.now()
        self.language = load(open(f"data/languages/{language}.json", encoding="UTF-8"))
        self.planet_names_loc = load(
            open(f"data/json/planets/planets.json", encoding="UTF-8")
        )
        self.campaigns = [
            item
            for item in sorted(
                data["campaigns"],
                key=lambda item: item["planet"]["statistics"]["playerCount"],
                reverse=True,
            )
        ]
        self.assignments = data["assignments"]
        self.planet_events = (
            [
                item
                for item in sorted(
                    data["planet_events"],
                    key=lambda item: item["statistics"]["playerCount"],
                    reverse=True,
                )
            ]
            if data["planet_events"] != None
            else None
        )
        self.planets = data["planets"]
        self.faction_dict = {
            "Automaton": "<:a_:1215036421551685672>",
            "Terminids": "<:t_:1215036423090999376>",
            "Illuminate": "<:i_:1218283483240206576>",
        }
        self.MO_planets = []
        self.total_players = sum(
            [planet["statistics"]["playerCount"] for planet in self.planets]
        )

        # make embeds
        self.major_orders_embed = Embed(
            title=self.language["dashboard.major_order"], colour=Colour.yellow()
        )
        self.defend_embed = Embed(
            title=self.language["dashboard.defending"], colour=Colour.blue()
        )
        self.automaton_embed = Embed(
            title=self.language["dashboard.attacking_automatons"], colour=Colour.red()
        )
        self.terminids_embed = Embed(
            title=self.language["dashboard.attacking_terminids"], colour=Colour.red()
        )
        self.illuminate_embed = Embed(
            title=self.language["dashboard.attacking_illuminate"], colour=Colour.red()
        )
        self.updated_embed = Embed(
            title=self.language["dashboard.other_updated"], colour=Colour.dark_theme()
        )

        # Major Orders
        if self.assignments != []:
            reward_types = load(open("data/json/assignments/reward/type.json"))
            self.major_orders_embed.set_thumbnail(
                "https://media.discordapp.net/attachments/1212735927223590974/1240708455040548997/MO_defend.png?ex=66478b4a&is=664639ca&hm=2593a504f96bd5e889772762c2e9790caa08fc279ca48ea0f03c70fa74efecb5&=&format=webp&quality=lossless"
            )
            for assignment in self.assignments:
                assignment["briefing"] = (
                    assignment["briefing"].replace("<i=1>", "**").replace("</i>", "**")
                )
                self.major_orders_embed.add_field(
                    f"{self.language['dashboard.major_order_message']} #{assignment['id']} - {assignment['description']}",
                    f"{assignment['briefing']}\n\u200b\n",
                    inline=False,
                )
                for task in assignment["tasks"]:
                    if task["type"] == 11 or task["type"] == 13:
                        planet = self.planets[task["values"][2]]
                        self.MO_planets.append(planet["name"])
                        if planet["event"] != None:
                            planet_health_bar = health_bar(
                                planet["event"]["health"],
                                planet["event"]["maxHealth"],
                                "MO",
                                True,
                            )
                            completed = (
                                f"🛡️ {self.faction_dict[planet['event']['faction']]}"
                            )
                            health_text = f"{1 - (planet['event']['health'] / planet['event']['maxHealth']):^25,.2%}"
                        else:
                            planet_health_bar = health_bar(
                                planet["health"],
                                planet["maxHealth"],
                                (
                                    "MO"
                                    if planet["currentOwner"] != "Humans"
                                    else "Humans"
                                ),
                                True if planet["currentOwner"] != "Humans" else False,
                            )
                            completed = (
                                self.language["dashboard.major_order_liberated"]
                                if planet["currentOwner"] == "Humans"
                                else ""
                            )
                            health_text = (
                                f"{1 - (planet['health'] / planet['maxHealth']):^25,.2%}"
                                if planet["currentOwner"] != "Humans"
                                else f"{(planet['health'] / planet['maxHealth']):^25,.2%}"
                            )
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
                    elif task["type"] == 12:
                        event_health_bar = health_bar(
                            assignment["progress"][0], i["values"][0], "MO"
                        )
                        self.major_orders_embed.add_field(
                            f"{self.language['dashboard.major_order_succeed_in_defense']} {task['values'][0]} {self.language['dashboard.planets']}",
                            (
                                f"{self.language['dashboard.major_order_progress']}: {assignment['progress'][0]}/{task['values'][0]}\n"
                                f"{event_health_bar}\n"
                                f"`{(assignment['progress'][0] / task['values'][0]):^25,.2%}`\n"
                            ),
                            inline=False,
                        )
                    elif task["type"] == 3:
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
                            assignment["progress"][0], task["values"][2], "MO"
                        )
                        self.major_orders_embed.add_field(
                            f"{self.language['dashboard.major_order_kill']} {short_format(task['values'][2])} {loc_faction[task['values'][0]]} {faction_dict[task['values'][0]]}",
                            (
                                f"{self.language['major_order.progress']}: **{short_format(assignment['progress'][0])}**/**{short_format(task['values'][2])}**\n"
                                f"{event_health_bar}\n"
                                f"`{(assignment['progress'][0] / task['values'][2]):^25,.2%}`\n"
                            ),
                            inline=False,
                        )
                    else:
                        self.major_orders_embed.add_field(
                            self.language["dashboard_major_order_new_title"],
                            self.language["major_order_new_value"],
                        )
                progress_made = 0
                for progress in assignment["progress"]:
                    if progress == 1:
                        progress_made += 1
                self.major_orders_embed.add_field(
                    "Progress",
                    f"{progress_made} / {len(assignment['progress'])}",
                )
                self.major_orders_embed.add_field(
                    self.language["dashboard.major_order_reward"],
                    f"{assignment['reward']['amount']} {self.language[reward_types[str(assignment['reward']['type'])].lower()]} <:medal:1226254158278037504>",
                    inline=False,
                )
                self.major_orders_embed.add_field(
                    self.language["dashboard.major_order_ends"],
                    f"<t:{int(datetime.fromisoformat(assignment['expiration']).timestamp())}:R>",
                )
        else:
            self.major_orders_embed.add_field(
                self.language["dashboard.major_order_none"], "\u200b"
            )

        # Defending
        if self.planet_events not in ([], None):
            self.defend_embed.set_thumbnail("https://helldivers.io/img/defense.png")
            for planet in self.planet_events:
                liberation_text = ""
                time_to_complete = ""
                winning = ""
                if liberation_changes != {}:
                    liberation_change = liberation_changes[planet["name"]]
                    if len(liberation_change["liberation_change"]) > 0:
                        above_zero = (
                            "+"
                            if (
                                sum(liberation_change["liberation_change"])
                                / len(liberation_change["liberation_change"])
                            )
                            > 0
                            else ""
                        )
                        now = int(datetime.now().timestamp())
                        seconds_to_complete = (
                            int(
                                (1 - liberation_change["liberation"])
                                / sum(liberation_change["liberation_change"])
                            )
                            * 3600
                        )
                        winning = {
                            True: f"**{self.language['dashboard.victory']}**",
                            False: f"**{self.language['dashboard.defeat']}**",
                        }[
                            datetime.fromtimestamp(now + seconds_to_complete)
                            < datetime.fromisoformat(
                                planet["event"]["endTime"]
                            ).replace(tzinfo=None)
                        ]
                        time_to_complete = (
                            f"<t:{now + seconds_to_complete}:R>"
                            if winning == f"**{self.language['dashboard.victory']}**"
                            else ""
                        )
                        change = (
                            f"{(sum(liberation_change['liberation_change'])):.2%}/hour"
                        )
                        liberation_text = f"\n`{(above_zero + change):^25}` "
                faction_icon = self.faction_dict[planet["event"]["faction"]]
                time_remaining = f"<t:{datetime.fromisoformat(planet['event']['endTime']).timestamp():.0f}:R>"
                event_health_bar = health_bar(
                    planet["event"]["health"],
                    planet["event"]["maxHealth"],
                    "Humans",
                    True,
                )
                exclamation = (
                    "<:MO:1240706769043456031>"
                    if planet["name"] in self.MO_planets
                    else ""
                )
                self.defend_embed.add_field(
                    f"{faction_icon} - __**{self.planet_names_loc[str(planet['index'])]['names'][supported_languages[language]]}**__ {exclamation}",
                    (
                        f"{self.language['dashboard.defend_embed_ends']}: {time_remaining}"
                        f"\n{self.language['dashboard.heroes']}: **{planet['statistics']['playerCount']:,}**"
                        f"\n{self.language["dashboard.outlook"]}: {winning} {time_to_complete}"
                        f"\n{self.language['dashboard.defend_embed_event_health']}:"
                        f"\n{event_health_bar}"
                        f"\n**`{1 - (planet['event']['health'] / planet['event']['maxHealth']):^25,.2%}`**"
                        f"{liberation_text}"
                        "\u200b\n"
                    ),
                    inline=False,
                )
        else:
            self.defend_embed.add_field(
                self.language["dashboard.defend_embed_no_threats"],
                f"||{self.language['dashboard.defend_embed_for_now']}||",
            )

        # Attacking
        for embed in (
            self.terminids_embed,
            self.automaton_embed,
            self.illuminate_embed,
        ):
            embed.set_thumbnail("https://helldivers.io/img/attack.png")
        if self.campaigns != []:
            (
                skipped_terminid_planets,
                skipped_automaton_planets,
                skipped_illuminate_planets,
                self.campaigns,
            ) = skipped_planets(self.campaigns, self.total_players)
            for i in self.campaigns:
                time_to_complete = ""
                liberation_text = ""
                if liberation_changes != {}:
                    liberation_change = liberation_changes[i["planet"]["name"]]
                    if len(liberation_change["liberation_change"]) > 0:
                        above_zero = (
                            "+"
                            if (
                                sum(liberation_change["liberation_change"])
                                / len(liberation_change["liberation_change"])
                            )
                            > 0
                            else ""
                        )
                        if above_zero == "+":
                            now = int(datetime.now().timestamp())
                            seconds_to_complete = int(
                                (
                                    (1 - liberation_change["liberation"])
                                    / sum(liberation_change["liberation_change"])
                                )
                                * 3600
                            )
                            time_to_complete = (
                                f"\n{self.language["dashboard.outlook"]}: {self.language["dashboard.victory"]} <t:{now + seconds_to_complete}:R>"
                            )
                        change = (
                            f"{(sum(liberation_change['liberation_change'])):.2%}/hour"
                        )
                        liberation_text = f"`{(above_zero + change):^25}`"

                if i["planet"]["event"] != None:
                    continue
                exclamation = (
                    "<:MO:1240706769043456031>"
                    if i["planet"]["name"] in self.MO_planets
                    else ""
                )
                faction_icon = self.faction_dict[i["planet"]["currentOwner"]]
                if len(self.campaigns) < 9:
                    planet_health_bar = health_bar(
                        i["planet"]["health"],
                        i["planet"]["maxHealth"],
                        i["planet"]["currentOwner"],
                        True,
                    )
                    planet_health_text = f"`{(1 - (i['planet']['health'] / i['planet']['maxHealth'])):^25.2%}`"
                else:
                    planet_health_bar = ""
                    planet_health_text = f"**`{(1 - (i['planet']['health'] / i['planet']['maxHealth'])):^15.2%}`**"
                if i["planet"]["currentOwner"] == "Automaton":
                    self.automaton_embed.add_field(
                        f"{faction_icon} - __**{self.planet_names_loc[str(i['planet']['index'])]['names'][supported_languages[language]]}**__ {exclamation}",
                        (
                            f"{self.language['dashboard.heroes']}: **{i['planet']['statistics']['playerCount']:,}**"
                            f"{time_to_complete}"
                            f"\n{self.language['dashboard.attack_embed_planet_health']}:"
                            f"\n{planet_health_bar}"
                            f"\n**{planet_health_text}**"
                            f"\n{liberation_text}"
                            "\n\u200b\n"
                        ),
                        inline=False,
                    )
                elif i["planet"]["currentOwner"] == "Terminids":
                    self.terminids_embed.add_field(
                        f"{faction_icon} - __**{self.planet_names_loc[str(i['planet']['index'])]['names'][supported_languages[language]]}**__ {exclamation}",
                        (
                            f"{self.language['dashboard.heroes']}: **{i['planet']['statistics']['playerCount']:,}**"
                            f"{time_to_complete}"
                            f"\n{self.language['dashboard.attack_embed_planet_health']}:"
                            f"\n{planet_health_bar}"
                            f"\n**{planet_health_text}**"
                            f"\n{liberation_text}"
                            "\n\u200b\n"
                        ),
                        inline=False,
                    )
                elif i["planet"]["currentOwner"] == "Illuminate":
                    self.illuminate_embed.add_field(
                        f"{faction_icon} - __**{self.planet_names_loc[str(i['planet']['index'])]['names'][supported_languages[language]]}**__ {exclamation}",
                        (
                            f"{self.language['dashboard.heroes']}: **{i['planet']['statistics']['playerCount']:,}**"
                            f"{time_to_complete}"
                            f"\n{self.language['dashboard.attack_embed_planet_health']}:"
                            f"\n{planet_health_bar}"
                            f"\n**{planet_health_text}**"
                            f"\n{liberation_text}"
                            "\n\u200b\n"
                        ),
                        inline=False,
                    )

        # Other
        self.timestamp = int(self.now.timestamp())
        skipped_dict = {
            "terminid": {
                "string": "",
                "planets": skipped_terminid_planets,
                "embed": self.terminids_embed,
            },
            "automaton": {
                "string": "",
                "planets": skipped_automaton_planets,
                "embed": self.automaton_embed,
            },
            "illuminate": {
                "string": "",
                "planets": skipped_illuminate_planets,
                "embed": self.illuminate_embed,
            },
        }
        for values in skipped_dict.values():
            for planet, planet_values in values["planets"].items():
                exclamation = (
                    "<:MO:1240706769043456031>"
                    if self.planets[int(planet)]["name"] in self.MO_planets
                    else ""
                )
                values[
                    "string"
                ] += f"{self.planet_names_loc[planet]['names'][supported_languages[language]]} - {self.faction_dict[planet_values['owner']]} - {planet_values['players']} {exclamation}\n"
            if values["string"] != "":
                values["embed"].add_field(
                    self.language["dashboard.low_impact"],
                    values["string"],
                    inline=False,
                )

        self.updated_embed.add_field(
            "",
            f"<t:{self.timestamp}:f> - <t:{self.timestamp}:R>",
            inline=False,
        )
        self.updated_embed.add_field(
            "Total Players", f"{self.total_players:,}", inline=False
        )
        if len(self.campaigns) >= 10:
            self.updated_embed.add_field(
                "",
                f"*{self.language['dashboard.lite_mode']}*",
            )
        if self.now.strftime("%d/%m") == "26/10":
            self.major_orders_embed.set_footer(self.language["dashboard.liberty_day"])
        if self.now.strftime("%d/%m") == "03/04":
            self.major_orders_embed.set_footer(
                self.language["dashboard.malevelon_creek_day"]
            )
        self.embeds = []
        for embed in (
            self.major_orders_embed,
            self.defend_embed,
            self.automaton_embed,
            self.terminids_embed,
            self.illuminate_embed,
            self.updated_embed,
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
                        f"{language['weapons.fire_modes']}:**{gun_fire_modes}**\n"
                        f"{language['weapons.features']}:{features}"
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
                                f"Medal Cost: **{item['medal_cost']} <:medal:1226254158278037504>**\n\n"
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
                else:
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
        variations = ""
        if variation == False and species_data["variations"] != None:
            for i in species_data["variations"]:
                variations += f"\n- {i}"
            self.add_field(language["enemy.variations"], variations)
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
        variations = ""
        if variation == False and bot_data["variations"] != None:
            for i in bot_data["variations"]:
                variations += f"\n- {i}"
            self.add_field(language["enemy.variations"], variations)
        try:
            self.set_thumbnail(
                file=File(f"resources/enemies/automatons/{file_name}.png")
            )
        except:
            pass


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
            6: ":extreme:1219232490288451595>",
            7: "<:suicide_mission:1219239152332312696>",
            8: "<:impossible:1219234932145131570>",
            9: "<:helldive:1219238179551318067>",
            "?": "?",
        }
        file_name = illuminate_name.replace(" ", "-")
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
        if variation == False and illuminate_data["variations"] != None:
            for i in illuminate_data["variations"]:
                variations += f"\n- {i}"
            self.add_field(language["enemy.variations"], variations)
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
