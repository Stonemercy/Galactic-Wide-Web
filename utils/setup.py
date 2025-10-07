from disnake import ButtonStyle, ChannelType, SelectOption
from disnake.ui import Button, ChannelSelect, StringSelect
from utils.dataclasses import Languages
from utils.emojis import Emojis


class Setup:
    class Dashboard:
        class SetDashboardButton(Button):
            def __init__(self, container_json: dict):
                super().__init__(
                    style=ButtonStyle.green,
                    label=container_json["set_feature"].format(
                        feature=container_json["dashboard_title"]
                    ),
                    custom_id="set_dashboard_button",
                )

        class ClearDashboardButton(Button):
            def __init__(self, container_json: dict):
                super().__init__(
                    style=ButtonStyle.red,
                    label=container_json["clear_feature"].format(
                        feature=container_json["dashboard_title"]
                    ),
                    custom_id="clear_dashboard_button",
                )

        class DashboardChannelSelect(ChannelSelect):
            def __init__(self, container_json: dict):
                super().__init__(
                    custom_id="dashboard_channel_select",
                    placeholder=container_json["dashboard_channel_select"],
                    channel_types=[
                        ChannelType.text,
                        ChannelType.news,
                        ChannelType.public_thread,
                    ],
                )

    class Map:
        class SetMapButton(Button):
            def __init__(self, container_json: dict):
                super().__init__(
                    style=ButtonStyle.green,
                    label=container_json["set_feature"].format(
                        feature=container_json["map_title"]
                    ),
                    custom_id="set_map_button",
                )

        class ClearMapButton(Button):
            def __init__(self, container_json: dict):
                super().__init__(
                    style=ButtonStyle.red,
                    label=container_json["clear_feature"].format(
                        feature=container_json["map_title"]
                    ),
                    custom_id="clear_map_button",
                )

        class MapChannelSelect(ChannelSelect):
            def __init__(self, container_json: dict):
                super().__init__(
                    custom_id="map_channel_select",
                    placeholder=container_json["map_channel_select"],
                    channel_types=[
                        ChannelType.text,
                        ChannelType.news,
                        ChannelType.public_thread,
                    ],
                )

    class Features:
        class SetFeatureButton(Button):
            def __init__(self, feature_type: str, container_json: dict):
                super().__init__(
                    style=ButtonStyle.green,
                    label=container_json["set_feature"].format(
                        feature=container_json[f"{feature_type}_title"]
                    ),
                    custom_id="set_features_button-" + feature_type,
                )

        class ClearFeatureButton(Button):
            def __init__(self, feature_type: str, container_json: dict):
                super().__init__(
                    style=ButtonStyle.red,
                    label=container_json["clear_feature"].format(
                        feature=container_json[f"{feature_type}_title"]
                    ),
                    custom_id="clear_features_button-" + feature_type,
                )

        class FeatureChannelSelect(ChannelSelect):
            def __init__(self, feature_type: str, container_json: dict):
                super().__init__(
                    custom_id="feature_channel_select-" + feature_type,
                    placeholder=container_json["feature_channel_select"],
                    channel_types=[
                        ChannelType.text,
                        ChannelType.news,
                        ChannelType.public_thread,
                    ],
                )

    class Language:
        class LanguageButton(Button):
            def __init__(self, container_json: dict, language_code: str):
                super().__init__(
                    style=ButtonStyle.gray,
                    label=container_json["language_button"],
                    custom_id="language_button",
                    emoji=getattr(Emojis.Flags, language_code.replace("-", "_")),
                )

        class LanguageSelect(StringSelect):
            def __init__(self, container_json: dict):
                super().__init__(
                    custom_id="language_select",
                    placeholder=container_json["language_select"],
                    options=[
                        SelectOption(
                            label=f"{lang.short_code}",
                            emoji=getattr(
                                Emojis.Flags, lang.short_code.replace("-", "_")
                            ),
                        )
                        for lang in Languages.all
                    ],
                )
