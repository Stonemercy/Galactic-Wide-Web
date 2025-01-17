from asyncio import sleep
from disnake import Forbidden, NotFound
from utils.db import GWWGuild
from utils.interactables import WikiButton


class InterfaceHandler:
    def __init__(self, bot):
        self.bot = bot
        self.busy = False
        self.loaded = False
        self.all_guilds: list[GWWGuild] = GWWGuild.get_all()
        self.dashboards = Dashboards(
            all_guilds=[
                guild
                for guild in self.all_guilds
                if guild.dashboard_channel_id and guild.dashboard_message_id
            ],
            bot=self.bot,
        )
        self.news_feeds = NewsFeeds(
            all_guilds=[
                guild for guild in self.all_guilds if guild.announcement_channel_id
            ],
            bot=self.bot,
        )
        self.maps = Maps(
            all_guilds=[
                guild
                for guild in self.all_guilds
                if guild.map_channel_id and guild.map_message_id
            ],
            bot=self.bot,
        )

    async def populate_lists(self):
        self.dashboards.clear()
        self.maps.clear()
        self.news_feeds.clear()
        await self.dashboards.populate()
        await self.news_feeds.populate()
        await self.maps.populate()
        self.loaded = True
        number_of_guilds = len(self.all_guilds)
        self.bot.logger.info(
            (
                f"populate_lists completed | "
                f"{len(self.dashboards)} dashboards ({(len(self.dashboards) / number_of_guilds):.0%}) | "
                f"{len(self.news_feeds.channels_dict['Generic'])} announcement channels ({(len(self.news_feeds.channels_dict['Generic']) / number_of_guilds):.0%}) | "
                f"{len(self.news_feeds.channels_dict['Patch'])} patch channels ({(len(self.news_feeds.channels_dict['Patch']) / number_of_guilds):.0%}) | "
                f"{len(self.news_feeds.channels_dict['MO'])} MO channels ({(len(self.news_feeds.channels_dict['MO']) / number_of_guilds):.0%}) | "
                f"{len(self.maps)} maps ({(len(self.maps) / number_of_guilds):.0%})"
            )
        )

    async def edit_dashboards(self, dashboards_dict: dict):
        self.busy = True

        async def edit_dashboard(message, embeds):
            try:
                await message.edit(embeds=embeds)
            except (NotFound, Forbidden) as e:
                self.dashboards.remove(message)
                guild = GWWGuild.get_by_id(message.guild.id)
                guild.dashboard_channel_id = 0
                guild.dashboard_message_id = 0
                guild.save_changes()
                return self.bot.logger.error(
                    f"edit_dashboard | {e} | removed from dashboards dict and reset in DB | {guild.id = }"
                )
            except Exception as e:
                return self.bot.logger.error(
                    f"edit_dashboard | {e} | {message.guild.id = }"
                )

        for message in self.dashboards.copy():
            guild = GWWGuild.get_by_id(message.guild.id)
            self.bot.loop.create_task(
                edit_dashboard(message, dashboards_dict[guild.language].embeds)
            )
            await sleep(0.03)  # discord accepts 1 message every 0.02s
        self.busy = False

    async def edit_maps(self, map_dict: dict):
        self.busy = True

        async def edit_map(message, embed):
            try:
                await message.edit(embed=embed)
            except (NotFound, Forbidden) as e:
                self.maps.remove(message)
                guild = GWWGuild.get_by_id(message.guild.id)
                guild.map_channel_id = 0
                guild.map_message_id = 0
                guild.save_changes()
                return self.bot.logger.error(
                    f"edit_map | {e} | removed from maps dict and reset in DB | {guild.id = }"
                )
            except Exception as e:
                return self.bot.logger.error(f"edit_map | {e} | {message.guild.id = }")

        for message in self.maps.copy():
            guild = GWWGuild.get_by_id(message.guild.id)
            self.bot.loop.create_task(edit_map(message, map_dict[guild.language]))
            await sleep(0.03)
        self.busy = False

    async def send_news(self, news_type: str, embeds_dict: dict):
        self.busy = True

        async def send_embed(channel, embed, components):
            try:
                await channel.send(embed=embed, components=components)
            except (NotFound, Forbidden) as e:
                for channels_list in self.news_feeds.channels_dict.values():
                    if channel in channels_list:
                        channels_list.remove(channel)
                guild = GWWGuild.get_by_id(channel.guild.id)
                guild.announcement_channel_id = 0
                guild.patch_notes = False
                guild.major_order_updates = False
                guild.save_changes()
                return self.bot.logger.error(
                    f"send_embed | {e} | removed from news feeds list and reset in DB | {guild.id = }"
                )
            except Exception as e:
                return self.bot.logger.error(f"send_embed | {e} | {guild.id = }")

        if news_type == "MO":
            components = [
                WikiButton(link=f"https://helldivers.wiki.gg/wiki/Major_Orders#Recent")
            ]
        else:
            components = None
        list_to_use = self.news_feeds.channels_dict[news_type]
        for channel in list_to_use.copy():
            guild = GWWGuild.get_by_id(channel.guild.id)
            self.bot.loop.create_task(
                send_embed(channel, embeds_dict[guild.language], components)
            )
            await sleep(0.03)
        self.busy = False


class Dashboards(list):
    """A list of all Dashboards configured"""

    def __init__(self, all_guilds: list[GWWGuild], bot):
        self.all_guilds = all_guilds
        self.bot = bot

    async def populate(self):
        """Fills the list with PartialMessages"""
        for guild in self.all_guilds:
            try:
                dashboard_channel = self.bot.get_channel(
                    guild.dashboard_channel_id
                ) or await self.bot.fetch_channel(guild.dashboard_channel_id)
                dashboard_message = dashboard_channel.get_partial_message(
                    guild.dashboard_message_id
                )
                self.append(dashboard_message)
            except NotFound as e:
                guild.dashboard_channel_id = 0
                guild.dashboard_message_id = 0
                guild.save_changes()
                self.bot.logger.error(
                    f"Dashboards.populate() ERROR | {e} | reset in DB | {guild.id = }"
                )
            except Exception as e:
                self.bot.logger.error(
                    f"Dashboards.populate() ERROR | {e} | {guild.id = }"
                )


class NewsFeeds:
    """All NewsFeeds configured"""

    def __init__(self, all_guilds: list[GWWGuild], bot):
        self.all_guilds = all_guilds
        self.bot = bot
        self.__announcement_channels__ = []
        self.__patch_note_channels__ = []
        self.__major_order_channels__ = []
        self.__personal_order_channels__ = []

    @property
    def channels_dict(self):
        return {
            "Generic": self.__announcement_channels__,
            "Patch": self.__patch_note_channels__,
            "MO": self.__major_order_channels__,
            "PO": self.__personal_order_channels__,
        }

    async def populate(self):
        """Fills the dicts with Channels"""
        for guild in self.all_guilds:
            try:
                announcement_channel = self.bot.get_channel(
                    guild.announcement_channel_id
                ) or await self.bot.fetch_channel(guild.announcement_channel_id)
                self.__announcement_channels__.append(announcement_channel)
                if guild.patch_notes:
                    self.__patch_note_channels__.append(announcement_channel)
                if guild.major_order_updates:
                    self.__major_order_channels__.append(announcement_channel)
                if guild.personal_order_updates:
                    self.__personal_order_channels__.append(announcement_channel)
            except NotFound as e:
                guild.announcement_channel_id = 0
                guild.patch_notes = False
                guild.major_order_updates = False
                guild.save_changes()
                self.bot.logger.error(
                    f"NewsFeeds.populate() ERROR | {e} | reset in DB | {guild.id = }"
                )
            except Exception as e:
                self.bot.logger.error(
                    f"NewsFeeds.populate() ERROR | {e} | {guild.id = }"
                )

    def clear(self):
        self.__announcement_channels__.clear()
        self.__patch_note_channels__.clear()
        self.__major_order_channels__.clear()
        self.__personal_order_channels__.clear()


class Maps(list):
    """A list of all Maps configured"""

    def __init__(self, all_guilds: list[GWWGuild], bot):
        self.all_guilds = all_guilds
        self.bot = bot

    async def populate(self):
        """Fills the dict with PartialMessages"""
        for guild in self.all_guilds:
            try:
                map_channel = self.bot.get_channel(
                    guild.map_channel_id
                ) or await self.bot.fetch_channel(guild.map_channel_id)
                map_message = map_channel.get_partial_message(guild.map_message_id)
                self.append(map_message)
            except NotFound as e:
                guild.map_channel_id = 0
                guild.map_message_id = 0
                guild.save_changes()
                self.bot.logger.error(
                    f"Maps.populate() ERROR | {e} | reset in DB | {guild.id = }"
                )
            except Exception as e:
                self.bot.logger.error(f"Maps.populate() ERROR | {e} | {guild.id = }")
