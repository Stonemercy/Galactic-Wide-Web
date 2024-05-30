from asyncio import sleep
from logging import getLogger
from disnake import Forbidden, TextChannel
from disnake.ext import commands, tasks
from helpers.db import Campaigns, Guilds
from helpers.embeds import CampaignEmbed
from helpers.functions import pull_from_api
from datetime import datetime

logger = getLogger("disnake")


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
            return logger.error(
                f"WarUpdatesCog, send_campaign, guild == None, {channel.guild.id}"
            )
        try:
            await channel.send(embed=embeds[guild[5]])
        except Forbidden:
            self.channels.remove(channel)
            logger.error(
                f"WarUpdatesCog, send_campaign, Forbidden, removing, {channel.id}"
            )
        except Exception as e:
            logger.error(f"WarUpdatesCog, send_campaign, {e}, {channel.id}")
            pass

    @tasks.loop(minutes=1)
    async def campaign_check(self):
        if len(self.channels) == 0 or datetime.now().minute in (0, 1, 15, 30, 45):
            return
        data = await pull_from_api(
            get_planets=True,
            get_campaigns=True,
        )
        for data_key, data_value in data.items():
            if data_value == None:
                logger.error(
                    f"WarUpdatesCog, campaign_check, {data_key} returned {data_value}"
                )
                return
        planets = data["planets"]
        new_campaigns = data["campaigns"]
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
            new_campaign_ids.append(campaign["id"])
        if old_campaigns == []:
            for new_campaign in new_campaigns:
                Campaigns.new_campaign(
                    new_campaign["id"],
                    new_campaign["planet"]["name"],
                    new_campaign["planet"]["currentOwner"],
                    new_campaign["planet"]["index"],
                )
            return
        old_campaign_ids = []
        for old_campaign in old_campaigns:  # loop through old campaigns
            old_campaign_ids.append(old_campaign[0])
            if old_campaign[0] not in new_campaign_ids:
                # if campaign is no longer active
                planet = planets[old_campaign[3]]
                if planet["currentOwner"] == "Humans" and old_campaign[2] == "Humans":
                    # if successful defence campaign
                    for lang, embed in embeds.items():
                        embed.add_def_victory(planet)
                    new_updates = True
                    Campaigns.remove_campaign(old_campaign[0])
                if planet["currentOwner"] != old_campaign[2]:  # if owner has changed
                    if old_campaign[2] == "Humans":  # if defence campaign loss
                        for lang, embed in embeds.items():
                            embed.add_planet_lost(planet)
                        new_updates = True
                        Campaigns.remove_campaign(old_campaign[0])
                    elif planet["currentOwner"] == "Humans":  # if attack campaign win
                        for lang, embed in embeds.items():
                            embed.add_campaign_victory(planet, old_campaign[2])
                        new_updates = True
                        Campaigns.remove_campaign(old_campaign[0])
                elif planet["currentOwner"] != "Humans":
                    Campaigns.remove_campaign(old_campaign[0])
        for new_campaign in new_campaigns:  # loop through new campaigns
            if new_campaign["id"] not in old_campaign_ids:  # if campaign is brand new
                planet = planets[new_campaign["planet"]["index"]]
                time_remaining = None
                if new_campaign["planet"]["event"] != None:
                    time_remaining = f"<t:{datetime.fromisoformat(new_campaign['planet']['event']['endTime']).timestamp():.0f}:R>"
                for lang, embed in embeds.items():
                    embed.add_new_campaign(new_campaign, time_remaining)
                new_updates = True
                Campaigns.new_campaign(
                    new_campaign["id"],
                    new_campaign["planet"]["name"],
                    planet["currentOwner"],
                    new_campaign["planet"]["index"],
                )
            continue
        if new_updates:
            for lang, embed in embeds.items():
                embed.remove_empty()
            chunked_channels = [
                self.channels[i : i + 50] for i in range(0, len(self.channels), 50)
            ]
            update_start = datetime.now()
            announcements_sent = 0
            for chunk in chunked_channels:
                for channel in chunk:
                    self.bot.loop.create_task(self.send_campaign(channel, embeds))
                    announcements_sent += 1
                await sleep(1.025)
            logger.info(
                f"Sent {announcements_sent} announcements in {(datetime.now() - update_start).total_seconds():.2} seconds"
            )

    @campaign_check.before_loop
    async def before_campaign_check(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(WarUpdatesCog(bot))
