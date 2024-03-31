from asyncio import sleep
from json import dumps, loads
from os import getenv
from aiohttp import ClientSession
from disnake import TextChannel
from disnake.ext import commands, tasks
from helpers.db import Campaigns, Guilds
from helpers.embeds import CampaignEmbeds


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
        api = getenv("API")
        async with ClientSession() as session:
            try:
                async with session.get(f"{api}/status") as r:
                    if r.status == 200:
                        js = await r.json()
                        self.status = loads(dumps(js))
                        await session.close()
                    else:
                        pass
            except Exception as e:
                print(("war updates - status", e))
        self.planet_status = self.status["planet_status"]
        self.new_campaigns = self.status["campaigns"]
        old_campaigns = Campaigns.get_all()

        new_campaign_ids = []
        for new_campaign_id in self.new_campaigns:
            new_campaign_ids.append(new_campaign_id["id"])

        if old_campaigns == []:
            for new_campaign in self.new_campaigns:
                for attacker in self.status["planet_events"]:
                    if new_campaign["planet"]["index"] == attacker["planet"]["index"]:
                        attacker_race = attacker["race"]
                    else:
                        attacker_race = "traitors to Democracy"
                Campaigns.new_campaign(
                    new_campaign["id"],
                    new_campaign["planet"]["name"],
                    self.status["planet_status"][new_campaign["planet"]["index"]][
                        "owner"
                    ],
                    self.status["planet_status"][new_campaign["planet"]["index"]][
                        "liberation"
                    ],
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
                    self.planet_status[new_campaign["planet"]["index"]],
                    attacker_race,
                    planet_thumbnail,
                )
                for channel in self.channels:
                    self.bot.loop.create_task(self.send_campaign(channel, embed))
                await sleep(1.0)
                continue
        campaign_ids = []
        for old_campaign in old_campaigns:
            campaign_ids.append(old_campaign[0])
            if old_campaign[0] not in new_campaign_ids:
                if (
                    self.planet_status[old_campaign[4]]["owner"] == "Humans"
                    and old_campaign[2] == "Humans"
                ):
                    embed = CampaignEmbeds.CampaignVictory(
                        self.planet_status[old_campaign[4]],
                        defended=True,
                        liberated_from=self.planet_status[old_campaign[4]]["planet"][
                            "initial_owner"
                        ],
                    )
                    for channel in self.channels:
                        self.bot.loop.create_task(self.send_campaign(channel, embed))
                    Campaigns.remove_campaign(old_campaign[0])
                if self.planet_status[old_campaign[4]]["owner"] != old_campaign[2]:
                    if old_campaign[2] == "Humans":
                        embed = CampaignEmbeds.CampaignLoss(
                            self.planet_status[old_campaign[4]],
                            defended=True,
                            liberator=self.planet_status[old_campaign[4]]["owner"],
                        )
                        for channel in self.channels:
                            self.bot.loop.create_task(
                                self.send_campaign(channel, embed)
                            )
                        Campaigns.remove_campaign(old_campaign[0])
                    elif self.planet_status[old_campaign[4]]["owner"] == "Humans":
                        embed = CampaignEmbeds.CampaignVictory(
                            self.planet_status[old_campaign[4]],
                            defended=False,
                            liberated_from=old_campaign[2],
                        )
                        for channel in self.channels:
                            self.bot.loop.create_task(
                                self.send_campaign(channel, embed)
                            )
                        Campaigns.remove_campaign(old_campaign[0])
        attacker_race = "traitors to Democracy"
        for def_campaign in self.new_campaigns:
            if def_campaign["id"] not in campaign_ids:
                for attacker in self.status["planet_events"]:
                    if def_campaign["planet"]["index"] == attacker["planet"]["index"]:
                        attacker_race = attacker["race"]
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
                    if def_campaign["planet"]["name"] == planet_tn["planet"]["name"]:
                        planet_thumbnail = (
                            f"https://helldivers.news{planet_tn['planet']['image']}"
                        )
                embed = CampaignEmbeds.NewCampaign(
                    def_campaign,
                    self.planet_status[def_campaign["planet"]["index"]],
                    attacker_race,
                    planet_thumbnail,
                )
                for j in self.channels:
                    self.bot.loop.create_task(self.send_campaign(j, embed))
                Campaigns.new_campaign(
                    def_campaign["id"],
                    def_campaign["planet"]["name"],
                    self.planet_status[def_campaign["planet"]["index"]]["owner"],
                    self.planet_status[def_campaign["planet"]["index"]]["liberation"],
                    def_campaign["planet"]["index"],
                )
            continue

    @campaign_check.before_loop
    async def before_dashboard(self):
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(WarUpdatesCog(bot))
