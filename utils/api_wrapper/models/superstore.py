from utils.api_wrapper.models import EndpointItem

SUPERSTORE_PAGE_NAMES = {
    283249225: "EXO EXPERTS",
    2614924774: "ENTRENCHED DIVISION",
    1669601065: "REDACTED REGIMENT",
    368843305: "PYTHON COMMANDOS",
    2183776237: "DUST DEVILS",
    3258839403: "FORCE OF LAW",
    1887517525: "CONTROL GROUP",
    2229425093: "MASTER OF CEREMONY",
    2169126685: "WAR HORSES",
    975650208: "BORDERLINE JUSTICE",
    2667798286: "SERVANTS OF FREEDOM",
    379435112: "URBAN LEGENDS",
    4148719263: "TRUTH ENFORCERS",
    1182958572: "CHEMICAL AGENTS",
    730644756: "FREEDOM'S FLAME",
    1286827538: "VIPER COMMANDOS",
    713525279: "POLAR PATRIOTS",
    3374923807: "DEMOCRATIC DETONATION",
    3681137759: "CUTTING EDGE",
    381110565: "STEELED VETERANS",
    3617744789: "STEELED VETERANS",
    2839523111: "STEELED VETERANS",
    95603839: "STEELED VETERANS",
    1714427655: "HELLDIVERS MOBILIZE",
    913805677: "HELLDIVERS MOBILIZE",
    820483819: "HELLDIVERS MOBILIZE",
}


class Superstore:
    def __init__(
        self,
        raw_superstore_data: dict,
        items_json: dict,
        endpoint_items: list[EndpointItem],
    ) -> None:
        self.pages: list[Superstore.Page] = []
        self.pages = [
            Superstore.Page(
                raw_page_dict=page, endpoint_items=endpoint_items, items_json=items_json
            )
            for page in raw_superstore_data
        ]

    def get_page(self, page_id: int):
        return next((p for p in self.pages if p.id == page_id), None)

    class Page:
        def __init__(
            self,
            raw_page_dict: dict,
            endpoint_items: list[EndpointItem],
            items_json: dict,
        ):
            self.page_json = raw_page_dict
            self.id: int = raw_page_dict.get("id32", 0)
            self.name: str = SUPERSTORE_PAGE_NAMES.get(
                self.id, f"UNKNOWN SUPERSTORE PAGE #{self.id}"
            )
            self.banner_image_id: int = raw_page_dict.get("bannerId32", 0)
            self.items: list[Superstore.Item] = []

            for i in raw_page_dict.get("items", []):
                endpoint_item = next(
                    (
                        j
                        for j in endpoint_items
                        if (j.parent_id and j.parent_id == i["mixId"])
                        or j.mix_id == i["mixId"]
                        or j.item_id == i["mixId"]
                    ),
                    None,
                )
                self.items.append(Superstore.Item(i, items_json, endpoint_item))
                for i in self.items:
                    if i.type == "Player Card":
                        if (
                            cape := next(
                                (j for j in self.items if j.type == "Cape"), None
                            )
                        ) is not None:
                            i.name = cape.name
                            i.description = cape.description

        def __repr__(self):
            return (
                f"Page(\n    id={self.id}"
                f"\n    name={self.name}"
                f"\n    banner_id={self.banner_image_id}"
                f"\n    items={self.items}"
                "\n)"
            )

    class Item:
        def __init__(
            self,
            raw_item_data: dict,
            items_json: dict,
            endpoint_item: EndpointItem | None,
        ):
            self.id = raw_item_data.get("itemMixId")
            if endpoint_item is not None:
                self.id = endpoint_item.mix_id
            self.json_entry: dict = items_json.get(str(self.id or 0), {})
            self.name: str = self.json_entry.get("name", "Unknown Item")
            self.description: str = self.json_entry.get(
                "description",
                "This item has not been confirmed by GWW yet. Please stand by.",
            )
            self.type: str = self.json_entry.get("type", "Unknown")
            self.cost: int = self.json_entry.get("cost", 0)
            if endpoint_item is not None:
                if self.type == "Unknown":
                    self.type = endpoint_item.category.name.replace("_", " ").title()
                if endpoint_item.buy_price != []:
                    self.cost = endpoint_item.buy_price[0]["amount"]

        def __repr__(self):
            return (
                f"Item(\n    id={self.id}"
                f"\n    name={self.name}"
                f"\n    descriptionn={self.description}"
                f"\n    type={self.type}"
                f"\n    cost={self.cost}"
                "\n)"
            )
