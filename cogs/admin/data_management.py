from datetime import datetime, time
from disnake import Activity, ActivityType
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.dataclasses import APIChanges
from utils.embeds import APIChangesEmbed, GalacticWarEffectEmbed
from utils.functions import out_of_normal_range


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
        if self.bot.data.loaded:
            first_load = False
            self.bot.previous_data = self.bot.data.copy()
        else:
            first_load = True
        await self.bot.data.pull_from_api(
            logger=self.bot.logger, moderator_channel=self.bot.moderator_channel
        )
        if first_load:
            now = datetime.now()
            if now < self.bot.ready_time:
                change = f"{(self.bot.ready_time - now).total_seconds():.2f} seconds faster than the given 30"
            else:
                change = f"Took {(now - self.bot.ready_time).total_seconds():.2f} seconds longer than the given 30"
            self.bot.logger.info(
                msg=f"Startup complete in {(now - self.bot.startup_time).total_seconds():.2f} seconds - {change}"
            )
            self.bot.ready_time = now

    @pull_from_api.before_loop
    async def before_pull_from_api(self):
        await self.bot.wait_until_ready()

    @tasks.loop(
        time=[time(hour=j, minute=i, second=15) for j in range(24) for i in range(59)]
    )
    async def check_changes(self):
        total_changes: list[APIChanges] = []
        if self.bot.previous_data:
            if self.bot.previous_data.galactic_impact_mod != 0 and out_of_normal_range(
                before=self.bot.previous_data.galactic_impact_mod,
                after=self.bot.data.galactic_impact_mod,
            ):
                total_changes.append(
                    APIChanges(
                        planet=self.bot.data.planets[0],
                        statistic="Galactic Impact Mod",
                        before=self.bot.previous_data.galactic_impact_mod,
                        after=self.bot.data.galactic_impact_mod,
                    )
                )
            for planet in self.bot.previous_data.planets.values():
                new_data = self.bot.data.planets[planet.index]
                if planet.regen_perc_per_hour != new_data.regen_perc_per_hour:
                    total_changes.append(
                        APIChanges(
                            planet=planet,
                            statistic="Regen %",
                            before=planet.regen_perc_per_hour,
                            after=new_data.regen_perc_per_hour,
                        )
                    )
                if planet.max_health != new_data.max_health:
                    total_changes.append(
                        APIChanges(
                            planet=planet,
                            statistic="Max Health",
                            before=planet.max_health,
                            after=new_data.max_health,
                        )
                    )
                if sorted(planet.waypoints) != sorted(new_data.waypoints):
                    total_changes.append(
                        APIChanges(
                            planet=planet,
                            statistic="Waypoints",
                            before=[
                                self.bot.data.planets[waypoint].name
                                for waypoint in planet.waypoints
                            ],
                            after=[
                                self.bot.data.planets[waypoint].name
                                for waypoint in new_data.waypoints
                            ],
                        )
                    )
                if planet.position != new_data.position and planet.index != 64:
                    total_changes.append(
                        APIChanges(
                            planet=planet,
                            statistic="Location",
                            before=(planet.position["x"], planet.position["y"]),
                            after=(new_data.position["x"], new_data.position["y"]),
                        )
                    )
                if sorted([ae.id for ae in planet.active_effects]) != sorted(
                    [ae.id for ae in new_data.active_effects]
                ):
                    total_changes.append(
                        APIChanges(
                            planet=planet,
                            statistic="Effects",
                            before=planet.active_effects,
                            after=new_data.active_effects,
                        )
                    )
                if planet.regions:
                    for region in planet.regions.values():
                        new_region = new_data.regions.get(region.index, None)
                        if (
                            new_region
                            and region.regen_per_sec != new_region.regen_per_sec
                        ):
                            total_changes.append(
                                APIChanges(
                                    planet=planet,
                                    statistic="Region Regen",
                                    before=region,
                                    after=new_region,
                                )
                            )
                if planet.current_owner != new_data.current_owner:
                    total_changes.append(
                        APIChanges(
                            planet=planet,
                            statistic="Planet Owner",
                            before=planet.current_owner,
                            after=new_data.current_owner,
                        )
                    )
        for effect in self.bot.data.galactic_war_effects:
            if not effect.planet_effect and effect.id not in self.mentioned_new_effects:
                await self.bot.moderator_channel.send(
                    f"{self.bot.owner.mention} New Effect",
                    embed=GalacticWarEffectEmbed(
                        gwe=effect,
                        planets_with_gwe=[
                            p
                            for p in self.bot.data.planets.values()
                            if effect.id in [e for e in p.active_effects]
                        ],
                        json_dict=self.bot.json_dict,
                    ),
                )
                self.mentioned_new_effects.add(effect.id)
        if total_changes:
            chunked_changes = [
                total_changes[i : i + 20] for i in range(0, len(total_changes), 20)
            ]
            for chunk in chunked_changes:
                embed = APIChangesEmbed(total_changes=chunk)

    @check_changes.before_loop
    async def before_check_changes(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(cog=DataManagementCog(bot))
