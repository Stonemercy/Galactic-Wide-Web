from disnake import Colour, Embed, ShardInfo
from utils.dbv2 import GWWGuild
from utils.mixins import EmbedReprMixin


class SetupEmbed(Embed, EmbedReprMixin):
    def __init__(self, guild: GWWGuild, language_json: dict, shard_info: ShardInfo):
        super().__init__(
            title=language_json["SetupEmbed"]["title"],
            colour=Colour.og_blurple(),
            description=f"Shard #**{shard_info.id}** - **{shard_info.latency * 1000:.0f}ms**",
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
        war_announcements_text = f"{language_json['SetupEmbed']['wa_desc']}"
        war_announcements_feature = [
            f for f in guild.features if f.name == "war_announcements"
        ]
        if war_announcements_feature:
            setup_emoji = ":white_check_mark:"
            war_announcements = war_announcements_feature[0]
            war_announcements_text += f"{language_json['SetupEmbed']['wa_channel']}: <#{war_announcements.channel_id}>\n"
        else:
            setup_emoji = ":x:"
            war_announcements_text += f"**{language_json['SetupEmbed']['not_set']}**"
        self.add_field(
            f"{setup_emoji} {language_json['SetupEmbed']['war_announcements']}",
            war_announcements_text,
            inline=False,
        )

        # dss announcements
        dss_announcements_text = f"{language_json['SetupEmbed']['dssa_desc']}"
        dss_announcements_feature = [
            f for f in guild.features if f.name == "dss_announcements"
        ]
        if dss_announcements_feature:
            setup_emoji = ":white_check_mark:"
            dss_announcements = dss_announcements_feature[0]
            dss_announcements_text += f"{language_json['SetupEmbed']['dssa_channel']}: <#{dss_announcements.channel_id}>"
        else:
            setup_emoji = ":x:"
            dss_announcements_text += f"**{language_json['SetupEmbed']['not_set']}**"
        self.add_field(
            f"{setup_emoji} {language_json['SetupEmbed']['dss_announcements']}",
            dss_announcements_text,
            inline=False,
        )

        # region announcements
        region_announcements_text = language_json["SetupEmbed"]["regiona_desc"]
        region_announcements_feature = [
            f for f in guild.features if f.name == "region_announcements"
        ]
        if region_announcements_feature:
            setup_emoji = ":white_check_mark:"
            region_announcements = region_announcements_feature[0]
            region_announcements_text += f"{language_json['SetupEmbed']['regiona_channel']}: <#{region_announcements.channel_id}>"
        else:
            setup_emoji = ":x:"
            region_announcements_text += f"**{language_json['SetupEmbed']['not_set']}**"
        self.add_field(
            f"{setup_emoji} {language_json['SetupEmbed']['region_announcements']}",
            region_announcements_text,
            inline=False,
        )

        # patch notes
        patch_notes_text = language_json["SetupEmbed"]["patch_notes_desc"]
        patch_notes_feature = [f for f in guild.features if f.name == "patch_notes"]
        if patch_notes_feature:
            setup_emoji = ":white_check_mark:"
            patch_notes = patch_notes_feature[0]
            patch_notes_text += f"{language_json['SetupEmbed']['patch_notes_channel']}: <#{patch_notes.channel_id}>"
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
            mo_updates_text += f"{language_json['SetupEmbed']['mo_updates_channel']}: <#{mo_updates.channel_id}>"
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
            mo_updates_text += f"{language_json['SetupEmbed']['detailed_dispatches_channel']}: <#{dd_dispatches.channel_id}>"
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
