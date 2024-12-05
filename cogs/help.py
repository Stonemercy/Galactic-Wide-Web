from disnake import AppCmdInter, ButtonStyle
from disnake.ext import commands
from disnake.ui import Button
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.embeds import HelpEmbed


class HelpCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    async def help_autocomp(inter: AppCmdInter, user_input: str):
        commands_list = [i.name for i in inter.bot.global_slash_commands]
        commands_list.insert(0, "all")
        return [command for command in commands_list if user_input in command.lower()][
            :25
        ]

    @wait_for_startup()
    @commands.slash_command(
        description='Get some help for a specific command, or a list of every command by using "all".'
    )
    async def help(
        self,
        inter: AppCmdInter,
        command: str = commands.Param(
            autocomplete=help_autocomp,
            description='The command you want to lookup, use "all" for a list of all available commands',
        ),
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.info(
            f"{self.qualified_name}, /{inter.application_command.name} <{command = }>"
        )
        help_embed = HelpEmbed(
            commands=(
                self.bot.global_application_commands
                if inter.guild
                else [
                    command
                    for command in self.bot.global_slash_commands
                    if command.dm_permission
                ]
            ),
            command_name=command,
        )
        return await inter.send(
            embed=help_embed,
            ephemeral=True,
            components=[
                Button(
                    label="Support Server",
                    style=ButtonStyle.link,
                    url="https://discord.gg/Z8Ae5H5DjZ",
                )
            ],
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(HelpCog(bot))
