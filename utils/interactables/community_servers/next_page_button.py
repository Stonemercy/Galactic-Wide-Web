from disnake import ButtonStyle
from disnake.ui import Button
from utils.emojis import Emojis


class NextPageButton(Button):
    def __init__(self, disabled: bool = False):
        super().__init__(
            style=ButtonStyle.green,
            label="Next Page",
            custom_id="CommunityServerNextPageButton",
            emoji=Emojis.Stratagems.right,
            disabled=disabled,
        )
