from datetime import time
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.containers import APIChangesContainer
from utils.dataclasses import APIChanges
from utils.embeds.personal_order_embed import PersonalOrderCommandEmbed

PLANET_STATS_TO_CHECK = {
    "Location": "position",
    "Waypoints": "waypoints",
    "Max HP": "max_health",
    "Owner": "faction",
    "Planet Regen": "regen_perc_per_hour",
    "DSS in orbit": "dss_in_orbit",
    "Active Effects": "active_effects",
    "Sector": "sector",
}

REGION_STATS_TO_CHECK = {
    "Owner": "owner",
    "Max Health": "max_health",
    "Region Regen": "regen_perc_per_hour",
    "Is available": "is_available",
    "Damage Multiplier": "damage_multiplier",
}


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
                self.bot.logger.info(
                    f"Global Resources changed from {[gr.id for gr in self.bot.data.previous_data.global_resources]} to {[gr.id for gr in self.bot.data.formatted_data.global_resources]}"
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
                self.bot.logger.info(
                    f"Galactic War Effects changed - Removed: {[gwe.id for gwe in self.bot.data.previous_data.war_effects.values() if gwe not in self.bot.data.formatted_data.war_effects.values()]} - Added: {[gwe.id for gwe in self.bot.data.formatted_data.war_effects.values() if gwe not in self.bot.data.previous_data.war_effects.values()]}"
                )

            for mo_index, old_assignment in enumerate(
                self.bot.data.previous_data.assignments.get("en", []), start=1
            ):
                new_assignment = next(
                    (
                        a
                        for a in self.bot.data.formatted_data.assignments.get("en", [])
                        if a.id == old_assignment.id
                    ),
                    None,
                )
                if new_assignment:
                    for index, (old_task, new_task) in enumerate(
                        zip(old_assignment.tasks, new_assignment.tasks), start=1
                    ):
                        if old_task.target and new_task.target:
                            if old_task.target != new_task.target:
                                total_changes.append(
                                    APIChanges(
                                        old_object=old_task,
                                        new_object=new_task,
                                        property=index,
                                        stat_name=f"MO #{mo_index}",
                                        stat_source="Task",
                                    )
                                )
                                self.bot.logger.info(
                                    f"MO #{mo_index} Task #{index} target changed from {old_task.target} to {new_task.target}"
                                )

            if (
                self.bot.data.previous_data.personal_order
                and self.bot.data.formatted_data.personal_order
            ):
                if (
                    self.bot.data.previous_data.personal_order.id
                    != self.bot.data.formatted_data.personal_order.id
                ):
                    old_po_text = (
                        PersonalOrderCommandEmbed(
                            self.bot.data.previous_data.personal_order,
                            self.bot.json_dict,
                        )
                        .fields[0]
                        .name
                    )
                    new_po_text = (
                        PersonalOrderCommandEmbed(
                            self.bot.data.formatted_data.personal_order,
                            self.bot.json_dict,
                        )
                        .fields[0]
                        .name
                    )
                    total_changes.append(
                        APIChanges(
                            old_object=self.bot.data.previous_data.personal_order,
                            new_object=self.bot.data.formatted_data.personal_order,
                            property="PO",
                            stat_name=f"{old_po_text}\n-# to\n{new_po_text}",
                            stat_source="Personal Order",
                        )
                    )
                    self.bot.logger.info(
                        f"Personal Order changed from |{old_po_text}| to |{new_po_text}|"
                    )

            for old_planet, new_planet in zip(
                self.bot.data.previous_data.planets.values(),
                self.bot.data.formatted_data.planets.values(),
            ):
                for stat_name, property in PLANET_STATS_TO_CHECK.items():
                    if getattr(new_planet, property) != getattr(old_planet, property):
                        total_changes.append(
                            APIChanges(
                                old_object=old_planet,
                                new_object=new_planet,
                                property=property,
                                stat_name=stat_name,
                                stat_source="Planet",
                            )
                        )
                        old_p_property = getattr(old_planet, property)
                        new_p_property = getattr(new_planet, property)
                        if property == "active_effects":
                            old_p_property = [gwe.id for gwe in old_p_property]
                            new_p_property = [gwe.id for gwe in new_p_property]
                        elif property == "faction":
                            old_p_property = old_p_property.full_name
                            new_p_property = new_p_property.full_name

                        self.bot.logger.info(
                            f"{old_planet.names.get('en-GB', old_planet.name)} {stat_name} changed from {old_p_property} to {new_p_property}"
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
                                old_r_property = getattr(old_region, property)
                                new_r_property = getattr(new_region, property)
                                if property == "owner":
                                    old_r_property = old_r_property.full_name
                                    new_r_property = new_r_property.full_name

                                self.bot.logger.info(
                                    f"{old_region.names.get('en-GB', old_region.name)} {stat_name} changed from {old_r_property} to {new_r_property}"
                                )
        else:
            self.bot.logger.info("No previous data, skipping API Changes loop")
            return

        if total_changes != []:
            chunked_changes = [
                total_changes[i : i + 10] for i in range(0, len(total_changes), 10)
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
