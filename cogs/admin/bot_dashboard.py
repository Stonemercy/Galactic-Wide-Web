from datetime import datetime, timedelta
from disnake import HTTPException, NotFound, ui
from disnake.ext import commands, tasks
from utils.bot import GalacticWideWebBot
from utils.containers import BotDashboardContainer
from utils.dbv2 import BotDashboard


class BotDashboardCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot
        self.bot_dashboard_db = None
        self.user_installs = 0

    def cog_load(self) -> None:
        if not self.bot_dashboard_db:
            self.bot_dashboard_db = BotDashboard()
        if not self.bot_dashboard.is_running():
            self.bot_dashboard.start()
            self.bot.loops.append(self.bot_dashboard)

    def cog_unload(self) -> None:
        if self.bot_dashboard.is_running():
            self.bot_dashboard.cancel()
        if self.bot_dashboard in self.bot.loops:
            self.bot.loops.remove(self.bot_dashboard)

    @tasks.loop(minutes=1)
    async def bot_dashboard(self) -> None:
        bot_dashboard = self.bot_dashboard_db
        if not self.bot.bot_dashboard_channel:
            self.bot.bot_dashboard_channel = self.bot.get_channel(
                bot_dashboard.channel_id
            ) or await self.bot.fetch_channel(bot_dashboard.channel_id)
        if not self.bot.bot_dashboard_message:
            try:
                self.bot.bot_dashboard_message = (
                    await self.bot.bot_dashboard_channel.fetch_message(
                        bot_dashboard.message_id
                    )
                )
            except NotFound:
                self.bot.bot_dashboard_message = (
                    await self.bot.bot_dashboard_channel.send(
                        components=[ui.TextDisplay("Placeholder please ignore")]
                    )
                )
                bot_dashboard.message_id = self.bot.bot_dashboard_message.id
                bot_dashboard.save_changes()
            except HTTPException:
                return
        now = datetime.now()
        if now.minute == 0 or now - timedelta(minutes=2) < self.bot.startup_time:
            app_info = await self.bot.application_info()
            self.user_installs = app_info.approximate_user_install_count
        dashboard = BotDashboardContainer(
            bot=self.bot, user_installs=self.user_installs
        )
        await self.bot.bot_dashboard_message.edit(components=dashboard)

    @bot_dashboard.before_loop
    async def before_bot_dashboard(self) -> None:
        await self.bot.wait_until_ready()

    @bot_dashboard.error
    async def bot_dashboard_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "bot_dashboard loop")


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(BotDashboardCog(bot))
