from disnake import ButtonStyle
from disnake.ui import Button
from utils.emojis import Emojis


class WikiButton(Button):
    def __init__(self, link: str = "https://helldivers.wiki.gg/wiki/Helldivers_Wiki"):
        super().__init__(
            style=ButtonStyle.link,
            label="Helldivers Wiki",
            url=link,
            emoji=Emojis.Icons.wiki,
        )
