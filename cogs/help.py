from logging import getLogger
from disnake import AppCmdInter
from disnake.ext import commands
from helpers.embeds import HelpEmbed

logger = getLogger("disnake")


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def help_autocomp(inter: AppCmdInter, user_input: str):
        commands_list: list[str] = []
        for i in inter.bot.global_slash_commands:
            commands_list.append(i.name)
        commands_list.append("all")
        return [command for command in commands_list if user_input in command.lower()]

    @commands.slash_command(
        description='Get some help for a specific command, or a list of every command by using "all".'
    )
    async def help(
        self,
        inter: AppCmdInter,
        command: str = commands.Param(autocomplete=help_autocomp),
    ):
        logger.info("help command used")
        await inter.response.defer(ephemeral=True)
        help_embed = HelpEmbed()
        if command == "all":
            for i in inter.bot.global_slash_commands:
                help_embed.add_field(f"/{i.name}", i.description, inline=False)
            return await inter.send(embed=help_embed, ephemeral=True)
        else:
            command_help = list(
                filter(
                    lambda cmd: cmd.name == command,
                    self.bot.global_application_commands,
                )
            )[0]
            help_embed.add_field(command_help.name, command_help.description)
            return await inter.send(embed=help_embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(HelpCog(bot))
