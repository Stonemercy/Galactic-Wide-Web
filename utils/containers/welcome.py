from disnake import ButtonStyle, Colour, Guild, MediaGalleryItem
from disnake.ui import (
    ActionRow,
    Button,
    Container,
    MediaGallery,
    Section,
    Separator,
    TextDisplay,
)
from utils.bot import GalacticWideWebBot
from utils.dataclasses import Factions
from utils.emojis import Emojis
from utils.interactables import SupportServerButton
from utils.functions import ordinal


class WelcomeContainer(Container):
    def __init__(self, guild: Guild, bot: GalacticWideWebBot):
        self.components = []
        self.components.append(
            MediaGallery(MediaGalleryItem("attachment://gww-banner.png"))
        )

        title_text = TextDisplay(
            f"# Welcome to the *Galactic Wide Web*! {Emojis.Icons.victory}"
            f"\n## You are the {ordinal(bot.guilds.index(guild) + 1)} server to join the GWW."
        )
        setup_seciton = Section(
            TextDisplay(
                "### Click this **setup** button to go straight to setting up your Dashboards and other features"
            ),
            accessory=Button(
                style=ButtonStyle.green,
                label="/setup",
                custom_id="welcome_setup_button",
            ),
        )
        help_section = Section(
            TextDisplay(
                "### ...or click this **help** button to see what other commands are available"
            ),
            accessory=Button(
                style=ButtonStyle.blurple,
                label="/help",
                custom_id="welcome_help_button",
            ),
        )
        self.components.extend(
            [
                title_text,
                Separator(),
                setup_seciton,
                Separator(),
                help_section,
                Separator(),
                ActionRow(SupportServerButton()),
            ]
        )

        super().__init__(
            *self.components,
            accent_colour=Colour.from_rgb(*Factions.humans.colour),
        )
