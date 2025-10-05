from datetime import datetime, timedelta
from disnake import (
    AppCmdInter,
    ButtonStyle,
    Colour,
    Embed,
    File,
    InteractionContextTypes,
    InteractionTimedOut,
    MessageInteraction,
    NotFound,
    Permissions,
    ui,
)
from disnake.ext import commands
from disnake.ui import ActionRow
from main import GalacticWideWebBot
from utils.containers import SetupContainer
from utils.checks import wait_for_startup
from utils.dbv2 import Feature, GWWGuild, GWWGuilds
from utils.embeds import Dashboard
from utils.maps import Maps
from utils.setup import Setup

CURRENT_FEATURES = [
    "war_announcements",
    "dss_announcements",
    "region_announcements",
    "patch_notes",
    "major_order_updates",
    "detailed_dispatches",
]

FEATURE_INDEXES = {
    "war_announcements": 7,
    "dss_announcements": 9,
    "region_announcements": 11,
    "patch_notes": 13,
    "major_order_updates": 15,
    "detailed_dispatches": 17,
}


class SetupCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.dashboard_perms_needed = Permissions(
            view_channel=True,
            send_messages=True,
            attach_files=True,
            use_external_emojis=True,
            embed_links=True,
        )
        self.annnnouncement_perms_needed = Permissions(
            view_channel=True,
            send_messages=True,
            use_external_emojis=True,
        )
        self.map_perms_needed = Permissions(
            view_channel=True,
            send_messages=True,
            attach_files=True,
            embed_links=True,
        )

    def reset_row(self, action_row: ActionRow):
        for button in action_row.children:
            if button.disabled:
                button.disabled = False
                button.emoji = None
                button.style = ButtonStyle.gray

    def clear_extra_buttons(self, action_rows: list[ActionRow], from_row: int = 1):
        for action_row in action_rows[from_row:]:
            action_rows.remove(action_row)

    @wait_for_startup()
    @commands.slash_command(
        description="Change GWW settings.",
        default_member_permissions=Permissions(manage_guild=True),
        contexts=InteractionContextTypes(guild=True),
        extras={
            "long_description": "Change the GWW settings for your server.",
            "example_usage": "**`/setup`** brings up a message with buttons you can use to change the bot's settings.",
        },
    )
    async def setup(
        self,
        inter: AppCmdInter,
    ):
        try:
            await inter.response.defer(ephemeral=True)
        except (NotFound, InteractionTimedOut):
            await inter.channel.send(
                "There was an error with that command, please try again.",
                delete_after=5,
            )
            return
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name}"
        )
        guild = GWWGuilds.get_specific_guild(id=inter.guild_id)
        if not guild:
            self.bot.logger.error(
                f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
            )
            guild: GWWGuild = GWWGuilds.add(inter.guild_id, "en", [])
        await inter.send(
            components=SetupContainer(
                guild=guild,
                container_json=self.bot.json_dict["languages"][guild.language][
                    "containers"
                ]["SetupContainer"],
                language_code=guild.language,
                shard_info=self.bot.shards[inter.guild.shard_id],
            )
        )

    @commands.Cog.listener("on_button_click")
    async def on_button_clicks(self, inter: MessageInteraction):
        allowed_ids = {
            "set_dashboard_button",
            "clear_dashboard_button",
            "set_map_button",
            "clear_map_button",
            "language_button",
        }
        if (
            inter.component.custom_id not in allowed_ids
            and "set_feature_button-" not in inter.component.custom_id
            and "clear_feature_button-" not in inter.component.custom_id
            and "features_button" not in inter.component.custom_id
        ):
            return
        try:
            await inter.response.defer()
        except (NotFound, InteractionTimedOut):
            await inter.channel.send(
                "There was an error with this interaction, please try again.",
                delete_after=5,
            )
            return
        guild: GWWGuild = GWWGuilds.get_specific_guild(inter.guild_id)
        guild_language = self.bot.json_dict["languages"][guild.language]
        container = ui.Container.from_component(inter.message.components[0])
        if "dashboard" in inter.component.custom_id:
            if inter.component.custom_id == "set_dashboard_button":
                container = SetupContainer(
                    guild=guild,
                    container_json=guild_language["containers"]["SetupContainer"],
                    language_code=guild.language,
                    shard_info=self.bot.shards[inter.guild.shard_id],
                )
                container.children.insert(
                    3,
                    ui.ActionRow(
                        Setup.Dashboard.DashboardChannelSelect(
                            container_json=guild_language["containers"][
                                "SetupContainer"
                            ]
                        )
                    ),
                )
                await inter.edit_original_response(components=container)
                return
            elif inter.component.custom_id == "clear_dashboard_button":
                try:
                    message = [
                        m
                        for m in self.bot.interface_handler.dashboards
                        if m.guild.id == guild.guild_id
                    ][0]
                    await message.delete()
                except:
                    pass
                guild.features = [f for f in guild.features if f.name != "dashboards"]
                guild.update_features()
                guild.save_changes()
                self.bot.interface_handler.dashboards.remove_entry(guild.guild_id)
                await inter.edit_original_response(
                    components=SetupContainer(
                        guild=guild,
                        container_json=self.bot.json_dict["languages"][guild.language][
                            "containers"
                        ]["SetupContainer"],
                        language_code=guild.language,
                        shard_info=self.bot.shards[inter.guild.shard_id],
                    )
                )
                return
        elif "map" in inter.component.custom_id:
            if inter.component.custom_id == "set_map_button":
                container = SetupContainer(
                    guild=guild,
                    container_json=guild_language["containers"]["SetupContainer"],
                    language_code=guild.language,
                    shard_info=self.bot.shards[inter.guild.shard_id],
                )
                container.children.insert(
                    5,
                    ui.ActionRow(
                        Setup.Map.MapChannelSelect(
                            container_json=guild_language["containers"][
                                "SetupContainer"
                            ]
                        )
                    ),
                )
                await inter.edit_original_response(components=container)
                return
            elif inter.component.custom_id == "clear_map_button":
                try:
                    message = [
                        m
                        for m in self.bot.interface_handler.maps
                        if m.guild.id == guild.guild_id
                    ][0]
                    await message.delete()
                except:
                    pass
                guild.features = [f for f in guild.features if f.name != "maps"]
                guild.update_features()
                guild.save_changes()
                self.bot.interface_handler.maps.remove_entry(guild.guild_id)
                await inter.edit_original_response(
                    components=SetupContainer(
                        guild=guild,
                        container_json=self.bot.json_dict["languages"][guild.language][
                            "containers"
                        ]["SetupContainer"],
                        language_code=guild.language,
                        shard_info=self.bot.shards[inter.guild.shard_id],
                    )
                )
                return
        elif "features_button" in inter.component.custom_id:
            if "set_features_button-" in inter.component.custom_id:
                feature_type = inter.component.custom_id.split("-")[1]
                container = SetupContainer(
                    guild=guild,
                    container_json=guild_language["containers"]["SetupContainer"],
                    language_code=guild.language,
                    shard_info=self.bot.shards[inter.guild.shard_id],
                )
                container.children.insert(
                    FEATURE_INDEXES[feature_type],
                    ui.ActionRow(
                        Setup.Features.FeatureChannelSelect(
                            feature_type=feature_type,
                            container_json=guild_language["containers"][
                                "SetupContainer"
                            ],
                        )
                    ),
                )
                await inter.edit_original_response(components=container)
                return
            elif "clear_features_button-" in inter.component.custom_id:
                feature_type = inter.component.custom_id.split("-")[1]
                guild.features = [f for f in guild.features if f.name != feature_type]
                guild.update_features()
                guild.save_changes()
                getattr(self.bot.interface_handler, feature_type).remove_entry(
                    guild.guild_id
                )
                await inter.edit_original_response(
                    components=SetupContainer(
                        guild=guild,
                        container_json=self.bot.json_dict["languages"][guild.language][
                            "containers"
                        ]["SetupContainer"],
                        language_code=guild.language,
                        shard_info=self.bot.shards[inter.guild.shard_id],
                    ),
                )
                return
        elif "language" in inter.component.custom_id:
            if inter.component.custom_id == "language_button":
                container = SetupContainer(
                    guild=guild,
                    container_json=guild_language["containers"]["SetupContainer"],
                    language_code=guild.language,
                    shard_info=self.bot.shards[inter.guild.shard_id],
                )
                container.children.insert(
                    len(container.children),
                    ui.ActionRow(
                        Setup.Language.LanguageSelect(
                            container_json=guild_language["containers"][
                                "SetupContainer"
                            ]
                        )
                    ),
                )
                try:
                    await inter.edit_original_response(
                        components=container,
                    )
                except Exception as e:
                    self.bot.logger.error(f"ERROR SetupCog | {e}")
                return

    @commands.Cog.listener("on_dropdown")
    async def on_dropdowns(self, inter: MessageInteraction):
        allowed_ids = {
            "dashboard_channel_select",
            "map_channel_select",
            "language_select",
        }
        if (
            inter.component.custom_id not in allowed_ids
            and "feature_channel_select-" not in inter.component.custom_id
        ):
            return
        try:
            await inter.response.defer()
        except (NotFound, InteractionTimedOut):
            await inter.channel.send(
                "There was an error with that dropdown, please try again.",
                delete_after=5,
            )
            return
        guild: GWWGuild = GWWGuilds.get_specific_guild(inter.guild_id)
        guild_language = self.bot.json_dict["languages"][guild.language]
        if inter.component.custom_id == "dashboard_channel_select":
            try:
                dashboard_channel = self.bot.get_channel(
                    inter.values[0]
                ) or await self.bot.fetch_channel(inter.values[0])
            except:  # TODO EXPAND THIS TO INCLUDE NOTFOUND AND FORBIDDEN
                await inter.send(
                    guild_language["setup"]["missing_perm"],
                    ephemeral=True,
                )
                return
            my_permissions = dashboard_channel.permissions_for(inter.guild.me)
            dashboard_perms_have = my_permissions.is_superset(
                self.dashboard_perms_needed
            )
            if not dashboard_perms_have:
                missing_permissions = [
                    f"\n- `{perm}`"
                    for perm, value in self.dashboard_perms_needed
                    if getattr(my_permissions, perm) is False
                    and getattr(self.dashboard_perms_needed, perm) is True
                ]
                await inter.send(
                    guild_language["setup"]["missing_perm"].format(
                        permissions="".join(missing_permissions)
                    ),
                    ephemeral=True,
                )
                return
            else:
                dashboard = Dashboard(
                    data=self.bot.data,
                    language_code=guild.language,
                    json_dict=self.bot.json_dict,
                )
                compact_level = 0
                while dashboard.character_count() > 6000 and compact_level < 2:
                    compact_level += 1
                    dashboard = Dashboard(
                        data=self.bot.data,
                        language_code=guild.language,
                        json_dict=self.bot.json_dict,
                        compact_level=compact_level,
                    )
                try:
                    message = await dashboard_channel.send(
                        embeds=dashboard.embeds, file=File("resources/banner.png")
                    )
                except Exception as e:
                    self.bot.logger.error(f"SetupCog | dashboard setup | {e}")
                    await inter.send(
                        "An error has occured, I have contacted Super Earth High Command.",
                        ephemeral=True,
                    )
                    return
                guild.features.append(
                    Feature(
                        "dashboards", guild.guild_id, dashboard_channel.id, message.id
                    )
                )
                guild.update_features()
                guild.save_changes()
                self.bot.interface_handler.dashboards.append(message)
                await inter.edit_original_response(
                    components=SetupContainer(
                        guild=guild,
                        container_json=guild_language["containers"]["SetupContainer"],
                        language_code=guild.language,
                        shard_info=self.bot.shards[inter.guild.shard_id],
                    ),
                )
        elif inter.component.custom_id == "map_channel_select":
            try:
                map_channel = self.bot.get_channel(
                    inter.values[0]
                ) or await self.bot.fetch_channel(inter.values[0])
            except:
                await inter.send(
                    guild_language["setup"]["missing_perm"],
                    ephemeral=True,
                )
                return
            my_permissions = map_channel.permissions_for(inter.guild.me)
            map_perms_have = my_permissions.is_superset(self.map_perms_needed)
            if not map_perms_have:
                missing_permissions = [
                    f"\n- `{perm}`"
                    for perm, value in self.map_perms_needed
                    if getattr(my_permissions, perm) is False
                    and getattr(self.map_perms_needed, perm) is True
                ]
                await inter.send(
                    guild_language["setup"]["missing_perm"].format(
                        permissions="".join(missing_permissions)
                    ),
                    ephemeral=True,
                )
                return
            else:
                latest_map = self.bot.maps.latest_maps.get(guild.language, None)
                fifteen_minutes_ago = datetime.now() - timedelta(minutes=15)
                if latest_map and latest_map.updated_at > fifteen_minutes_ago:
                    message = await map_channel.send(
                        embed=Embed(colour=Colour.dark_embed())
                        .set_image(url=latest_map.map_link)
                        .add_field(
                            "", f"-# Updated <t:{int(datetime.now().timestamp())}:R>"
                        ),
                    )
                else:
                    generating_message = await inter.channel.send(
                        "Generating map, please wait..."
                    )
                    self.bot.maps.update_base_map(
                        planets=self.bot.data.planets,
                        assignments=self.bot.data.assignments["en"],
                        campaigns=self.bot.data.campaigns,
                        sector_names=self.bot.json_dict["sectors"],
                    )
                    self.bot.maps.localize_map(
                        language_code_short=guild_language["code"],
                        language_code_long=guild_language["code_long"],
                        planets=self.bot.data.planets,
                        active_planets=[
                            campaign.planet.index
                            for campaign in self.bot.data.campaigns
                        ],
                        planet_names_json=self.bot.json_dict["planets"],
                    )
                    message = await self.bot.channels.waste_bin_channel.send(
                        file=File(
                            fp=self.bot.maps.FileLocations.localized_map_path(
                                guild_language["code"]
                            )
                        )
                    )
                    self.bot.maps.latest_maps[guild_language["code"]] = Maps.LatestMap(
                        datetime.now(), message.attachments[0].url
                    )
                    self.bot.maps.add_icons(
                        lang=guild_language["code"],
                        long_code=guild_language["code_long"],
                        planets=self.bot.data.planets,
                        active_planets=[
                            c.planet.index for c in self.bot.data.campaigns
                        ],
                        dss=self.bot.data.dss,
                        planet_names_json=self.bot.json_dict["planets"],
                    )
                    latest_map = self.bot.maps.latest_maps[guild_language["code"]]
                    message = await map_channel.send(
                        embed=Embed(colour=Colour.dark_embed())
                        .set_image(url=latest_map.map_link)
                        .add_field(
                            "", f"-# Updated <t:{int(datetime.now().timestamp())}:R>"
                        ),
                    )
                    await generating_message.delete()
                guild.features.append(
                    Feature("maps", guild.guild_id, map_channel.id, message.id)
                )
                guild.update_features()
                guild.save_changes()
                self.bot.interface_handler.maps.append(message)
                await inter.edit_original_response(
                    components=SetupContainer(
                        guild=guild,
                        container_json=guild_language["containers"]["SetupContainer"],
                        language_code=guild.language,
                        shard_info=self.bot.shards[inter.guild.shard_id],
                    )
                )
        elif "feature_channel_select-" in inter.component.custom_id:
            feature_type = inter.component.custom_id.split("-")[1]
            try:
                channel = self.bot.get_channel(
                    inter.values[0]
                ) or await self.bot.fetch_channel(inter.values[0])
            except:
                await inter.send(
                    guild_language["setup"]["cant_find_channel"],
                    ephemeral=True,
                )
                return
            my_permissions = channel.permissions_for(inter.guild.me)
            annnnouncement_perms_have = my_permissions.is_superset(
                self.annnnouncement_perms_needed
            )
            if not annnnouncement_perms_have:
                missing_permissions = [
                    f"\n- `{perm}`"
                    for perm, value in self.annnnouncement_perms_needed
                    if getattr(my_permissions, perm) is False
                    and getattr(self.annnnouncement_perms_needed, perm) is True
                ]
                await inter.send(
                    guild_language["setup"]["missing_perm"].format(
                        permissions="".join(missing_permissions)
                    ),
                    ephemeral=True,
                )
                return
            else:
                guild.features.append(Feature(feature_type, guild.guild_id, channel.id))
                guild.update_features()
                guild.save_changes()
                list_to_update: list = getattr(self.bot.interface_handler, feature_type)
                list_to_update.append(channel)
                await inter.edit_original_response(
                    components=SetupContainer(
                        guild=guild,
                        container_json=guild_language["containers"]["SetupContainer"],
                        language_code=guild.language,
                        shard_info=self.bot.shards[inter.guild.shard_id],
                    )
                )
        elif inter.component.custom_id == "language_select":
            guild.language = inter.values[0].lower()
            guild.save_changes()
            guild_language = self.bot.json_dict["languages"][guild.language]
            await inter.edit_original_response(
                components=SetupContainer(
                    guild=guild,
                    container_json=self.bot.json_dict["languages"][guild.language][
                        "containers"
                    ]["SetupContainer"],
                    language_code=guild.language,
                    shard_info=self.bot.shards[inter.guild.shard_id],
                ),
            )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(SetupCog(bot))
