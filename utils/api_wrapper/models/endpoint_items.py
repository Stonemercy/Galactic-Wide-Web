from data.lists import STRATAGEM_ID_DICT
from utils.dataclasses.enums import ItemCategory

WEAPON_CATEGORY_REPLACEMENTS = {
    "Primary Weapon": ItemCategory.PRIMARY_WEAPON,
    "Throwable Weapon": ItemCategory.THROWABLE_WEAPON,
    "Sidearm Weapon": ItemCategory.SIDEARM_WEAPON,
}


class EndpointItem:
    def __init__(self, raw_endpoint_item_data: dict, json_dict: dict):
        self._json = raw_endpoint_item_data
        self.item_id: int = self._json.get("itemId", 0)
        self.item_name: str | None = (
            STRATAGEM_ID_DICT.get(self.item_id)
            or json_dict["strings"].get(str(self.item_id))
            or json_dict["items"]["items"].get(str(self.item_id), {}).get("name")
            or json_dict["items"]["boosters"].get(str(self.item_id), {}).get("name")
            or json_dict["items"]["vehicle_skins"].get(str(self.item_id))
            or json_dict["items"]["player_cards"].get(str(self.item_id))
            or json_dict["items"]["rewards"].get(str(self.item_id))
        )
        self.mix_id: int = self._json.get("mixId", 0)
        self.mix_name: str | None = (
            STRATAGEM_ID_DICT.get(self.mix_id)
            or json_dict["strings"].get(str(self.mix_id))
            or json_dict["items"]["items"].get(str(self.mix_id), {}).get("name")
            or json_dict["items"]["boosters"].get(str(self.mix_id), {}).get("name")
            or json_dict["items"]["vehicle_skins"].get(str(self.mix_id))
            or json_dict["items"]["player_cards"].get(str(self.item_id))
            or json_dict["items"]["rewards"].get(str(self.mix_id))
        )
        self.parent_id: int | None = self._json.get("parentId")
        self.parent_item: EndpointItem | None = None
        self.child_item: EndpointItem | None = None
        self.is_consumable: bool = self._json.get("mixId", 0)
        self._category: int = self._json.get("progressionCategory", 0)
        self.category: ItemCategory = ItemCategory(self._category)
        if self.category == ItemCategory.WEAPON:
            self.category = WEAPON_CATEGORY_REPLACEMENTS.get(
                json_dict["items"]["items"].get(str(self.mix_id), {}).get("type"),
                self.category,
            )
        self.tags: list = self._json.get("tags", [])
        self.required_items: list = self._json.get("requiredItems", [])
        self.buy_price: list = self._json.get("buyPrice", [])
        self.sell_price: list = self._json.get("sellPrice", [])

    @property
    def parent_name(self):
        return (
            (self.parent_item.mix_name or self.parent_item.item_name)
            if self.parent_item is not None
            else None
        )

    @property
    def child_name(self):
        return (
            (self.child_item.mix_name or self.child_item.item_name)
            if self.child_item is not None
            else None
        )

    @property
    def child_id(self):
        return (self.child_item.mix_id) if self.child_item is not None else None

    @property
    def name(self):
        return self.mix_name or self.item_name or self.child_name or self.parent_name

    def __str__(self):
        fmt_text = "".join(
            [
                f"\n    {k} = {v}"
                for k, v in self.__dict__.items()
                if not k.startswith("_") and "child" not in k and "parent" not in k
            ]
            + [
                f"\n    parent_id = {self.parent_id}",
                f"\n    parent_name = {self.parent_name}",
                f"\n    child_id = {self.child_id}",
                f"\n    child_name = {self.child_name}",
            ]
        )
        return f"EndpointItem({fmt_text}\n)"

    def __repr__(self):
        return f"EndpointItem({self._json})"

    def __eq__(self, value):
        if not isinstance(value, type(self)):
            return False
        return self.mix_id == value.mix_id

    def __hash__(self):
        return hash((self.mix_id))
