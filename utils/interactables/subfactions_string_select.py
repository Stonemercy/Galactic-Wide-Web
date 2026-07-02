from disnake import SelectOption
from disnake.ui import StringSelect
from utils.api_wrapper.models import Planet
from utils.dataclasses import Factions, Subfactions


class SubfactionsStringSelect(StringSelect):
    def __init__(self, planets: dict[int, Planet]):
        options = sorted(
            [
                SelectOption(
                    label=f"{sf.eng_name.title()} - {len([p for p in planets.values() if sf in p.subfactions and (p.faction != Factions.humans or p.faction == Factions.humans and p.event)])} Planets",
                    emoji=sf.emoji,
                )
                for sf in Subfactions._all
            ],
            key=lambda x: int(
                x.label[-9]
            ),  # this needs updating if any subfactions ever appear on more than 9 planets
            reverse=True,
        )
        super().__init__(
            placeholder="Choose Subfaction",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="subfactions",
        )
