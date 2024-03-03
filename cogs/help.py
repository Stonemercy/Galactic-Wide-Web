from disnake import AppCmdInter
from disnake.ext import commands
from helpers.embeds import HelpEmbed


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Help cog has finished loading")

    async def help_autocomp(inter, user_input: str):
        commands_list = []
        for i in inter.bot.global_slash_commands:
            commands_list.append(i.name)
        commands_list.append("all")
        return [command for command in commands_list if user_input in command.lower()]

    @commands.slash_command(
        description="Get some help for a specific command, or a list of every command!"
    )
    async def help(
        self,
        inter: AppCmdInter,
        command: str = commands.Param(autocomplete=help_autocomp),
    ):
        await inter.response.defer()
        help_embed = HelpEmbed()
        if command == "all":
            for i in inter.bot.global_slash_commands:
                help_embed.add_field(i.name, i.description, inline=False)
            return await inter.send(embed=help_embed, ephemeral=True)
        else:
            for i in inter.bot.global_slash_commands:
                if i.name == command:
                    help_embed.add_field(i.name, i.description)
                    return await inter.send(embed=help_embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(HelpCog(bot))
