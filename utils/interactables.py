from data.lists import language_dict
from disnake import ButtonStyle, ChannelType, SelectOption, TextInputStyle
from disnake.ui import Button, ChannelSelect, StringSelect, Modal, TextInput
from utils.emojis import Emojis


class FeedbackModal(Modal):
    def __init__(self):
        components = [
            TextInput(
                label="Quick title",
                custom_id="title",
                placeholder="tl;dr of your feedback",
                style=TextInputStyle.short,
                max_length=100,
            ),
            TextInput(
                label="Description",
                custom_id="description",
                placeholder="Your feedback goes here",
                style=TextInputStyle.paragraph,
            ),
        ]
        super().__init__(
            title="Provide feedback",
            components=components,
            custom_id="feedback",
            timeout=6000,
        )


class WikiButton(Button):
    def __init__(self, link: str = "https://helldivers.wiki.gg/wiki/Helldivers_Wiki"):
        super().__init__(
            style=ButtonStyle.link,
            label="Helldivers Wiki",
            url=link,
            emoji=Emojis.Icons.wiki,
        )


class HDCButton(Button):
    def __init__(self, link: str = "https://helldiverscompanion.com/"):
        super().__init__(
            style=ButtonStyle.link,
            label="Helldivers Companion",
            url=link,
            emoji=Emojis.Icons.hdc,
        )


class AppDirectoryButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.primary,
            label="App Directory",
            url="https://discord.com/application-directory/1212535586972369008",
            emoji=Emojis.Icons.discord,
        )


class KoFiButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.success,
            label="Ko-Fi",
            url="https://ko-fi.com/galacticwideweb",
            emoji=Emojis.Icons.kofi,
        )


class GitHubButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.secondary,
            label="GitHub",
            url="https://github.com/Stonemercy/Galactic-Wide-Web",
            emoji=Emojis.Icons.github,
        )


class SupportServerButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.link,
            label="Support Server",
            url="https://discord.gg/Z8Ae5H5DjZ",
        )


class SteamStringSelect(StringSelect):
    def __init__(self, data):
        super().__init__(
            placeholder="Choose Patch Notes",
            min_values=1,
            max_values=1,
            options=[SelectOption(label=steam.title) for steam in data.steam],
            custom_id="steam",
        )


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

    class Announcements:
        class AnnouncementsButton(Button):
            def __init__(self, language_json: dict, selected: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label=language_json["setup"]["buttons"]["announcements"],
                    custom_id="announcements_button",
                )
                if selected:
                    self.emoji = Emojis.Icons.victory
                    self.style = ButtonStyle.blurple
                    self.disabled = True

        class SetAnnouncementsButton(Button):
            def __init__(self, language_json: dict):
                super().__init__(
                    style=ButtonStyle.green,
                    label=language_json["setup"]["buttons"]["set_announcements"],
                    custom_id="set_announcements_button",
                )

        class AnnouncementsChannelSelect(ChannelSelect):
            def __init__(self, language_json: dict):
                super().__init__(
                    custom_id="announcements_channel_select",
                    placeholder=language_json["setup"]["buttons"][
                        "announcements_channel_select"
                    ],
                    channel_types=[ChannelType.text, ChannelType.news],
                )

        class ClearAnnouncementsButton(Button):
            def __init__(self, language_json: dict):
                super().__init__(
                    style=ButtonStyle.red,
                    label=language_json["setup"]["buttons"]["clear_announcements"],
                    custom_id="clear_announcements_button",
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
                        SelectOption(label=lang.upper())
                        for lang in language_dict.values()
                    ],
                )

    class PatchNotes:
        class PatchNotesButton(Button):
            def __init__(self, language_json: dict, enabled: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label=language_json["setup"]["buttons"]["patch_notes"],
                    custom_id="patch_notes_button",
                    disabled=True,
                )
                if enabled:
                    self.emoji = "✅"
                else:
                    self.emoji = "❌"

    class MajorOrderUpdates:
        class MajorOrderUpdatesButton(Button):
            def __init__(self, language_json: dict, enabled: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label=language_json["setup"]["buttons"]["major_order_updates"],
                    custom_id="major_order_updates_button",
                    disabled=True,
                )
                if enabled:
                    self.emoji = "✅"
                else:
                    self.emoji = "❌"

    class PersonalOrder:
        class PersonalOrderUpdatesButton(Button):
            def __init__(self, language_json: dict, enabled: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label=language_json["setup"]["buttons"]["personal_order"],
                    custom_id="personal_order_updates_button",
                    disabled=True,
                )
                if enabled:
                    self.emoji = "✅"
                else:
                    self.emoji = "❌"

    class DetailedDispatches:
        class DetailedDispatchesButton(Button):
            def __init__(self, language_json: dict, enabled: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label=language_json["setup"]["buttons"]["detailed_dispatches"],
                    custom_id="detailed_dispatches_updates_button",
                    disabled=True,
                )
                if enabled:
                    self.emoji = "✅"
                else:
                    self.emoji = "❌"
