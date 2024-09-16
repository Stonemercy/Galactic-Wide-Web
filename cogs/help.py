from data.lists import help_dict
from disnake import AppCmdInter, OptionType, ButtonStyle
from disnake.ext import commands
from disnake.ui import Button
from main import GalacticWideWebBot
from utils.embeds import HelpEmbed


class HelpCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    async def help_autocomp(inter: AppCmdInter, user_input: str):
        commands_list = [i.name for i in inter.bot.global_slash_commands]
        commands_list.append("all")
        return [command for command in commands_list if user_input in command.lower()][
            :25
        ]

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
        help_embed = HelpEmbed()
        if command == "all":
            for global_command in inter.bot.global_slash_commands:
                options = "Options:\n" if global_command.options != [] else ""
                for option in global_command.options:
                    if option.type == OptionType.sub_command:
                        options += f"- </{global_command.name} {option.name}:{global_command.id}>\n"
                        for sub_option in option.options:
                            options += f" - **`{sub_option.name}`**: `{sub_option.type.name}` {'[Required]' if sub_option.required else '<Optional>'}- {sub_option.description} \n"
                    else:
                        options += f"- **`{option.name}`**: `{option.type.name}` {'[Required]' if option.required else '<Optional>'} - {option.description}\n"
                help_embed.add_field(
                    f"</{global_command.name}:{global_command.id}>",
                    (f"{global_command.description}\n" f"{options}\n"),
                    inline=False,
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
        else:
            command_help = list(
                filter(
                    lambda cmd: cmd.name == command,
                    self.bot.global_application_commands,
                )
            )[0]
            options = "" if command_help.options == [] else "**Options:**\n"
            for option in command_help.options:
                if option.type == OptionType.sub_command:
                    options += (
                        f"- </{command_help.name} {option.name}:{command_help.id}>\n"
                    )
                    for sub_option in option.options:
                        options += f" - **`{sub_option.name}`** `{sub_option.type.name}` {'[Required]' if sub_option.required else '<Optional>'}- {sub_option.description} \n"
                else:
                    options += f"- **`{option.name}`**: `{option.type.name}` {'[Required]' if option.required else '<Optional>'} - {option.description}\n"
            help_embed.add_field(
                f"</{command_help.name}:{command_help.id}>",
                (
                    f"{help_dict[command]['long_description']}\n\n"
                    f"{options}"
                    f"**Example usage:**\n- {help_dict[command]['example_usage']}\n"
                ),
                inline=False,
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
