from utils.api_wrapper.models import EndpointItem
from utils.dataclasses.enums import ItemCategory

WARBOND_NAMES: dict[int, str] = {
    1929468580: "HELLDIVERS MOBILIZE",
    610512218: "STEELED VETERANS",
    19991972: "CUTTING EDGE",
    3361652624: "DEMOCRATIC DETONATION",
    2771132378: "POLAR PATRIOTS",
    1817825735: "VIPER COMMANDOS",
    1227305489: "FREEDOM'S FLAME",
    4150031036: "CHEMICAL AGENTS",
    2597223066: "TRUTH ENFORCERS",
    1960598782: "URBAN LEGENDS",
    1183163392: "SERVANTS OF FREEDOM",
    1941379384: "BORDERLINE JUSTICE",
    3301315302: "MASTERS OF CEREMONY",
    896747512: "FORCE OF LAW",
    1518605421: "CONTROL GROUP",
    1859364959: "OBEDIENT DEMOCRACY SUPPORT TROOPERS",
    1579552700: "DUST DEVILS",
    593507300: "PYTHON COMMANDOS",
    2248848355: "RIGHTEOUS REVENANTS",
    1452732551: "REDACTED REGIMENT",
    1193171589: "SIEGE BREAKERS",
    3978214801: "ENTRENCHED DIVISION",
    4228295283: "EXO EXPERTS",
    3224975204: "CASTELLAN'S CREED",
}


class Warbond:
    def __init__(self, items_list: list[EndpointItem], raw_warbond_data: dict) -> None:
        self._raw_warbond_data: dict = raw_warbond_data
        self.id: int | None = raw_warbond_data.get("id32")
        self.page_requirements: list[int] = raw_warbond_data.get("pageRequirements", [])
        self.total_cost: int | None = raw_warbond_data.get("totalCost")
        self.name: str = WARBOND_NAMES.get(self.id, f"UNKNOWN WARBOND {self.id}")
        self.pages: list[Warbond.Page] = [
            Warbond.Page(items_list, p)
            for p in raw_warbond_data.get("seasonPassPages", [])
        ]

    class Page:
        def __init__(self, items_list: list[EndpointItem], raw_page_data: dict) -> None:
            self.items: list[Warbond.Item] = [
                Warbond.Item(items_list, i)
                for i in raw_page_data.get("seasonPassItems", [])
            ]

    class Item:
        def __init__(
            self,
            endpoint_items: list[EndpointItem],
            raw_item_data: dict,
        ) -> None:
            self.is_premium: bool = raw_item_data.get("isPremium")
            self.is_repeatable: bool = raw_item_data.get("isRepeatable")
            self.mix_id: int = raw_item_data.get("itemMixId")
            self.cost: int = raw_item_data.get("medalCost")
            self.endpoint_item: EndpointItem | None = next(
                (
                    i
                    for i in endpoint_items
                    if i.parent_id == self.mix_id
                    or i.mix_id == self.mix_id
                    or i.item_id == self.mix_id
                ),
                None,
            )
            if self.endpoint_item.category == ItemCategory.STRATAGEM:
                self.endpoint_item = next(
                    (i for i in endpoint_items if i.parent_id == self.mix_id), None
                )
            self.name = (
                self.endpoint_item.mix_name
                or self.endpoint_item.item_name
                or self.endpoint_item.parent_name
                or f"Unknown item {self.mix_id}"
            ).upper()

        def __repr__(self):
            return f"WarbondItem(name={self.name}, id={self.mix_id})"

        def __eq__(self, value):
            if not isinstance(value, type(self)):
                return False
            return self.mix_id == value.mix_id
