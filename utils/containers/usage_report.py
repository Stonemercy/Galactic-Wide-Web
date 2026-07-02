from disnake import Colour
from disnake.ui import Container, Section, Separator, TextDisplay, Thumbnail


class UsageContainer(Container):
    def __init__(self, usage_dict: dict[str, dict[str, int]], guilds_joined: int):
        self.components = []

        for category, _usage_dict in usage_dict.items():
            if not _usage_dict:
                continue
            component = TextDisplay(f"# {category.title()} Usage")
            for i, usage in sorted(
                _usage_dict.items(), key=lambda x: x[1], reverse=True
            ):
                component.content += f"\n-# {i} - **{usage}**"
            self.components.extend([component, Separator()])

        self.components.append(
            Section(
                TextDisplay(f"Guilds Joined: **{guilds_joined}**"),
                accessory=Thumbnail(
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
