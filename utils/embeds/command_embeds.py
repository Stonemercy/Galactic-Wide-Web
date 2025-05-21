from datetime import datetime, timedelta
from math import sqrt
from data.lists import (
    SpecialUnits,
    faction_colours,
    stratagem_id_dict,
    stratagem_image_dict,
)
from disnake import APISlashCommand, Colour, Embed, File, Guild, OptionType
from utils.data import DarkEnergy, PersonalOrder, Planet, Planets, SiegeFleet, Steam
from utils.db import GWWGuild
from utils.emojis import Emojis
from utils.functions import health_bar, short_format
from utils.mixins import EmbedReprMixin
from utils.trackers import BaseTracker, BaseTrackerEntry
from disnake.ext.commands.slash_core import InvokableSlashCommand


class PlanetCommandEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        planet_name: str,
        planet: Planet,
        language_json: dict,
        planet_effects_json: dict,
        liberation_changes: BaseTracker,
        total_players: int,
    ):
        super().__init__(colour=Colour.from_rgb(*faction_colours[planet.current_owner]))
        self.add_planet_info(
            planet_name=planet_name,
            planet=planet,
            language_json=language_json,
            planet_effects_json=planet_effects_json,
            liberation_changes=liberation_changes,
            total_players=total_players,
        )
        self.add_mission_stats(planet=planet, language_json=language_json)
        self.add_hero_stats(planet=planet, language_json=language_json)
        self.add_field(name="", value="", inline=False)
        self.add_misc_stats(planet=planet, language_json=language_json)

    def add_planet_info(
        self,
        planet_name: str,
        planet: Planet,
        language_json: dict,
        planet_effects_json: list,
        liberation_changes: BaseTracker,
        total_players: int,
    ):
        sector = language_json["PlanetEmbed"]["sector"].format(sector=planet.sector)
        owner = language_json["PlanetEmbed"]["owner"].format(
            faction=language_json["factions"][planet.current_owner],
            faction_emoji=getattr(Emojis.Factions, planet.current_owner.lower()),
        )
        biome = language_json["PlanetEmbed"]["biome"].format(
            biome_name=planet.biome["name"],
            biome_description=planet.biome["description"],
        )
        environmentals = language_json["PlanetEmbed"]["environmentals"].format(
            environmentals="".join(
                [
                    f"\n- {getattr(Emojis.Weather, hazard['name'].replace(' ', '_').lower(), '')} **{hazard['name']}**\n  - -# {hazard['description']}"
                    for hazard in planet.hazards
                ]
            )
        )
        title_exclamation = ""
        if planet.dss_in_orbit:
            title_exclamation += Emojis.DSS.icon
            title_exclamation += Emojis.DSS.operational_support
        if planet.in_assignment:
            title_exclamation += Emojis.Icons.mo
        self.add_field(
            f"__**{planet_name}**__ {title_exclamation}",
            (f"{sector}" f"{owner}" f"{biome}" f"{environmentals}"),
            inline=False,
        )

        outlook_text = ""
        required_players = ""
        liberation_text = ""
        if liberation_changes.has_data:
            liberation_change = liberation_changes.get_entry(key=planet.index)
            if liberation_change:
                now = datetime.now()
                now_seconds = int(now.timestamp())
                if liberation_change.change_rate_per_hour != 0:
                    seconds_until_complete = int(
                        (
                            (100 - liberation_change.value)
                            / liberation_change.change_rate_per_hour
                        )
                        * 3600
                    )
        else:
            liberation_change = None
        if planet.event:
            planet_health_bar = (
                health_bar(planet.event.progress, planet.event.faction, True)
                + f" 🛡️ {getattr(Emojis.Factions, planet.event.faction.lower())}"
            )
            if liberation_change and liberation_change.change_rate_per_hour != 0:
                winning = (
                    datetime.fromtimestamp(now_seconds + seconds_until_complete)
                    < planet.event.end_time_datetime
                )
                if winning:
                    outlook_text = f"{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + seconds_until_complete}:R>\n"
                else:
                    outlook_text = f"{language_json['dashboard']['outlook'].format(outlook=language_json['defeat'])}\n"
                change = f"{liberation_change.change_rate_per_hour:+.2f}%/hour"
                liberation_text = f"\n`{change:^25}`"
                if planet.event.required_players:
                    if 0 < planet.event.required_players < 2.5 * total_players:
                        required_players = f"{language_json['dashboard']['DefenceEmbed']['players_required']}: **~{planet.event.required_players:,.0f}+**"
                    else:
                        if planet.event.start_time_datetime > now - timedelta(hours=1):
                            required_players = f"{language_json['dashboard']['DefenceEmbed']['players_required']}: *Gathering Data*"
                        else:
                            required_players = f"{language_json['dashboard']['DefenceEmbed']['players_required']}: **IMPOSSIBLE**"
            health_text = f"{1 - planet.event.progress:^25,.2%}"
            self.add_field(
                "",
                (
                    f"{outlook_text}"
                    f"Heroes: **{planet.stats['playerCount']:,}**\n"
                    f"{required_players}"
                    f"\n{language_json['PlanetEmbed']['liberation_progress']}"
                    f"\n{planet_health_bar}"
                    f"\n`{health_text}`"
                    f"{liberation_text}"
                    "\u200b\n"
                ),
                inline=False,
            )
        else:
            health_text = (
                f"{1 - (planet.health_perc):^25,.2%}"
                if planet.current_owner != "Humans"
                else f"{(planet.health_perc):^25,.2%}"
            )
            planet_health_bar = health_bar(
                planet.health_perc,
                planet.current_owner,
                True if planet.current_owner != "Humans" else False,
            )
            if liberation_change and liberation_change.change_rate_per_hour > 0:
                change = f"{liberation_change.change_rate_per_hour:+.2f}%/hour"
                liberation_text = f"\n`{change:^25}`"
                outlook_text = f"{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{now_seconds + seconds_until_complete}:R>\n"
            self.add_field(
                "",
                (
                    f"{outlook_text}"
                    f"Heroes: **{planet.stats['playerCount']:,}**"
                    f"\n{language_json['PlanetEmbed']['liberation_progress']}"
                    f"\n{planet_health_bar}"
                    f"\n`{health_text}`"
                    f"{liberation_text}"
                    "\u200b\n"
                ),
                inline=False,
            )
        if planet.dss_in_orbit:
            self.add_field(
                f"{Emojis.DSS.operational_support} Operational Support",
                f"The presence of the {Emojis.DSS.icon} DSS near this planet provides a slight boost to **Liberation Campaign** progress.",
                inline=False,
            )
        effects = ""
        special_units = []
        for ae in planet.active_effects:
            if special_unit := SpecialUnits.get_from_effects_list([ae]):
                special_unit = list(special_unit)[0]
                if special_unit not in special_units:
                    special_units.append(special_unit)
                    effects += f"\n- **{special_unit[0]}** {special_unit[1]}"
            else:
                try:
                    effect = planet_effects_json[str(ae)]
                    effects += (
                        f"\n- **{effect['name']}**\n  - -# {effect['description']}"
                    )
                except:
                    pass
        if effects:
            self.add_field("Planetary Effects", effects, inline=False)
        self.add_field(
            "Distance from Super Earth",
            f"**{sqrt(planet.position['x']**2 + planet.position['y']**2) * 1000:.2f}** SU",
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
    def __init__(
        self,
        commands: list[APISlashCommand] = None,
        command: InvokableSlashCommand = None,
    ):
        super().__init__(colour=Colour.green(), title="Help")
        if commands:
            for global_command in sorted(commands, key=lambda cmd: cmd.name):
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
        elif command:
            options = "" if command.options == [] else "**Options:**\n"
            for option in command.options:
                if option.type == OptionType.sub_command:
                    options += f"- /{command.name} {option.name}\n"
                    for sub_option in option.options:
                        options += f" - **`{sub_option.name}`** {'**[Required]**' if sub_option.required else '**<Optional>**'}- {sub_option.description}\n"
                else:
                    options += f"- **`{option.name}`** {'**[Required]**' if option.required else '**<Optional>**'} - {option.description}\n"
            self.add_field(
                f"/{command.name}",
                (
                    f"{command.extras['long_description']}\n\n"
                    f"{options}"
                    f"**Example usage:**\n- {command.extras['example_usage']}\n"
                ),
                inline=False,
            )


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
            "es": ":flag_es:",
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
                    full_objective = f"Successfully extract with {task.values[2]} {item}s {getattr(Emojis.Items, item.replace(' ', '_').lower())}"
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
                f"{reward.amount} {reward_name}s {getattr(Emojis.Items, reward_name.replace(' ', '_').lower())}",
                inline=False,
            )


class MeridiaCommandEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        language_json: dict,
        planet_names_json: dict,
        dark_energy_resource: DarkEnergy | None,
        total_de_available: int,
        active_invasions: int,
        dark_energy_changes: dict[str:int, str:list],
        time_to_reach_planets: dict[str:float],
    ):
        super().__init__(
            title="Meridia",
            colour=Colour.from_rgb(106, 76, 180),
            description="-# This is the path Meridia has taken\n-# ||the gaps were caused by AH||",
        )
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
        active_invasions_fmt = ""
        total_to_be_harvested = ""
        if dark_energy_resource:
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
            active_invasions_fmt = language_json["MeridiaEmbed"][
                "active_invasions"
            ].format(number=active_invasions)
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


class CommunityServersCommandEmbed(Embed, EmbedReprMixin):
    def __init__(self, guilds: list[Guild], language_json: dict, new_index: int):
        super().__init__(
            title="Community Servers",
            colour=Colour.blue(),
            description=f"The GWW is in **{len(guilds)}** community servers",
        )
        for index, guild in enumerate(
            guilds[new_index - 16 : new_index], start=max(1, new_index - 15)
        ):
            if self.character_count() < 6000 and len(self.fields) < 24:
                self.add_field(
                    name=f"{index}. {guild.name}",
                    value=f"Members: **{guild.member_count}**\nInvite: [Link](<https://discord.com/invite/{guild.vanity_url_code}>)",
                )
                if index % 2 == 0:
                    self.add_field("", "", inline=False)
            else:
                break
        self.set_footer(text=f"{max(0, new_index)}/{len(guilds)}")

    def character_count(self):
        total_characters = 0
        if self.title:
            total_characters += len(self.title.strip())
        if self.description:
            total_characters += len(self.description.strip())
        if self.footer:
            total_characters += len(self._footer.get("text", "").strip())
        if self.author:
            total_characters += len(self._author.get("name", "").strip())
        if self.fields:
            for field in self.fields:
                total_characters += len(field.name.strip())
                total_characters += len(field.value.strip())
        return total_characters


class WarfrontAllPlanetsEmbed(Embed, EmbedReprMixin):
    def __init__(self, planets: Planets, faction: str):
        planets_list = sorted(
            [p for p in planets.values() if p.current_owner == faction],
            key=lambda planet: planet.stats["playerCount"],
            reverse=True,
        )
        super().__init__(
            title=f"All planets for {faction}",
            colour=Colour.from_rgb(*faction_colours[faction]),
            description=f"There are **{len(planets_list)}** planets under {faction} control",
        )
        name = "Planets list"
        value = " - ".join([f"**{p.name}**" for p in planets_list])
        self.add_field(name=name, value=value)


class SiegeFleetCommandEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        siege_fleet: SiegeFleet,
        siege_changes: BaseTrackerEntry,
        language_json: dict,
    ):
        super().__init__(
            title=f"{siege_fleet.name}",
            description=f"-# {siege_fleet.description}",
            colour=Colour.from_rgb(*faction_colours[siege_fleet.faction]),
        )
        rate = f"{siege_changes.change_rate_per_hour:+.2%}/hr"
        completion_timestamp = None
        if siege_changes.change_rate_per_hour != 0:
            completion_timestamp = language_json["dashboard"]["DarkEnergyEmbed"][
                "reaches"
            ].format(
                number=100 if siege_changes.change_rate_per_hour > 0 else 0,
                timestamp=(
                    int(datetime.now().timestamp())
                    + siege_changes.seconds_until_complete
                ),
            )
        self.add_field(
            "",
            (
                f"{siege_fleet.health_bar}\n"
                f"**`{siege_fleet.perc:^25.3%}`**\n"
                f"**`{rate:^25}`**"
            ),
            inline=False,
        )
        if completion_timestamp:
            self.add_field(
                "",
                (f"-# {completion_timestamp}\n"),
            )
        self.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1212735927223590974/1372960719653568603/iluminat.png?ex=6828accf&is=68275b4f&hm=9069a2c2b0ab944699c5e5382aa2b58611b6eb9af22eef56433e63c9fa9c27c2&"
        )
