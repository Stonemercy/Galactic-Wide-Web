from disnake import Embed, Colour, File
from datetime import datetime
from helpers.functions import dispatch_format, health_bar, short_format, steam_format
from data.lists import reward_types


class Planet(Embed):
    def __init__(self, data):
        super().__init__(colour=Colour.blue())
        self.planet = data
        if self.planet["currentOwner"] != "Humans":
            atk_def = "atk"
        else:
            atk_def = "def"
        planet_health_bar = health_bar(
            self.planet["health"], self.planet["maxHealth"], atk_def
        )
        self.add_field(
            f"__**{self.planet['name']}**__",
            (
                f"Sector: **{self.planet['sector']}**\n"
                f"Planet health:\n"
                f"{planet_health_bar}\n"
                f"`{self.planet['health']:>9,}/{self.planet['maxHealth']:<10,} +{self.planet['regenPerSecond']:.1f}/s`\n"
                "\u200b\n"
            ),
            inline=False,
        ).add_field(
            "Missions Stats",
            (
                f"Missions Won: **{short_format(self.planet['statistics']['missionsWon'])}**\n"
                f"Missions Lost: **{short_format(self.planet['statistics']['missionsLost'])}**\n"
                f"Mission Winrate: **{self.planet['statistics']['missionSuccessRate']}%**\n"
                f"Time spent in missions: **{self.planet['statistics']['missionTime']/31556952:.1f} years**"
            ),
        ).add_field(
            "Hero Stats",
            (
                f"Active heroes: **{self.planet['statistics']['playerCount']:,}**\n"
                f"Heroes lost: **{short_format(self.planet['statistics']['deaths'])}**\n"
                f"Friendly-fire Accidents: **{short_format(self.planet['statistics']['friendlies'])}**\n"
                f"Shots Fired: **{short_format(self.planet['statistics']['bulletsFired'])}**\n"
                f"Shots Hit: **{short_format(self.planet['statistics']['bulletsHit'])}**\n"
                f"Hero Accuracy: **{self.planet['statistics']['accuracy']}%**\n"
            ),
        )
        if self.planet["currentOwner"] == "Automaton":
            self.add_field(
                "Automaton Kills:",
                f"**{short_format(self.planet['statistics']['automatonKills'])}**",
                inline=False,
            )
            self.set_author(
                name="Liberation Progress",
                icon_url="https://cdn.discordapp.com/emojis/1215036421551685672.webp?size=44&quality=lossless",
            )
        elif self.planet["currentOwner"] == "Terminid":
            self.add_field(
                "Terminid Kills:",
                f"**{short_format(self.planet['statistics']['terminidKills'])}**",
                inline=False,
            )
            self.set_author(
                name="Liberation Progress",
                icon_url="https://cdn.discordapp.com/emojis/1215036423090999376.webp?size=44&quality=lossless",
            )
        self.set_thumbnail(file=File(f"resources/freedom.gif"))
        self.add_field(
            "", f"As of <t:{int(datetime.now().timestamp())}:R>", inline=False
        )


class HelpEmbed(Embed):
    def __init__(self):
        super().__init__(colour=Colour.green(), title="Help")


class BotDashboardEmbed(Embed):
    def __init__(self, dt: datetime):
        super().__init__(colour=Colour.green(), title="GWW Overview")
        self.description = (
            "This is the dashboard for all information about the GWW itself"
        )
        self.set_footer(text=f"Updated at {dt.strftime('%H:%M')}GMT")


class MajorOrderEmbed(Embed):
    def __init__(self, assignment, planets):
        super().__init__(title="MAJOR ORDER UPDATE", colour=Colour.brand_red())
        self.assignment = assignment
        self.planets = planets

        self.set_footer(text=f"MESSAGE #{self.assignment['id']}")
        self.add_field(self.assignment["description"], self.assignment["briefing"])
        for i in self.assignment["tasks"]:
            if i["type"] == 11:
                planet = self.planets[i["values"][2]]
                planet_health_bar = health_bar(
                    planet["health"], planet["maxHealth"], "atk"
                )
                self.add_field(
                    planet["name"],
                    f"Heroes: **{planet['statistics']['playerCount']:,}\n{planet_health_bar}**",
                    inline=False,
                )
        self.add_field(
            "Reward",
            f"{self.assignment['reward']['amount']} {reward_types[self.assignment['reward']['type']]} <:medal:1226254158278037504>",
            inline=False,
        )


class DispatchesEmbed(Embed):
    def __init__(self, dispatch):
        super().__init__(colour=Colour.brand_red())
        self.dispatch = dispatch
        self.set_footer(text=f"MESSAGE #{self.dispatch['id']}")
        message: str = self.dispatch["message"]
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
        self.description = content


class CampaignEmbeds:
    class NewCampaign(Embed):
        def __init__(
            self,
            campaign,
            planet_status,
            attacker: str,
            thumbnail_link: str = None,
        ):
            super().__init__(
                title="**⚠️ URGENT CALL TO ALL HELLDIVERS ⚠️**", colour=Colour.brand_red()
            )
            self.planet_status = planet_status
            self.attacker = attacker
            if thumbnail_link != None:
                self.set_thumbnail(thumbnail_link)
            if self.planet_status["currentOwner"] != "Humans":
                self.description = (
                    f"**{campaign['planet']['name']}** requires liberation from the **{self.planet_status['currentOwner']}**!\n\n"
                    f"Assist the other **{self.planet_status['statistics']['playerCount']} Helldivers** in the fight for **Democracy**"
                )
                self.add_field("Objective", "Attack")
            elif self.planet_status["currentOwner"] == "Humans":
                self.description = (
                    f"**{campaign['planet']['name']}** requires defending from the **{self.attacker}**!\n\n"
                    f"Assist the other **{self.planet_status['statistics']['playerCount']}** Helldivers in the fight for **Democracy**"
                )
                self.colour = Colour.blue()
                self.add_field("Objective", "Defend")

    class CampaignVictory(Embed):
        def __init__(self, planet_status, defended: bool, liberated_from: str = None):
            super().__init__(
                colour=Colour.brand_green(),
                title=f"VICTORY IN {planet_status['name']}!",
            )
            if defended == True:
                self.description = f"{planet_status['name']} has successfully pushed back the attacks thanks to the brave actions of **{planet_status['statistics']['playerCount']} Helldivers**"
                self.set_image(
                    "https://cdn.discordapp.com/attachments/1212735927223590974/1224286105726222386/freedom.gif?ex=661cf049&is=660a7b49&hm=ac1f27724e7b998593793abab579e4cfd8b52972c54a03a6c21aaace35a9dd09&"
                )
            else:
                self.description = f"{planet_status['name']} has been successfully liberated from the {liberated_from.capitalize()} thanks to the brave actions of **{planet_status['statistics']['playerCount']} Helldivers**"
                self.set_image(
                    "https://cdn.discordapp.com/attachments/1212735927223590974/1224286105726222386/freedom.gif?ex=661cf049&is=660a7b49&hm=ac1f27724e7b998593793abab579e4cfd8b52972c54a03a6c21aaace35a9dd09&"
                )

    class CampaignLoss(Embed):
        def __init__(self, planet_status, defended: bool, liberator: str = None):
            super().__init__(colour=Colour.brand_red(), title="Tragic Loss")
            if defended == True:
                self.description = f"{planet_status['planet']['name']} has been taken by the **{liberator}**\nWe must not let them keep it!"
            else:
                self.description = f"We have failed to take {planet_status['name']} from the {planet_status['currentOwner']}.\nWe must try harder next time!"


class Dashboard:
    def __init__(self, data):
        # organise data
        self.now = datetime.now()
        self.campaigns = data["campaigns"]
        self.assignment = data["assignments"][0]
        self.planet_events = data["planet_events"]
        self.planets = data["planets"]
        if self.planets == None:
            print(True)
        self.faction_dict = {
            "Automaton": "<:automaton:1215036421551685672>",
            "Terminids": "<:terminid:1215036423090999376>",
        }

        # make embeds
        self.defend_embed = Embed(title="Defending", colour=Colour.blue())
        self.attack_embed = Embed(title="Attacking", colour=Colour.red())
        self.major_orders_embed = Embed(title="Major Order", colour=Colour.red())

        # Major Orders
        if self.assignment != None:
            self.major_orders_embed.add_field(
                f"MESSAGE #{self.assignment['id']} - {self.assignment['description']}",
                f"`{self.assignment['briefing']}`\n\u200b\n",
                inline=False,
            )
            for i in self.assignment["tasks"]:
                if i["type"] == 11:
                    planet = self.planets[i["values"][2]]
                    atk_def = "def" if planet["currentOwner"] == "Humans" else "atk"
                    completed = (
                        "LIBERATED" if planet["currentOwner"] == "Humans" else ""
                    )
                    planet_health_bar = health_bar(
                        planet["health"], planet["maxHealth"], atk_def
                    )
                    self.major_orders_embed.add_field(
                        planet["name"],
                        f"Heroes: **{planet['statistics']['playerCount']:,}\n{planet_health_bar}** {completed}",
                        inline=False,
                    )
                else:
                    self.major_orders_embed.add_field(
                        i["values"], i["valuesTypes"], inline=False
                    )

            self.major_orders_embed.add_field(
                "Reward",
                f"{self.assignment['reward']['amount']} {reward_types[self.assignment['reward']['type']]} <:medal:1226254158278037504>",
                inline=False,
            )

        # Defending
        if self.planet_events != None:
            for i in self.planet_events:
                faction_icon = self.faction_dict[i["event"]["faction"]]
                time = datetime.fromisoformat(i["event"]["endTime"]) or None
                time_remaining = (
                    f"<t:{time.timestamp():.0f}:f>" if time != None else "Unavailable"
                )
                planet_health_bar = health_bar(i["health"], i["maxHealth"])
                event_health_bar = health_bar(
                    i["event"]["health"], i["event"]["max_health"], "atk"
                )
                self.defend_embed.add_field(
                    f"{faction_icon} - __**{i['name']}**__",
                    (
                        f"Time left: {time_remaining}\n"
                        f"Heroes: **{i['planet']['statistics']['players']:,}**\n\n"
                        f"Event health:\n"
                        f"{event_health_bar}\n"
                        f"`{i['health']:>10,}/{i['maxHealth']:<11,}`\n\n"
                        f"Planet health:\n"
                        f"{planet_health_bar}\n"
                        f"`{i['event']['health']:>10,}/{i['event']['max_health']:<11,} +{i['planet']['regenPerSecond']:.0f}/s`\n"
                        "\u200b\n"
                    ),
                    inline=False,
                )

        if len(self.defend_embed.fields) < 1:
            self.defend_embed.add_field(
                "There are currently no threats to our Freedom", "||for now...||"
            )

        # Attacking
        for i in self.campaigns:
            if i["planet"]["event"] != None:
                continue
            faction_icon = self.faction_dict[i["planet"]["currentOwner"]]
            planet_health_bar = health_bar(
                i["planet"]["health"], i["planet"]["maxHealth"], "atk"
            )
            if i["planet"]["currentOwner"] == "Automaton":
                self.attack_embed.insert_field_at(
                    0,
                    f"{faction_icon} - __**{i['planet']['name']}**__ - Battle **#{i['count']}**",
                    (
                        f"Sector: **{i['planet']['sector']}**\n"
                        f"Heroes: **{i['planet']['statistics']['playerCount']:,}**\n"
                        f"Mission sucess rate: **{i['planet']['statistics']['missionSuccessRate']}%**\n"
                        f"Automaton kill count: **{short_format(i['planet']['statistics']['automatonKills'])}**\n"
                        f"Planet health:\n"
                        f"{planet_health_bar}\n"
                        f"`{i['planet']['health']:>10,}/{i['planet']['maxHealth']:<11,} +{i['planet']['regenPerSecond']:.0f}/s`\n"
                        "\u200b\n"
                    ),
                    inline=False,
                )
            else:
                self.attack_embed.add_field(
                    f"{faction_icon} - __**{i['planet']['name']}**__ - Battle **#{i['count']}**",
                    (
                        f"Sector: **{i['planet']['sector']}**\n"
                        f"Heroes: **{i['planet']['statistics']['playerCount']:,}**\n"
                        f"Mission sucess rate: **{i['planet']['statistics']['missionSuccessRate']}%**\n"
                        f"Terminid kill count: **{short_format(i['planet']['statistics']['terminidKills'])}**\n"
                        f"Planet Health:\n"
                        f"{planet_health_bar}\n"
                        f"`{i['planet']['health']:>10,}/{i['planet']['maxHealth']:<11,} +{i['planet']['regenPerSecond']:.0f}/s`\n"
                        "\u200b\n"
                    ),
                    inline=False,
                )

        # Other
        self.timestamp = int(self.now.timestamp())
        self.attack_embed.add_field(
            "\u200b",
            f"Updated on <t:{self.timestamp}:f> - <t:{self.timestamp}:R>",
            inline=False,
        )

        if len(self.major_orders_embed.fields) < 1:
            self.major_orders_embed.add_field("There are no Major Orders", "\u200b")
        self.attack_embed.set_image("https://i.imgur.com/cThNy4f.png")
        self.defend_embed.set_image("https://i.imgur.com/cThNy4f.png")
        self.major_orders_embed.set_image("https://i.imgur.com/cThNy4f.png")
        self.embeds = [
            self.major_orders_embed,
            self.defend_embed,
            self.attack_embed,
        ]


class Weapons:
    class All(Embed):
        def __init__(self, data: list):
            super().__init__(colour=Colour.blue(), title="The Arsenal")
            self.data = data
            for n, i in enumerate(self.data):
                self.fire_modes = []
                stats = i[1]
                if stats["fire modes"]["semi"]:
                    self.fire_modes.append("Semi-automatic")
                if stats["fire modes"]["burst"]:
                    self.fire_modes.append("Burst")
                if stats["fire modes"]["auto"]:
                    self.fire_modes.append("Automatic")
                self.fire_modes = ", ".join(self.fire_modes)

                self.add_field(
                    name=f"{n + 1} - {i[0]}",
                    value=(
                        f"Type: `{stats['type']}`\n"
                        f"Damage: `{stats['damage']}`\n"
                        f"Fire Rate: `{stats['fire rate']}`\n"
                        f"DPS: `{stats['dps']}`\n"
                        f"Recoil: `{stats['recoil']}`\n"
                        f"Capacity: `{stats['capacity']}`\n"
                        f"Armour Pen: `{stats['armour penetration']}`\n"
                        f"Fire Modes: `{self.fire_modes}`\n"
                        f"Special Effects: `{stats['effects']}`\n"
                    ),
                )

    class Single(Embed):
        def __init__(self, name: str, data: dict):
            super().__init__(colour=Colour.blue())
            self.data = data
            self.fire_modes = []
            if self.data["fire modes"]["semi"]:
                self.fire_modes.append("Semi-automatic")
            if self.data["fire modes"]["burst"]:
                self.fire_modes.append("Burst")
            if self.data["fire modes"]["auto"]:
                self.fire_modes.append("Automatic")
            self.fire_modes = ", ".join(self.fire_modes)

            self.add_field(
                name=name,
                value=(
                    f"Type: `{self.data['type']}`\n"
                    f"Damage: `{self.data['damage']}`\n"
                    f"Fire Rate: `{self.data['fire rate']}`\n"
                    f"DPS: `{self.data['dps']}`\n"
                    f"Recoil: `{self.data['recoil']}`\n"
                    f"Capacity: `{self.data['capacity']}`\n"
                    f"Armour Pen: `{self.data['armour penetration']}`\n"
                    f"Fire Modes: `{self.fire_modes}`\n"
                    f"Special Effects: `{self.data['effects']}`\n"
                ),
            )
            try:
                file_name = name.replace(" ", "-")
                self.set_thumbnail(file=File(f"resources/weapons/{file_name}.png"))
            except Exception as e:
                print("passing", e)
                pass


class Terminid(Embed):
    def __init__(self, species_name: str, species_data: dict, variation: bool = False):
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
            "Introduced",
            f"Difficulty {species_data['start']} {difficulty_dict[species_data['start']]}",
            inline=False,
        ).add_field("Tactics", species_data["tactics"], inline=False).add_field(
            "Weak Spots", species_data["weak spots"], inline=False
        )
        variations = []
        if variation == False and species_data["variations"] != None:
            for i in species_data["variations"]:
                variations.append(i)
            self.add_field("Variations", ", ".join(variations))
        try:
            self.set_thumbnail(
                file=File(f"resources/enemies/terminids/{file_name}.png")
            )
        except:
            pass


class Automaton(Embed):
    def __init__(self, bot_name: str, bot_data: dict, variation: bool = False):
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
            "Introduced",
            f"Difficulty {bot_data['start']} {difficulty_dict[bot_data['start']]}",
            inline=False,
        ).add_field("Tactics", bot_data["tactics"], inline=False).add_field(
            "Weak Spots", bot_data["weak spots"], inline=False
        )
        variations = []
        if variation == False and bot_data["variations"] != None:
            for i in bot_data["variations"]:
                variations.append(i)
            self.add_field("Variations", ", ".join(variations))
        try:
            self.set_thumbnail(
                file=File(f"resources/enemies/automatons/{file_name}.png")
            )
        except:
            pass
