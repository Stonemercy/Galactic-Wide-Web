from random import choice
from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    InteractionContextTypes,
    MessageInteraction,
)
from disnake.ext.commands import Cog, Param, slash_command
from utils.bot import GalacticWideWebBot
from utils.containers import HelpContainer
from utils.checks import wait_for_startup

PRIVATE_COMMANDS = ("global_event", "gwe", "pmajor_order", "items")


class HelpCog(Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    @wait_for_startup()
    @slash_command(
        description='Get help for a specific command, or use "all" for a full command list',
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": 'Shows a detailed description and example usage for a specific command. Use "all" to see a list of every available command. Autocomplete will suggest command names as you type.',
            "example_usage": "**`/help command:planet public:Yes`** returns a detailed description and example usage for the `/planet` command, visible to everyone.\n- **`/help command:all`** lists every available command.",
        },
    )
    async def help(
        self,
        inter: AppCmdInter,
        public: str = Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ) -> None:
        await inter.response.defer(ephemeral=public != "Yes")
        slash_command = choice(
            [
                c
                for c in self.bot.global_application_commands
                if c.name not in PRIVATE_COMMANDS
            ]
        )

        await inter.send(
            components=HelpContainer(
                command=slash_command, commands=self.bot.global_application_commands
            ),
            ephemeral=public != "Yes",
        )

    @Cog.listener("on_button_click")
    async def on_button_clicks(self, inter: MessageInteraction) -> None:
        if inter.component.custom_id != "welcome_help_button":
            return
        if not self.bot.ready:
            await self.bot.bot_not_ready(inter)
            return
        await inter.send(
            components=HelpContainer(
                commands=[
                    c
                    for c in self.bot.global_application_commands
                    if c.name not in PRIVATE_COMMANDS
                ],
            ),
            ephemeral=True,
        )

    @Cog.listener("on_dropdown")
    async def on_dropdowns(self, inter: MessageInteraction) -> None:
        if inter.component.custom_id != "help":
            return
        if inter.author != inter.message.interaction_metadata.user:
            await self.bot.not_interaction_author(inter)
            return
        if not self.bot.ready:
            await self.bot.bot_not_ready(inter)
            return

        command = next(
            (
                c
                for c in self.bot.global_application_commands
                if c.name == inter.values[0]
            ),
            None,
        )
        if command is None:
            print(inter.values)
            await inter.send(
                "That command wasn't found, please try again", ephemeral=True
            )
            return

        container = HelpContainer(
            command=command, commands=self.bot.global_application_commands
        )
        await inter.response.edit_message(components=container)


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(HelpCog(bot))
