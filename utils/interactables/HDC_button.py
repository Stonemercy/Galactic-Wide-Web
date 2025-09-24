from disnake import ButtonStyle
from disnake.ui import Button
from utils.emojis import Emojis


class HDCButton(Button):
    def __init__(
        self,
        label: str = "Helldivers Companion",
        link: str = "https://helldiverscompanion.com/",
    ):
        super().__init__(
            style=ButtonStyle.link,
            label=label,
            url=link,
            emoji=Emojis.Icons.hdc,
        )
