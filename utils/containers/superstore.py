from disnake import Colour, MediaGalleryItem
from disnake.ui import (
    ActionRow,
    Container,
    MediaGallery,
    Section,
    Separator,
    TextDisplay,
    Thumbnail,
)
from utils.api_wrapper.models import Superstore
from utils.emojis import Emojis
from utils.interactables import SuperstoreStringSelect
from utils.mixins import ReprMixin

DROPDOWN_TWO_PAGE_NAMES = [
    "HELLDIVERS MOBILIZE",
]


class SuperstoreContainer(Container, ReprMixin):
    def __init__(
        self, superstore: Superstore, usable_images: list[str], page_id: int = None
    ):
        self.components = []
        self.page = (
            superstore.pages[0] if page_id is None else superstore.get_page(page_id)
        )
        if f"{self.page.banner_image_id}.png" in usable_images:
            self.components.append(
                MediaGallery(
                    MediaGalleryItem(f"attachment://{self.page.banner_image_id}.png")
                )
            )
        sorted_items = sorted(self.page.items, key=lambda x: x.name)
        for i in sorted_items:
            item_link = f"https://helldivers.wiki.gg/wiki/Special:Search?search={i.name.replace(' ', '_') if 'Unknown' not in i.name else 'Superstore'}"
            self.components.append(
                TextDisplay(
                    f"### [{i.name}](<{item_link}>) - **{i.cost}**{Emojis.Items.super_credit}"
                    f"\n-# {getattr(Emojis.Items, i.type.replace(' ', '_').lower(), '')} **{i.type}**"
                    f"\n{'-# ' + i.description if i.description else ''}"
                ),
            )
            if i.type == "Emote" and f"{i.id}.png" in usable_images:
                self.components.append(
                    Section(
                        Emojis.Icons.blank,
                        accessory=Thumbnail(f"attachment://{i.id}.png"),
                    )
                )
            if i.type == "Player Card" and f"{i.id}.png" in usable_images:
                self.components.append(
                    Section(
                        Emojis.Icons.blank,
                        accessory=Thumbnail(f"attachment://{i.id}.png"),
                    )
                )
            self.components.append(Separator())
        dropdown_one_pages = [
            p for p in superstore.pages if p.name not in DROPDOWN_TWO_PAGE_NAMES
        ]
        dropdown_two_pages = [
            p for p in superstore.pages if p.name in DROPDOWN_TWO_PAGE_NAMES
        ]
        self.components.extend(
            [
                ActionRow(
                    SuperstoreStringSelect(dropdown_one_pages, dropdown_num=1),
                ),
                ActionRow(
                    SuperstoreStringSelect(dropdown_two_pages, dropdown_num=2),
                ),
            ]
        )
        super().__init__(*self.components, accent_colour=Colour.blue())
