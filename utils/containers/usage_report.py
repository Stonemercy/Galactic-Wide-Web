from disnake import Colour, ui
from utils.mixins import ReprMixin


class UsageContainer(ui.Container, ReprMixin):
    def __init__(self, usage_dict: dict[str, dict[str, int]], guilds_joined: int):
        self.components = []

        for category, _usage_dict in usage_dict.items():
            if not _usage_dict:
                continue
            component = ui.TextDisplay(f"# {category.title()} Usage")
            for i, usage in _usage_dict.items():
                component.content += f"\n-# {i} - **{usage}**"
            self.components.extend([component, ui.Separator()])

        self.components.append(
            ui.Section(
                ui.TextDisplay(f"Guilds Joined: **{guilds_joined}**"),
                accessory=ui.Thumbnail(
                    "https://cdn.discordapp.com/emojis/1288680892516274196.webp?size=96"
                    if guilds_joined > 0
                    else "https://cdn.discordapp.com/emojis/1303048630583820342.webp?size=96"
                ),
            )
        )

        super().__init__(
            *self.components,
            accent_colour=(
                Colour.brand_green() if guilds_joined > 0 else Colour.brand_red()
            ),
        )
