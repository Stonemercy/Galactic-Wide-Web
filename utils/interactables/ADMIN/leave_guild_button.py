from disnake import ButtonStyle
from disnake.ui import Button
from utils.emojis import Emojis


class LeaveGuildButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.red,
            label="LEAVE THIS GUILD",
            emoji=Emojis.Decoration.alert_icon,
            custom_id="leave_guild_button",
        )
