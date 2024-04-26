from json import load
from disnake import Embed, Colour, File
from datetime import datetime
from helpers.functions import dispatch_format, health_bar, short_format, steam_format
from data.lists import emojis_dict


class Planet(Embed):
    def __init__(self, data, thumbnail_url: str, biome, enviros):
        super().__init__(colour=Colour.blue())
        self.planet = data
        planet_health_bar = health_bar(
            self.planet["health"], self.planet["maxHealth"], self.planet["currentOwner"]
        )
        enviros_text = ""
        for i in enviros:
            enviros_text += f"**\n{i['name']}**\n{i['description']}\n"
        self.add_field(
            f"__**{self.planet['name']}**__",
            (
                f"Sector: **{self.planet['sector']}**\n"
                f"Owner: **{self.planet['currentOwner']}**\n\n"
                f"Biome: \n**{biome['name']}**\n{biome['description']}\n\n"
                f"Environmental(s): {enviros_text}\n\n"
                f"Planet health:\n"
                f"{planet_health_bar}\n"
                f"`{(self.planet['health'] / self.planet['maxHealth']):^25,.2%}`\n"
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
        faction_colour = {
            "Automaton": Colour.from_rgb(r=252, g=76, b=79),
            "Terminids": Colour.from_rgb(r=253, g=165, b=58),
            "Illuminate": Colour.from_rgb(r=116, g=163, b=180),
            "Humans": Colour.from_rgb(r=36, g=205, b=76),
        }
        self.colour = faction_colour[self.planet["currentOwner"]]
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
        elif self.planet["currentOwner"] == "Terminids":
            self.add_field(
                "Terminid Kills:",
                f"**{short_format(self.planet['statistics']['terminidKills'])}**",
                inline=False,
            )
            self.set_author(
                name="Liberation Progress",
                icon_url="https://cdn.discordapp.com/emojis/1215036423090999376.webp?size=44&quality=lossless",
            )
        if thumbnail_url is not None:
            self.set_thumbnail(url=thumbnail_url)
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
        self.set_footer(text=f"Updated at {dt.strftime('%H:%M')}BST")


class MajorOrderEmbed(Embed):
    def __init__(self, assignment, planets):
        super().__init__(title="MAJOR ORDER UPDATE", colour=Colour.brand_red())
        reward_types = load(open("data/json/assignments/reward/type.json"))
        self.set_footer(text=f"MESSAGE #{assignment['id']}")
        self.add_field(assignment["description"], assignment["briefing"])
        for i in assignment["tasks"]:
            if i["type"] == 11:
                planet = planets[i["values"][2]]
                planet_health_bar = health_bar(
                    planet["health"], planet["maxHealth"], "Humans"
                )
                self.add_field(
                    planet["name"],
                    f"Heroes: **{planet['statistics']['playerCount']:,}\n{planet_health_bar}**",
                    inline=False,
                )
        self.add_field(
            "Reward",
            f"{self.assignment['reward']['amount']} {reward_types[str(self.assignment['reward']['type'])]} <:medal:1226254158278037504>",
            inline=False,
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
        self.description = content


class CampaignEmbed(Embed):
    def __init__(self):
        super().__init__(
            title=f"{emojis_dict['Left Banner']} Critical War Updates! {emojis_dict['Right Banner']}",
            colour=Colour.brand_red(),
        )
        self.add_field("Victories", "", inline=False)
        self.add_field("New Battles", "", inline=False)
        self.add_field("Planets Lost", "", inline=False)
        self.faction_dict = {
            "Automaton": "<:automaton:1215036421551685672>",
            "Terminids": "<:terminid:1215036423090999376>",
            "Illuminate": "<:illuminate:1218283483240206576>",
        }

    def add_new_campaign(self, campaign, time_remaining):
        name = self.fields[1].name
        description = self.fields[1].value
        if time_remaining:
            description += f"🛡️ Defend **{campaign['planet']['name']}**. Ends {time_remaining} {self.faction_dict[campaign['planet']['event']['faction']]}\n"
        else:
            description += f"⚔️ Liberate {campaign['planet']['name']} {self.faction_dict[campaign['planet']['currentOwner']]}\n"
        self.set_field_at(1, name, description, inline=self.fields[1].inline)

    def add_campaign_victory(self, planet, liberatee):
        name = self.fields[0].name
        description = self.fields[0].value
        description += f"**{planet['name']}** has been liberated from the {liberatee} {self.faction_dict[liberatee]}!\n"
        self.set_field_at(0, name, description, inline=self.fields[0].inline)

    def add_def_victory(self, planet):
        name = self.fields[0].name
        description = self.fields[0].value
        description += f"**🛡️ {planet['name']}** has been successfully defended!\n"
        self.set_field_at(0, name, description, inline=self.fields[0].inline)

    def add_planet_lost(self, planet):
        name = self.fields[2].name
        description = self.fields[2].value
        description += f"**💀 {planet['name']}** has been lost to the {planet['currentOwner']} {self.faction_dict[planet['currentOwner']]}.\n"
        self.set_field_at(2, name, description, inline=self.fields[2].inline)

    def remove_empty(self):
        for field in self.fields:
            if field.value == "":
                self.remove_field(self.fields.index(field))


class Dashboard:
    def __init__(self, data):
        # organise data
        self.now = datetime.now()
        self.campaigns = data["campaigns"]
        self.assignment = data["assignments"]
        self.planet_events = data["planet_events"]
        self.planets = data["planets"]
        self.war = data["war_state"]
        self.faction_dict = {
            "Automaton": "<:automaton:1215036421551685672>",
            "Terminids": "<:terminid:1215036423090999376>",
            "Illuminate": "<:illuminate:1218283483240206576>",
        }

        # make embeds
        self.defend_embed = Embed(title="Defending", colour=Colour.blue())
        self.automaton_embed = Embed(title="Attacking Automatons", colour=Colour.red())
        self.terminids_embed = Embed(title="Attacking Terminids", colour=Colour.red())
        self.major_orders_embed = Embed(title="Major Order", colour=Colour.yellow())

        # Major Orders
        if self.assignment not in (None, []):
            reward_types = load(open("data/json/assignments/reward/type.json"))
            self.major_orders_embed.set_thumbnail(
                "https://helldivers.io/img/majororder.png"
            )
            self.assignment = self.assignment[0]
            self.major_orders_embed.add_field(
                f"MESSAGE #{self.assignment['id']} - {self.assignment['description']}",
                f"{self.assignment['briefing']}\n\u200b\n",
                inline=False,
            )
            for i in self.assignment["tasks"]:
                if i["type"] == 11 or i["type"] == 13:

                    planet = self.planets[i["values"][2]]
                    completed = (
                        "LIBERATED" if planet["currentOwner"] == "Humans" else ""
                    )
                    planet_health_bar = health_bar(
                        planet["health"],
                        planet["maxHealth"],
                        ("MO" if planet["currentOwner"] != "Humans" else "Humans"),
                    )
                    self.major_orders_embed.add_field(
                        planet["name"],
                        (
                            f"Heroes: **{planet['statistics']['playerCount']:,}\n"
                            f"Occupied by: **{planet['currentOwner']}**\n"
                            f"{planet_health_bar}** {completed}\n"
                            f"`{(planet['health'] / planet['maxHealth']):^25,.2%}`\n"
                        ),
                        inline=False,
                    )
                elif i["type"] == 12:
                    event_health_bar = health_bar(
                        self.assignment["progress"][0], i["values"][0], "MO"
                    )
                    self.major_orders_embed.add_field(
                        f"Succeed in the defence of at least {i['values'][0]} planets",
                        (
                            f"Current progress: {self.assignment['progress'][0]}/{i['values'][0]}\n"
                            f"{event_health_bar}\n"
                            f"`{(self.assignment['progress'][0] / i['values'][0]):^25,.2%}`\n"
                        ),
                        inline=False,
                    )
                elif i["type"] == 3:
                    faction_dict = {
                        0: "Humans",
                        1: "Automaton <:automaton:1215036421551685672>",
                        2: "Terminids <:terminid:1215036423090999376>",
                        3: "Illuminate <:illuminate:1218283483240206576>",
                    }
                    event_health_bar = health_bar(
                        self.assignment["progress"][0], i["values"][2], "MO"
                    )
                    self.major_orders_embed.add_field(
                        f"Kill {short_format(i['values'][2])} {faction_dict[i['values'][0]]}",
                        (
                            f"Current progress: {short_format(self.assignment['progress'][0])}/{short_format(i['values'][2])}\n"
                            f"{event_health_bar}\n"
                            f"`{(self.assignment['progress'][0] / i['values'][2]):^25,.2%}`\n"
                        ),
                        inline=False,
                    )
                else:
                    self.major_orders_embed.add_field(
                        "New Major Order format provided", "Calibrating output..."
                    )

            self.major_orders_embed.add_field(
                "Reward",
                f"{self.assignment['reward']['amount']} {reward_types[str(self.assignment['reward']['type'])]} <:medal:1226254158278037504>",
                inline=False,
            )
            self.major_orders_embed.add_field(
                "Ends",
                f"<t:{int(datetime.fromisoformat(self.assignment['expiration']).timestamp())}:R>",
            )
        if len(self.major_orders_embed.fields) < 1:
            self.major_orders_embed.add_field(
                "Stand by for further orders from Super Earth High Command", "\u200b"
            )

        # Defending
        if self.planet_events != None:
            self.defend_embed.set_thumbnail("https://helldivers.io/img/defense.png")
            try:
                war_now = datetime.fromisoformat(self.war["now"]).timestamp()
            except Exception as e:
                print("war_now", e)
                war_now = None
            current_time = datetime.now().timestamp()
            for i in self.planet_events:
                faction_icon = self.faction_dict[i["event"]["faction"]]
                try:
                    end_time = datetime.fromisoformat(i["event"]["endTime"]).timestamp()
                except Exception as e:
                    print("end_time", e)
                    end_time = None
                if war_now != None and current_time != None and end_time != None:
                    time_remaining = (
                        f"<t:{((current_time - war_now) + end_time):.0f}:R>"
                    )
                else:
                    time_remaining = "Unavailable"
                event_health_bar = health_bar(
                    i["event"]["health"], i["event"]["maxHealth"], "Humans"
                )
                self.defend_embed.add_field(
                    f"{faction_icon} - __**{i['name']}**__",
                    (
                        f"Ends: {time_remaining}\n"
                        f"Heroes: **{i['statistics']['playerCount']:,}**\n"
                        f"Event health:\n"
                        f"{event_health_bar}\n"
                        f"`{(i['event']['health'] / i['event']['maxHealth']):^25,.2%}`\n"
                        "\u200b\n"
                    ),
                    inline=False,
                )

        if len(self.defend_embed.fields) < 1:
            self.defend_embed.add_field(
                "There are currently no threats to our Freedom", "||for now...||"
            )

        # Attacking
        self.terminids_embed.set_thumbnail("https://helldivers.io/img/attack.png")
        self.automaton_embed.set_thumbnail("https://helldivers.io/img/attack.png")
        if self.campaigns != None:
            for i in self.campaigns:
                if i["planet"]["event"] != None:
                    continue
                faction_icon = self.faction_dict[i["planet"]["currentOwner"]]
                planet_health_bar = health_bar(
                    i["planet"]["health"],
                    i["planet"]["maxHealth"],
                    i["planet"]["currentOwner"],
                )
                if i["planet"]["currentOwner"] == "Automaton":
                    if i["planet"]["sector"] == "L_estrade":  # remove when API updated
                        i["planet"]["sector"] = "Le'strade"
                    self.automaton_embed.add_field(
                        f"{faction_icon} - __**{i['planet']['name']}**__ - Battle **#{i['count']}**",
                        (
                            f"Sector: **{i['planet']['sector']}**\n"
                            f"Heroes: **{i['planet']['statistics']['playerCount']:,}**\n"
                            f"Planet health:\n"
                            f"{planet_health_bar}\n"
                            f"`{(i['planet']['health'] / i['planet']['maxHealth']):^25,.2%}`\n"
                            "\u200b\n"
                        ),
                        inline=False,
                    )
                else:
                    if i["planet"]["sector"] == "L_estrade":  # remove when API updated
                        i["planet"]["sector"] = "Le'strade"
                    self.terminids_embed.add_field(
                        f"{faction_icon} - __**{i['planet']['name']}**__ - Battle **#{i['count']}**",
                        (
                            f"Sector: **{i['planet']['sector']}**\n"
                            f"Heroes: **{i['planet']['statistics']['playerCount']:,}**\n"
                            f"Planet Health:\n"
                            f"{planet_health_bar}\n"
                            f"`{(i['planet']['health'] / i['planet']['maxHealth']):^25,.2%}`\n"
                            "\u200b\n"
                        ),
                        inline=False,
                    )

        # Other
        self.timestamp = int(self.now.timestamp())
        self.terminids_embed.add_field(
            "\u200b",
            f"Updated on <t:{self.timestamp}:f> - <t:{self.timestamp}:R>",
            inline=False,
        )
        if self.now.strftime("%d/%m") == "26/10":
            self.major_orders_embed.set_footer("The GWW wishes you a happy Liberty Day")
        if self.now.strftime("%d/%m") == "03/04":
            self.major_orders_embed.set_footer(
                "The GWW wishes you a happy Malevelon Creek Memorial Day"
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
                self, primary: dict, types: dict, fire_modes: dict, traits: dict
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
                if types[str(primary["type"])] == "Energy-based":
                    primary["capacity"] = (
                        f"{primary['capacity']} seconds of constant fire"
                    )
                    primary["fire_rate"] = 60
                if primary["capacity"] == 999:
                    primary["capacity"] = "♾️"
                self.add_field(
                    "Information",
                    (
                        f"Type: **{types[str(primary['type'])]}**\n"
                        f"Damage: **{primary['damage']}**\n"
                        f"Fire Rate: **{primary['fire_rate']}rpm**\n"
                        f"DPS: **{(primary['damage']*primary['fire_rate'])/60:.2f}/s**\n"
                        f"Capacity: **{primary['capacity']}** {emojis_dict['Capacity'] if primary['fire_rate'] != 0 else ''}\n"
                        f"Fire Modes:**{gun_fire_modes}**"
                        f"Features:**{features}**"
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
            def __init__(self, secondary: dict, fire_modes: dict, traits: dict):
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
                    features += f"\n- {traits[str(i)]} {emojis_dict[traits[str(i)]]}"
                if secondary["fire_rate"] == 0:
                    secondary["capacity"] = (
                        f"{secondary['capacity']} seconds of constant fire"
                    )
                self.add_field(
                    "Information",
                    (
                        f"Damage: **{secondary['damage']}**\n"
                        f"Fire Rate: **{secondary['fire_rate']}rpm**\n"
                        f"DPS: **{(secondary['damage']*secondary['fire_rate'])/60:.2f}/s**\n"
                        f"Capacity: **{secondary['capacity']}** {emojis_dict['Capacity'] if secondary['fire_rate'] != 0 else ''}\n"
                        f"Fire Modes:**{gun_fire_modes}**"
                        f"Features:**{features}**"
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
            def __init__(self, grenade: dict):
                super().__init__(
                    colour=Colour.blue(),
                    title=grenade["name"],
                    description=grenade["description"],
                )
                self.add_field(
                    "Information",
                    (
                        f"Damage: **{grenade['damage']}**\n"
                        f"Fuse Time: **{grenade['fuse_time']} seconds**\n"
                        f"Penetration: **{grenade['penetration']}**\n"
                        f"Radius: **{grenade['outer_radius']}**"
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
            item_number = 1
            for item in warbond_page["items"]:
                self.add_field(
                    f"{item_names[str(item['item_id'])]['name']}",
                    f"Medal cost: **{item['medal_cost']} <:medal:1226254158278037504>**",
                )
                if item_number % 2 == 0:
                    self.add_field("", "")
                item_number += 1


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
            except:
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


class ReactRoleDashboard(Embed):
    def __init__(self):
        super().__init__(title="Roles", colour=Colour.dark_theme())
        self.add_field(
            "Select the buttons below to be given specific roles.",
            "These buttons only give roles in this server.",
        )
