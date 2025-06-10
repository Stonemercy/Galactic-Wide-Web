from asyncio import to_thread
from datetime import datetime
from disnake import File
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from os import getenv
from utils.dbv2 import DSSInfo, GWWGuilds, WarCampaigns
from utils.embeds.loop_embeds import CampaignLoopEmbed
from utils.maps import Maps

SUPPORT_SERVER = [int(getenv("SUPPORT_SERVER"))]


class WarUpdatesCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.loops = (self.campaign_check, self.dss_check)
        for loop in self.loops:
            if not loop.is_running():
                loop.start()

    def cog_unload(self):
        for loop in self.loops:
            if loop.is_running():
                loop.stop()

    @tasks.loop(minutes=1)
    async def campaign_check(self):
        update_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or not self.bot.data.loaded
            or not self.bot.previous_data
            or update_start < self.bot.ready_time
            or self.bot.interface_handler.busy
        ):
            return
        old_campaigns = WarCampaigns()
        unique_langs = GWWGuilds().unique_languages
        embeds = {
            lang: [
                CampaignLoopEmbed(
                    language_json=self.bot.json_dict["languages"][lang],
                    planet_names_json=self.bot.json_dict["planets"],
                )
            ]
            for lang in unique_langs
        }
        new_updates = False
        need_to_update_sectors = False
        if not old_campaigns:
            for new_campaign in self.bot.data.campaigns:
                old_campaigns.add(
                    campaign_id=new_campaign.id,
                    planet_index=new_campaign.planet.index,
                    planet_owner=new_campaign.planet.current_owner,
                    event=bool(new_campaign.planet.event),
                    event_type=(
                        new_campaign.planet.event.type
                        if new_campaign.planet.event
                        else None
                    ),
                    event_faction=(
                        new_campaign.planet.event.faction
                        if new_campaign.planet.event
                        else None
                    ),
                )
            return

        new_campaign_ids = [c.id for c in self.bot.data.campaigns]
        for old_campaign in old_campaigns:
            # loop through old campaigns
            if old_campaign.campaign_id not in new_campaign_ids:
                # if campaign has ended
                planet = self.bot.data.planets[old_campaign.planet_index]
                if (
                    planet.current_owner == "Humans"
                    and old_campaign.planet_owner == "Humans"
                ):
                    # if campaign was defence and we won
                    if old_campaign.event_type == 2:
                        # if event was invasion (no territory taken)
                        previous_data_planet = self.bot.previous_data.planets[
                            old_campaign.planet_index
                        ]
                        win_status = False
                        hours_left = 0
                        if previous_data_planet.event:
                            # if I have data on the event (sometimes dont)
                            win_status = (
                                previous_data_planet.event.end_time_datetime
                                > update_start
                            )
                            hours_left = (
                                previous_data_planet.event.end_time_datetime
                                - update_start
                            ).total_seconds() / 3600
                        for embed_list in embeds.values():
                            embed_list[0].add_invasion_over(
                                planet=planet,
                                faction=old_campaign.event_faction,
                                hours_left=hours_left,
                                win_status=win_status,
                            )
                    else:
                        # if event wasnt invasion (territory taken)
                        # TODO: if event is type 3, siege victory
                        for embed_list in embeds.values():
                            embed_list[0].add_def_victory(planet=planet)
                elif planet.current_owner != old_campaign.planet_owner:
                    # if owner has changed
                    if old_campaign.planet_owner == "Humans":
                        # if defence campaign loss
                        for embed_list in embeds.values():
                            embed_list[0].add_planet_lost(planet=planet)
                    elif planet.current_owner == "Humans":
                        # if attack campaign win
                        for embed_list in embeds.values():
                            embed_list[0].add_campaign_victory(
                                planet=planet, taken_from=old_campaign.planet_owner
                            )
                self.bot.data.liberation_changes.remove_entry(key=planet.index)
                old_campaign.delete()
                new_updates = True
                need_to_update_sectors = True

        old_campaign_ids = [old_campaign.campaign_id for old_campaign in old_campaigns]
        for new_campaign in self.bot.data.campaigns:
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
                time_remaining = (
                    None
                    if not new_campaign.planet.event
                    else f"<t:{new_campaign.planet.event.end_time_datetime.timestamp():.0f}:R>"
                )
                for embed_list in embeds.values():
                    embed_list[0].add_new_campaign(new_campaign, time_remaining)
                old_campaigns.add(
                    campaign_id=new_campaign.id,
                    planet_index=new_campaign.planet.index,
                    planet_owner=new_campaign.planet.current_owner,
                    event=bool(new_campaign.planet.event),
                    event_type=(
                        new_campaign.planet.event.type
                        if new_campaign.planet.event
                        else None
                    ),
                    event_faction=(
                        new_campaign.planet.event.faction
                        if new_campaign.planet.event
                        else None
                    ),
                )
                new_updates = True
                need_to_update_sectors = True

        if new_updates:
            for embed_list in embeds.values():
                embed_list[0].remove_empty()
            await self.bot.interface_handler.send_feature("war_announcements", embeds)
            self.bot.logger.info(
                f"Sent war announcements out to {len(self.bot.interface_handler.war_announcements)} channels"
            )
            if need_to_update_sectors:
                await to_thread(
                    self.bot.maps.update_sectors, planets=self.bot.data.planets
                )
                self.bot.maps.update_waypoint_lines(planets=self.bot.data.planets)
            self.bot.maps.update_assignment_tasks(
                assignments=self.bot.data.assignments,
                planets=self.bot.data.planets,
                campaigns=self.bot.data.campaigns,
            )
            self.bot.maps.update_planets(
                planets=self.bot.data.planets,
                active_planets=[
                    campaign.planet.index for campaign in self.bot.data.campaigns
                ],
            )
            self.bot.maps.update_dss(
                dss=self.bot.data.dss,
                type_3_campaigns=[c for c in self.bot.data.campaigns if c.type == 3],
            )
            for lang in self.bot.json_dict["languages"].values():
                self.bot.maps.localize_map(
                    language_code_short=lang["code"],
                    language_code_long=lang["code_long"],
                    planets=self.bot.data.planets,
                    active_planets=[
                        campaign.planet.index for campaign in self.bot.data.campaigns
                    ],
                    type_3_campaigns=[
                        c for c in self.bot.data.campaigns if c.type == 3
                    ],
                    planet_names_json=self.bot.json_dict["planets"],
                )
                message = await self.bot.waste_bin_channel.send(
                    file=File(
                        fp=self.bot.maps.FileLocations.localized_map_path(lang["code"])
                    )
                )
                self.bot.maps.latest_maps[lang["code"]] = Maps.LatestMap(
                    datetime.now(), message.attachments[0].url
                )

    @campaign_check.before_loop
    async def before_campaign_check(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def dss_check(self):
        update_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or not self.bot.data.loaded
            or not self.bot.previous_data
            or update_start < self.bot.ready_time
            or self.bot.interface_handler.busy
        ):
            return

        dss_updates = False
        unique_langs = GWWGuilds().unique_languages
        if self.bot.data.dss != None:
            # DSS updates
            embeds = {
                lang: [
                    CampaignLoopEmbed(
                        language_json=self.bot.json_dict["languages"][lang],
                        planet_names_json=self.bot.json_dict["planets"],
                    )
                ]
                for lang in unique_langs
            }
            last_dss_info = DSSInfo()

            if (
                last_dss_info.planet_index == None
                or not last_dss_info.tactical_action_statuses
            ):
                last_dss_info.planet_index = self.bot.data.dss.planet.index
                last_dss_info.tactical_action_statuses = {
                    ta.id: ta.status for ta in self.bot.data.dss.tactical_actions
                }
                last_dss_info.save_changes()
                return
            if last_dss_info.planet_index != self.bot.data.dss.planet.index:
                # if DSS has moved
                for embed_list in embeds.values():
                    embed_list[0].dss_moved(
                        before_planet=self.bot.data.planets[last_dss_info.planet_index],
                        after_planet=self.bot.data.dss.planet,
                    )
                last_dss_info.planet_index = self.bot.data.dss.planet.index
                last_dss_info.save_changes()
                dss_updates = True
            for ta in self.bot.data.dss.tactical_actions:
                old_status = last_dss_info.tactical_action_statuses.get(ta.id)
                if not old_status or old_status != ta.status:
                    for embed_list in embeds.values():
                        embed_list[0].ta_status_changed(ta)
                        last_dss_info.tactical_action_statuses[ta.id] = ta.status
                        last_dss_info.save_changes()
                    dss_updates = True

        if dss_updates:
            for embed_list in embeds.values():
                embed_list[0].remove_empty()
            await self.bot.interface_handler.send_feature("dss_announcements", embeds)
            self.bot.logger.info(
                f"Sent DSS announcements out to {len(self.bot.interface_handler.dss_announcements)} channels"
            )
            self.bot.maps.update_planets(
                planets=self.bot.data.planets,
                active_planets=[
                    campaign.planet.index for campaign in self.bot.data.campaigns
                ],
            )
            self.bot.maps.update_dss(
                dss=self.bot.data.dss,
                type_3_campaigns=[c for c in self.bot.data.campaigns if c.type == 3],
            )
            for lang in unique_langs:
                lang_json = self.bot.json_dict["languages"][lang]
                self.bot.maps.localize_map(
                    language_code_short=lang,
                    language_code_long=lang_json["code_long"],
                    planets=self.bot.data.planets,
                    active_planets=[
                        campaign.planet.index for campaign in self.bot.data.campaigns
                    ],
                    type_3_campaigns=[
                        c for c in self.bot.data.campaigns if c.type == 3
                    ],
                    planet_names_json=self.bot.json_dict["planets"],
                )
                message = await self.bot.waste_bin_channel.send(
                    file=File(fp=self.bot.maps.FileLocations.localized_map_path(lang))
                )
                self.bot.maps.latest_maps[lang] = Maps.LatestMap(
                    datetime.now(), message.attachments[0].url
                )

    @dss_check.before_loop
    async def before_dss_check(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(WarUpdatesCog(bot))
