from asyncio import to_thread
from datetime import datetime
from disnake import File
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.containers import (
    DSSChangesContainer,
    RegionChangesContainer,
    CampaignChangesContainer,
)
from utils.dataclasses import CampaignChangesJson, DSSChangesJson, RegionChangesJson
from utils.dbv2 import GWWGuilds
from utils.maps import Maps


class WarUpdatesCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot
        self.loops = (self.campaign_check, self.dss_check, self.region_check)

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

    @tasks.loop(minutes=1)
    async def campaign_check(self) -> None:
        update_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or not self.bot.data.loaded
            or not self.bot.data.previous_data
            or update_start < self.bot.ready_time
            or self.bot.interface_handler.busy
        ):
            return
        unique_langs = GWWGuilds.unique_languages()
        components = {
            lang: CampaignChangesContainer(
                CampaignChangesJson(
                    lang_code_long=self.bot.json_dict["languages"][lang]["code_long"],
                    container=self.bot.json_dict["languages"][lang]["containers"][
                        "CampaignChangesContainer"
                    ],
                    special_units=self.bot.json_dict["languages"][lang][
                        "special_units"
                    ],
                    factions=self.bot.json_dict["languages"][lang]["factions"],
                    regions=self.bot.json_dict["languages"][lang]["regions"],
                )
            )
            for lang in unique_langs
        }
        new_updates = False
        need_to_update_sectors = False
        if not self.bot.databases.war_campaigns:
            for new_campaign in self.bot.data.formatted_data.campaigns:
                self.bot.databases.war_campaigns.add(
                    campaign_id=new_campaign.id,
                    planet_index=new_campaign.planet.index,
                    planet_owner=new_campaign.planet.faction.full_name,
                    event=bool(new_campaign.planet.event),
                    event_type=(
                        new_campaign.planet.event.type
                        if new_campaign.planet.event
                        else None
                    ),
                    event_faction=(
                        new_campaign.planet.event.faction.full_name
                        if new_campaign.planet.event
                        else None
                    ),
                )
            return

        new_campaign_ids = [c.id for c in self.bot.data.formatted_data.campaigns]
        for old_campaign in self.bot.databases.war_campaigns.copy():
            # loop through old campaigns
            if old_campaign.campaign_id not in new_campaign_ids:
                # if campaign has ended
                planet = self.bot.data.formatted_data.planets.get(
                    old_campaign.planet_index
                )
                if not planet:
                    continue
                if planet.faction.full_name == old_campaign.planet_owner == "Humans":
                    # if campaign was defence and we won
                    previous_data_planet = self.bot.data.previous_data.planets.get(
                        old_campaign.planet_index
                    )
                    hours_remaining = 0.0
                    if not previous_data_planet:
                        continue
                    if previous_data_planet.event:
                        hours_remaining = (
                            previous_data_planet.event.end_time_datetime - update_start
                        ).total_seconds() / 3600
                    for container in components.values():
                        container.add_defence_victory(
                            planet=planet,
                            defended_against=old_campaign.event_faction,
                            hours_remaining=hours_remaining,
                        )
                    new_updates = True
                elif planet.faction.full_name != old_campaign.planet_owner:
                    # if owner has changed
                    if old_campaign.planet_owner == "Humans":
                        # if defence campaign loss
                        for container in components.values():
                            container.add_planet_lost(planet=planet)
                    elif planet.faction.full_name == "Humans":
                        # if attack campaign win
                        for container in components.values():
                            container.add_liberation_victory(
                                planet=planet, taken_from=old_campaign.planet_owner
                            )
                    new_updates = True
                self.bot.data.tracking_service.liberation_changes.remove_entry(
                    key=planet.index
                )
                old_campaign.delete()
                self.bot.databases.war_campaigns.remove(old_campaign)
                need_to_update_sectors = True

        old_campaign_ids = [
            old_campaign.campaign_id
            for old_campaign in self.bot.databases.war_campaigns
        ]
        for new_campaign in self.bot.data.formatted_data.campaigns:
            # loop through new campaigns
            if new_campaign.id not in old_campaign_ids:
                # if campaign is brand new
                if (
                    new_campaign.planet.event
                    and new_campaign.planet.event.type == 2
                    and new_campaign.planet.event.potential_buildup == 0
                ):
                    # if campaign is an illuminate invasion but doesnt have the buildup data
                    continue
                for container in components.values():
                    container.add_new_campaign(
                        campaign=new_campaign,
                        gambit_planets=self.bot.data.formatted_data.gambit_planets,
                    )
                self.bot.databases.war_campaigns.add(
                    campaign_id=new_campaign.id,
                    planet_index=new_campaign.planet.index,
                    planet_owner=new_campaign.planet.faction.full_name,
                    event=bool(new_campaign.planet.event),
                    event_type=(
                        new_campaign.planet.event.type
                        if new_campaign.planet.event
                        else None
                    ),
                    event_faction=(
                        new_campaign.planet.event.faction.full_name
                        if new_campaign.planet.event
                        else None
                    ),
                )
                new_updates = True
                need_to_update_sectors = True

        if new_updates:
            await self.bot.interface_handler.send_feature(
                feature_type="war_announcements", content=components
            )
            self.bot.logger.info(
                f"Sent war announcements out to {len(self.bot.interface_handler.war_announcements)} channels in {(datetime.now() - update_start).total_seconds():.2f}s"
            )
            if need_to_update_sectors:
                await to_thread(
                    self.bot.maps.update_sectors,
                    planets=self.bot.data.formatted_data.planets,
                )
                self.bot.maps.update_waypoint_lines(
                    planets=self.bot.data.formatted_data.planets
                )
            self.bot.maps.update_assignment_tasks(
                assignments=self.bot.data.formatted_data.assignments.get("en", []),
                planets=self.bot.data.formatted_data.planets,
            )
            self.bot.maps.update_planets(planets=self.bot.data.formatted_data.planets)
            for lang in self.bot.json_dict["languages"].values():
                self.bot.maps.localize_map(
                    language_code_short=lang["code"],
                    language_code_long=lang["code_long"],
                    planets=self.bot.data.formatted_data.planets,
                    planet_names_json=self.bot.json_dict["planets"],
                )
                self.bot.maps.add_icons(
                    lang=lang["code"],
                    long_code=lang["code_long"],
                    planets=self.bot.data.formatted_data.planets,
                    dss=self.bot.data.formatted_data.dss,
                )
                message = await self.bot.channels.waste_bin_channel.send(
                    file=File(
                        fp=self.bot.maps.FileLocations.localized_map_path(lang["code"])
                    )
                )
                self.bot.maps.latest_maps[lang["code"]] = Maps.LatestMap(
                    datetime.now(), message.attachments[0].url
                )

    @campaign_check.before_loop
    async def before_campaign_check(self) -> None:
        await self.bot.wait_until_ready()

    @campaign_check.error
    async def campaign_check_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "campaign_check loop")

    @tasks.loop(minutes=1)
    async def dss_check(self) -> None:
        update_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or not self.bot.data.loaded
            or not self.bot.data.previous_data
            or update_start < self.bot.ready_time
            or self.bot.interface_handler.busy
        ):
            return
        dss_updates = False
        unique_langs = GWWGuilds.unique_languages()
        if self.bot.data.formatted_data.dss != None:
            # DSS updates
            containers = {
                lang: DSSChangesContainer(
                    json=DSSChangesJson(
                        lang_code_long=self.bot.json_dict["languages"][lang][
                            "code_long"
                        ],
                        container=self.bot.json_dict["languages"][lang]["containers"][
                            "DSSChangesContainer"
                        ],
                        special_units=self.bot.json_dict["languages"][lang][
                            "special_units"
                        ],
                        regions=self.bot.json_dict["languages"][lang]["regions"],
                    )
                )
                for lang in unique_langs
            }
            if (
                self.bot.databases.dss_info.planet_index == None
                or not self.bot.databases.dss_info.tactical_action_statuses
            ):
                self.bot.databases.dss_info.planet_index = (
                    self.bot.data.formatted_data.dss.planet.index
                )
                self.bot.databases.dss_info.tactical_action_statuses = {
                    ta.id: ta.status
                    for ta in self.bot.data.formatted_data.dss.tactical_actions
                }
                self.bot.databases.dss_info.save_changes()
                return
            dss_has_moved = False
            if (
                self.bot.databases.dss_info.planet_index
                != self.bot.data.formatted_data.dss.planet.index
            ):
                # if DSS has moved
                for container in containers.values():
                    before_planet = self.bot.data.formatted_data.planets.get(
                        self.bot.databases.dss_info.planet_index
                    )
                    if not before_planet:
                        return
                    container.dss_moved(
                        before_planet=before_planet,
                        after_planet=self.bot.data.formatted_data.dss.planet,
                    )
                self.bot.databases.dss_info.planet_index = (
                    self.bot.data.formatted_data.dss.planet.index
                )
                self.bot.databases.dss_info.save_changes()
                dss_updates = True
                dss_has_moved = True
            for ta in self.bot.data.formatted_data.dss.tactical_actions:
                old_status = self.bot.databases.dss_info.tactical_action_statuses.get(
                    ta.id
                )
                if old_status == None or old_status != ta.status:
                    for container in containers.values():
                        container.ta_status_changed(tactical_action=ta)
                        self.bot.databases.dss_info.tactical_action_statuses[ta.id] = (
                            ta.status
                        )
                        self.bot.databases.dss_info.save_changes()
                    dss_updates = True

        if dss_updates:
            await self.bot.interface_handler.send_feature(
                feature_type="dss_announcements", content=containers
            )
            self.bot.logger.info(
                f"Sent DSS announcements out to {len(self.bot.interface_handler.dss_announcements)} channels in {(datetime.now() - update_start).total_seconds():.2f}s"
            )
            if dss_has_moved:
                self.bot.maps.update_planets(
                    planets=self.bot.data.formatted_data.planets
                )
                for lang in unique_langs:
                    lang_json = self.bot.json_dict["languages"][lang]
                    self.bot.maps.localize_map(
                        language_code_short=lang,
                        language_code_long=lang_json["code_long"],
                        planets=self.bot.data.formatted_data.planets,
                        planet_names_json=self.bot.json_dict["planets"],
                    )
                    self.bot.maps.add_icons(
                        lang=lang,
                        long_code=lang_json["code_long"],
                        planets=self.bot.data.formatted_data.planets,
                        dss=self.bot.data.formatted_data.dss,
                    )
                    message = await self.bot.channels.waste_bin_channel.send(
                        file=File(
                            fp=self.bot.maps.FileLocations.localized_map_path(lang)
                        )
                    )
                    self.bot.maps.latest_maps[lang] = Maps.LatestMap(
                        datetime.now(), message.attachments[0].url
                    )

    @dss_check.before_loop
    async def before_dss_check(self) -> None:
        await self.bot.wait_until_ready()

    @dss_check.error
    async def dss_check_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "dss_check loop")

    @tasks.loop(minutes=1)
    async def region_check(self) -> None:
        update_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or not self.bot.data.loaded
            or not self.bot.data.previous_data
            or update_start < self.bot.ready_time
            or self.bot.interface_handler.busy
        ):
            return
        region_updates = False
        unique_langs = GWWGuilds.unique_languages()
        all_regions = [
            r
            for p in self.bot.data.formatted_data.planets.values()
            for r in p.regions.values()
        ]
        if not self.bot.databases.planet_regions:
            for region in all_regions:
                if region.is_available:
                    self.bot.databases.planet_regions.add(region)
            return

        components = {
            lang: RegionChangesContainer(
                container_json=RegionChangesJson(
                    lang_code_long=self.bot.json_dict["languages"][lang]["code_long"],
                    container=self.bot.json_dict["languages"][lang]["containers"][
                        "RegionChangesContainer"
                    ],
                    special_units=self.bot.json_dict["languages"][lang][
                        "special_units"
                    ],
                    factions=self.bot.json_dict["languages"][lang]["factions"],
                )
            )
            for lang in unique_langs
        }

        active_region_hashes = [r.settings_hash for r in all_regions if r.is_available]
        for old_region in self.bot.databases.planet_regions.copy():
            # loop through old regions
            if old_region.settings_hash not in active_region_hashes:
                # if region has become unavailable
                region_list = [
                    r
                    for r in all_regions
                    if r.settings_hash == old_region.settings_hash
                ]
                if region_list:
                    # if region is still in API
                    region = region_list[0]
                    if region.owner.full_name != old_region.owner:
                        # if owner has changed
                        if region.owner.full_name == "Humans":
                            if (
                                not region.planet.event
                                and region.planet.faction.full_name == "Humans"
                            ):
                                # if campaign has been won
                                pass
                            else:
                                # region win
                                for container in components.values():
                                    container.add_region_victory(
                                        region=region,
                                    )
                                region_updates = True
                    self.bot.data.tracking_service.region_changes.remove_entry(
                        old_region.settings_hash
                    )
                    self.bot.databases.planet_regions.delete(old_region)

        if all_regions:
            # region updates
            old_region_hashes = [
                r.settings_hash for r in self.bot.databases.planet_regions
            ]
            for region in all_regions:
                # loop through new regions
                if (
                    region.settings_hash not in old_region_hashes
                    and region.is_available
                    and region.owner.full_name != "Humans"
                ):
                    if (
                        not region.planet.event
                        and region.planet.faction.full_name == "Humans"
                    ):
                        continue
                    # if region is brand new
                    for container in components.values():
                        container.add_new_region(
                            region=region,
                        )
                    self.bot.databases.planet_regions.add(region)
                    region_updates = True

            if region_updates:
                await self.bot.interface_handler.send_feature(
                    "region_announcements", components
                )
                self.bot.logger.info(
                    f"Sent region announcements out to {len(self.bot.interface_handler.region_announcements)} channels in {(datetime.now() - update_start).total_seconds():.2f}s"
                )

    @region_check.before_loop
    async def before_region_check(self) -> None:
        await self.bot.wait_until_ready()

    @region_check.error
    async def region_check_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "region_check loop")


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(WarUpdatesCog(bot))
