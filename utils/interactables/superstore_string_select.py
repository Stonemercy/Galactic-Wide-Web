from disnake import SelectOption
from disnake.ui import StringSelect
from utils.api_wrapper.models import Superstore


class SuperstoreStringSelect(StringSelect):
    def __init__(self, super_store_pages: list[Superstore.Page]):
        choices: list[SelectOption] = []
        for page in super_store_pages:
            choice_name = page.name
            if (
                amount := len([p for p in super_store_pages if p.name == page.name])
            ) > 1:
                number = len([c for c in choices if page.name in c.label]) + 1
                choice_name += f" {number}/{amount}"
            choice = SelectOption(
                label=choice_name,
                description=f"{len(page.items)} items - total cost: {sum(i.cost for i in page.items):,} SC",
                value=page.id,
            )
            choices.append(choice)
        super().__init__(
            placeholder="Choose Superstore Page",
            min_values=1,
            max_values=1,
            options=choices,
            custom_id="superstore_page",
        )
