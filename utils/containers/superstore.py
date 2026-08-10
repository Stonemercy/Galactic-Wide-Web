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
from utils.interactables import WikiButton, SuperstoreStringSelect
from utils.mixins import ReprMixin


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
            self.components.append(
                Section(
                    TextDisplay(
                        f"### {i.name} - **{i.cost}**{Emojis.Items.super_credit}"
                        f"\n-# {getattr(Emojis.Items, i.type.replace(' ', '_').lower(), '')} **{i.type}**"
                        f"\n{'-# ' + i.description if i.description else ''}"
                    ),
                    accessory=WikiButton(
                        link=f"https://helldivers.wiki.gg/wiki/Special:Search?search={i.name.replace(' ', '_')}"
                    ),
                )
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
        self.components.extend([ActionRow(SuperstoreStringSelect(superstore.pages))])
        super().__init__(*self.components, accent_colour=Colour.blue())
