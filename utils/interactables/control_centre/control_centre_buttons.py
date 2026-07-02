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
