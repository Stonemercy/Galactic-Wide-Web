from datetime import datetime, time, timezone
from disnake import Activity, ActivityType, Status
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.bot import STARTUP_SECONDS


class DataManagementCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot
        self.loops = (self.startup, self.pull_from_api)
        self.fetch_skips = 0

    def cog_load(self) -> None:
        for loop in self.loops:
            if not loop.is_running():
                loop.start()
                self.bot.loops.append(loop)

    def cog_unload(self) -> None:
        for loop in self.loops:
            if loop.is_running():
                loop.cancel()
            if loop in self.bot.loops:
                self.bot.loops.remove(loop)

    @tasks.loop(count=1)
    async def startup(self) -> None:
        self.bot.logger.info("startup loop started")
        await self.bot.interface_handler.populate_lists()
        await self.bot.change_presence(
            activity=Activity(name="/setup - /help", type=ActivityType.listening),
            status=Status.online,
        )
        self.bot.logger.info("startup loop completed")
        now = datetime.now()
        secs_until_pull_from_api = (
            (
                now.replace(second=45)
                if now.second < 45
                else now.replace(minute=now.minute + 1, second=45)
            )
            - now
        ).total_seconds()
        self.bot.logger.info(
            f"pull_from_api should begin in {secs_until_pull_from_api:.1f} seconds"
        )

    @startup.before_loop
    async def before_startup(self) -> None:
        await self.bot.wait_until_ready()

    @startup.error
    async def startup_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "startup loop")

    @tasks.loop(
        time=[time(hour=j, minute=i, second=45) for j in range(24) for i in range(60)]
    )
    async def pull_from_api(self) -> None:
        if self.bot.data.fetching and self.fetch_skips < 5:
            self.fetch_skips += 1
            self.bot.logger.warning(
                f"Bot is already fetching. Skipped {self.fetch_skips} times so far"
            )
            return
        first_load = not self.bot.data.loaded
        await self.bot.data.pull_from_api()
        self.bot.data.format_data()
        if self.fetch_skips != 0:
            self.fetch_skips = 0
        if first_load:
            now = datetime.now(tz=timezone.utc)
            self.bot.logger.info(
                f"Galactic Wide Web booted in {(now - self.bot.startup_time).total_seconds():.2f} seconds with {len(self.bot.guilds):,} Discord guilds"
            )
            self.bot.ready_time = now

    @pull_from_api.before_loop
    async def before_pull_from_api(self) -> None:
        await self.bot.wait_until_ready()

    @pull_from_api.error
    async def api_changes_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "api_changes loop")


def setup(bot: GalacticWideWebBot):
    bot.add_cog(DataManagementCog(bot))
