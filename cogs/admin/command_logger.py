from datetime import time
from disnake import AppCmdInter
from disnake.ext import commands, tasks
from utils.bot import GalacticWideWebBot
from utils.embeds import CommandUsageEmbed


class CommandLoggerCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.command_report.start()

    def cog_unload(self):
        self.command_report.stop()

    @commands.Cog.listener()
    async def on_slash_command(self, inter: AppCmdInter):
        if inter.application_command.name not in self.bot.command_usage:
            self.bot.command_usage[inter.application_command.name] = 0
        self.bot.command_usage[inter.application_command.name] += 1

    @tasks.loop(time=time(hour=22, minute=0, second=0))
    async def command_report(self):
        if self.bot.command_usage == {}:
            return
        embed = CommandUsageEmbed(self.bot.command_usage)
        await self.bot.moderator_channel.send(embed=embed)
        self.bot.command_usage.clear()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(CommandLoggerCog(bot))
