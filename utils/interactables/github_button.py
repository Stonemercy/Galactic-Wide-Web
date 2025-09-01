from disnake import ButtonStyle
from disnake.ui import Button
from utils.emojis import Emojis


class GitHubButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.secondary,
            label="GitHub",
            url="https://github.com/Stonemercy/Galactic-Wide-Web",
            emoji=Emojis.Icons.github,
        )
