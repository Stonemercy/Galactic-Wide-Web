from disnake import ButtonStyle, Colour, MediaGalleryItem, ui
from data.lists import CUSTOM_COLOURS
from utils.dataclasses import RandomiserData
from utils.emojis import Emojis
from utils.mixins import ReprMixin


class RandomiserContainer(ui.Container, ReprMixin):
    def __init__(self, randomiser_data: RandomiserData, limited: bool):
        """List-like class that organises the data provided into embeds"""
        self.randomiser_data = randomiser_data
        self.components = []
        self.add_primary_weapon()
        self.add_secondary_weapon()
        self.add_grenade()
        self.add_booster()
        self.add_stratagems()
        self.components.append(
            ui.ActionRow(
                ui.Button(
                    style=ButtonStyle.danger,
                    label="Re-roll",
                    custom_id=f"re_roll_randomiser{'_limited' if limited else ''}",
                )
            )
        )
        super().__init__(
            *self.components, accent_colour=Colour.from_rgb(*CUSTOM_COLOURS["MO"])
        )

    def add_primary_weapon(self):
        weapon_json = self.randomiser_data.primary_weapon
        media_gal = ui.MediaGallery(MediaGalleryItem(weapon_json["image_link"]))
        text_display = ui.TextDisplay(
            f"# {weapon_json['name']}\n-# {weapon_json['description']}"
        )
        self.components.extend([media_gal, text_display, ui.Separator()])

    def add_secondary_weapon(self):
        weapon_json = self.randomiser_data.secondary_weapon
        section = ui.Section(
            ui.TextDisplay(f"# {weapon_json['name']}\n-# {weapon_json['description']}"),
            accessory=ui.Thumbnail(weapon_json["image_link"]),
        )
        self.components.extend([section, ui.Separator()])

    def add_grenade(self):
        grenade_json = self.randomiser_data.grenade
        section = ui.Section(
            ui.TextDisplay(
                f"# {grenade_json['name']}\n-# {grenade_json['description']}"
            ),
            accessory=ui.Thumbnail(grenade_json["image_link"]),
        )
        self.components.extend([section, ui.Separator()])

    def add_booster(self):
        booster_json = self.randomiser_data.booster
        section = ui.Section(
            ui.TextDisplay(
                (
                    f"# {booster_json['name']}\n-# {booster_json['description']}\n\n\n-# ||Booster icons are broken currently, sorry :pensive:||"
                )
            ),
            accessory=ui.Thumbnail(booster_json["image_link"]),
        )
        self.components.extend([section, ui.Separator()])

    def add_stratagems(self):
        sections = []
        for strat_name, strat_info in self.randomiser_data.stratagems:
            if not strat_info["image_link"]:
                sections.append(ui.TextDisplay((f"# {strat_name}")))
            else:
                sections.append(
                    ui.Section(
                        ui.TextDisplay(
                            (f"# {strat_name}\n-# {strat_info['description']}")
                        ),
                        accessory=ui.Thumbnail(strat_info["image_link"]),
                    )
                )
        self.components.extend(sections + [ui.Separator()])
