from disnake import AppCmdInter, InteractionContextTypes, ApplicationInstallTypes
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.embeds.command_embeds import HelpCommandEmbed
from utils.interactables import SupportServerButton


class HelpCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    async def help_autocomp(inter: AppCmdInter, user_input: str):
        commands_list = [i.name for i in inter.bot.global_slash_commands]
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
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.info(
            f"{self.qualified_name}, /{inter.application_command.name} <{command = }>"
        )
        commands_list = (
            self.bot.global_application_commands
            if inter.guild
            else [
                command
                for command in self.bot.global_slash_commands
                if command.contexts.private_channel
            ]
        )
        if command not in [command.name for command in commands_list] and not "all":
            return await inter.send(
                "That command was not found, please select from the list.",
                ephemeral=True,
            )
        return await inter.send(
            embed=HelpCommandEmbed(
                commands=commands_list,
                command_name=command,
            ),
            ephemeral=public != "Yes",
            components=[SupportServerButton()],
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(HelpCog(bot))
