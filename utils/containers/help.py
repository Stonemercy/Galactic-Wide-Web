from disnake import APISlashCommand, Colour, ui, OptionType
from disnake.ext.commands.slash_core import InvokableSlashCommand
from utils.interactables.support_server_button import SupportServerButton
from utils.mixins import ReprMixin


# DOESNT NEED LOCALIZATION (YET)
class HelpContainer(ui.Container, ReprMixin):
    def __init__(
        self,
        commands: list[APISlashCommand] = None,
        command: InvokableSlashCommand = None,
    ):
        components = []
        if commands:
            for global_command in sorted(
                (cmd for cmd in commands if cmd.name not in ("global_event", "gwe")),
                key=lambda cmd: cmd.name,
            ):

                options = "*Options:*\n" if global_command.options != [] else ""
                for option in global_command.options:
                    if option.type == OptionType.sub_command:
                        options += f"- </{global_command.name} {option.name}:{global_command.id}>\n"
                        for sub_option in option.options:
                            options += f" - **`{sub_option.name}`**: `{sub_option.type.name}` {'**[Required]**' if sub_option.required else '**<Optional>**'}- {sub_option.description} \n"
                    else:
                        options += f"- **`{option.name}`**: `{option.type.name}` {'**[Required]**' if option.required else '**<Optional>**'} - {option.description}\n"
                components.extend(
                    [
                        ui.TextDisplay(
                            f"## </{global_command.name}:{global_command.id}>\n-# {global_command.description}\n{options}"
                        ),
                        ui.Separator(),
                    ]
                )
        elif command:
            options = "" if command.options == [] else "**Options:**\n"
            for option in command.options:
                if option.type == OptionType.sub_command:
                    options += f"- /{command.name} {option.name}\n"
                    for sub_option in option.options:
                        options += f" - **`{sub_option.name}`** {'**[Required]**' if sub_option.required else '**<Optional>**'}- {sub_option.description}\n"
                else:
                    options += f"- **`{option.name}`** {'**[Required]**' if option.required else '**<Optional>**'} - {option.description}\n"
            components.append(
                ui.TextDisplay(
                    f"# /{command.name}\n{command.extras['long_description']}\n\n{options}\n**Example usage:**\n- {command.extras['example_usage']}"
                )
            )

        components.append(ui.ActionRow(SupportServerButton()))

        super().__init__(*components, accent_colour=Colour.green())
