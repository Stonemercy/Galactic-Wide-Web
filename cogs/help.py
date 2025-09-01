from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    InteractionContextTypes,
    InteractionTimedOut,
    NotFound,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.embeds import HelpEmbed
from utils.interactables import SupportServerButton


class HelpCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    async def help_autocomp(inter: AppCmdInter, user_input: str):
        commands_list = sorted([i.name for i in inter.bot.global_slash_commands])
        commands_list.insert(0, "all")
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
    ):
        try:
            await inter.response.defer(ephemeral=public != "Yes")
        except (NotFound, InteractionTimedOut):
            await inter.channel.send(
                "There was an error with that command, please try again.",
                delete_after=5,
            )
            return
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{command = }>"
        )
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
            return await inter.send(
                "That command was not found, please select from the list.",
                ephemeral=True,
            )
        await inter.send(
            embed=HelpEmbed(
                commands=slash_commands,
                command=slash_command,
            ),
            ephemeral=public != "Yes",
            components=[SupportServerButton()],
        )
        return


def setup(bot: GalacticWideWebBot):
    bot.add_cog(HelpCog(bot))
