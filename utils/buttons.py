from disnake import ButtonStyle
from disnake.ui import Button
from data.lists import emojis_dict


class WikiButton(Button):
    def __init__(self, link: str = "https://helldivers.wiki.gg/wiki/Helldivers_Wiki"):
        super().__init__(
            style=ButtonStyle.link,
            label="More info",
            url=link,
            emoji=emojis_dict["wiki"],
        )


class AppDirectoryButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.primary,
            label="App Directory",
            url="https://discord.com/application-directory/1212535586972369008",
            emoji=emojis_dict["discordlogo"],
        )


class KoFiButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.success,
            label="Ko-Fi",
            url="https://ko-fi.com/galacticwideweb",
            emoji=emojis_dict["kofilogo"],
        )


class GitHubButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.secondary,
            label="GitHub",
            url="https://github.com/Stonemercy/Galactic-Wide-Web",
            emoji=emojis_dict["githublogo"],
        )
