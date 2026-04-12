from disnake import Colour, ui
from utils.api_wrapper.models import Superstore
from utils.emojis import Emojis
from utils.interactables import WikiButton
from utils.mixins import ReprMixin


class SuperstoreContainer(ui.Container, ReprMixin):
    def __init__(self, superstore: Superstore):
        self.components = []

        self.components.append(
            ui.TextDisplay(
                f"-# The Superstore refreshes <t:{int(superstore.expire_time.timestamp())}:R>"
            )
        )
        for section in superstore.sections:
            sorted_items = self.sort_items(section.items)
            for i in sorted_items:
                if not i.name:
                    continue
                else:
                    self.components.append(
                        ui.Section(
                            ui.TextDisplay(
                                f"### {i.name} - **{i.cost}**{Emojis.Items.super_credit}"
                                f"\n-# **{i.type}**"
                                f"\n{'-# ' + i.description if i.description else ''}"
                            ),
                            accessory=WikiButton(
                                link=f"https://helldivers.wiki.gg/wiki/{i.name.replace(' ', '_')}"
                            ),
                        )
                    )

        super().__init__(*self.components, accent_colour=Colour.blue())

    def sort_items(self, items: list[Superstore.Section.Item]):
        sorted_items: list[Superstore.Section.Item] = []
        sorted_items.extend([i for i in items if "weapon" in i.type.lower()])
        sorted_items.extend(
            [
                i
                for i in items
                if "armor" in i.type.lower() or "helmet" in i.type.lower()
            ]
        )
        sorted_items.extend([i for i in items if "cape" in i.type.lower()])
        sorted_items.extend([i for i in items if "player card" in i.type.lower()])
        sorted_items.extend([i for i in items if "emote" in i.type.lower()])
        return sorted_items
