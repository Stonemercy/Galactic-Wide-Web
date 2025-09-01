from disnake import ButtonStyle
from disnake.ui import Button
from utils.emojis import Emojis


class KoFiButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.success,
            label="Ko-Fi",
            url="https://ko-fi.com/galacticwideweb",
            emoji=Emojis.Icons.kofi,
        )
