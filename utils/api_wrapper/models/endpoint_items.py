from utils.dataclasses.enums import ItemCategory


class EndpointItem:
    def __init__(self, raw_endpoint_item_data: dict):
        self.item_id: int = raw_endpoint_item_data.get("itemId", 0)
        self.mix_id: int = raw_endpoint_item_data.get("mixId", 0)
        self.parent_id: int = raw_endpoint_item_data.get("parentId", 0)
        self.is_consumable: bool = raw_endpoint_item_data.get("mixId", 0)
        self._category: int = raw_endpoint_item_data.get("progressionCategory", 0)
        self.category: ItemCategory = ItemCategory(self._category)
        self.tags: list = raw_endpoint_item_data.get("tags", [])
        self.required_items: list = raw_endpoint_item_data.get("requiredItems", [])
        self.buy_price: list = raw_endpoint_item_data.get("buyPrice", [])
        self.sell_price: list = raw_endpoint_item_data.get("sellPrice", [])

    def __repr__(self):
        fmt_text = "".join([f"\n    {k} = {v}" for k, v in self.__dict__.items()])
        return f"EndpointItem({fmt_text}\n)"
