from asyncio import sleep
from disnake import Forbidden, TextChannel
from disnake.ext import commands, tasks
from helpers.db import Campaigns, Guilds
from helpers.embeds import CampaignEmbed
from helpers.api import API, Data
from datetime import datetime
from main import GalacticWideWebBot


class WarUpdatesCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.campaign_check.start()

    def cog_unload(self):
        self.campaign_check.stop()

    async def send_campaign(self, channel: TextChannel, embeds):
        guild = Guilds.get_info(channel.guild.id)
        if not guild:
            self.bot.announcement_channels.remove(channel)
            return self.bot.logger.error(
                f"WarUpdatesCog, send_campaign, guild == None, {channel.guild.id}"
            )
        try:
            await channel.send(embed=embeds[guild[5]])
        except Forbidden:
            self.bot.announcement_channels.remove(channel)
            self.bot.logger.error(
                f"WarUpdatesCog, send_campaign, Forbidden, removing, {channel.id}"
            )
        except Exception as e:
            self.bot.logger.error(f"WarUpdatesCog, send_campaign, {e}, {channel.id}")
            pass

    @tasks.loop(minutes=1)
    async def campaign_check(self):
        update_start = datetime.now()
        if self.bot.announcement_channels == [] or update_start.minute in (
            0,
            15,
            30,
            45,
        ):
            return
        api = API()
        await api.pull_from_api(
            get_planets=True,
            get_campaigns=True,
        )
        if api.error:
            return await self.bot.moderator_channel.send(
                f"<@164862382185644032>{api.error[0]}\n{api.error[1]}\n:warning:"
            )
        data = Data(data_from_api=api)
        old_campaigns = Campaigns.get_all()
        languages = Guilds.get_used_languages()
        embeds = {lang: CampaignEmbed(lang) for lang in languages}
        new_updates = False
        new_campaign_ids = [campaign.id for campaign in data.campaigns]
        if not data.campaigns:
            return
        if old_campaigns == []:
            for new_campaign in data.campaigns:
                Campaigns.new_campaign(
                    new_campaign.id,
                    new_campaign.planet.name,
                    new_campaign.planet.current_owner,
                    new_campaign.planet.index,
                )
            return
        old_campaign_ids = [old_campaign[0] for old_campaign in old_campaigns]
        liberation_changes: dict = self.bot.get_cog("DashboardCog").liberation_changes
        for old_campaign in old_campaigns:  # loop through old campaigns
            if old_campaign[0] not in new_campaign_ids:
                # if campaign is no longer active
                planet = data.planets[old_campaign[3]]
                if planet.current_owner == "Humans" and old_campaign[2] == "Humans":
                    # if successful defence campaign
                    for embed in embeds.values():
                        embed.add_def_victory(planet)
                    new_updates = True
                    liberation_changes.pop(planet.name, None)
                    Campaigns.remove_campaign(old_campaign[0])
                if planet.current_owner != old_campaign[2]:  # if owner has changed
                    if old_campaign[2] == "Humans":  # if defence campaign loss
                        for embed in embeds.values():
                            embed.add_planet_lost(planet)
                        new_updates = True
                        liberation_changes.pop(planet.name, None)
                        Campaigns.remove_campaign(old_campaign[0])
                    elif planet.current_owner == "Humans":  # if attack campaign win
                        for embed in embeds.values():
                            embed.add_campaign_victory(planet, old_campaign[2])
                        new_updates = True
                        liberation_changes.pop(planet.name, None)
                        Campaigns.remove_campaign(old_campaign[0])
                elif planet.current_owner != "Humans":
                    Campaigns.remove_campaign(old_campaign[0])
        for new_campaign in data.campaigns:  # loop through new campaigns
            if new_campaign.id not in old_campaign_ids:  # if campaign is brand new
                time_remaining = None
                if new_campaign.planet.event:
                    time_remaining = f"<t:{datetime.fromisoformat(new_campaign.planet.event.end_time).timestamp():.0f}:R>"
                for embed in embeds.values():
                    embed.add_new_campaign(new_campaign, time_remaining)
                new_updates = True
                Campaigns.new_campaign(
                    new_campaign.id,
                    new_campaign.planet.name,
                    new_campaign.planet.current_owner,
                    new_campaign.planet.index,
                )
            continue
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
                await sleep(1.025)
            self.bot.logger.info(
                f"{announcements_sent} war updates sent in {(datetime.now() - update_start).total_seconds():.2f} seconds"
            )
            self.bot.get_cog("StatsCog").announcements_sent += announcements_sent

    @campaign_check.before_loop
    async def before_campaign_check(self):
        await self.bot.wait_until_ready()


def setup(bot: GalacticWideWebBot):
    bot.add_cog(WarUpdatesCog(bot))
