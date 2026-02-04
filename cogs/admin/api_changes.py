from datetime import time
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
    "Damage Multiplier": "damage_multiplier",
}

FETCH_SKIP_LIMIT = 5


class APIChangesCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    def cog_load(self) -> None:
        if not self.api_changes.is_running():
            self.api_changes.start()
            self.bot.loops.append(self.api_changes)

    def cog_unload(self) -> None:
        if self.api_changes.is_running():
            self.api_changes.cancel()
        if self.api_changes in self.bot.loops:
            self.bot.loops.remove(self.api_changes)

    @tasks.loop(
        time=[time(hour=j, minute=i, second=15) for j in range(24) for i in range(60)]
    )
    async def api_changes(self) -> None:
        total_changes: list[APIChanges] = []
        if self.bot.data.previous_data:
            if (
                self.bot.data.previous_data.global_resources
                != self.bot.data.formatted_data.global_resources
            ):
                total_changes.append(
                    APIChanges(
                        old_object=self.bot.data.previous_data.global_resources,
                        new_object=self.bot.data.formatted_data.global_resources,
                        property="",
                        stat_name="",
                        stat_source="Global Resources",
                    )
                )

            if (
                self.bot.data.previous_data.war_effects
                != self.bot.data.formatted_data.war_effects
            ):
                total_changes.append(
                    APIChanges(
                        old_object=self.bot.data.previous_data.war_effects,
                        new_object=self.bot.data.formatted_data.war_effects,
                        property="",
                        stat_name="",
                        stat_source="Galactic War Effects",
                    )
                )

            for old_planet, new_planet in zip(
                self.bot.data.previous_data.planets.values(),
                self.bot.data.formatted_data.planets.values(),
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
        if total_changes != []:
            if len(total_changes) > 20:
                await self.bot.channels.moderator_channel.send(
                    f"TOTAL API CHANGES LENGTH = {len(total_changes)}\nCANCELLING MESSAGE"
                )
                return
            chunked_changes = [
                total_changes[i : i + 5] for i in range(0, len(total_changes), 5)
            ]
            for chunk in chunked_changes:
                components = [
                    APIChangesContainer(
                        api_changes=chunk, planets=self.bot.data.formatted_data.planets
                    )
                ]
                msg = await self.bot.channels.api_changes_channel.send(
                    components=components
                )
                await msg.publish()

    @api_changes.before_loop
    async def before_api_changes(self):
        await self.bot.wait_until_ready()

    @api_changes.error
    async def api_changes_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "api_changes loop")


def setup(bot: GalacticWideWebBot):
    bot.add_cog(APIChangesCog(bot))
