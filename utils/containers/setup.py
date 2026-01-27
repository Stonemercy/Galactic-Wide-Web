from disnake import Colour, ui, ShardInfo
from utils.dbv2 import GWWGuild
from utils.emojis import Emojis
from utils.mixins import ReprMixin
from utils.setup import Setup


class SetupContainer(ui.Container, ReprMixin):
    def __init__(
        self,
        guild: GWWGuild,
        container_json: dict,
        language_code: str,
        shard_info: ShardInfo,
        active_category: str = None,
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

        if not active_category:
            self.components.extend(
                [
                    ui.ActionRow(
                        Setup.Dashboards.DashboardsButton(),
                        Setup.Features.FeaturesButton(),
                    ),
                    ui.Separator(),
                    ui.Section(
                        ui.TextDisplay(
                            container_json["language"].format(
                                flag_emoji=getattr(
                                    Emojis.Flags,
                                    guild.language.lower().replace("-", "_"),
                                )
                            )
                            + f"\n**{guild.language_long}**"
                        ),
                        accessory=Setup.Language.LanguageButton(
                            container_json=container_json, language_code=language_code
                        ),
                    ),
                ]
            )
        else:
            self.components.append(ui.TextDisplay(f"# {active_category.title()}"))
            if active_category == "dashboards":
                dashboard_feature = [
                    f for f in guild.features if f.name == "dashboards"
                ]
                if dashboard_feature:
                    dashboard_section = ui.Section(
                        ui.TextDisplay(
                            f":white_check_mark: {container_json['dashboard_title']}\n{container_json['dashboard_desc']}"
                        ),
                        accessory=Setup.Dashboards.Dashboard.ClearDashboardButton(
                            container_json=container_json
                        ),
                    )
                    dashboard = dashboard_feature[0]
                    dashboard_section.children[0].content += (
                        f"{container_json['channel']}: <#{dashboard.channel_id}>"
                        f"\n{container_json['message']}: https://discord.com/channels/{guild.guild_id}/{dashboard.channel_id}/{dashboard.message_id}"
                    )
                    self.components.extend([ui.Separator(), dashboard_section])
                else:
                    text_display = ui.TextDisplay(
                        f":x: {container_json['dashboard_title']}\n{container_json['dashboard_desc']}**{container_json['not_set']}**"
                    )
                    self.components.extend(
                        [
                            text_display,
                            ui.ActionRow(
                                Setup.Dashboards.Dashboard.DashboardChannelSelect(
                                    container_json=container_json
                                )
                            ),
                            ui.Separator(),
                        ]
                    )

                # map
                map_feature = [f for f in guild.features if f.name == "maps"]
                if map_feature:
                    map_section = ui.Section(
                        ui.TextDisplay(
                            f":white_check_mark: {container_json['map_title']}\n{container_json['map_desc']}"
                        ),
                        accessory=ui.Button(),
                    )
                    galaxy_map = map_feature[0]
                    map_section.children[0].content += (
                        f"{container_json['channel']}: <#{galaxy_map.channel_id}>"
                        f"\n{container_json['message']}: https://discord.com/channels/{guild.guild_id}/{galaxy_map.channel_id}/{galaxy_map.message_id}"
                    )
                    map_section.accessory = Setup.Dashboards.Map.ClearMapButton(
                        container_json=container_json
                    )
                    self.components.extend([ui.Separator(), map_section])
                else:
                    text_display = ui.TextDisplay(
                        f":x: {container_json['map_title']}\n{container_json['map_desc']}**{container_json['not_set']}**"
                    )
                    self.components.extend(
                        [
                            text_display,
                            ui.ActionRow(
                                Setup.Dashboards.Map.MapChannelSelect(
                                    container_json=container_json
                                )
                            ),
                            ui.Separator(),
                        ]
                    )
            elif active_category == "features":
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
                        ":white_check_mark: "
                        + war_announcements_section.children[0].content
                    )
                    war_announcements = war_announcements_feature[0]
                    war_announcements_section.children[
                        0
                    ].content += f"{container_json['channel']}: <#{war_announcements.channel_id}>"
                    war_announcements_section.accessory = (
                        Setup.Features.ClearFeatureButton(
                            feature_type="war_announcements",
                            container_json=container_json,
                        )
                    )
                else:
                    war_announcements_section.children[0].content = (
                        ":x: " + war_announcements_section.children[0].content
                    )
                    war_announcements_section.children[
                        0
                    ].content += f"**{container_json['not_set']}**"
                    war_announcements_section.accessory = (
                        Setup.Features.SetFeatureButton(
                            feature_type="war_announcements",
                            container_json=container_json,
                        )
                    )
                self.components.extend([ui.Separator(), war_announcements_section])

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
                        ":white_check_mark: "
                        + dss_announcements_section.children[0].content
                    )
                    dss_announcements = dss_announcements_feature[0]
                    dss_announcements_section.children[
                        0
                    ].content += f"{container_json['channel']}: <#{dss_announcements.channel_id}>"
                    dss_announcements_section.accessory = (
                        Setup.Features.ClearFeatureButton(
                            feature_type="dss_announcements",
                            container_json=container_json,
                        )
                    )
                else:
                    dss_announcements_section.children[0].content = (
                        ":x: " + dss_announcements_section.children[0].content
                    )
                    dss_announcements_section.children[
                        0
                    ].content += f"**{container_json['not_set']}**"
                    dss_announcements_section.accessory = (
                        Setup.Features.SetFeatureButton(
                            feature_type="dss_announcements",
                            container_json=container_json,
                        )
                    )
                self.components.extend([ui.Separator(), dss_announcements_section])

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
                        ":white_check_mark: "
                        + region_announcements_section.children[0].content
                    )
                    region_announcements = region_announcements_feature[0]
                    region_announcements_section.children[
                        0
                    ].content += f"{container_json['channel']}: <#{region_announcements.channel_id}>"
                    region_announcements_section.accessory = (
                        Setup.Features.ClearFeatureButton(
                            feature_type="region_announcements",
                            container_json=container_json,
                        )
                    )
                else:
                    region_announcements_section.children[0].content = (
                        ":x: " + region_announcements_section.children[0].content
                    )
                    region_announcements_section.children[
                        0
                    ].content += f"**{container_json['not_set']}**"
                    region_announcements_section.accessory = (
                        Setup.Features.SetFeatureButton(
                            feature_type="region_announcements",
                            container_json=container_json,
                        )
                    )
                self.components.extend([ui.Separator(), region_announcements_section])

                # patch notes
                patch_notes_section = ui.Section(
                    ui.TextDisplay(
                        f"{container_json['patch_notes_title']}\n{container_json['patch_notes_desc']}"
                    ),
                    accessory=ui.Button(),
                )
                patch_notes_feature = [
                    f for f in guild.features if f.name == "patch_notes"
                ]
                if patch_notes_feature:
                    patch_notes_section.children[0].content = (
                        ":white_check_mark: " + patch_notes_section.children[0].content
                    )
                    patch_notes = patch_notes_feature[0]
                    patch_notes_section.children[
                        0
                    ].content += (
                        f"{container_json['channel']}: <#{patch_notes.channel_id}>"
                    )
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
                self.components.extend([ui.Separator(), patch_notes_section])

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
                    ].content += (
                        f"{container_json['channel']}: <#{mo_updates.channel_id}>"
                    )
                    mo_updates_section.accessory = Setup.Features.ClearFeatureButton(
                        feature_type="major_order_updates",
                        container_json=container_json,
                    )
                else:
                    mo_updates_section.children[0].content = (
                        ":x: " + mo_updates_section.children[0].content
                    )
                    mo_updates_section.children[
                        0
                    ].content += f"**{container_json['not_set']}**"
                    mo_updates_section.accessory = Setup.Features.SetFeatureButton(
                        feature_type="major_order_updates",
                        container_json=container_json,
                    )
                self.components.extend([ui.Separator(), mo_updates_section])

                # po updates
                po_updates_section = ui.Section(
                    ui.TextDisplay(
                        f"{container_json['personal_order_updates_title']}\n{container_json['personal_order_updates_desc']}"
                    ),
                    accessory=ui.Button(),
                )
                po_updates_feature = [
                    f for f in guild.features if f.name == "personal_order_updates"
                ]
                if po_updates_feature:
                    po_updates_section.children[0].content = (
                        ":white_check_mark: " + po_updates_section.children[0].content
                    )
                    po_updates = po_updates_feature[0]
                    po_updates_section.children[
                        0
                    ].content += (
                        f"{container_json['channel']}: <#{po_updates.channel_id}>"
                    )
                    po_updates_section.accessory = Setup.Features.ClearFeatureButton(
                        feature_type="personal_order_updates",
                        container_json=container_json,
                    )
                else:
                    po_updates_section.children[0].content = (
                        ":x: " + po_updates_section.children[0].content
                    )
                    po_updates_section.children[
                        0
                    ].content += f"**{container_json['not_set']}**"
                    po_updates_section.accessory = Setup.Features.SetFeatureButton(
                        feature_type="personal_order_updates",
                        container_json=container_json,
                    )
                self.components.extend([ui.Separator(), po_updates_section])

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
                    ].content += (
                        f"{container_json['channel']}: <#{dd_dispatches.channel_id}>"
                    )
                    ddispatches_section.accessory = Setup.Features.ClearFeatureButton(
                        feature_type="detailed_dispatches",
                        container_json=container_json,
                    )
                else:
                    ddispatches_section.children[0].content = (
                        ":x: " + ddispatches_section.children[0].content
                    )
                    ddispatches_section.children[
                        0
                    ].content += f"**{container_json['not_set']}**"
                    ddispatches_section.accessory = Setup.Features.SetFeatureButton(
                        feature_type="detailed_dispatches",
                        container_json=container_json,
                    )
                self.components.extend([ui.Separator(), ddispatches_section])

        if active_category:
            self.components.extend([ui.Separator(), ui.ActionRow(Setup.HomeButton())])

        super().__init__(
            *self.components,
            accent_colour=Colour.og_blurple(),
        )
