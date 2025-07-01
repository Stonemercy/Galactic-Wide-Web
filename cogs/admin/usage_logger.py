from datetime import time
from disnake import AppCmdInter, Guild
from disnake.ext import commands, tasks
from utils.bot import GalacticWideWebBot
from utils.embeds.loop_embeds import UsageLoopEmbed


class UsageLoggerCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.guilds_joined = 0
        if not self.usage_report.is_running():
            self.usage_report.start()
            self.bot.loops.append(self.usage_report)

    def cog_unload(self):
        if self.usage_report.is_running():
            self.usage_report.stop()

    @commands.Cog.listener()
    async def on_slash_command(self, inter: AppCmdInter):
        if inter.application_command.name not in self.bot.command_usage:
            self.bot.command_usage[inter.application_command.name] = 0
        self.bot.command_usage[inter.application_command.name] += 1

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild):
        self.guilds_joined += 1

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        self.guilds_joined -= 1

    @tasks.loop(time=time(hour=21, minute=0, second=0))
    async def usage_report(self):
        if self.bot.command_usage == {}:
            return
        embed = UsageLoopEmbed(self.bot.command_usage, self.guilds_joined)
        await self.bot.moderator_channel.send(embed=embed)
        self.bot.command_usage.clear()
        self.guilds_joined = 0

    @usage_report.before_loop
    async def before_usage_report(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(cog=UsageLoggerCog(bot))
