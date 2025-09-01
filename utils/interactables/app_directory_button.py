from disnake import ButtonStyle
from disnake.ui import Button
from utils.emojis import Emojis


class AppDirectoryButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.primary,
            label="App Directory",
            url="https://discord.com/application-directory/1212535586972369008",
            emoji=Emojis.Icons.discord,
        )
