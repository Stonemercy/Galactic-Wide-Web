from asyncio import sleep
from disnake import Embed, Forbidden, NotFound, PartialMessage, TextChannel
from disnake.ext.commands import AutoShardedInteractionBot
from utils.dbv2 import Feature, GWWGuilds, GWWGuild as GWWGuild
from utils.interactables import WikiButton
from utils.mixins import ReprMixin

# Time to wait between feature updates to avoid rate limits (in seconds)
WAIT_TIME = 0.022


class InterfaceHandler:
    def __init__(self, bot: AutoShardedInteractionBot):
        self.wait_time = WAIT_TIME
        self.bot = bot
        self.busy = False
        self.loaded = False
        self.all_guilds = GWWGuilds(fetch_all=True)
        self.dashboards = BaseFeatureInteractionHandler(
            features=[
                f for g in self.all_guilds for f in g.features if f.name == "dashboards"
            ],
            bot=self.bot,
        )
        self.war_announcements = BaseFeatureInteractionHandler(
            features=[
                f
                for g in self.all_guilds
                for f in g.features
                if f.name == "war_announcements"
            ],
            bot=self.bot,
        )
        self.dss_announcements = BaseFeatureInteractionHandler(
            features=[
                f
                for g in self.all_guilds
                for f in g.features
                if f.name == "dss_announcements"
            ],
            bot=self.bot,
        )
        self.region_announcements = BaseFeatureInteractionHandler(
            features=[
                f
                for g in self.all_guilds
                for f in g.features
                if f.name == "region_announcements"
            ],
            bot=self.bot,
        )
        self.patch_notes = BaseFeatureInteractionHandler(
            features=[
                f
                for g in self.all_guilds
                for f in g.features
                if f.name == "patch_notes"
            ],
            bot=self.bot,
        )
        self.major_order_updates = BaseFeatureInteractionHandler(
            features=[
                f
                for g in self.all_guilds
                for f in g.features
                if f.name == "major_order_updates"
            ],
            bot=self.bot,
        )
        # self.personal_order_updates = BaseFeatureInteractionHandler(
        #     features=[
        #         f
        #         for g in self.all_guilds
        #         for f in g.features
        #         if f.name == "personal_order_updates"
        #     ],
        #     bot=self.bot,
        # )
        self.detailed_dispatches = BaseFeatureInteractionHandler(
            features=[
                f
                for g in self.all_guilds
                for f in g.features
                if f.name == "detailed_dispatches"
            ],
            bot=self.bot,
        )
        self.maps = BaseFeatureInteractionHandler(
            features=[
                f for g in self.all_guilds for f in g.features if f.name == "maps"
            ],
            bot=self.bot,
        )
        self.lists = {
            "dashboards": self.dashboards,
            "war_announcements": self.war_announcements,
            "dss_announcements": self.dss_announcements,
            "region_announcements": self.region_announcements,
            "patch_notes": self.patch_notes,
            "major_order_updates": self.major_order_updates,
            # "personal_order_updates": self.personal_order_updates,
            "detailed_dispatches": self.detailed_dispatches,
            "maps": self.maps,
        }

    async def populate_lists(self):
        number_of_guilds = len(self.all_guilds)
        for feature_type, feature_list in self.lists.items():
            feature_list.clear()
            await feature_list.populate()
            self.bot.logger.info(
                f"{len(feature_list)} {feature_type.replace('_', ' ')} {'messages' if feature_type in ('dashboards', 'maps') else 'channels'} ({(len(feature_list) / number_of_guilds):.1%})"
            )
        self.loaded = True
        self.bot.logger.info("InterfaceHandler has been populated")

    async def edit_dashboard(self, message: PartialMessage, embeds: list[Embed]):
        try:
            await message.edit(embeds=embeds)
        except (NotFound, Forbidden) as e:
            self.dashboards.remove(message)
            guild: GWWGuild = GWWGuilds.get_specific_guild(message.guild.id)
            guild.features = [f for f in guild.features if f.name != "dashboards"]
            guild.update_features()
            guild.save_changes()
            return self.bot.logger.error(
                f"edit_dashboard | {e} | reset in DB | {guild.guild_id = }"
            )
        except Exception as e:
            return self.bot.logger.error(
                f"edit_dashboard | {e} | {message.guild.id = }"
            )

    async def edit_map(self, message: PartialMessage, embed: Embed):
        try:
            await message.edit(embed=embed)
        except (NotFound, Forbidden) as e:
            self.maps.remove(message)
            guild: GWWGuild = GWWGuilds.get_specific_guild(message.guild.id)
            guild.features = [f for f in guild.features if f.name != "maps"]
            guild.update_features()
            guild.save_changes()
            return self.bot.logger.error(
                f"edit_map | {e} | reset in DB | {guild.guild_id = }"
            )
        except Exception as e:
            return self.bot.logger.error(f"edit_map | {e} | {message.guild.id = }")

    async def send_embeds(
        self,
        feature_type: str,
        channel: TextChannel,
        embeds: list[Embed],
        components: list,
    ):
        try:
            await channel.send(embeds=embeds, components=components)
        except (NotFound, Forbidden) as e:
            feature_list: list[Feature] = getattr(self, feature_type)
            if channel in feature_list:
                feature_list.remove(channel)
            guild: GWWGuild = GWWGuilds.get_specific_guild(channel.guild.id)
            guild.features = [f for f in guild.features if f.name != feature_type]
            guild.update_features()
            guild.save_changes()
            return self.bot.logger.error(
                f"send_embed | {feature_type} | {e} | reset in DB | {channel.guild.id = }"
            )
        except Exception as e:
            return self.bot.logger.error(f"send_embed | {e} | {channel.guild.id = }")

    async def send_feature(
        self, feature_type: str, content: dict, announcement_type: str = None
    ):
        self.busy = True
        list_to_use: BaseFeatureInteractionHandler = getattr(self, feature_type)
        components = None
        match feature_type:
            case "dashboards":
                for message in list_to_use.copy():
                    message: PartialMessage
                    guild: GWWGuild = GWWGuilds.get_specific_guild(message.guild.id)
                    if not guild:
                        list_to_use.remove(message)
                        self.bot.logger.error(
                            f"send_feature {feature_type} | guild not found in DB | {message.guild.id = }"
                        )
                        continue
                    else:
                        localized_dashboard = content.get(guild.language, content["en"])
                        self.bot.loop.create_task(
                            self.edit_dashboard(message, localized_dashboard.embeds)
                        )
                        await sleep(self.wait_time)
            case "maps":
                for message in list_to_use.copy():
                    message: PartialMessage
                    guild: GWWGuild = GWWGuilds.get_specific_guild(message.guild.id)
                    if not guild:
                        list_to_use.remove(message)
                        self.bot.logger.error(
                            f"send_feature {feature_type} | guild not found in DB | {message.guild.id = }"
                        )
                        continue
                    else:
                        self.bot.loop.create_task(
                            self.edit_map(message, content[guild.language])
                        )
                        await sleep(self.wait_time)
            case _:
                if announcement_type == "MO":
                    components = [
                        WikiButton(
                            link=f"https://helldivers.wiki.gg/wiki/Major_Orders#Recent"
                        )
                    ]
                else:
                    components = None
                for channel in list_to_use.copy():
                    channel: TextChannel
                    guild = GWWGuilds.get_specific_guild(channel.guild.id)
                    if not guild:
                        list_to_use.remove(channel)
                        self.bot.logger.error(
                            f"send_feature | guild not found in DB | {channel.guild.id = }"
                        )
                        continue
                    else:
                        self.bot.loop.create_task(
                            self.send_embeds(
                                feature_type,
                                channel,
                                content[guild.language],
                                components,
                            )
                        )
                        await sleep(self.wait_time)
        self.busy = False


class BaseFeatureInteractionHandler(list, ReprMixin):
    def __init__(self, features: list[Feature], bot: AutoShardedInteractionBot):
        self.features = features
        self.bot = bot

    async def populate(self):
        """Fills the list with PartialMessages or Channels"""
        for feature in self.features:
            try:
                channel = self.bot.get_channel(
                    feature.channel_id
                ) or await self.bot.fetch_channel(feature.channel_id)
                if feature.message_id:
                    message = channel.get_partial_message(feature.message_id)
                    self.append(message)
                else:
                    self.append(channel)
            except NotFound as e:
                guild: GWWGuild = GWWGuilds.get_specific_guild(id=feature.guild_id)
                if not guild:
                    self.bot.logger.error(
                        f"{feature.name}.populate() ERROR | {e} | not found in DB either | {feature.guild_id = }"
                    )
                    continue
                else:
                    guild.features = [
                        f for f in guild.features if f.name != feature.name
                    ]
                    guild.update_features()
                    guild.save_changes()
                    self.bot.logger.error(
                        f"{feature.name}.populate() ERROR | {e} | reset in DB | {guild.guild_id = }"
                    )
                self.remove_entry(feature.guild_id)
            except Exception as e:
                self.bot.logger.error(
                    f"{feature.name}.populate() ERROR | {e} | {feature.guild_id = }"
                )

    def add_entry(self, feature: Feature):
        if feature not in self:
            self.append(feature)

    def remove_entry(self, guild_id_to_remove: int):
        features_to_remove = [
            f for f in self.copy() if f.guild.id == guild_id_to_remove
        ]
        for feature in features_to_remove:
            if feature in self:
                self.remove(feature)
