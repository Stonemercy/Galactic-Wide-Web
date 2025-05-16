from datetime import datetime, time
from disnake import Activity, ActivityType
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.embeds.loop_embeds import APIChanges, APIChangesLoopEmbed


class DataManagementCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.startup.start()
        self.pull_from_api.start()
        self.check_changes.start()
        self.mentioned_new_effects = set()

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
            if (
                self.bot.previous_data.galactic_impact_mod != 0
                and abs(
                    self.bot.data.galactic_impact_mod
                    - self.bot.previous_data.galactic_impact_mod
                )
                >= 0.1
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
                if planet.active_effects != new_data.active_effects:
                    total_changes.append(
                        APIChanges(
                            planet=planet,
                            statistic="Effects",
                            before=[
                                self.bot.json_dict["planet_effects"].get(
                                    str(effect), effect
                                )
                                for effect in planet.active_effects
                            ],
                            after=[
                                self.bot.json_dict["planet_effects"].get(
                                    str(effect), effect
                                )
                                for effect in new_data.active_effects
                            ],
                        )
                    )
            active_effects = {
                str(e)
                for planet in self.bot.data.planets.values()
                if planet.active_effects
                for e in planet.active_effects
            } | {
                str(id)
                for ge in self.bot.data.global_events
                if ge.effect_ids
                for id in ge.effect_ids
            }
            new_effects: set = {
                e
                for e in (active_effects - self.bot.json_dict["planet_effects"].keys())
                if e not in self.mentioned_new_effects
            }
            if new_effects:
                formatted_effects = "\n-# - ".join(new_effects)
                await self.bot.moderator_channel.send(
                    f"NEW EFFECTS {self.bot.owner.mention}\n-# - {formatted_effects}"
                )
                self.mentioned_new_effects |= new_effects
        if total_changes:
            embed = APIChangesLoopEmbed(total_changes=total_changes)
            msg = await self.bot.api_changes_channel.send(embed=embed)
            await msg.publish()

    @check_changes.before_loop
    async def before_check_changes(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(cog=DataManagementCog(bot))
