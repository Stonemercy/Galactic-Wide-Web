from datetime import datetime, timedelta
from disnake import (
    AppCmdInter,
    ButtonStyle,
    Colour,
    Embed,
    File,
    InteractionContextTypes,
    InteractionTimedOut,
    Message,
    MessageInteraction,
    NotFound,
    Permissions,
)
from disnake.ext import commands
from disnake.ui import ActionRow
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.dbv2 import Feature, GWWGuild, GWWGuilds
from utils.embeds import Dashboard, SetupEmbed
from utils.maps import Maps
from utils.setup import Setup


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
        self.current_features = [
            "war_announcements",
            "dss_announcements",
            "region_announcements",
            "patch_notes",
            "major_order_updates",
            "detailed_dispatches",
        ]

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
                msg=f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
            )
            guild: GWWGuild = GWWGuilds.add(inter.guild_id, "en", [])
        guild_language = self.bot.json_dict["languages"][guild.language]
        components = [
            ActionRow(
                Setup.Dashboard.DashboardButton(language_json=guild_language),
                Setup.Map.MapButton(language_json=guild_language),
                Setup.Features.FeaturesButton(language_json=guild_language),
                Setup.Language.LanguageButton(language_json=guild_language),
            )
        ]
        await inter.send(
            embed=SetupEmbed(
                guild=guild,
                language_json=self.bot.json_dict["languages"][guild.language],
            ),
            components=components,
        )

    @commands.Cog.listener("on_button_click")
    async def on_button_clicks(self, inter: MessageInteraction):
        allowed_ids = {
            "dashboard_button",
            "set_dashboard_button",
            "clear_dashboard_button",
            "map_button",
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
        action_rows = ActionRow.rows_from_message(inter.message)
        guild: GWWGuild = GWWGuilds.get_specific_guild(inter.guild_id)
        guild_language = self.bot.json_dict["languages"][guild.language]
        active_feature_names = [f.name for f in guild.features]
        if "dashboard" in inter.component.custom_id:
            self.clear_extra_buttons(action_rows)
            if inter.component.custom_id == "dashboard_button":
                if "dashboards" in active_feature_names:
                    dashboard_row = ActionRow(
                        Setup.Dashboard.ClearDashboardButton(
                            language_json=guild_language
                        )
                    )
                else:
                    dashboard_row = ActionRow(
                        Setup.Dashboard.SetDashboardButton(language_json=guild_language)
                    )
                action_rows.append(dashboard_row)
                self.reset_row(action_rows[0])
                action_rows[0].pop(0)
                action_rows[0].insert_item(
                    0,
                    Setup.Dashboard.DashboardButton(
                        language_json=guild_language, selected=True
                    ),
                )
                try:
                    await inter.edit_original_response(components=action_rows)
                    return
                except NotFound:
                    await inter.send(
                        "There was an issue editing the setup message. Your settings have been saved so just use the command again!\nApologies for the inconvenience",
                        ephemeral=True,
                    )
                    return
            elif inter.component.custom_id == "set_dashboard_button":
                action_rows.append(
                    ActionRow(
                        Setup.Dashboard.DashboardChannelSelect(
                            language_json=guild_language
                        )
                    )
                )
                await inter.edit_original_response(components=action_rows)
                return
            elif inter.component.custom_id == "clear_dashboard_button":
                guild.features = [f for f in guild.features if f.name != "dashboards"]
                guild.update_features()
                guild.save_changes()
                self.bot.interface_handler.dashboards.remove_entry(guild.guild_id)
                self.reset_row(action_rows[0])
                await inter.edit_original_response(
                    embed=SetupEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
                return
        elif "map" in inter.component.custom_id:
            if inter.component.custom_id == "map_button":
                self.clear_extra_buttons(action_rows)
                if "maps" in active_feature_names:
                    map_row = ActionRow(
                        Setup.Map.ClearMapButton(language_json=guild_language)
                    )
                else:
                    map_row = ActionRow(
                        Setup.Map.SetMapButton(language_json=guild_language)
                    )
                action_rows.append(map_row)
                self.reset_row(action_rows[0])
                action_rows[0].pop(1)
                action_rows[0].insert_item(
                    1, Setup.Map.MapButton(language_json=guild_language, selected=True)
                )
                try:
                    await inter.edit_original_response(components=action_rows)
                    return
                except NotFound as e:
                    await self.bot.moderator_channel.send(f"Setup\n```py\n{e}\n```")
            elif inter.component.custom_id == "set_map_button":
                self.clear_extra_buttons(action_rows)
                action_rows.append(
                    ActionRow(Setup.Map.MapChannelSelect(language_json=guild_language))
                )
                try:
                    await inter.edit_original_response(components=action_rows)
                    return
                except NotFound as e:
                    await self.bot.moderator_channel.send(f"Setup\n```py\n{e}\n```")
            elif inter.component.custom_id == "clear_map_button":
                self.clear_extra_buttons(action_rows)
                guild.features = [f for f in guild.features if f.name != "maps"]
                guild.update_features()
                guild.save_changes()
                self.bot.interface_handler.maps.remove_entry(guild.guild_id)
                self.reset_row(action_rows[0])
                await inter.edit_original_response(
                    embed=SetupEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
                return
        elif "features_button" in inter.component.custom_id:
            if inter.component.custom_id == "features_button":
                self.clear_extra_buttons(action_rows)
                feature_buttons = [
                    Setup.Features.FeatureButton(
                        feature_type=f, language_json=guild_language
                    )
                    for f in self.current_features
                ]
                for i in range(0, len(feature_buttons), 3):
                    action_rows.append(ActionRow(*feature_buttons[i : i + 3]))
                self.reset_row(action_rows[0])
                action_rows[0].pop(2)
                action_rows[0].insert_item(
                    2,
                    Setup.Features.FeaturesButton(
                        language_json=guild_language, selected=True
                    ),
                )
                try:
                    await inter.edit_original_response(components=action_rows)
                    return
                except NotFound as e:
                    await self.bot.moderator_channel.send(f"Setup\n```py\n{e}\n```")
            elif "set_features_button-" in inter.component.custom_id:
                self.clear_extra_buttons(action_rows=action_rows, from_row=3)
                feature_type = inter.component.custom_id.split("-")[1]
                action_rows.append(
                    ActionRow(
                        Setup.Features.FeatureChannelSelect(
                            feature_type=feature_type,
                            language_json=guild_language,
                        )
                    )
                )
                await inter.edit_original_response(components=action_rows)
                return
            elif "clear_features_button-" in inter.component.custom_id:
                feature_type = inter.component.custom_id.split("-")[1]
                guild.features = [f for f in guild.features if f.name != feature_type]
                guild.update_features()
                guild.save_changes()
                getattr(self.bot.interface_handler, feature_type).remove_entry(
                    guild.guild_id
                )
                self.clear_extra_buttons(action_rows=action_rows, from_row=3)
                self.reset_row(action_rows[1])
                self.reset_row(action_rows[2])
                await inter.edit_original_response(
                    embed=SetupEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
                return
            elif "_features_button" in inter.component.custom_id:
                for feature in self.current_features:
                    if inter.component.custom_id == f"{feature}_features_button":
                        currently_enabled = feature in active_feature_names
                        self.clear_extra_buttons(action_rows=action_rows, from_row=3)
                        if currently_enabled:
                            action_rows.append(
                                ActionRow(
                                    Setup.Features.ClearFeatureButton(
                                        feature_type=feature,
                                        language_json=guild_language,
                                    )
                                )
                            )
                        else:
                            action_rows.append(
                                ActionRow(
                                    Setup.Features.SetFeatureButton(
                                        feature_type=feature,
                                        language_json=guild_language,
                                    )
                                )
                            )
                        button_index = None
                        row_index = None
                        buttons_to_check = (
                            action_rows[1].children,
                            action_rows[2].children,
                        )
                        for r_index, row in enumerate(buttons_to_check, 1):
                            for b_index, button in enumerate(row):
                                if feature in button.custom_id:
                                    button_index = b_index
                                    break
                            if button_index != None:
                                row_index = r_index
                                break
                        for row in action_rows[1:]:
                            self.reset_row(row)
                        action_rows[row_index].pop(button_index)
                        action_rows[row_index].insert_item(
                            button_index,
                            Setup.Features.FeatureButton(
                                feature_type=feature,
                                language_json=guild_language,
                                selected=True,
                            ),
                        )
                        try:
                            await inter.edit_original_response(components=action_rows)
                            return
                        except NotFound as e:
                            await self.bot.moderator_channel.send(
                                f"Setup\n```py\n{e}\n```"
                            )
                        return

        elif "language" in inter.component.custom_id:
            if inter.component.custom_id == "language_button":
                self.clear_extra_buttons(action_rows)
                action_rows.append(
                    ActionRow(
                        Setup.Language.LanguageSelect(language_json=guild_language)
                    )
                )
                self.reset_row(action_rows[0])
                action_rows[0].pop(3)
                action_rows[0].insert_item(
                    3,
                    Setup.Language.LanguageButton(
                        language_json=guild_language, selected=True
                    ),
                )
                try:
                    await inter.edit_original_response(
                        embed=SetupEmbed(
                            guild, self.bot.json_dict["languages"][guild.language]
                        ),
                        components=action_rows,
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
        action_rows = ActionRow.rows_from_message(inter.message)
        guild: GWWGuild = GWWGuilds.get_specific_guild(inter.guild_id)
        guild_language = self.bot.json_dict["languages"][guild.language]
        if inter.component.custom_id == "dashboard_channel_select":
            try:
                dashboard_channel = self.bot.get_channel(
                    inter.values[0]
                ) or await self.bot.fetch_channel(inter.values[0])
            except:
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
                embed = SetupEmbed(guild, guild_language)
                self.clear_extra_buttons(action_rows)
                self.reset_row(action_rows[0])
                await inter.edit_original_response(embed=embed, components=action_rows)
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
                self.clear_extra_buttons(action_rows)
                self.reset_row(action_rows[0])
                await inter.edit_original_response(components=action_rows)
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
                    generating_message: Message = await inter.channel.send(
                        "Generating map, please wait..."
                    )
                    self.bot.maps.update_base_map(
                        planets=self.bot.data.planets,
                        assignments=self.bot.data.assignments,
                        campaigns=self.bot.data.campaigns,
                        dss=self.bot.data.dss,
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
                        type_3_campaigns=[
                            c for c in self.bot.data.campaigns if c.type == 3
                        ],
                        planet_names_json=self.bot.json_dict["planets"],
                    )
                    message = await self.bot.waste_bin_channel.send(
                        file=File(
                            fp=self.bot.maps.FileLocations.localized_map_path(
                                guild_language["code"]
                            )
                        )
                    )
                    self.bot.maps.latest_maps[guild_language["code"]] = Maps.LatestMap(
                        datetime.now(), message.attachments[0].url
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
                embed = SetupEmbed(guild, guild_language)
                await inter.edit_original_response(embed=embed, components=action_rows)
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
                embed = SetupEmbed(guild, guild_language)
                self.clear_extra_buttons(action_rows, from_row=3)
                self.reset_row(action_rows[1])
                self.reset_row(action_rows[2])
                await inter.edit_original_response(embed=embed, components=action_rows)
        elif inter.component.custom_id == "language_select":
            guild.language = inter.values[0].lower()
            guild.save_changes()
            guild_language = self.bot.json_dict["languages"][guild.language]
            embed = SetupEmbed(guild, self.bot.json_dict["languages"][guild.language])
            await inter.edit_original_response(
                embed=embed,
                components=[
                    ActionRow(
                        Setup.Dashboard.DashboardButton(language_json=guild_language),
                        Setup.Map.MapButton(language_json=guild_language),
                        Setup.Features.FeaturesButton(language_json=guild_language),
                        Setup.Language.LanguageButton(language_json=guild_language),
                    )
                ],
            )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(SetupCog(bot))
