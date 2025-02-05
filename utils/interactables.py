from data.lists import language_dict
from disnake import ButtonStyle, ChannelType, SelectOption
from disnake.ui import Button, ChannelSelect, StringSelect
from utils.emojis import Emojis


class WikiButton(Button):
    def __init__(self, link: str = "https://helldivers.wiki.gg/wiki/Helldivers_Wiki"):
        super().__init__(
            style=ButtonStyle.link,
            label="Helldivers Wiki",
            url=link,
            emoji=Emojis.icons["wiki"],
        )


class HDCButton(Button):
    def __init__(self, link: str = "https://helldiverscompanion.com/"):
        super().__init__(
            style=ButtonStyle.link,
            label="Helldivers Companion",
            url=link,
            emoji=Emojis.icons["hdc"],
        )


class AppDirectoryButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.primary,
            label="App Directory",
            url="https://discord.com/application-directory/1212535586972369008",
            emoji=Emojis.icons["discord"],
        )


class KoFiButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.success,
            label="Ko-Fi",
            url="https://ko-fi.com/galacticwideweb",
            emoji=Emojis.icons["kofi"],
        )


class GitHubButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.secondary,
            label="GitHub",
            url="https://github.com/Stonemercy/Galactic-Wide-Web",
            emoji=Emojis.icons["github"],
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
            def __init__(self, selected: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label="Dashboard",
                    custom_id="dashboard_button",
                )
                if selected:
                    self.emoji = Emojis.icons["victory"]
                    self.style = ButtonStyle.blurple
                    self.disabled = True

        class SetDashboardButton(Button):
            def __init__(self):
                super().__init__(
                    style=ButtonStyle.green,
                    label="Set Dashboard",
                    custom_id="set_dashboard_button",
                )

        class DashboardChannelSelect(ChannelSelect):
            def __init__(self):
                super().__init__(
                    custom_id="dashboard_channel_select",
                    placeholder="Select the channel or start typing",
                    channel_types=[ChannelType.text, ChannelType.news],
                )

        class ClearDashboardButton(Button):
            def __init__(self):
                super().__init__(
                    style=ButtonStyle.red,
                    label="Clear Dashboard",
                    custom_id="clear_dashboard_button",
                )

    class Announcements:
        class AnnouncementsButton(Button):
            def __init__(self, selected: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label="Announcements",
                    custom_id="announcements_button",
                )
                if selected:
                    self.emoji = Emojis.icons["victory"]
                    self.style = ButtonStyle.blurple
                    self.disabled = True

        class SetAnnouncementsButton(Button):
            def __init__(self):
                super().__init__(
                    style=ButtonStyle.green,
                    label="Set Announcements",
                    custom_id="set_announcements_button",
                )

        class AnnouncementsChannelSelect(ChannelSelect):
            def __init__(self):
                super().__init__(
                    custom_id="announcements_channel_select",
                    placeholder="Select the channel or start typing",
                    channel_types=[ChannelType.text, ChannelType.news],
                )

        class ClearAnnouncementsButton(Button):
            def __init__(self):
                super().__init__(
                    style=ButtonStyle.red,
                    label="Clear Announcements",
                    custom_id="clear_announcements_button",
                )

    class Map:
        class MapButton(Button):
            def __init__(self, selected: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label="Map",
                    custom_id="map_button",
                )
                if selected:
                    self.emoji = Emojis.icons["victory"]
                    self.style = ButtonStyle.blurple
                    self.disabled = True

        class SetMapButton(Button):
            def __init__(self):
                super().__init__(
                    style=ButtonStyle.green,
                    label="Set Map",
                    custom_id="set_map_button",
                )

        class MapChannelSelect(ChannelSelect):
            def __init__(self):
                super().__init__(
                    custom_id="map_channel_select",
                    placeholder="Select the channel or start typing",
                    channel_types=[ChannelType.text, ChannelType.news],
                )

        class ClearMapButton(Button):
            def __init__(self):
                super().__init__(
                    style=ButtonStyle.red,
                    label="Clear the Map",
                    custom_id="clear_map_button",
                )

    class Language:
        class LanguageButton(Button):
            def __init__(self, selected: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label="Language",
                    custom_id="language_button",
                )
                if selected:
                    self.emoji = Emojis.icons["victory"]
                    self.style = ButtonStyle.blurple
                    self.disabled = True

        class LanguageSelect(StringSelect):
            def __init__(self):
                super().__init__(
                    custom_id="language_select",
                    placeholder="Select the language you want",
                    options=[
                        SelectOption(label=lang.upper())
                        for lang in language_dict.values()
                    ],
                )

    class PatchNotes:
        class PatchNotesButton(Button):
            def __init__(self, enabled: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label="Patch Notes",
                    custom_id="patch_notes_button",
                    disabled=True,
                )
                if enabled:
                    self.emoji = "✅"
                else:
                    self.emoji = "❌"

    class MajorOrderUpdates:
        class MajorOrderUpdatesButton(Button):
            def __init__(self, enabled: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label="Major Order Updates",
                    custom_id="major_order_updates_button",
                    disabled=True,
                )
                if enabled:
                    self.emoji = "✅"
                else:
                    self.emoji = "❌"

    class PersonalOrder:
        class PersonalOrderUpdatesButton(Button):
            def __init__(self, enabled: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label="Personal Order",
                    custom_id="personal_order_updates_button",
                    disabled=True,
                )
                if enabled:
                    self.emoji = "✅"
                else:
                    self.emoji = "❌"

    class DetailedDispatches:
        class DetailedDispatchesButton(Button):
            def __init__(self, enabled: bool = False):
                super().__init__(
                    style=ButtonStyle.gray,
                    label="Detailed Dispatches",
                    custom_id="detailed_dispatches_updates_button",
                    disabled=True,
                )
                if enabled:
                    self.emoji = "✅"
                else:
                    self.emoji = "❌"
