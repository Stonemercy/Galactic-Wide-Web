from disnake import ButtonStyle, Emoji
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
