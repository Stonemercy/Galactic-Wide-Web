from datetime import datetime, timedelta
from data.lists import (
    faction_colours,
    help_dict,
    warbond_images_dict,
    emotes_list,
    player_cards_list,
    victory_poses_list,
    titles_list,
    stratagem_permit_list,
    stratagem_id_dict,
    stratagem_image_dict,
)
from disnake import APISlashCommand, Colour, Embed, File, ModalInteraction, OptionType
from utils.data import DSS, GlobalResources, PersonalOrder, Planet, Steam, Superstore
from utils.db import GWWGuild
from utils.emojis import Emojis
from utils.functions import health_bar, short_format
from utils.mixins import EmbedReprMixin


class PlanetCommandEmbed(Embed, EmbedReprMixin):
    def __init__(self, planet_names: dict, planet: Planet, language_json: dict):
        super().__init__(colour=Colour.from_rgb(*faction_colours[planet.current_owner]))
        self.add_planet_info(planet_names, planet, language_json)
        self.add_mission_stats(planet, language_json)
        self.add_hero_stats(planet, language_json)
        self.add_field("", "", inline=False)
        self.add_misc_stats(planet, language_json)

    def add_planet_info(self, planet_names: dict, planet: Planet, language_json: dict):
        sector = language_json["PlanetEmbed"]["sector"].format(sector=planet.sector)
        owner = language_json["PlanetEmbed"]["owner"].format(
            faction=language_json["factions"][planet.current_owner],
            faction_emoji=Emojis.factions[planet.current_owner],
        )
        biome = language_json["PlanetEmbed"]["biome"].format(
            biome_name=planet.biome["name"],
            biome_description=planet.biome["description"],
        )
        environmentals = language_json["PlanetEmbed"]["environmentals"].format(
            environmentals="".join(
                [
                    f"\n- **{hazard['name']}**\n  - -# {hazard['description']}"
                    for hazard in planet.hazards
                ]
            )
        )
        title_exclamation = ""
        if planet.dss:
            title_exclamation += Emojis.dss["dss"]
        if planet.in_assignment:
            title_exclamation += Emojis.icons["MO"]
        planet_health_bar = health_bar(
            (planet.event.progress if planet.event else planet.health_perc),
            (planet.event.faction if planet.event else planet.current_owner),
            True if planet.event else False,
        )
        if planet.event:
            planet_health_bar += f" 🛡️ {Emojis.factions[planet.event.faction]}"
        if planet.current_owner == "Humans":
            health_text = (
                f"{1 - planet.event.progress:^25,.2%}"
                if planet.event
                else f"{(planet.health_perc):^25,.2%}"
            )
        else:
            health_text = f"{1 - (planet.health_perc):^25,.2%}"
        self.add_field(
            f"__**{planet_names['names'][language_json['code_long']]}**__ {title_exclamation}",
            (
                f"{sector}"
                f"{owner}"
                f"{biome}"
                f"{environmentals}"
                f"{language_json['PlanetEmbed']['liberation_progress']}\n"
                f"{planet_health_bar}\n"
                f"`{health_text}`\n"
                "\u200b\n"
            ),
            inline=False,
        )

    def add_mission_stats(self, planet: Planet, language_json: dict):
        self.add_field(
            language_json["PlanetEmbed"]["mission_stats"],
            (
                f"{language_json['PlanetEmbed']['missions_won']}: **`{short_format(planet.stats['missionsWon'])}`**\n"
                f"{language_json['PlanetEmbed']['missions_lost']}: **`{short_format(planet.stats['missionsLost'])}`**\n"
                f"{language_json['PlanetEmbed']['missions_winrate']}: **`{planet.stats['missionSuccessRate']}%`**\n"
                f"{language_json['PlanetEmbed']['missions_time_spent']}: **`{planet.stats['missionTime']/31556952:.1f} years`**"
            ),
        )

    def add_hero_stats(self, planet: Planet, language_json: dict):
        self.add_field(
            language_json["PlanetEmbed"]["hero_stats"],
            (
                f"{language_json['PlanetEmbed']['active_heroes']}: **`{planet.stats['playerCount']:,}`**\n"
                f"{language_json['PlanetEmbed']['heroes_lost']}: **`{short_format(planet.stats['deaths'])}`**\n"
                f"{language_json['PlanetEmbed']['accidentals']}: **`{short_format(planet.stats['friendlies'])}`**\n"
                f"{language_json['PlanetEmbed']['shots_fired']}: **`{short_format(planet.stats['bulletsFired'])}`**\n"
                f"{language_json['PlanetEmbed']['shots_hit']}: **`{short_format(planet.stats['bulletsHit'])}`**\n"
                f"{language_json['PlanetEmbed']['accuracy']}: **`{planet.stats['accuracy']}%`**\n"
            ),
        )

    def add_misc_stats(self, planet: Planet, language_json: dict):
        faction = planet.current_owner if not planet.event else planet.event.faction
        if faction != "Humans":
            faction_kills = {
                "Automaton": "automatonKills",
                "Terminids": "terminidKills",
                "Illuminate": "illuminateKills",
            }[(faction)]
            self.add_field(
                f"💀 {language_json['factions'][faction]} {language_json['PlanetEmbed']['killed']}:",
                f"**{short_format(planet.stats[faction_kills])}**",
                inline=False,
            ).set_author(
                name=language_json["PlanetEmbed"]["liberation_progress"],
                icon_url={
                    "Automaton": "https://cdn.discordapp.com/emojis/1215036421551685672.webp?size=44&quality=lossless",
                    "Terminids": "https://cdn.discordapp.com/emojis/1215036423090999376.webp?size=44&quality=lossless",
                    "Illuminate": "https://cdn.discordapp.com/emojis/1317057914145603635.webp?size=44&quality=lossless",
                }.get(
                    faction,
                    None,
                ),
            )
        if planet.feature:
            self.add_field("Feature", planet.feature)
        if planet.thumbnail:
            self.set_thumbnail(url=planet.thumbnail)
        elif planet.index == 64:
            self.set_thumbnail(
                url="https://cdn.discordapp.com/emojis/1331357764039086212.webp?size=96"
            )
        try:
            self.set_image(
                file=File(
                    f"resources/biomes/{planet.biome['name'].lower().replace(' ', '_')}.png"
                )
            )
            self.image_set = True
        except:
            self.image_set = False


class HelpCommandEmbed(Embed, EmbedReprMixin):
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


class WeaponCommandEmbeds:
    class Primary(Embed, EmbedReprMixin):
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
                gun_fire_modes += f"\n- **{json_dict['items']['fire_modes'][str(i)]}**"

            features = ""
            for i in weapon_json["traits"]:
                if i != 0:
                    features += f"\n- **{json_dict['items']['weapon_traits'][str(i)]}**"
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

    class Secondary(Embed, EmbedReprMixin):
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
                gun_fire_modes += f"\n- **{json_dict['items']['fire_modes'][str(i)]}**"

            features = ""
            for i in weapon_json["traits"]:
                if i != 0:
                    features += f"\n- **{json_dict['items']['weapon_traits'][str(i)]}**"
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

    class Grenade(Embed, EmbedReprMixin):
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


class BoosterCommandEmbed(Embed, EmbedReprMixin):
    def __init__(self, booster: dict):
        super().__init__(
            colour=Colour.blue(),
            title=booster["name"],
            description=booster["description"],
        )
        try:
            self.set_thumbnail(
                file=File(f"resources/boosters/{booster['name'].replace(' ', '_')}.png")
            )
            self.image_set = True
        except:
            self.image_set = False


class WarbondCommandEmbed(Embed, EmbedReprMixin):
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
            for item_key, item_value in json_dict["items"]["primary_weapons"].items():
                if item_type != None:
                    break
                if int(item_key) == item["item_id"]:
                    item_json = item_value
                    item_type = "primary"
                    break
            for item_key, item_value in json_dict["items"]["secondary_weapons"].items():
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
                        f"{item_json['name']}",
                        (
                            "Type: **Primary**\n"
                            f"Weapon type: **{json_dict['items']['weapon_types'][str(item_json['type'])]}**\n"
                            f"Damage: **{item_json['damage']}**\n"
                            f"Capacity: **{item_json['capacity']}**\n"
                            f"Recoil: **{item_json['recoil']}**\n"
                            f"Fire Rate: **{item_json['fire_rate']}**\n"
                            f"Medal Cost: **{item['medal_cost']} {Emojis.items['Medal']}**\n\n"
                        ),
                    )
                elif item_type == "secondary":
                    self.add_field(
                        f"{item_json['name']}",
                        (
                            "Type: **Secondary**\n"
                            f"Damage: **{item_json['damage']}**\n"
                            f"Capacity: **{item_json['capacity']}**\n"
                            f"Recoil: **{item_json['recoil']}**\n"
                            f"Fire Rate: **{item_json['fire_rate']}**\n"
                            f"Medal Cost: **{item['medal_cost']} {Emojis.items['Medal']}**\n\n"
                        ),
                    )
                elif item_type == "grenade":
                    self.add_field(
                        f"{item_json['name']}",
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


class StratagemCommandEmbed(Embed, EmbedReprMixin):
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


class FactionCommandEmbed(Embed, EmbedReprMixin):
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
        start_emoji = Emojis.difficulty[species_info["info"]["start"]]
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


class SetupCommandEmbed(Embed, EmbedReprMixin):
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
            "pt-br": ":flag_br:",
            "ru": ":flag_ru:",
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


class FeedbackCommandEmbed(Embed, EmbedReprMixin):
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


class SuperstoreCommandEmbed(Embed, EmbedReprMixin):
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


class DSSCommandEmbed(Embed, EmbedReprMixin):
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
            ta_health_bar = health_bar(
                tactical_action.cost.progress,
                "MO" if tactical_action.cost.progress != 1 else "Humans",
            )
            status = {1: "preparing", 2: "active", 3: "on_cooldown"}[
                tactical_action.status
            ]
            if status == "preparing":
                submittable_formatted = language_json["dashboard"]["DSSEmbed"][
                    "max_submitable"
                ].format(
                    emoji=Emojis.items[tactical_action.cost.item],
                    number=f"{tactical_action.cost.max_per_seconds[0]:,}",
                    item=tactical_action.cost.item,
                    hours=f"{tactical_action.cost.max_per_seconds[1]/3600:.0f}",
                )
                cost = (
                    f"{submittable_formatted}\n"
                    f"{ta_health_bar}\n"
                    f"`{tactical_action.cost.progress:^25.2%}`"
                )
            elif status == "active":
                cost = f"{language_json['ends']} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
            elif status == "on_cooldown":
                cost = f"{language_json['dashboard']['DSSEmbed']['off_cooldown'].capitalize()} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
            ta_long_description = tactical_action.strategic_description.replace(
                ". ", ".\n-# "
            )
            self.add_field(
                f"{Emojis.dss[tactical_action.name.lower().replace(' ', '_')]} {tactical_action.name.title()}",
                (
                    f"{language_json['dashboard']['DSSEmbed']['status']}: **{language_json['dashboard']['DSSEmbed'][status].capitalize()}**\n"
                    f"-# {ta_long_description}\n"
                    f"{cost}\n\u200b\n"
                ),
                inline=False,
            )


class PersonalOrderCommandEmbed(Embed, EmbedReprMixin):
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


class MeridiaCommandEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        language_json: dict,
        planet_names_json: dict,
        dark_energy_resource: GlobalResources.DarkEnergy,
        total_de_available: int,
        active_invasions: int,
        dark_energy_changes: dict[str:int, str:list],
        time_to_reach_planets: dict[str:float],
    ):
        super().__init__(title="Meridia", colour=Colour.from_rgb(106, 76, 180))
        rate_per_hour = sum(dark_energy_changes["changes"]) * 12
        rate = f"{rate_per_hour:+.2%}/hr"
        completion_timestamp = ""
        now_seconds = int(datetime.now().timestamp())
        if rate_per_hour > 0:
            seconds_until_complete = int(
                ((1 - dark_energy_changes["total"]) / rate_per_hour) * 3600
            )
            complete_seconds = now_seconds + seconds_until_complete
            completion_timestamp = language_json["MeridiaEmbed"]["reaches"].format(
                number=100, timestamp=complete_seconds
            )
        elif rate_per_hour < 0:
            seconds_until_zero = int(
                (dark_energy_changes["total"] / abs(rate_per_hour)) * 3600
            )
            complete_seconds = now_seconds + seconds_until_zero
            completion_timestamp = language_json["MeridiaEmbed"]["reaches"].format(
                number=0, timestamp=complete_seconds
            )
        self.add_field(
            "",
            f"{dark_energy_resource.health_bar}\n**`{dark_energy_resource.perc:^25.3%}`**\n**`{rate:^25}`**",
            inline=False,
        )
        warning = ""
        if (
            (total_de_available / dark_energy_resource.max_value)
            + dark_energy_resource.perc
        ) > 1:
            warning = ":warning:"
        active_invasions_fmt = language_json["MeridiaEmbed"]["active_invasions"].format(
            number=active_invasions
        )
        total_to_be_harvested = language_json["MeridiaEmbed"][
            "total_to_be_harvested"
        ].format(
            warning=warning,
            number=f"{(total_de_available / dark_energy_resource.max_value):.2%}",
            total_available=f"{(total_de_available / dark_energy_resource.max_value)+dark_energy_resource.perc:.2%}",
        )
        self.add_field(
            "",
            (
                f"{completion_timestamp}\n"
                f"{active_invasions_fmt}\n"
                f"{total_to_be_harvested}"
            ),
        )
        self.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/1331357764039086212.webp?size=96"
        )
        if time_to_reach_planets:
            self.add_field(
                language_json["MeridiaEmbed"]["planets_in_path"],
                "\n".join(
                    [
                        f"{planet_names_json[str(planet)]['names'][language_json['code_long']]} <t:{int(seconds)}:R>"
                        for planet, seconds in time_to_reach_planets.items()
                    ]
                ),
                inline=False,
            )


class SteamCommandEmbed(Embed, EmbedReprMixin):
    def __init__(self, steam: Steam, language_json: dict):
        super().__init__(title=steam.title, colour=Colour.dark_grey(), url=steam.url)
        self.set_footer(text=language_json["message"].format(message_id=steam.id))
        if len(steam.content) > 4000:
            steam.content = steam.content[:3900] + language_json["SteamEmbed"][
                "head_here"
            ].format(url=steam.url)
        self.description = steam.content
