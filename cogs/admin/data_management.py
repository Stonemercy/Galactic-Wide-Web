from datetime import datetime, time
from disnake import Activity, ActivityType, Status
from disnake.ext import commands, tasks
from main import GalacticWideWebBot


FETCH_SKIP_LIMIT = 5


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
                loop.stop()
            if loop in self.bot.loops:
                self.bot.loops.remove(loop)

    @tasks.loop(count=1)
    async def startup(self) -> None:
        await self.bot.interface_handler.populate_lists()
        await self.pull_from_api()
        await self.bot.change_presence(
            activity=Activity(name="/setup - /help", type=ActivityType.listening),
            status=Status.online,
        )

    @startup.before_loop
    async def before_startup(self) -> None:
        await self.bot.wait_until_ready()

    @tasks.loop(
        time=[time(hour=j, minute=i, second=45) for j in range(24) for i in range(60)]
    )
    async def pull_from_api(self) -> None:
        if self.bot.data.fetching and self.fetch_skips < FETCH_SKIP_LIMIT:
            self.fetch_skips += 1
            self.bot.logger.warning(
                f"Bot is already fetching. Skipped {self.fetch_skips} times so far"
            )
            return
        if self.fetch_skips > 0:
            self.fetch_skips = 0
        if self.bot.data.loaded:
            first_load = False
        else:
            first_load = True
        await self.bot.data.pull_from_api()
        self.bot.data.format_data()
        if first_load:
            now = datetime.now()
            if now < self.bot.ready_time:
                change = f"{(self.bot.ready_time - now).total_seconds():.2f} seconds faster than the given 45"
            else:
                change = f"Took {(now - self.bot.ready_time).total_seconds():.2f} seconds longer than the given 45"
            self.bot.logger.info(
                f"Startup complete in {(now - self.bot.startup_time).total_seconds():.2f} seconds - {change}"
            )
            self.bot.ready_time = now

    @pull_from_api.before_loop
    async def before_pull_from_api(self) -> None:
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(DataManagementCog(bot))
