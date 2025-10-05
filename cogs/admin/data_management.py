from datetime import datetime, time
from disnake import Activity, ActivityType
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.containers import APIChangesContainer
from utils.dataclasses import APIChanges


PLANET_STATS_TO_CHECK = {
    "Location": "position",
    "Waypoints": "waypoints",
    "Max HP": "max_health",
    "Owner": "faction",
    "Planet Regen": "regen_perc_per_hour",
    "DSS in orbit": "dss_in_orbit",
    "Active Effects": "active_effects",
}

REGION_STATS_TO_CHECK = {
    "Owner": "owner",
    "Max Health": "max_health",
    "Region Regen": "regen_perc_per_hour",
    "Is available": "is_available",
}


class DataManagementCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.loops = (self.startup, self.pull_from_api, self.check_changes)
        for loop in self.loops:
            if not loop.is_running():
                loop.start()
                self.bot.loops.append(loop)
        self.mentioned_new_effects = set()

    def cog_unload(self):
        for loop in self.loops:
            if loop.is_running():
                loop.stop()
                self.bot.loops.remove(loop)

    @tasks.loop(count=1)
    async def startup(self):
        await self.bot.interface_handler.populate_lists()
        await self.pull_from_api()
        await self.bot.change_presence(
            activity=Activity(
                name="democracy spread",
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
        print("pull_from_api loop starting")
        if self.bot.data.fetching:
            print("bot is already fetching, returning")
            return
        if self.bot.data.loaded:
            first_load = False
            self.bot.previous_data = self.bot.data.copy()
        else:
            first_load = True
        await self.bot.data.pull_from_api(
            logger=self.bot.logger,
            moderator_channel=self.bot.channels.moderator_channel,
        )
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
    async def before_pull_from_api(self):
        print("pull_from_loop about to start")
        await self.bot.wait_until_ready()

    @tasks.loop(
        time=[time(hour=j, minute=i, second=15) for j in range(24) for i in range(59)]
    )
    async def check_changes(self):
        total_changes: list[APIChanges] = []
        if self.bot.previous_data:
            if (
                self.bot.previous_data.global_resources
                != self.bot.data.global_resources
            ):
                total_changes.append(
                    APIChanges(
                        old_object=self.bot.previous_data.global_resources,
                        new_object=self.bot.data.global_resources,
                        property="",
                        stat_name="",
                        stat_source="Global Resources",
                    )
                )
            if (
                self.bot.previous_data.galactic_war_effects
                != self.bot.data.galactic_war_effects
            ):
                total_changes.append(
                    APIChanges(
                        old_object=self.bot.previous_data.galactic_war_effects,
                        new_object=self.bot.data.galactic_war_effects,
                        property="",
                        stat_name="",
                        stat_source="Galactic War Effects",
                    )
                )
            for old_planet, new_planet in zip(
                self.bot.previous_data.planets.values(), self.bot.data.planets.values()
            ):
                for stat_name, property in PLANET_STATS_TO_CHECK.items():
                    old_attr = getattr(old_planet, property)
                    new_attr = getattr(new_planet, property)
                    if new_attr != old_attr:
                        total_changes.append(
                            APIChanges(
                                old_object=old_planet,
                                new_object=new_planet,
                                property=property,
                                stat_name=stat_name,
                                stat_source="Planet",
                            )
                        )
                if old_planet.regions:
                    for old_region, new_region in zip(
                        old_planet.regions.values(), new_planet.regions.values()
                    ):
                        for stat_name, property in REGION_STATS_TO_CHECK.items():
                            if getattr(new_region, property) != getattr(
                                old_region, property
                            ):
                                total_changes.append(
                                    APIChanges(
                                        old_object=old_region,
                                        new_object=new_region,
                                        property=property,
                                        stat_name=stat_name,
                                        stat_source="Region",
                                    )
                                )
        if total_changes:
            chunked_changes = [
                total_changes[i : i + 10] for i in range(0, len(total_changes), 10)
            ]
            for chunk in chunked_changes:
                components = [APIChangesContainer(api_changes=chunk)]
                msg = await self.bot.channels.api_changes_channel.send(
                    components=components
                )
                await msg.publish()

    @check_changes.before_loop
    async def before_check_changes(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(cog=DataManagementCog(bot))
