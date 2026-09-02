from enum import Enum
from disnake import ButtonStyle
from disnake.ui import Button
from utils.emojis import Emojis


class WarbondButtonType(Enum):
    PREV_PAGE = 0
    NEXT_PAGE = 1


class WarbondPageButton(Button):
    def __init__(
        self,
        button_type: WarbondButtonType,
        warbond_id: int,
        page_number: int,
        disabled: bool = False,
    ):
        super().__init__(
            disabled=disabled,
            style=ButtonStyle.primary if not disabled else ButtonStyle.secondary,
            label=f"Page {page_number + 1}" if not disabled else "",
            emoji=(
                Emojis.Stratagems.left
                if button_type == WarbondButtonType.PREV_PAGE
                else Emojis.Stratagems.right
            ),
            custom_id=f"warbonds_button_{warbond_id}_{page_number}",
        )
