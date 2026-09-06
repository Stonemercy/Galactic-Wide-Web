from disnake import APISlashCommand, Colour, OptionType
from disnake.ui import ActionRow, Container, TextDisplay
from utils.interactables import (
    GuildInstallButton,
    HelpStringSelect,
    SupportServerButton,
    UserInstallButton,
)


# DOESNT NEED LOCALIZATION (YET)
class HelpContainer(Container):
    def __init__(self, command: APISlashCommand, commands: list):
        components = []
        options = "" if command.options == [] else "**Options:**\n"
        for option in command.options:
            if option.type == OptionType.sub_command:
                options += f"- /{command.name} {option.name}\n"
                for sub_option in option.options:
                    options += f" - **`{sub_option.name}`** {'**[Required]**' if sub_option.required else '**<Optional>**'}- {sub_option.description}\n"
            else:
                options += f"- **`{option.name}`** {'**[Required]**' if option.required else '**<Optional>**'} - {option.description}\n"
        components.append(
            TextDisplay(
                f"# </{command.name}:{command.id}>\n-# {command.description}\n{options}"
            )
        )

        components.extend(
            [
                ActionRow(HelpStringSelect(commands=commands)),
                ActionRow(
                    SupportServerButton(), GuildInstallButton(), UserInstallButton()
                ),
            ]
        )

        super().__init__(*components, accent_colour=Colour.green())
