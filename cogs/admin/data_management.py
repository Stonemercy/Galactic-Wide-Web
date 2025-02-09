from dataclasses import dataclass
from datetime import time
from disnake import Activity, ActivityType
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.data import Planet
from utils.embeds.loop_embeds import APIChangesLoopEmbed


@dataclass
class APIChanges:
    planet: Planet
    statistic: str
    before: int | list
    after: int | list


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
        total_changes: list[APIChanges] = []
        if self.bot.previous_data:
            for planet in self.bot.previous_data.planets.values():
                new_data = self.bot.data.planets[planet.index]
                if planet.regen_perc_per_hour != new_data.regen_perc_per_hour:
                    total_changes.append(
                        APIChanges(
                            planet,
                            "Regen %",
                            planet.regen_perc_per_hour,
                            new_data.regen_perc_per_hour,
                        )
                    )
                if planet.waypoints != new_data.waypoints:
                    old_waypoints = [
                        self.bot.data.planets[waypoint].name
                        for waypoint in planet.waypoints
                    ]
                    new_waypoints = [
                        self.bot.data.planets[waypoint].name
                        for waypoint in new_data.waypoints
                    ]
                    total_changes.append(
                        APIChanges(planet, "Waypoints", old_waypoints, new_waypoints)
                    )
        if total_changes:
            await self.bot.api_changes_channel.send(
                embed=APIChangesLoopEmbed(total_changes)
            )

    @check_changes.before_loop
    async def before_check_changes(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(DataManagementCog(bot))
