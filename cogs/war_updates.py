from asyncio import sleep
from datetime import datetime, timedelta
from disnake import AppCmdInter, Permissions, TextChannel
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from os import getenv
from random import choice
from utils.checks import wait_for_startup
from utils.db import DSS as DSSDB, GWWGuild, Campaign
from utils.embeds import CampaignEmbed
from utils.data import DSS

SUPPORT_SERVER = [int(getenv("SUPPORT_SERVER"))]


class WarUpdatesCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.campaign_check.start()

    def cog_unload(self):
        self.campaign_check.stop()

    async def send_campaign(self, channel: TextChannel, embeds):
        guild = GWWGuild.get_by_id(channel.guild.id)
        if not guild:
            self.bot.announcement_channels.remove(channel)
            return self.bot.logger.error(
                f"{self.qualified_name} | send_campaign | {guild = } | {channel.guild.id = }"
            )
        try:
            await channel.send(embed=embeds[guild.language])
        except Exception as e:
            self.bot.announcement_channels.remove(channel)
            self.bot.logger.error(
                f"{self.qualified_name} | send_campaign | {e} | {channel.id = }"
            )

    @tasks.loop(minutes=1)
    async def campaign_check(self):
        update_start = datetime.now()
        if (
            self.bot.announcement_channels == []
            or update_start.minute in (0, 15, 30, 45)
            or not self.bot.data.loaded
            or not self.bot.c_n_m_loaded
        ):
            return
        old_campaigns: list[Campaign] = Campaign.get_all()
        languages = list({guild.language for guild in GWWGuild.get_all()})
        embeds = {
            lang: CampaignEmbed(self.bot.json_dict["languages"][lang])
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
                        for embed in embeds.values():
                            embed.add_invasion_over(planet, old_campaign.event_faction)
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
            chunked_channels = [
                self.bot.announcement_channels[i : i + 50]
                for i in range(0, len(self.bot.announcement_channels), 50)
            ]
            announcements_sent = 0
            for chunk in chunked_channels:
                for channel in chunk:
                    self.bot.loop.create_task(self.send_campaign(channel, embeds))
                    announcements_sent += 1
                await sleep(1.1)
            self.bot.logger.info(
                f"{announcements_sent} war updates sent in {(datetime.now() - update_start).total_seconds():.2f} seconds"
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
        update_start = datetime.now()
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        languages = list({guild.language for guild in GWWGuild.get_all()})
        embeds = {
            lang: CampaignEmbed(self.bot.json_dict["languages"][lang])
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
                        if campaign.planet.event
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
                )
            else:
                embed.add_new_campaign(
                    self.bot.data.campaigns[0],
                    f"<t:{(datetime.now() + timedelta(days=2)).timestamp():.0f}:R>",
                )
            if self.bot.data.dss != "Error":
                embed.dss_moved(campaign, choice(list(self.bot.data.planets.values())))
                embed.ta_status_changed(choice(self.bot.data.dss.tactical_actions))

        for embed in embeds.values():
            embed.remove_empty()
        chunked_channels = [
            self.bot.announcement_channels[i : i + 50]
            for i in range(0, len(self.bot.announcement_channels), 50)
        ]
        announcements_sent = 0
        for chunk in chunked_channels:
            for channel in chunk:
                self.bot.loop.create_task(self.send_campaign(channel, embeds))
                announcements_sent += 1
            await sleep(1.1)
        self.bot.logger.info(
            f"{announcements_sent} war updates sent in {(datetime.now() - update_start).total_seconds():.2f} seconds"
        )
        await inter.send(
            f"{announcements_sent} war updates sent in {(datetime.now() - update_start).total_seconds():.2f} seconds",
            ephemeral=True,
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(WarUpdatesCog(bot))
