from disnake import SelectOption
from disnake.ui import StringSelect
from utils.api_wrapper.models import Dispatch


class DispatchStringSelect(StringSelect):
    def __init__(self, dispatches: list[Dispatch]):
        super().__init__(
            placeholder="Choose Dispatch",
            min_values=1,
            max_values=1,
            options=[
                SelectOption(
                    label=(
                        dispatch.title[:100] if dispatch.title else "Untitled dispatch"
                    ),
                    description=(dispatch.description.replace("*", "")[:95] + "..."),
                    value=dispatch.id,
                )
                for dispatch in sorted(
                    dispatches[-25:], key=lambda x: x.id, reverse=True
                )
            ],
            custom_id="dispatch",
        )
