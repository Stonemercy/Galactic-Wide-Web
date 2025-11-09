from disnake import Colour, ui, ShardInfo
from utils.dbv2 import GWWGuild
from utils.mixins import ReprMixin
from utils.setup import Setup

FLAG_DICT = {
    "en": ":flag_gb:",
    "fr": ":flag_fr:",
    "de": ":flag_de:",
    "it": ":flag_it:",
    "pt-br": ":flag_br:",
    "ru": ":flag_ru:",
    "es": ":flag_es:",
}


class SetupContainer(ui.Container, ReprMixin):
    def __init__(
        self,
        guild: GWWGuild,
        container_json: dict,
        language_code: str,
        shard_info: ShardInfo,
    ):
        self.components = []

        self.components.extend(
            [
                ui.TextDisplay(
                    container_json["shard_info"].format(
                        shard_id=shard_info.id,
                        latency=f"{shard_info.latency * 1000:.0f}",
                    )
                ),
                ui.Separator(),
            ]
        )

        # dashboard
        dashboard_section = ui.Section(
            ui.TextDisplay(
                f"{container_json['dashboard_title']}\n{container_json['dashboard_desc']}"
            ),
            accessory=ui.Button(),
        )
        dashboard_feature = [f for f in guild.features if f.name == "dashboards"]
        if dashboard_feature:
            dashboard_section.children[0].content = (
                ":white_check_mark: " + dashboard_section.children[0].content
            )
            dashboard = dashboard_feature[0]
            dashboard_section.children[0].content += (
                f"{container_json['channel']}: <#{dashboard.channel_id}>"
                f"\n{container_json['message']}: https://discord.com/channels/{guild.guild_id}/{dashboard.channel_id}/{dashboard.message_id}"
            )
            dashboard_section.accessory = Setup.Dashboard.ClearDashboardButton(
                container_json=container_json
            )
        else:
            dashboard_section.children[0].content = (
                ":x: " + dashboard_section.children[0].content
            )
            dashboard_section.children[0].content += f"**{container_json['not_set']}**"
            dashboard_section.accessory = Setup.Dashboard.SetDashboardButton(
                container_json=container_json
            )
        self.components.extend([dashboard_section, ui.Separator()])

        # map
        map_section = ui.Section(
            ui.TextDisplay(
                f"{container_json['map_title']}\n{container_json['map_desc']}"
            ),
            accessory=ui.Button(),
        )
        map_feature = [f for f in guild.features if f.name == "maps"]
        if map_feature:
            map_section.children[0].content = (
                ":white_check_mark: " + map_section.children[0].content
            )
            galaxy_map = map_feature[0]
            map_section.children[0].content += (
                f"{container_json['channel']}: <#{galaxy_map.channel_id}>"
                f"\n{container_json['message']}: https://discord.com/channels/{guild.guild_id}/{galaxy_map.channel_id}/{galaxy_map.message_id}"
            )
            map_section.accessory = Setup.Map.ClearMapButton(
                container_json=container_json
            )
        else:
            map_section.children[0].content = ":x: " + map_section.children[0].content
            map_section.children[0].content += f"**{container_json['not_set']}**"
            map_section.accessory = Setup.Map.SetMapButton(
                container_json=container_json
            )
        self.components.extend([map_section, ui.Separator()])

        # war announcements
        war_announcements_section = ui.Section(
            ui.TextDisplay(
                f"{container_json['war_announcements_title']}\n{container_json['war_announcements_desc']}"
            ),
            accessory=ui.Button(),
        )
        war_announcements_feature = [
            f for f in guild.features if f.name == "war_announcements"
        ]
        if war_announcements_feature:
            war_announcements_section.children[0].content = (
                ":white_check_mark: " + war_announcements_section.children[0].content
            )
            war_announcements = war_announcements_feature[0]
            war_announcements_section.children[
                0
            ].content += (
                f"{container_json['channel']}: <#{war_announcements.channel_id}>"
            )
            war_announcements_section.accessory = Setup.Features.ClearFeatureButton(
                feature_type="war_announcements", container_json=container_json
            )
        else:
            war_announcements_section.children[0].content = (
                ":x: " + war_announcements_section.children[0].content
            )
            war_announcements_section.children[
                0
            ].content += f"**{container_json['not_set']}**"
            war_announcements_section.accessory = Setup.Features.SetFeatureButton(
                feature_type="war_announcements", container_json=container_json
            )
        self.components.extend([war_announcements_section, ui.Separator()])

        # dss announcements
        dss_announcements_section = ui.Section(
            ui.TextDisplay(
                f"{container_json['dss_announcements_title']}\n{container_json['dss_announcements_desc']}"
            ),
            accessory=ui.Button(),
        )
        dss_announcements_feature = [
            f for f in guild.features if f.name == "dss_announcements"
        ]
        if dss_announcements_feature:
            dss_announcements_section.children[0].content = (
                ":white_check_mark: " + dss_announcements_section.children[0].content
            )
            dss_announcements = dss_announcements_feature[0]
            dss_announcements_section.children[
                0
            ].content += (
                f"{container_json['channel']}: <#{dss_announcements.channel_id}>"
            )
            dss_announcements_section.accessory = Setup.Features.ClearFeatureButton(
                feature_type="dss_announcements", container_json=container_json
            )
        else:
            dss_announcements_section.children[0].content = (
                ":x: " + dss_announcements_section.children[0].content
            )
            dss_announcements_section.children[
                0
            ].content += f"**{container_json['not_set']}**"
            dss_announcements_section.accessory = Setup.Features.SetFeatureButton(
                feature_type="dss_announcements", container_json=container_json
            )
        self.components.extend([dss_announcements_section, ui.Separator()])

        # region announcements
        region_announcements_section = ui.Section(
            ui.TextDisplay(
                f"{container_json['region_announcements_title']}\n{container_json['region_announcements_desc']}"
            ),
            accessory=ui.Button(),
        )
        region_announcements_feature = [
            f for f in guild.features if f.name == "region_announcements"
        ]
        if region_announcements_feature:
            region_announcements_section.children[0].content = (
                ":white_check_mark: " + region_announcements_section.children[0].content
            )
            region_announcements = region_announcements_feature[0]
            region_announcements_section.children[
                0
            ].content += (
                f"{container_json['channel']}: <#{region_announcements.channel_id}>"
            )
            region_announcements_section.accessory = Setup.Features.ClearFeatureButton(
                feature_type="region_announcements", container_json=container_json
            )
        else:
            region_announcements_section.children[0].content = (
                ":x: " + region_announcements_section.children[0].content
            )
            region_announcements_section.children[
                0
            ].content += f"**{container_json['not_set']}**"
            region_announcements_section.accessory = Setup.Features.SetFeatureButton(
                feature_type="region_announcements", container_json=container_json
            )
        self.components.extend([region_announcements_section, ui.Separator()])

        # patch notes
        patch_notes_section = ui.Section(
            ui.TextDisplay(
                f"{container_json['patch_notes_title']}\n{container_json['patch_notes_desc']}"
            ),
            accessory=ui.Button(),
        )
        patch_notes_feature = [f for f in guild.features if f.name == "patch_notes"]
        if patch_notes_feature:
            patch_notes_section.children[0].content = (
                ":white_check_mark: " + patch_notes_section.children[0].content
            )
            patch_notes = patch_notes_feature[0]
            patch_notes_section.children[
                0
            ].content += f"{container_json['channel']}: <#{patch_notes.channel_id}>"
            patch_notes_section.accessory = Setup.Features.ClearFeatureButton(
                feature_type="patch_notes", container_json=container_json
            )
        else:
            patch_notes_section.children[0].content = (
                ":x: " + patch_notes_section.children[0].content
            )
            patch_notes_section.children[
                0
            ].content += f"**{container_json['not_set']}**"
            patch_notes_section.accessory = Setup.Features.SetFeatureButton(
                feature_type="patch_notes", container_json=container_json
            )
        self.components.extend([patch_notes_section, ui.Separator()])

        # mo updates
        mo_updates_section = ui.Section(
            ui.TextDisplay(
                f"{container_json['major_order_updates_title']}\n{container_json['major_order_updates_desc']}"
            ),
            accessory=ui.Button(),
        )
        mo_updates_feature = [
            f for f in guild.features if f.name == "major_order_updates"
        ]
        if mo_updates_feature:
            mo_updates_section.children[0].content = (
                ":white_check_mark: " + mo_updates_section.children[0].content
            )
            mo_updates = mo_updates_feature[0]
            mo_updates_section.children[
                0
            ].content += f"{container_json['channel']}: <#{mo_updates.channel_id}>"
            mo_updates_section.accessory = Setup.Features.ClearFeatureButton(
                feature_type="major_order_updates", container_json=container_json
            )
        else:
            mo_updates_section.children[0].content = (
                ":x: " + mo_updates_section.children[0].content
            )
            mo_updates_section.children[0].content += f"**{container_json['not_set']}**"
            mo_updates_section.accessory = Setup.Features.SetFeatureButton(
                feature_type="major_order_updates", container_json=container_json
            )
        self.components.extend([mo_updates_section, ui.Separator()])

        # detailed dispatches
        ddispatches_section = ui.Section(
            ui.TextDisplay(
                f"{container_json['detailed_dispatches_title']}\n{container_json['detailed_dispatches_desc']}"
            ),
            accessory=ui.Button(),
        )
        ddispatches_feature = [
            f for f in guild.features if f.name == "detailed_dispatches"
        ]
        if ddispatches_feature:
            ddispatches_section.children[0].content = (
                ":white_check_mark: " + ddispatches_section.children[0].content
            )
            dd_dispatches = ddispatches_feature[0]
            ddispatches_section.children[
                0
            ].content += f"{container_json['channel']}: <#{dd_dispatches.channel_id}>"
            ddispatches_section.accessory = Setup.Features.ClearFeatureButton(
                feature_type="detailed_dispatches", container_json=container_json
            )
        else:
            ddispatches_section.children[0].content = (
                ":x: " + ddispatches_section.children[0].content
            )
            ddispatches_section.children[
                0
            ].content += f"**{container_json['not_set']}**"
            ddispatches_section.accessory = Setup.Features.SetFeatureButton(
                feature_type="detailed_dispatches", container_json=container_json
            )
        self.components.extend([ddispatches_section, ui.Separator()])

        # language
        self.components.append(
            ui.Section(
                ui.TextDisplay(
                    container_json["language"].format(
                        flag_emoji=FLAG_DICT[guild.language]
                    )
                    + f"\n**{guild.language_long}**"
                ),
                accessory=Setup.Language.LanguageButton(
                    container_json=container_json, language_code=language_code
                ),
            )
        )

        super().__init__(
            *self.components,
            accent_colour=Colour.og_blurple(),
        )
