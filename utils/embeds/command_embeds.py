from datetime import datetime, timedelta
from inspect import getmembers
from math import sqrt
from data.lists import (
    SpecialUnits,
    faction_colours,
    stratagem_id_dict,
    stratagem_image_dict,
)
from disnake import APISlashCommand, Colour, Embed, File, Guild, OptionType
from utils.bot import GalacticWideWebBot
from utils.data import DarkEnergy, Planet, Planets, SiegeFleet, Steam
from utils.dbv2 import GWWGuild
from utils.emojis import Emojis
from utils.functions import health_bar, short_format
from utils.mixins import EmbedReprMixin
from utils.trackers import BaseTracker, BaseTrackerEntry
from disnake.ext.commands.slash_core import InvokableSlashCommand
from disnake.ext.tasks import Loop


class PlanetCommandEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        planet_name: str,
        planet: Planet,
        language_json: dict,
        planet_effects_json: dict,
        liberation_change: BaseTrackerEntry,
        total_players: int,
    ):
        super().__init__(colour=Colour.from_rgb(*faction_colours[planet.current_owner]))
        self.add_planet_info(
            planet_name=planet_name,
            planet=planet,
            language_json=language_json,
            planet_effects_json=planet_effects_json,
            liberation_change=liberation_change,
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
        liberation_change: BaseTrackerEntry | None,
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
        if planet.event:
            planet_health_bar = (
                health_bar(planet.event.progress, planet.event.faction, True)
                + f" 🛡️ {getattr(Emojis.Factions, planet.event.faction.lower())}"
            )
            if liberation_change and liberation_change.change_rate_per_hour != 0:
                estimated_end_timestamp = int(
                    datetime.now().timestamp()
                    + liberation_change.seconds_until_complete
                )
                winning = (
                    datetime.fromtimestamp(estimated_end_timestamp)
                    < planet.event.end_time_datetime
                )
                if winning:
                    outlook_text = f"{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{estimated_end_timestamp}:R>\n"
                else:
                    outlook_text = f"{language_json['dashboard']['outlook'].format(outlook=language_json['defeat'])}\n"
                change = f"{liberation_change.change_rate_per_hour:+.2%}/hour"
                liberation_text = f"\n`{change:^25}`"
                if planet.event.required_players:
                    if 0 < planet.event.required_players < 2.5 * total_players:
                        required_players = f"\n{language_json['dashboard']['DefenceEmbed']['players_required']}: **~{planet.event.required_players:,.0f}+**"
                    else:
                        if (
                            planet.event.start_time_datetime
                            > datetime.now() - timedelta(hours=1)
                        ):
                            required_players = f"\n{language_json['dashboard']['DefenceEmbed']['players_required']}: *Gathering Data*"
                        else:
                            required_players = f"\n{language_json['dashboard']['DefenceEmbed']['players_required']}: **IMPOSSIBLE**"
            health_text = f"{planet.event.progress:^25,.2%}"
            self.add_field(
                "",
                (
                    f"{outlook_text}"
                    f"Heroes: **{planet.stats['playerCount']:,}**"
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
                estimated_end_timestamp = int(
                    datetime.now().timestamp()
                    + liberation_change.seconds_until_complete
                )
                change = f"{liberation_change.change_rate_per_hour:+.2f}%/hour"
                liberation_text = f"\n`{change:^25}`"
                outlook_text = f"{language_json['dashboard']['outlook'].format(outlook=language_json['victory'])} <t:{estimated_end_timestamp}:R>\n"
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


class PlanetCommandRegionEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        planet: Planet,
        planet_changes: BaseTrackerEntry,
        region_changes: BaseTracker,
    ):
        super().__init__(colour=Colour.from_rgb(*faction_colours[planet.current_owner]))
        for region in planet.regions.values():
            region_emojis = getattr(Emojis.RegionIcons, region.owner)
            level_emoji = getattr(region_emojis, f"_{region.size}")
            description = f"{level_emoji} **{region.size}*** {region.type}"
            if region.description:
                description += f"\n-# {region.description}"
            if region.is_available:
                description += f"\n-# Heroes: **{region.players}** ({region.players / planet.stats['playerCount']:.2%})"
                health_to_get_from = (
                    planet.max_health if not planet.event else planet.event.max_health
                )
                description += f"\nBoost when liberated: **{(region.max_health * 1.5) / health_to_get_from:.2%}**"
                description += f"\n{region.health_bar}"
                description += f"\n`{region.perc:^25,.2%}`"
                region_change = region_changes.get_entry(region.settings_hash)
                if region_change:
                    change = f"{region_change.change_rate_per_hour:+.2%}/hour"
                    description += f"\n`{change:^25}`"
            elif region.owner != "Humans":
                stat_to_use = "liberation" if not planet.event else "defence duration"
                if region.availability_factor != 1 and (
                    1 - region.availability_factor
                ) > (planet.event.progress if planet.event else 1 - planet.health_perc):
                    description += f"\nUnlocks when **{stat_to_use}** reaches **{1 - region.availability_factor:.0%}**"
                if planet_changes.change_rate_per_hour > 0:
                    if planet.event:
                        seconds_until_we_win = planet_changes.seconds_until_complete
                        event_duration_in_seconds = (
                            planet.event.end_time_datetime.timestamp()
                            - planet.event.start_time_datetime.timestamp()
                        )
                        progress_in_seconds = (
                            datetime.now().timestamp()
                            - planet.event.start_time_datetime.timestamp()
                        )
                        current_progress = (
                            progress_in_seconds / event_duration_in_seconds
                        )
                        progress_needed = (
                            1 - region.availability_factor
                        ) - current_progress
                        time_to_unlock = seconds_until_we_win * progress_needed
                        description += f"\n-# <t:{int(datetime.now().timestamp() + time_to_unlock)}:R>"
                    else:
                        seconds_until_we_win = planet_changes.seconds_until_complete
                        current_progress = 1 - planet.health_perc
                        progress_needed = (
                            1 - region.availability_factor
                        ) - current_progress
                        time_to_unlock = seconds_until_we_win * progress_needed
                        description += f"\n-# <t:{int(datetime.now().timestamp() + time_to_unlock)}:R>"

            self.add_field(
                f"{getattr(Emojis.Factions, region.owner.lower() or planet.current_owner.lower())} {region.name}",
                description,
                inline=False,
            )
            self.set_image("https://i.imgur.com/cThNy4f.png")


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
        dashboard_text = language_json["SetupEmbed"]["dashboard_desc"]
        dashboard_feature = [f for f in guild.features if f.name == "dashboards"]
        if dashboard_feature:
            setup_emoji = ":white_check_mark:"
            dashboard = dashboard_feature[0]
            dashboard_text += (
                f"{language_json['SetupEmbed']['dashboard_channel']}: <#{dashboard.channel_id}>\n"
                f"{language_json['SetupEmbed']['dashboard_message']}: https://discord.com/channels/{guild.guild_id}/{dashboard.channel_id}/{dashboard.message_id}"
            )
        else:
            setup_emoji = ":x:"
            dashboard_text += f"**{language_json['SetupEmbed']['not_set']}**"
        self.add_field(
            f"{setup_emoji} {language_json['SetupEmbed']['dashboard']}",
            dashboard_text,
            inline=False,
        )

        # map
        map_text = language_json["SetupEmbed"]["map_desc"]
        map_feature = [f for f in guild.features if f.name == "maps"]
        if map_feature:
            setup_emoji = ":white_check_mark:"
            galaxy_map = map_feature[0]
            map_text += (
                f"{language_json['SetupEmbed']['map_channel']}: <#{galaxy_map.channel_id}>\n"
                f"{language_json['SetupEmbed']['map_message']}: https://discord.com/channels/{guild.guild_id}/{galaxy_map.channel_id}/{galaxy_map.message_id}"
            )
        else:
            setup_emoji = ":x:"
            map_text += f"**{language_json['SetupEmbed']['not_set']}**"
        self.add_field(
            f"{setup_emoji} {language_json['SetupEmbed']['map']}",
            map_text,
            inline=False,
        )

        # war announcements
        # war_announcements_text = f"{language_json['SetupEmbed']['announcements_desc']}" # TRANSLATE
        war_announcements_text = "-# General announcements regarding the war (e.g. New MO's, planets lost/won, general dispatches etc.)\n"
        war_announcements_feature = [
            f for f in guild.features if f.name == "war_announcements"
        ]
        if war_announcements_feature:
            setup_emoji = ":white_check_mark:"
            war_announcements = war_announcements_feature[0]
            # war_announcements_text += f"{language_json['SetupEmbed']['announcement_channel']}: <#{war_announcements.channel_id}>" # TRANSLATE
            war_announcements_text += (
                f"War Announcements Channel: <#{war_announcements.channel_id}>"
            )
        else:
            setup_emoji = ":x:"
            war_announcements_text += f"**{language_json['SetupEmbed']['not_set']}**"
        self.add_field(
            # language_json["SetupEmbed"]["announcements"], # TRANSLATE
            f"{setup_emoji} War Announcements",
            war_announcements_text,
            inline=False,
        )

        # dss announcements
        # dss_announcements_text = f"{language_json['SetupEmbed']['announcements_desc']}" # TRANSLATE
        dss_announcements_text = "-# Announcements regarding the DSS (e.g. DSS moves or the status of Tactical Actions changes)\n"
        dss_announcements_feature = [
            f for f in guild.features if f.name == "dss_announcements"
        ]
        if dss_announcements_feature:
            setup_emoji = ":white_check_mark:"
            dss_announcements = dss_announcements_feature[0]
            # dss_announcements_text += f"{language_json['SetupEmbed']['announcement_channel']}: <#{dss_announcements.channel_id}>" # TRANSLATE
            dss_announcements_text += (
                f"DSS Announcements Channel: <#{dss_announcements.channel_id}>"
            )
        else:
            setup_emoji = ":x:"
            dss_announcements_text += f"**{language_json['SetupEmbed']['not_set']}**"
        self.add_field(
            # language_json["SetupEmbed"]["announcements"], # TRANSLATE
            f"{setup_emoji} DSS Announcements",
            dss_announcements_text,
            inline=False,
        )

        # region announcements
        # region_announcements_text = f"{language_json['SetupEmbed']['announcements_desc']}" # TRANSLATE
        region_announcements_text = "-# Announcements regarding planetary regions (e.g. new regions have appeared or regions have been won etc.)\n"
        region_announcements_feature = [
            f for f in guild.features if f.name == "region_announcements"
        ]
        if region_announcements_feature:
            setup_emoji = ":white_check_mark:"
            region_announcements = region_announcements_feature[0]
            # region_announcements_text += f"{language_json['SetupEmbed']['announcement_channel']}: <#{dss_announcements.channel_id}>" # TRANSLATE
            region_announcements_text += (
                f"Region Announcements Channel: <#{region_announcements.channel_id}>"
            )
        else:
            setup_emoji = ":x:"
            region_announcements_text += f"**{language_json['SetupEmbed']['not_set']}**"
        self.add_field(
            # language_json["SetupEmbed"]["announcements"], # TRANSLATE
            f"{setup_emoji} Region Announcements",
            region_announcements_text,
            inline=False,
        )

        # patch notes
        patch_notes_text = language_json["SetupEmbed"]["patch_notes_desc"]
        patch_notes_feature = [f for f in guild.features if f.name == "patch_notes"]
        if patch_notes_feature:
            setup_emoji = ":white_check_mark:"
            patch_notes = patch_notes_feature[0]
            # patch_notes_text += f"{language_json['SetupEmbed']['announcement_channel']}: <#{dss_announcements.channel_id}>" # TRANSLATE
            patch_notes_text += f"Patch Notes Channel: <#{patch_notes.channel_id}>"
        else:
            setup_emoji = ":x:"
            patch_notes_text += f"**{language_json['SetupEmbed']['not_set']}**"
        self.add_field(
            f"{setup_emoji} {language_json['SetupEmbed']['patch_notes']}",
            patch_notes_text,
            inline=False,
        )

        # mo updates
        mo_updates_text = language_json["SetupEmbed"]["mo_updates_desc"]
        mo_updates_feature = [
            f for f in guild.features if f.name == "major_order_updates"
        ]
        if mo_updates_feature:
            setup_emoji = ":white_check_mark:"
            mo_updates = mo_updates_feature[0]
            # mo_updates_text += f"{language_json['SetupEmbed']['announcement_channel']}: <#{dss_announcements.channel_id}>" # TRANSLATE
            mo_updates_text += (
                f"Major Order Updates Channel: <#{mo_updates.channel_id}>"
            )
        else:
            setup_emoji = ":x:"
            mo_updates_text += f"**{language_json['SetupEmbed']['not_set']}**"
        self.add_field(
            f"{setup_emoji} {language_json['SetupEmbed']['mo_updates']}",
            mo_updates_text,
            inline=False,
        )

        # detailed dispatches
        ddispatches_text = language_json["SetupEmbed"]["detailed_dispatches_desc"]
        ddispatches_feature = [
            f for f in guild.features if f.name == "detailed_dispatches"
        ]
        if ddispatches_feature:
            setup_emoji = ":white_check_mark:"
            dd_dispatches = ddispatches_feature[0]
            # ddispatches_text += f"{language_json['SetupEmbed']['announcement_channel']}: <#{dss_announcements.channel_id}>" # TRANSLATE
            ddispatches_text += (
                f"Detailed Dispatches Channel: <#{dd_dispatches.channel_id}>"
            )
        else:
            setup_emoji = ":x:"
            ddispatches_text += f"**{language_json['SetupEmbed']['not_set']}**"
        self.add_field(
            f"{setup_emoji} {language_json['SetupEmbed']['detailed_dispatches']}",
            ddispatches_text,
            inline=False,
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


class MeridiaCommandEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        language_json: dict,
        planet_names_json: dict,
        dark_energy_resource: DarkEnergy | None,
        total_de_available: int,
        active_invasions: int,
        dark_energy_changes: BaseTrackerEntry | None,
        time_to_reach_planets: dict[str:float],
    ):
        super().__init__(
            title="Meridia",
            colour=Colour.from_rgb(106, 76, 180),
            description="-# This is the path Meridia has taken\n-# ||the gaps were caused by AH||",
        )
        completion_timestamp = ""
        if dark_energy_changes:
            rate = f"{dark_energy_changes.change_rate_per_hour:+.2%}/hr"
            now_seconds = int(datetime.now().timestamp())
            if dark_energy_changes.change_rate_per_hour > 0:
                complete_seconds = (
                    now_seconds + dark_energy_changes.seconds_until_complete
                )
                completion_timestamp = language_json["MeridiaEmbed"]["reaches"].format(
                    number=100, timestamp=complete_seconds
                )
            elif dark_energy_changes.change_rate_per_hour < 0:
                complete_seconds = (
                    now_seconds + dark_energy_changes.seconds_until_complete
                )
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
                    value=(
                        f"Members: **{guild.member_count}**"
                        f"\nInvite: [Link](<https://discord.com/invite/{guild.vanity_url_code}>)"
                        f"\nLocale: **{guild.preferred_locale}**"
                        f"\nCreated: <t:{int(guild.created_at.timestamp())}:R>"
                    ),
                )
                if index % 2 == 0:
                    self.add_field("", "", inline=False)
            else:
                break
        try:
            self.set_image([g for g in guilds if g.banner][0].banner.url)
        except:
            pass
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
        formatted_timestamp = ""
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
            formatted_timestamp = f"\n-# {completion_timestamp}"
        self.add_field(
            "",
            (
                f"{siege_fleet.health_bar}\n"
                f"**`{siege_fleet.perc:^25.3%}`**\n"
                f"**`{rate:^25}`**"
                f"{formatted_timestamp}"
            ),
            inline=False,
        )
        self.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/1212735927223590974/1372960719653568603/iluminat.png?ex=6828accf&is=68275b4f&hm=9069a2c2b0ab944699c5e5382aa2b58611b6eb9af22eef56433e63c9fa9c27c2&"
        )


class BotInfoCommandEmbeds(list[Embed]):
    def __init__(self, bot: GalacticWideWebBot):
        self.append(self.HeaderEmbed(bot=bot))
        self.extend(self.CogEmbeds(bot=bot))
        self.append(self.InterfaceHandlerEmbed(bot=bot))

    class HeaderEmbed(Embed, EmbedReprMixin):
        def __init__(self, bot: GalacticWideWebBot):
            super().__init__(
                title="Galactic Wide Web bot info", colour=Colour.dark_theme()
            )
            uptime_seconds = (datetime.now() - bot.startup_time).total_seconds()
            hours = uptime_seconds // 3600
            minutes = (uptime_seconds % 3600) // 60
            remaining_seconds = uptime_seconds % 60

            self.add_field(
                "Uptime",
                f"{hours:.0f} hours, {minutes:.0f} minutes and {remaining_seconds:.0f} seconds",
                inline=False,
            )

    class CogEmbeds(list[Embed]):
        def __init__(self, bot: GalacticWideWebBot):

            cog_ids = []
            embed_count = 1
            embed = Embed(title=f"Cogs {embed_count}", colour=Colour.dark_theme())
            for cog_name, cog in bot.cogs.items():
                cog_info_text = f"-# id=**{id(cog)}**"
                for name, member in getmembers(cog):
                    if isinstance(member, Loop):
                        if member.next_iteration:
                            timestamp = (
                                f" - <t:{int(member.next_iteration.timestamp())}:R>"
                            )
                        elif member.count:
                            timestamp = " - COMPLETED"
                        else:
                            timestamp = " - ERROR :warning:"
                        cog_info_text += f"\n-#  - {name} {timestamp}"
                cog_ids.append(id(cog))
                embed.add_field(cog_name, cog_info_text, inline=False)
                if len(embed.fields) > 5:
                    self.append(embed)
                    embed_count += 1
                    embed = Embed(
                        title=f"Cogs {embed_count}", colour=Colour.dark_theme()
                    )
            duplicate_ids = [
                cog_id
                for cog_id in cog_ids
                if len([cid for cid in cog_ids if cid == cog_id]) > 1
            ]
            if duplicate_ids:
                self.append(Embed(title="Duplicate ID's", description=duplicate_ids))

    class InterfaceHandlerEmbed(Embed, EmbedReprMixin):
        def __init__(self, bot=GalacticWideWebBot):
            super().__init__(
                title="Interface handler lengths", colour=Colour.dark_theme()
            )
            for type, list in bot.interface_handler.lists.items():
                list_length = len(list)
                set_length = len(set(list))
                warning = "" if list_length == set_length else ":warning:"
                self.add_field(
                    type, f"Length: {list_length}\nSet Length: {set_length} {warning}"
                )
