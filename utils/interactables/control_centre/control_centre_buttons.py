from enum import Enum
from disnake import ButtonStyle
from disnake.ui import Button
from utils.emojis import Emojis


class OverviewButton(Button):
    def __init__(self, is_active: bool):
        super().__init__(
            style=ButtonStyle.gray if not is_active else ButtonStyle.green,
            label="Overview",
            custom_id="overview_button",
            emoji=Emojis.ControlCentre.overview,
            disabled=is_active,
        )


class ActiveCampaignButton(Button):
    def __init__(self, is_active: bool):
        super().__init__(
            style=ButtonStyle.gray if not is_active else ButtonStyle.green,
            label="Active Campaign",
            custom_id="active_campaign_button",
            emoji=Emojis.ControlCentre.active_campaigns,
            disabled=is_active,
        )


class PastCampaignsButton(Button):
    def __init__(self, is_active: bool):
        super().__init__(
            style=ButtonStyle.gray if not is_active else ButtonStyle.green,
            label="Past Campaigns",
            custom_id="past_campaigns_button",
            emoji=Emojis.ControlCentre.past_campaigns,
            disabled=is_active,
        )


class ControlCenterArchivePageButtonType(Enum):
    PREV_PAGE = 0
    NEXT_PAGE = 1


class ArchivePageButton(Button):
    def __init__(
        self,
        button_type: ControlCenterArchivePageButtonType,
        page_number: int,
        disabled: bool,
    ):
        super().__init__(
            style=ButtonStyle.primary if not disabled else ButtonStyle.secondary,
            label=f"Page {page_number}" if not disabled else "",
            custom_id=f"control_centre_past_campaigns_page_{page_number}",
            emoji=(
                Emojis.Stratagems.left
                if button_type == ControlCenterArchivePageButtonType.PREV_PAGE
                else Emojis.Stratagems.right
            ),
            disabled=disabled,
        )
