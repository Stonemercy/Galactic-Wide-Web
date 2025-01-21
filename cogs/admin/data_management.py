from datetime import time
from disnake import Activity, ActivityType
from disnake.ext import commands, tasks
from main import GalacticWideWebBot


class DataManagementCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.startup.start()
        self.pull_from_api.start()

    def cog_unload(self):
        self.startup.stop()
        self.pull_from_api.stop()

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
        await self.bot.data.pull_from_api(self.bot)

    @pull_from_api.before_loop
    async def before_pull_from_api(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(DataManagementCog(bot))
