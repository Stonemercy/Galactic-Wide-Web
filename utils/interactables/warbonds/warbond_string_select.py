from disnake import SelectOption
from disnake.ui import StringSelect
from utils.api_wrapper.models import Warbond


class WarbondsStringSelect(StringSelect):
    def __init__(self, warbonds: list[Warbond]):
        super().__init__(
            placeholder="Choose Warbond",
            min_values=1,
            max_values=1,
            options=[
                SelectOption(
                    label=warbond.name,
                    value=warbond.id,
                    description=f"{len(warbond.pages)} Pages - {len([i for p in warbond.pages for i in p.items])} items - total cost {sum([i.cost for p in warbond.pages for i in p.items])} Medals",
                )
                for warbond in warbonds[:25]
            ],
            custom_id="warbond_dropdown",
        )
