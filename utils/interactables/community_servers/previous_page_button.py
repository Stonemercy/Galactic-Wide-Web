from disnake import ButtonStyle
from disnake.ui import Button
from utils.emojis import Emojis


class PreviousPageButton(Button):
    def __init__(self, disabled: bool = False):
        super().__init__(
            style=ButtonStyle.green,
            label="Previous Page",
            custom_id="CommunityServerPreviousPageButton",
            emoji=Emojis.Stratagems.left,
            disabled=disabled,
        )
