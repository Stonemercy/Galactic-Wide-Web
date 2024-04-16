from asyncio import sleep
from json import dumps, loads
from aiohttp import ClientSession
from disnake import TextChannel
from disnake.ext import commands, tasks
from helpers.db import Campaigns, Guilds
from helpers.embeds import CampaignEmbeds
from helpers.functions import pull_from_api
from datetime import datetime


class WarUpdatesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channels = []
        self.campaign_check.start()
        self.cache_channels.start()
        print("War Updates cog has finished loading")

    def cog_unload(self):
        self.campaign_check.stop()
        self.cache_channels.stop()

    async def channel_list_gen(self, channel_id: int):
        try:
            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(
                channel_id
            )
            self.channels.append(channel)
        except:
            print(channel_id, "channel not found")
            pass

    async def send_campaign(self, channel: TextChannel, embed):
        try:
            await channel.send(embed=embed)
        except Exception as e:
            print("Send campaign", e, channel)
            pass

    @tasks.loop(count=1)
    async def cache_channels(self):
        guilds = Guilds.get_all_guilds()
        if not guilds:
            return
        self.channels = []
        for guild in guilds:
            if guild[3] == 0:
                continue
            self.bot.loop.create_task(self.channel_list_gen(guild[3]))

    @cache_channels.before_loop
    async def before_caching(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def campaign_check(self):
        data = await pull_from_api(
            get_planets=True, get_campaigns=True, get_war_state=True
        )
        self.planets = data["planets"]
        self.war = data["war_state"]
        self.new_campaigns = data["campaigns"]
        old_campaigns = Campaigns.get_all()

        new_campaign_ids = []
        for campaign in self.new_campaigns:
            new_campaign_ids.append(campaign["id"])

        if old_campaigns == []:
            for new_campaign in self.new_campaigns:
                if new_campaign["planet"]["event"] != None:
                    attacker_race = new_campaign["planet"]["event"]["faction"]
                else:
                    attacker_race = "traitors to Democracy"
                Campaigns.new_campaign(
                    new_campaign["id"],
                    new_campaign["planet"]["name"],
                    new_campaign["planet"]["currentOwner"],
                    new_campaign["planet"]["index"],
                )

                async with ClientSession() as session:
                    try:
                        async with session.get(
                            f"https://helldivers.news/api/planets"
                        ) as r:
                            if r.status == 200:
                                js = await r.json()
                                self.planet_thumbnails = loads(dumps(js))
                                await session.close()
                            else:
                                pass
                    except Exception as e:
                        print(("Planet Thumbnail", e))
                planet_thumbnail = None
                for planet_tn in self.planet_thumbnails:
                    if new_campaign["planet"]["name"] == planet_tn["planet"]["name"]:
                        planet_thumbnail = (
                            f"https://helldivers.news{planet_tn['planet']['image']}"
                        )

                embed = CampaignEmbeds.NewCampaign(
                    new_campaign,
                    new_campaign["planet"],
                    attacker_race,
                    planet_thumbnail,
                )
                chunked_channels = [
                    self.channels[i : i + 50] for i in range(0, len(self.channels), 50)
                ]
                for chunk in chunked_channels:
                    for channel in chunk:
                        self.bot.loop.create_task(self.send_campaign(channel, embed))
                    await sleep(2)
                continue
        campaign_ids = []
        for old_campaign in old_campaigns:  # loop through old campaigns
            campaign_ids.append(old_campaign[0])
            if old_campaign[0] not in new_campaign_ids:  # if campaign is not active
                if (
                    self.planets[old_campaign[3]]["currentOwner"] == "Humans"
                    and old_campaign[2] == "Humans"
                    # if current owner of the planet is human and the old owner is human (successful defence campaign)
                ):
                    embed = CampaignEmbeds.CampaignVictory(
                        self.planets[old_campaign[3]],
                        defended=True,
                    )
                    chunked_channels = [
                        self.channels[i : i + 50]
                        for i in range(0, len(self.channels), 50)
                    ]
                    for chunk in chunked_channels:
                        for channel in chunk:
                            self.bot.loop.create_task(
                                self.send_campaign(channel, embed)
                            )
                        await sleep(2)
                    Campaigns.remove_campaign(old_campaign[0])
                if (
                    self.planets[old_campaign[3]]["currentOwner"] != old_campaign[2]
                ):  # if new owner doesnt equal old owner
                    if (
                        old_campaign[2] == "Humans"
                    ):  # if old owner was humans (defence campaign loss)
                        embed = CampaignEmbeds.CampaignLoss(
                            self.planets[old_campaign[3]],
                            defended=True,
                            liberator=self.planets[old_campaign[3]]["currentOwner"],
                        )
                        chunked_channels = [
                            self.channels[i : i + 50]
                            for i in range(0, len(self.channels), 50)
                        ]
                        for chunk in chunked_channels:
                            for channel in chunk:
                                self.bot.loop.create_task(
                                    self.send_campaign(channel, embed)
                                )
                            await sleep(2)
                        Campaigns.remove_campaign(old_campaign[0])
                    elif (
                        self.planets[old_campaign[3]]["currentOwner"] == "Humans"
                    ):  # if new owner is humans (attack campaign win)
                        embed = CampaignEmbeds.CampaignVictory(
                            self.planets[old_campaign[3]],
                            defended=False,
                            liberated_from=old_campaign[2],
                        )
                        chunked_channels = [
                            self.channels[i : i + 50]
                            for i in range(0, len(self.channels), 50)
                        ]
                        for chunk in chunked_channels:
                            for channel in chunk:
                                self.bot.loop.create_task(
                                    self.send_campaign(channel, embed)
                                )
                        await sleep(2)
                        Campaigns.remove_campaign(old_campaign[0])
        attacker_race = "traitors to Democracy"
        for new_campaign in self.new_campaigns:  # loop through new campaigns
            if (
                new_campaign["id"] not in campaign_ids
            ):  # if campaign is brand new (not in db)
                if (
                    new_campaign["planet"]["event"] != None
                ):  # check if campaign is a defence campaign (for attacker_race)
                    attacker_race = new_campaign["planet"]["event"]["faction"]
                async with ClientSession() as session:
                    try:
                        async with session.get(
                            f"https://helldivers.news/api/planets"
                        ) as r:
                            if r.status == 200:
                                js = await r.json()
                                self.planet_thumbnails = loads(
                                    dumps(js)
                                )  # getting planet thumbnails
                                await session.close()
                            else:
                                pass
                    except Exception as e:
                        print(("Planet Thumbnail", e))
                planet_thumbnail = None
                for (
                    planet_tn
                ) in self.planet_thumbnails:  # loop through posted thumbnails
                    if (
                        new_campaign["planet"]["name"] == planet_tn["planet"]["name"]
                    ):  # check if new campaign planet name is in the list of planet thumbnails
                        thumbnail_url: str = planet_tn["planet"]["image"]
                        thumbnail_url = thumbnail_url.replace(" ", "%20")
                        planet_thumbnail = f"https://helldivers.news{thumbnail_url}"
                try:
                    war_now = datetime.fromisoformat(self.war["now"]).timestamp()
                except Exception as e:
                    print("war_now", e)
                    war_now = None
                try:
                    end_time = datetime.fromisoformat(
                        new_campaign["planet"]["event"]["endTime"]
                    ).timestamp()
                except Exception as e:
                    print("end_time", e)
                    end_time = None
                current_time = datetime.now().timestamp()
                if war_now != None and current_time != None and end_time != None:
                    time_remaining = (
                        f"<t:{((current_time - war_now) + end_time):.0f}:R>"
                    )
                else:
                    time_remaining = "Unavailable"
                embed = CampaignEmbeds.NewCampaign(
                    new_campaign,
                    self.planets[new_campaign["planet"]["index"]],
                    attacker_race,
                    planet_thumbnail,
                    time_remaining,
                )
                chunked_channels = [
                    self.channels[i : i + 50] for i in range(0, len(self.channels), 50)
                ]
                for chunk in chunked_channels:
                    for channel in chunk:
                        self.bot.loop.create_task(self.send_campaign(channel, embed))
                    await sleep(2)
                Campaigns.new_campaign(
                    new_campaign["id"],
                    new_campaign["planet"]["name"],
                    self.planets[new_campaign["planet"]["index"]]["currentOwner"],
                    new_campaign["planet"]["index"],
                )
            continue

    @campaign_check.before_loop
    async def before_dashboard(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(WarUpdatesCog(bot))
