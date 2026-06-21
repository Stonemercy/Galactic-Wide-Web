from disnake import AppCmdInter, ApplicationInstallTypes, InteractionContextTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.containers import HelpContainer
from utils.checks import wait_for_startup

PRIVATE_COMMANDS = ("global_event", "gwe", "pmajor_order")


class HelpCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    async def help_autocomp(inter: AppCmdInter, user_input: str) -> list[str]:
        if not inter.bot.ready:
            return []
        return [
            command
            for command in ["all"]
            + sorted(
                [
                    i.name
                    for i in inter.bot.global_slash_commands
                    if i.name not in PRIVATE_COMMANDS
                ]
            )
            if user_input.lower() in command.lower()
        ][:25]

    @wait_for_startup()
    @commands.slash_command(
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
        command: str = commands.Param(
            autocomplete=help_autocomp,
            description='The command you want to lookup, use "all" for a list of all available commands',
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ) -> None:
        await inter.response.defer(ephemeral=public != "Yes")
        slash_commands = None
        slash_command = None
        if command != "all":
            slash_command = self.bot.get_slash_command(command)
        else:
            slash_commands = [
                c
                for c in self.bot.global_application_commands
                if c.name not in PRIVATE_COMMANDS
            ]

        if not slash_command and not slash_commands:
            await inter.send(
                "That command was not found, please select from the list.",
                ephemeral=True,
            )
        else:
            await inter.send(
                components=HelpContainer(
                    commands=slash_commands,
                    command=slash_command,
                ),
                ephemeral=public != "Yes",
            )


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(HelpCog(bot))
