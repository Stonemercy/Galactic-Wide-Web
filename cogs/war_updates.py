from asyncio import to_thread
from datetime import datetime, timedelta
from disnake import AppCmdInter, File, Permissions
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from os import getenv
from random import choice
from utils.checks import wait_for_startup
from utils.db import DSS as DSSDB, GWWGuild, Campaign
from utils.embeds.loop_embeds import CampaignLoopEmbed
from utils.maps import Maps

SUPPORT_SERVER = [int(getenv("SUPPORT_SERVER"))]


class WarUpdatesCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.campaign_check.start()

    def cog_unload(self):
        self.campaign_check.stop()

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
        old_campaigns: list[Campaign] = Campaign.get_all()
        languages = list({guild.language for guild in GWWGuild.get_all()})
        embeds = {
            lang: CampaignLoopEmbed(
                language_json=self.bot.json_dict["languages"][lang],
                planet_names_json=self.bot.json_dict["planets"],
            )
            for lang in languages
        }
        new_updates = False
        need_to_update_sectors = False
        if not old_campaigns:
            for new_campaign in self.bot.data.campaigns:
                Campaign.new(
                    id=new_campaign.id,
                    owner=new_campaign.planet.current_owner,
                    planet_index=new_campaign.planet.index,
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
        # loop through old campaigns
        for old_campaign in old_campaigns:

            # if campaign has ended
            if old_campaign.id not in new_campaign_ids:
                planet = self.bot.data.planets[old_campaign.planet_index]

                # if campaign was defence and we won
                if planet.current_owner == "Humans" and old_campaign.owner == "Humans":

                    # if event was invasion (no territory taken)
                    if old_campaign.event_type == 2:
                        previous_data_planet = self.bot.previous_data.planets[
                            old_campaign.planet_index
                        ]
                        win_status = False
                        hours_left = 0

                        # if I have data on the event (sometimes dont)
                        if previous_data_planet.event:
                            win_status = (
                                previous_data_planet.event.end_time_datetime
                                > update_start
                            )
                            hours_left = (
                                previous_data_planet.event.end_time_datetime
                                - update_start
                            ).total_seconds() / 3600
                        for embed in embeds.values():
                            embed.add_invasion_over(
                                planet=planet,
                                faction=old_campaign.event_faction,
                                hours_left=hours_left,
                                win_status=win_status,
                            )
                    else:
                        # if event wasnt invasion (territory taken)
                        for embed in embeds.values():
                            embed.add_def_victory(planet=planet)

                # if owner has changed
                if planet.current_owner != old_campaign.owner:

                    # if defence campaign loss
                    if old_campaign.owner == "Humans":
                        for embed in embeds.values():
                            embed.add_planet_lost(planet=planet)

                    # if attack campaign win
                    elif planet.current_owner == "Humans":
                        for embed in embeds.values():
                            embed.add_campaign_victory(
                                planet=planet, taken_from=old_campaign.owner
                            )
                self.bot.data.liberation_changes.remove_entry(planet_index=planet.index)
                Campaign.delete(old_campaign.id)
                new_updates = True
                need_to_update_sectors = True

        old_campaign_ids = [old_campaign.id for old_campaign in old_campaigns]
        # loop through old campaigns
        for new_campaign in self.bot.data.campaigns:

            # if campaign is brand new
            if new_campaign.id not in old_campaign_ids:

                # if campaign is an illuminate invasion but doesnt have the buildup data
                if (
                    new_campaign.planet.event
                    and new_campaign.planet.event.type == 2
                    and new_campaign.planet.event.potential_buildup == 0
                ):
                    continue
                time_remaining = (
                    None
                    if not new_campaign.planet.event
                    else f"<t:{new_campaign.planet.event.end_time_datetime.timestamp():.0f}:R>"
                )
                for embed in embeds.values():
                    embed.add_new_campaign(new_campaign, time_remaining)
                Campaign.new(
                    id=new_campaign.id,
                    owner=new_campaign.planet.current_owner,
                    planet_index=new_campaign.planet.index,
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

        # DSS updates
        if self.bot.data.dss != None and type(self.bot.data.dss) != str:
            last_dss_info = DSSDB()

            # if DSS has moved
            if last_dss_info.planet_index != self.bot.data.dss.planet.index:
                for embed in embeds.values():
                    embed.dss_moved(
                        before_planet=self.bot.data.planets[last_dss_info.planet_index],
                        after_planet=self.bot.data.dss.planet,
                    )
                last_dss_info.planet_index = self.bot.data.dss.planet.index
                last_dss_info.save_changes()
                new_updates = True
            for index, ta in enumerate(self.bot.data.dss.tactical_actions, 1):
                old_status = getattr(last_dss_info, f"ta{index}_status")
                if old_status != ta.status:
                    for embed in embeds.values():
                        embed.ta_status_changed(ta)
                    setattr(last_dss_info, f"ta{index}_status", ta.status)
                    last_dss_info.save_changes()
                    new_updates = True

        if new_updates:
            for embed in embeds.values():
                embed.remove_empty()
            await self.bot.interface_handler.send_news("Generic", embeds)
            self.bot.logger.info(
                f"Sent war announcements out to {len(self.bot.interface_handler.news_feeds.channels_dict['Generic'])} channels"
            )
            if need_to_update_sectors:
                await to_thread(
                    self.bot.maps.update_sectors, planets=self.bot.data.planets
                )
                self.bot.maps.update_waypoint_lines(planets=self.bot.data.planets)
            self.bot.maps.update_assignment_tasks(
                assignment=self.bot.data.assignment,
                planets=self.bot.data.planets,
                campaigns=self.bot.data.campaigns,
            )
            self.bot.maps.update_planets(
                planets=self.bot.data.planets,
                active_planets=[
                    campaign.planet.index for campaign in self.bot.data.campaigns
                ],
            )
            self.bot.maps.update_dss(dss=self.bot.data.dss)
            for lang in self.bot.json_dict["languages"].values():
                self.bot.maps.localize_map(
                    language_code_short=lang["code"],
                    language_code_long=lang["code_long"],
                    planets=self.bot.data.planets,
                    active_planets=[
                        campaign.planet.index for campaign in self.bot.data.campaigns
                    ],
                    dss=self.bot.data.dss,
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


def setup(bot: GalacticWideWebBot):
    bot.add_cog(WarUpdatesCog(bot))
