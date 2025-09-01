from disnake import APISlashCommand, Colour, Embed, OptionType
from disnake.ext.commands.slash_core import InvokableSlashCommand
from utils.mixins import EmbedReprMixin


class HelpEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        commands: list[APISlashCommand] = None,
        command: InvokableSlashCommand = None,
    ):
        super().__init__(colour=Colour.green(), title="Help")
        if commands:
            for global_command in sorted(commands, key=lambda cmd: cmd.name):
                options = "*Options:*\n" if global_command.options != [] else ""
                for option in global_command.options:
                    if option.type == OptionType.sub_command:
                        options += f"- </{global_command.name} {option.name}:{global_command.id}>\n"
                        for sub_option in option.options:
                            options += f" - **`{sub_option.name}`**: `{sub_option.type.name}` {'**[Required]**' if sub_option.required else '**<Optional>**'}- {sub_option.description} \n"
                    else:
                        options += f"- **`{option.name}`**: `{option.type.name}` {'**[Required]**' if option.required else '**<Optional>**'} - {option.description}\n"
                self.add_field(
                    f"</{global_command.name}:{global_command.id}>",
                    (f"-# {global_command.description}\n" f"{options}\n"),
                    inline=False,
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
            self.add_field(
                f"/{command.name}",
                (
                    f"{command.extras['long_description']}\n\n"
                    f"{options}"
                    f"**Example usage:**\n- {command.extras['example_usage']}\n"
                ),
                inline=False,
            )
