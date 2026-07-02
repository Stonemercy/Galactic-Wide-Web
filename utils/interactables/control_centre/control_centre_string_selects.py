from disnake import SelectOption
from disnake.ui import StringSelect
from utils.api_wrapper.models import ControlCentre
from utils.dataclasses.enums import ControlCentreStatus

EMOJIS_DICT = {
    ControlCentreStatus.InProgress: "🟡",
    ControlCentreStatus.Success: "✅",
    ControlCentreStatus.Failed: "❌",
}


class ControlCentreActiveCampaignsStringSelect(StringSelect):
    def __init__(self, episode_id: int, phases: list[ControlCentre.Episode.Phase]):
        options = [
            SelectOption(
                label=f"{phase.intro_title} - {index}/{len(phases)}",
                value=phase.id,
                emoji=EMOJIS_DICT.get(phase.status, "❔"),
            )
            for index, phase in enumerate(phases, start=1)
        ]
        super().__init__(
            placeholder="Choose Major Order",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"cc_active_campaigns_dropdown_{episode_id}",
        )
