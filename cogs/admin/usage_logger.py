from datetime import time
from disnake import AppCmdInter, Guild, MessageInteraction
from disnake.ext import commands, tasks
from utils.bot import GalacticWideWebBot
from utils.containers import UsageContainer
from utils.functions import dict_empty


class UsageLoggerCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot
        self.usage_dict = {
            "commands": {},
            "buttons": {},
            "dropdowns": {},
        }
        self.guilds_joined = 0

    def cog_load(self) -> None:
        if not self.usage_report.is_running():
            self.usage_report.start()
            self.bot.loops.append(self.usage_report)

    def cog_unload(self) -> None:
        if self.usage_report.is_running():
            self.usage_report.cancel()
        if self.usage_report in self.bot.loops:
            self.bot.loops.remove(self.usage_report)

    @commands.Cog.listener()
    async def on_slash_command(self, inter: AppCmdInter) -> None:
        if inter.application_command.name not in self.usage_dict["commands"]:
            self.usage_dict["commands"][inter.application_command.name] = 1
        self.usage_dict["commands"][inter.application_command.name] += 1
        options_str = ", ".join([f"{k}={v}" for k, v in inter.filled_options.items()])
        self.bot.logger.info(
            f"Command: /{inter.application_command.name} "
            f"| User: {inter.author} "
            f"| Guild: {inter.guild.name if inter.guild else 'DM'} "
            f"| Options: {options_str if options_str else 'None'}"
        )

    @commands.Cog.listener()
    async def on_button_click(self, inter: MessageInteraction) -> None:
        if inter.component.custom_id not in self.usage_dict["buttons"]:
            self.usage_dict["buttons"][inter.component.custom_id] = 1
        self.usage_dict["buttons"][inter.component.custom_id] += 1
        self.bot.logger.info(
            f"Button clicked: '{inter.component.custom_id}' "
            f"| User: {inter.author} (ID: {inter.author.id}) "
            f"| Guild: {inter.guild.name if inter.guild else 'DM'} "
            f"| Channel: {inter.channel.name if hasattr(inter.channel, 'name') else 'DM'} "
        )

    @commands.Cog.listener()
    async def on_dropdown(self, inter: MessageInteraction) -> None:
        if inter.component.custom_id not in self.usage_dict["dropdowns"]:
            self.usage_dict["dropdowns"][inter.component.custom_id] = 1
        self.usage_dict["dropdowns"][inter.component.custom_id] += 1
        self.bot.logger.info(
            f"Dropdown used: '{inter.component.custom_id}' "
            f"| Selected: {inter.values[0]} "
            f"| User: {inter.author} (ID: {inter.author.id}) "
            f"| Guild: {inter.guild.name if inter.guild else 'DM'} "
            f"| Channel: {inter.channel.name if hasattr(inter.channel, 'name') else 'DM'} "
        )

    @commands.Cog.listener()
    async def on_guild_join(self, guild: Guild) -> None:
        self.guilds_joined += 1

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: Guild) -> None:
        self.guilds_joined -= 1

    @tasks.loop(time=time(hour=22, minute=0, second=0))
    async def usage_report(self) -> None:
        if dict_empty(self.usage_dict):
            return
        container = UsageContainer(
            usage_dict=self.usage_dict, guilds_joined=self.guilds_joined
        )
        await self.bot.channels.moderator_channel.send(components=container)
        for _dict in self.usage_dict.values():
            _dict.clear()
        self.guilds_joined = 0

    @usage_report.before_loop
    async def before_usage_report(self) -> None:
        await self.bot.wait_until_ready()

    @usage_report.error
    async def usage_report_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "usage_report loop")


def setup(bot: GalacticWideWebBot):
    bot.add_cog(UsageLoggerCog(bot))
