from disnake import APISlashCommand, SelectOption
from disnake.ui import StringSelect

PRIVATE_COMMANDS = ("global_event", "gwe", "pmajor_order", "items")


class HelpStringSelect(StringSelect):
    def __init__(self, commands: list[APISlashCommand]):
        super().__init__(
            placeholder="Choose Command",
            min_values=1,
            max_values=1,
            options=[
                SelectOption(
                    label=f"/{command.name}",
                    description=command.description,
                    value=command.name,
                )
                for command in sorted(commands[-25:], key=lambda x: x.name)
                if command.name not in PRIVATE_COMMANDS
            ],
            custom_id="help",
        )
