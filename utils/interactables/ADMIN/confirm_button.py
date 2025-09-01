from disnake import ButtonStyle
from disnake.ui import Button
from utils.emojis import Emojis


class ConfirmButton(Button):
    def __init__(self, action_type: str, guild_name: str):
        super().__init__(
            style=ButtonStyle.red,
            label=f"Confirm {action_type} {guild_name}",
            emoji=Emojis.Decoration.alert_icon,
            custom_id=f"{action_type}_confirm_button",
        )
