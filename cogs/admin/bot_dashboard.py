from datetime import datetime, timedelta, timezone
from disnake import DiscordServerError, HTTPException, NotFound
from disnake.ext.commands import Cog
from disnake.ext.tasks import loop
from disnake.ui import TextDisplay
from utils.bot import GalacticWideWebBot
from utils.containers import BotDashboardContainer
from utils.dbv2 import BotDashboard


class BotDashboardCog(Cog):
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

    @loop(minutes=1)
    async def bot_dashboard(self) -> None:
        if not self.bot.ready:
            self.bot.logger.warning(
                "bot_dashboard loop returning - the bot isn't ready"
            )
            return
        if not self.bot.bot_dashboard_channel:
            self.bot.logger.warning(
                "bot_dashboard loop - bot_dashboard_channel missing"
            )
            self.bot.bot_dashboard_channel = self.bot.get_channel(
                self.bot_dashboard_db.channel_id
            ) or await self.bot.fetch_channel(self.bot_dashboard_db.channel_id)
        if not self.bot.bot_dashboard_message:
            self.bot.logger.warning(
                "bot_dashboard loop - bot_dashboard_message missing"
            )
            try:
                self.bot.bot_dashboard_message = (
                    await self.bot.bot_dashboard_channel.fetch_message(
                        self.bot_dashboard_db.message_id
                    )
                )
                self.bot.logger.warning(
                    "bot_dashboard loop - bot_dashboard_message fetched"
                )
            except NotFound:
                self.bot.logger.error(
                    "bot_dashboard loop - dashboard message not found, sending new one"
                )
                self.bot.bot_dashboard_message = (
                    await self.bot.bot_dashboard_channel.send(
                        components=[TextDisplay("Placeholder please ignore")]
                    )
                )
                self.bot_dashboard_db.message_id = self.bot.bot_dashboard_message.id
                self.bot_dashboard_db.save_changes()
            except HTTPException as e:
                self.bot.logger.error(f"bot_dashboard loop returning - {e}")
                return
        now = datetime.now(tz=timezone.utc)
        if now.minute == 0 or now - timedelta(minutes=2) < self.bot.startup_time:
            try:
                app_info = await self.bot.application_info()
                self.user_installs = app_info.approximate_user_install_count
            except HTTPException as e:
                self.bot.logger.error(f"bot_dashboard loop application_info - {e}")

        dashboard = BotDashboardContainer(
            bot=self.bot, user_installs=self.user_installs
        )
        try:
            await self.bot.bot_dashboard_message.edit(components=dashboard)
        except DiscordServerError:
            self.bot.logger.error(f"bot_dashboard loop returning - {e}")

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
