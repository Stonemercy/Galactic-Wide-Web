from disnake import ButtonStyle
from disnake.ui import Button


class SupportServerButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.link,
            label="Support Server",
            url="https://discord.gg/Z8Ae5H5DjZ",
        )
