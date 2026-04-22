from datetime import datetime
from utils.mixins import ReprMixin


class Superstore(ReprMixin):
    __slots__ = ("expire_time", "sections")

    def __init__(self, raw_superstore_data: dict, items_json: dict) -> None:
        """Organised data for the Super Store"""
        self.expire_time: datetime = datetime.fromtimestamp(
            raw_superstore_data["expireTime"]
        )
        sales_page = raw_superstore_data.get("salesPage", {})
        sections = sales_page.get("sections", [])

        self.sections: list[Superstore.Section] = []
        for section in sections:
            self.sections.append(Superstore.Section(section, items_json))

    class Section(ReprMixin):
        __slots__ = ("items",)

        def __init__(self, raw_section_data: dict, items_json: dict) -> None:
            self.items: list[Superstore.Section.Item] = []
            items = raw_section_data.get("items", [])
            for i in items:
                self.items.append(Superstore.Section.Item(i, items_json))

            for i in self.items:
                if not i.name:
                    if cape := next(
                        (j for j in self.items.copy() if j.type == "Cape"), None
                    ):
                        i.name = cape.name
                        i.cost = 20
                        i.type = "Player Card"

        class Item(ReprMixin):
            __slots__ = ("id", "name", "description", "type", "cost")

            def __init__(self, raw_item_data: dict, items_json: dict):
                self.id = raw_item_data.get("mixId")
                json_entry: dict = items_json.get(str(self.id), {})
                self.name: str = json_entry.get("name", "")
                self.description: str = json_entry.get("description", "")
                self.type: str = json_entry.get("type", "")
                self.cost: int = json_entry.get("cost")
