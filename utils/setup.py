from disnake import ButtonStyle, ChannelType, SelectOption
from disnake.ui import Button, ChannelSelect, StringSelect
from utils.dataclasses import Languages
from utils.emojis import Emojis


class Setup:
    class Dashboard:
        class DashboardButton(Button):
            def __init__(self, language_json: dict, selected: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label=language_json["setup"]["buttons"]["dashboard"],
                    custom_id="dashboard_button",
                )
                if selected:
                    self.emoji = Emojis.Icons.victory
                    self.style = ButtonStyle.blurple
                    self.disabled = True

        class SetDashboardButton(Button):
            def __init__(self, language_json: dict):
                super().__init__(
                    style=ButtonStyle.green,
                    label=language_json["setup"]["buttons"]["set_dashboard"],
                    custom_id="set_dashboard_button",
                )

        class DashboardChannelSelect(ChannelSelect):
            def __init__(self, language_json: dict):
                super().__init__(
                    custom_id="dashboard_channel_select",
                    placeholder=language_json["setup"]["buttons"][
                        "dashboard_channel_select"
                    ],
                    channel_types=[ChannelType.text, ChannelType.news],
                )

        class ClearDashboardButton(Button):
            def __init__(self, language_json: dict):
                super().__init__(
                    style=ButtonStyle.red,
                    label=language_json["setup"]["buttons"]["clear_dashboard"],
                    custom_id="clear_dashboard_button",
                )

    class Features:
        class FeaturesButton(Button):
            def __init__(self, language_json: dict, selected: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label=language_json["setup"]["buttons"]["features"],
                    custom_id="features_button",
                )
                if selected:
                    self.emoji = Emojis.Icons.victory
                    self.style = ButtonStyle.blurple
                    self.disabled = True

        class FeatureButton(Button):
            def __init__(
                self, feature_type: str, language_json: dict, selected: bool = False
            ):
                super().__init__(
                    style=ButtonStyle.gray,
                    label=language_json["setup"]["buttons"][feature_type],
                    custom_id=f"{feature_type}_features_button",
                )
                if selected:
                    self.emoji = Emojis.Icons.victory
                    self.style = ButtonStyle.blurple
                    self.disabled = True

        class SetFeatureButton(Button):
            def __init__(self, feature_type: str, language_json: dict):
                super().__init__(
                    style=ButtonStyle.green,
                    label=language_json["setup"]["buttons"]["set_feature"],
                    custom_id="set_features_button-" + feature_type,
                )

        class ClearFeatureButton(Button):
            def __init__(self, feature_type: str, language_json: dict):
                super().__init__(
                    style=ButtonStyle.red,
                    label=language_json["setup"]["buttons"]["clear_feature"],
                    custom_id="clear_features_button-" + feature_type,
                )

        class FeatureChannelSelect(ChannelSelect):
            def __init__(self, feature_type: str, language_json: dict):
                super().__init__(
                    custom_id="feature_channel_select-" + feature_type,
                    placeholder=language_json["setup"]["buttons"][
                        "feature_channel_select"
                    ],
                    channel_types=[
                        ChannelType.text,
                        ChannelType.news,
                        ChannelType.public_thread,
                    ],
                )

    class Map:
        class MapButton(Button):
            def __init__(self, language_json: dict, selected: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label=language_json["setup"]["buttons"]["map"],
                    custom_id="map_button",
                )
                if selected:
                    self.emoji = Emojis.Icons.victory
                    self.style = ButtonStyle.blurple
                    self.disabled = True

        class SetMapButton(Button):
            def __init__(self, language_json: dict):
                super().__init__(
                    style=ButtonStyle.green,
                    label=language_json["setup"]["buttons"]["set_map"],
                    custom_id="set_map_button",
                )

        class MapChannelSelect(ChannelSelect):
            def __init__(self, language_json: dict):
                super().__init__(
                    custom_id="map_channel_select",
                    placeholder=language_json["setup"]["buttons"]["map_channel_select"],
                    channel_types=[ChannelType.text, ChannelType.news],
                )

        class ClearMapButton(Button):
            def __init__(self, language_json: dict):
                super().__init__(
                    style=ButtonStyle.red,
                    label=language_json["setup"]["buttons"]["clear_map"],
                    custom_id="clear_map_button",
                )

    class Language:
        class LanguageButton(Button):
            def __init__(self, language_json: dict, selected: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label=language_json["setup"]["buttons"]["language"],
                    custom_id="language_button",
                )
                if selected:
                    self.emoji = Emojis.Icons.victory
                    self.style = ButtonStyle.blurple
                    self.disabled = True

        class LanguageSelect(StringSelect):
            def __init__(self, language_json: dict):
                super().__init__(
                    custom_id="language_select",
                    placeholder=language_json["setup"]["buttons"]["language_select"],
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
