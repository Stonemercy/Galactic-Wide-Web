from datetime import datetime, time
from disnake import Activity, ActivityType
from disnake.ext import commands, tasks
from main import GalacticWideWebBot


class DataManagementCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.startup.start()
        self.pull_from_api.start()
        self.check_changes.start()

    def cog_unload(self):
        self.startup.stop()
        self.pull_from_api.stop()
        self.check_changes.stop()

    @tasks.loop(count=1)
    async def startup(self):
        await self.bot.interface_handler.populate_lists()
        await self.pull_from_api()
        await self.bot.change_presence(
            activity=Activity(
                name=f"democracy spread",
                type=ActivityType.watching,
            )
        )

    @startup.before_loop
    async def before_startup(self):
        await self.bot.wait_until_ready()

    @tasks.loop(
        time=[time(hour=j, minute=i, second=45) for j in range(24) for i in range(59)]
    )
    async def pull_from_api(self):
        if self.bot.data.loaded:
            self.bot.previous_data = self.bot.data.copy()
        await self.bot.data.pull_from_api(self.bot)

    @pull_from_api.before_loop
    async def before_pull_from_api(self):
        await self.bot.wait_until_ready()

    @tasks.loop(
        time=[time(hour=j, minute=i, second=15) for j in range(24) for i in range(59)]
    )
    async def check_changes(self):
        changes_start = datetime.now()
        total_changes = {}
        if self.bot.previous_data:
            for planet in self.bot.previous_data.planets.values():
                new_data = self.bot.data.planets[planet.index]
                if planet.regen_perc_per_hour != new_data.regen_perc_per_hour:
                    total_changes["planet_regen"][planet.name] = {
                        "before": planet.regen_perc_per_hour,
                        "after": new_data.regen_perc_per_hour,
                    }
        if total_changes:
            await self.bot.moderator_channel.send(total_changes)
        self.bot.logger.info(
            f"changes checked in {(datetime.now() - changes_start).total_seconds():.3f} seconds"
        )

    @check_changes.before_loop
    async def before_check_changes(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(DataManagementCog(bot))
