from asyncio import sleep
from disnake import Forbidden, TextChannel
from disnake.ext import commands, tasks
from helpers.db import Campaigns, Guilds
from helpers.embeds import CampaignEmbed
from helpers.api import API, Data
from datetime import datetime


class WarUpdatesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channels = []
        self.campaign_check.start()

    def cog_unload(self):
        self.campaign_check.stop()

    async def send_campaign(self, channel: TextChannel, embeds):
        guild = Guilds.get_info(channel.guild.id)
        if guild == None:
            self.channels.remove(channel)
            return self.bot.logger.error(
                f"WarUpdatesCog, send_campaign, guild == None, {channel.guild.id}"
            )
        try:
            await channel.send(embed=embeds[guild[5]])
        except Forbidden:
            self.channels.remove(channel)
            self.bot.logger.error(
                f"WarUpdatesCog, send_campaign, Forbidden, removing, {channel.id}"
            )
        except Exception as e:
            self.bot.logger.error(f"WarUpdatesCog, send_campaign, {e}, {channel.id}")
            pass

    @tasks.loop(minutes=1)
    async def campaign_check(self):
        update_start = datetime.now()
        if self.channels == [] or update_start.minute in (0, 15, 30, 45):
            return
        api = API()
        await api.pull_from_api(
            get_planets=True,
            get_campaigns=True,
        )
        if api.error:
            error_channel = self.bot.get_channel(
                1212735927223590974
            ) or await self.bot.fetch_channel(1212735927223590974)
            return await error_channel.send(
                f"<@164862382185644032>{api.error[0]}\n{api.error[1]}\n:warning:"
            )
        data = Data(data_from_api=api)
        planets = data.planets
        new_campaigns = data.campaigns
        old_campaigns = Campaigns.get_all()
        languages = Guilds.get_used_languages()
        embeds: dict[str, CampaignEmbed] = {}
        for lang in languages:
            embeds[lang] = CampaignEmbed(lang)
        new_updates = False
        new_campaign_ids = []
        if new_campaigns == None:
            return
        for campaign in new_campaigns:
            new_campaign_ids.append(campaign.id)
        if old_campaigns == []:
            for new_campaign in new_campaigns:
                Campaigns.new_campaign(
                    new_campaign.id,
                    new_campaign.planet.name,
                    new_campaign.planet.current_owner,
                    new_campaign.planet.index,
                )
            return
        old_campaign_ids = []
        liberation_changes: dict = self.bot.get_cog("DashboardCog").liberation_changes
        for old_campaign in old_campaigns:  # loop through old campaigns
            old_campaign_ids.append(old_campaign[0])
            if old_campaign[0] not in new_campaign_ids:
                # if campaign is no longer active
                planet = planets[old_campaign[3]]
                if planet.current_owner == "Humans" and old_campaign[2] == "Humans":
                    # if successful defence campaign
                    for lang, embed in embeds.items():
                        embed.add_def_victory(planet)
                    new_updates = True
                    liberation_changes.pop(planet.name, None)
                    Campaigns.remove_campaign(old_campaign[0])
                if planet.current_owner != old_campaign[2]:  # if owner has changed
                    if old_campaign[2] == "Humans":  # if defence campaign loss
                        for lang, embed in embeds.items():
                            embed.add_planet_lost(planet)
                        new_updates = True
                        liberation_changes.pop(planet.name, None)
                        Campaigns.remove_campaign(old_campaign[0])
                    elif planet.current_owner == "Humans":  # if attack campaign win
                        for lang, embed in embeds.items():
                            embed.add_campaign_victory(planet, old_campaign[2])
                        new_updates = True
                        liberation_changes.pop(planet.name, None)
                        Campaigns.remove_campaign(old_campaign[0])
                elif planet.current_owner != "Humans":
                    Campaigns.remove_campaign(old_campaign[0])
        for new_campaign in new_campaigns:  # loop through new campaigns
            if new_campaign.id not in old_campaign_ids:  # if campaign is brand new
                time_remaining = None
                if new_campaign.planet.event:
                    time_remaining = f"<t:{datetime.fromisoformat(new_campaign.planet.event.end_time).timestamp():.0f}:R>"
                for lang, embed in embeds.items():
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
            for lang, embed in embeds.items():
                embed.remove_empty()
            chunked_channels = [
                self.channels[i : i + 50] for i in range(0, len(self.channels), 50)
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


def setup(bot: commands.Bot):
    bot.add_cog(WarUpdatesCog(bot))
