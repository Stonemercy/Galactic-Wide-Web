from datetime import datetime, timedelta
from disnake import AppCmdInter, Permissions
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from os import getenv
from random import choice
from utils.checks import wait_for_startup
from utils.db import DSS as DSSDB, GWWGuild, Campaign
from utils.embeds.loop_embeds import CampaignLoopEmbed
from utils.data import DSS

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
                self.bot.json_dict["languages"][lang], self.bot.json_dict["planets"]
            )
            for lang in languages
        }
        new_updates = False
        new_campaign_ids = [campaign.id for campaign in self.bot.data.campaigns]
        if not old_campaigns:
            for new_campaign in self.bot.data.campaigns:
                Campaign.new(
                    new_campaign.id,
                    new_campaign.planet.current_owner,
                    new_campaign.planet.index,
                    new_campaign.planet.event is not None,
                    (
                        new_campaign.planet.event.type
                        if new_campaign.planet.event
                        else None
                    ),
                    (
                        new_campaign.planet.event.faction
                        if new_campaign.planet.event
                        else None
                    ),
                )
            return
        old_campaign_ids = [old_campaign.id for old_campaign in old_campaigns]
        for old_campaign in old_campaigns:  # loop through old campaigns
            if old_campaign.id not in new_campaign_ids:
                # if campaign is no longer active
                planet = self.bot.data.planets[old_campaign.planet_index]
                if planet.current_owner == "Humans" and old_campaign.owner == "Humans":
                    if old_campaign.event_type == 2:
                        old_planet = self.bot.previous_data.planets[
                            old_campaign.planet_index
                        ]
                        win_status = False
                        hours_left = 0
                        if old_planet.event:
                            win_status = (
                                old_planet.event.end_time_datetime > datetime.now()
                            )
                            hours_left = (
                                old_planet.event.end_time_datetime - datetime.now()
                            ).total_seconds() / 3600
                        for embed in embeds.values():
                            embed.add_invasion_over(
                                planet,
                                old_campaign.event_faction,
                                hours_left=hours_left,
                                win_status=win_status,
                            )
                    else:
                        for embed in embeds.values():
                            embed.add_def_victory(planet)
                    new_updates = True
                    self.bot.data.liberation_changes.pop(planet.index, None)
                    Campaign.delete(old_campaign.id)
                if planet.current_owner != old_campaign.owner:  # if owner has changed
                    if old_campaign.owner == "Humans":  # if defence campaign loss
                        for embed in embeds.values():
                            embed.add_planet_lost(planet)
                        new_updates = True
                        self.bot.data.liberation_changes.pop(planet.index, None)
                        Campaign.delete(old_campaign.id)
                    elif planet.current_owner == "Humans":  # if attack campaign win
                        for embed in embeds.values():
                            embed.add_campaign_victory(planet, old_campaign.owner)
                        new_updates = True
                        self.bot.data.liberation_changes.pop(planet.index, None)
                        Campaign.delete(old_campaign.id)
                elif planet.current_owner != "Humans":
                    Campaign.delete(old_campaign.id)
        for new_campaign in self.bot.data.campaigns:  # loop through new campaigns
            if new_campaign.id not in old_campaign_ids:  # if campaign is brand new
                time_remaining = (
                    None
                    if not new_campaign.planet.event
                    else f"<t:{datetime.fromisoformat(new_campaign.planet.event.end_time).timestamp():.0f}:R>"
                )
                for embed in embeds.values():
                    embed.add_new_campaign(new_campaign, time_remaining)
                new_updates = True
                Campaign.new(
                    new_campaign.id,
                    new_campaign.planet.current_owner,
                    new_campaign.planet.index,
                    new_campaign.planet.event is not None,
                    (
                        new_campaign.planet.event.type
                        if new_campaign.planet.event
                        else None
                    ),
                    (
                        new_campaign.planet.event.faction
                        if new_campaign.planet.event
                        else None
                    ),
                )
            continue

        # DSS STUFF
        if self.bot.data.dss != "Error":
            last_dss_info = DSSDB()
            if last_dss_info.planet_index != self.bot.data.dss.planet.index:
                for embed in embeds.values():
                    embed.dss_moved(
                        self.bot.data.planets[last_dss_info.planet_index],
                        self.bot.data.dss.planet,
                    )
                last_dss_info.planet_index = self.bot.data.dss.planet.index
                last_dss_info.save_changes()
                new_updates = True
            for index, ta in enumerate(self.bot.data.dss.tactical_actions, 1):
                ta: DSS.TacticalAction
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

    @campaign_check.before_loop
    async def before_campaign_check(self):
        await self.bot.wait_until_ready()

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER,
        description="Test announcements",
        default_member_permissions=Permissions(administrator=True),
    )
    async def test_announcements(self, inter: AppCmdInter):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        languages = list({guild.language for guild in GWWGuild.get_all()})
        embeds = {
            lang: CampaignLoopEmbed(
                self.bot.json_dict["languages"][lang], self.bot.json_dict["planets"]
            )
            for lang in languages
        }
        campaign = choice(self.bot.data.campaigns)
        for embed in embeds.values():
            embed.add_campaign_victory(
                campaign.planet, choice(["Terminids", "Automaton", "Illuminate"])
            )
            embed.add_new_campaign(campaign, None)
            if self.bot.data.planet_events:
                def_campaign = choice(
                    [
                        campaign
                        for campaign in self.bot.data.campaigns
                        if campaign.planet.event and campaign.planet.event.type == 2
                    ]
                )
                embed.add_new_campaign(
                    def_campaign,
                    f"<t:{datetime.fromisoformat(self.bot.data.planet_events[0].event.end_time).timestamp():.0f}:R>",
                )
                embed.add_def_victory(def_campaign.planet)
                embed.add_planet_lost(def_campaign.planet)
                embed.add_invasion_over(
                    def_campaign.planet,
                    choice(["Terminids", "Automaton", "Illuminate"]),
                    win_status=True,
                    hours_left=(
                        def_campaign.planet.event.end_time_datetime - datetime.now()
                    ).total_seconds()
                    / 3600,
                )
                embed.add_invasion_over(
                    def_campaign.planet,
                    choice(["Terminids", "Automaton", "Illuminate"]),
                    win_status=False,
                )
            else:
                embed.add_new_campaign(
                    self.bot.data.campaigns[0],
                    f"<t:{(datetime.now() + timedelta(days=2)).timestamp():.0f}:R>",
                )
            if self.bot.data.dss != "Error":
                embed.dss_moved(
                    campaign.planet, choice(list(self.bot.data.planets.values()))
                )
                embed.ta_status_changed(choice(self.bot.data.dss.tactical_actions))

        for embed in embeds.values():
            embed.remove_empty()
        await self.bot.interface_handler.send_news("Generic", embeds)
        text = f"Sent test announcements out to {len(self.bot.interface_handler.news_feeds.channels_dict['Generic'])} channels"
        await inter.send(text, ephemeral=True)
        self.bot.logger.info(text)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(WarUpdatesCog(bot))
