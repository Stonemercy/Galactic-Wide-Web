from data.lists import CUSTOM_COLOURS
from disnake import Colour, ui
from utils.interactables.wiki_button import WikiButton
from utils.mixins import ReprMixin


class MOUnavailableContainer(ui.Container, ReprMixin):
    def __init__(self):
        section = ui.Section(
            ui.TextDisplay(
                f"# Awaiting Major Order\nStand by for further orders from Super Earth High Command"
            ),
            accessory=ui.Thumbnail(
                "https://cdn.discordapp.com/attachments/1212735927223590974/1424515626277277786/0x4557f77a0c886e64.png?ex=68e43b0f&is=68e2e98f&hm=0e06e7be7daa3d870746974bfe329ac8ac1a7917a28c96d6f6140002fb9190bf&"
            ),
        )

        super().__init__(
            section,
            ui.ActionRow(
                WikiButton(link=f"https://helldivers.wiki.gg/wiki/Major_Orders#Recent")
            ),
            accent_colour=Colour.from_rgb(*CUSTOM_COLOURS["MO"]),
        )
