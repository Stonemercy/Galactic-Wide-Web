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
from utils.api_wrapper.models import Warbond
from utils.dataclasses.enums import ItemCategory
from utils.emojis import Emojis
from utils.interactables import WikiButton, WarbondsStringSelect, WarbondPageButton
from utils.interactables.warbonds.page_buttons import WarbondButtonType
from utils.mixins import ReprMixin


class WarbondsContainer(Container, ReprMixin):
    def __init__(
        self,
        warbonds: dict[int, Warbond],
        with_banner: bool,
        warbond_id: int = None,
        page_index: int = None,
    ):
        self.components = []
        warbond = (
            next((wb for wb in list(warbonds.values())[::-1]))
            if warbond_id is None
            else warbonds[warbond_id]
        )
        if with_banner:
            self.components.append(
                MediaGallery(MediaGalleryItem(f"attachment://{warbond.id}.png"))
            )
        page_index = page_index or 0
        page: Warbond.Page = warbond.pages[page_index]
        self.components.append(
            TextDisplay(
                f"# **{warbond.name}**\n## Page **{page_index + 1}/{len(warbond.pages)}**"
            )
        )
        for i in page.items:
            item_name = str(i.name)
            if i.endpoint_item.category == ItemCategory.PLAYER_CARD:
                cape = next(
                    (
                        ci
                        for ci in page.items
                        if ci.endpoint_item.category == ItemCategory.ARMOR
                        and len([di for di in page.items if di.name == ci.name]) == 1
                    ),
                    None,
                )
                if cape is not None:
                    item_name = cape.name

            item_type = i.endpoint_item.category.name.replace("_", " ").replace(
                "EFFECTID MIX ID", "PERMIT"
            )
            if (
                item_type == "ARMOR"
                and len([di for di in page.items if di.name == i.name]) == 1
            ):
                item_type = "CAPE"
            elif (
                item_type == "ARMOR"
                and len(
                    [di for di in page.items if di.name == i.name and di.cost > i.cost]
                )
                == 1
            ):
                item_type = "HELMET"
            if item_type != "SUPER CREDIT PACK":
                emoji_str = ""
                if (
                    available_emoji := getattr(
                        Emojis.Items, item_type.lower().replace(" ", "_"), None
                    )
                ) is not None:
                    emoji_str = f"{available_emoji} "
                self.components.append(
                    Section(
                        TextDisplay(
                            (
                                f"\n-# **{item_name}** - **{i.cost}**{Emojis.Items.medal}"
                                f"\n-# {emoji_str} {item_type}"
                            )
                        ),
                        accessory=WikiButton(
                            link=f"https://helldivers.wiki.gg/wiki/Special:Search?search={item_name.title().replace(' ', '_') if 'Unknown' not in i.name else 'Warbonds'}"
                        ),
                    )
                )
            else:
                self.components.append(
                    TextDisplay(
                        (
                            f"\n-# **{item_name}** - **{i.cost}**{Emojis.Items.medal}"
                            f"\n-# {Emojis.Items.super_credit} {item_type}"
                        )
                    )
                )
        self.components.extend(
            [
                ActionRow(
                    WarbondPageButton(
                        WarbondButtonType.PREV_PAGE,
                        warbond.id,
                        page_index - 1,
                        disabled=page_index - 1 < 0,
                    ),
                    WarbondPageButton(
                        WarbondButtonType.NEXT_PAGE,
                        warbond.id,
                        page_index + 1,
                        disabled=page_index + 2 > len(warbond.pages),
                    ),
                ),
                ActionRow(
                    WarbondsStringSelect(list(warbonds.values())),
                ),
            ]
        )
        super().__init__(*self.components, accent_colour=Colour.blue())
