from disnake import AppCmdInter, ApplicationInstallTypes, InteractionContextTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.containers import HelpContainer
from utils.checks import wait_for_startup


class HelpCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    async def help_autocomp(inter: AppCmdInter, user_input: str) -> list[str]:
        if not inter.bot.global_slash_commands:
            return []
        commands_list = ["all"] + sorted(
            [
                i.name
                for i in inter.bot.global_slash_commands
                if i.name not in ["gwe", "global_event"]
            ]
        )
        return [
            command
            for command in commands_list
            if user_input.lower() in command.lower()
        ][:25]

    @wait_for_startup()
    @commands.slash_command(
        description='Get some help for a specific command, or a list of every command by using "all".',
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Get some help for a specific command or all commands. You can obtain longer descriptions and examples when you lookup a specific command.",
            "example_usage": "**`/help command:Automatons public:Yes`** would return an embed with useful information about the Automatons command including example usage that other members in the server can see.",
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
            slash_commands = (
                self.bot.global_application_commands
                if inter.guild
                else [
                    command
                    for command in self.bot.global_slash_commands
                    if command.contexts and command.contexts.private_channel
                ]
            )

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
