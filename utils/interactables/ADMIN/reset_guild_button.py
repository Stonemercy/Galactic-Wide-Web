from disnake import ButtonStyle
from disnake.ui import Button
from utils.emojis import Emojis


class ResetGuildButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.gray,
            label="Reset this guild",
            emoji=Emojis.Decoration.alert_icon,
            custom_id="reset_guild_button",
        )
