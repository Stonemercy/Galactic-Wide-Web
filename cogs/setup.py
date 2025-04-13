from datetime import datetime, timedelta
from disnake import (
    AppCmdInter,
    ButtonStyle,
    Colour,
    Embed,
    File,
    MessageInteraction,
    NotFound,
    Permissions,
    InteractionContextTypes,
)
from disnake.ext import commands
from disnake.ui import ActionRow
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GWWGuild
from utils.embeds.dashboard import Dashboard
from utils.embeds.command_embeds import SetupCommandEmbed
from utils.interactables import Setup
from utils.maps import Maps


class SetupCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.dashboard_perms_needed = Permissions(
            send_messages=True,
            view_channel=True,
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
            view_channel=True, send_messages=True, attach_files=True, embed_links=True
        )

    def reset_row_1(self, action_row: ActionRow):
        for button in action_row.children:
            if button.disabled:
                button.disabled = False
                button.emoji = None
                button.style = ButtonStyle.gray

    def clear_extra_buttons(self, action_rows: list[ActionRow]):
        for action_row in action_rows[2:]:
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
        await inter.response.defer(ephemeral=True)
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name}"
        )
        guild = GWWGuild.get_by_id(inter.guild_id)
        if not guild:
            self.bot.logger.error(
                msg=f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
            )
            guild = GWWGuild.new(inter.guild_id)
        guild_language = self.bot.json_dict["languages"][guild.language]
        components = [
            (
                ActionRow(
                    Setup.Dashboard.DashboardButton(language_json=guild_language),
                    Setup.Announcements.AnnouncementsButton(
                        language_json=guild_language
                    ),
                    Setup.Map.MapButton(language_json=guild_language),
                    Setup.Language.LanguageButton(language_json=guild_language),
                )
            ),
            (
                ActionRow(
                    Setup.PatchNotes.PatchNotesButton(
                        language_json=guild_language, enabled=guild.patch_notes
                    ),
                    Setup.MajorOrderUpdates.MajorOrderUpdatesButton(
                        language_json=guild_language, enabled=guild.major_order_updates
                    ),
                    Setup.PersonalOrder.PersonalOrderUpdatesButton(
                        language_json=guild_language,
                        enabled=guild.personal_order_updates,
                    ),
                    Setup.DetailedDispatches.DetailedDispatchesButton(
                        language_json=guild_language, enabled=guild.detailed_dispatches
                    ),
                )
            ),
        ]
        if guild.announcement_channel_id != 0:
            components[1][0].disabled = False
            components[1][1].disabled = False
            components[1][2].disabled = False
            components[1][3].disabled = False
        await inter.send(
            embed=SetupCommandEmbed(
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
            "announcements_button",
            "set_announcements_button",
            "clear_announcements_button",
            "map_button",
            "set_map_button",
            "clear_map_button",
            "language_button",
            "patch_notes_button",
            "major_order_updates_button",
            "personal_order_updates_button",
            "detailed_dispatches_updates_button",
        }
        if inter.component.custom_id not in allowed_ids:
            return
        await inter.response.defer()
        action_rows = ActionRow.rows_from_message(inter.message)
        guild = GWWGuild.get_by_id(inter.guild_id)
        guild_language = self.bot.json_dict["languages"][guild.language]
        if "dashboard" in inter.component.custom_id:
            self.clear_extra_buttons(action_rows)
            if inter.component.custom_id == "dashboard_button":
                dashboard_row = ActionRow(
                    Setup.Dashboard.ClearDashboardButton(language_json=guild_language)
                    if 0
                    not in (
                        guild.dashboard_channel_id,
                        guild.dashboard_message_id,
                    )
                    else Setup.Dashboard.SetDashboardButton(
                        language_json=guild_language
                    )
                )
                action_rows.append(dashboard_row)
                self.reset_row_1(action_rows[0])
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
                guild.dashboard_channel_id = 0
                guild.dashboard_message_id = 0
                guild.save_changes()
                self.bot.interface_handler.dashboards = [
                    message
                    for message in self.bot.interface_handler.dashboards.copy()
                    if message.guild.id != inter.guild_id
                ]
                self.reset_row_1(action_rows[0])
                await inter.edit_original_response(
                    embed=SetupCommandEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
                return
        elif "announcements" in inter.component.custom_id:
            self.clear_extra_buttons(action_rows)
            if inter.component.custom_id == "announcements_button":
                action_rows.append(
                    ActionRow(
                        Setup.Announcements.ClearAnnouncementsButton(
                            language_json=guild_language
                        )
                        if guild.announcement_channel_id != 0
                        else Setup.Announcements.SetAnnouncementsButton(
                            language_json=guild_language
                        )
                    )
                )
                self.reset_row_1(action_rows[0])
                action_rows[0].pop(1)
                action_rows[0].insert_item(
                    1,
                    Setup.Announcements.AnnouncementsButton(
                        language_json=guild_language, selected=True
                    ),
                )
                try:
                    await inter.edit_original_response(components=action_rows)
                    return
                except NotFound as e:
                    await self.bot.moderator_channel.send(f"Setup\n```py\n{e}\n```")
            elif inter.component.custom_id == "set_announcements_button":
                action_rows.append(
                    ActionRow(
                        Setup.Announcements.AnnouncementsChannelSelect(
                            language_json=guild_language
                        )
                    )
                )
                await inter.edit_original_response(components=action_rows)
                return
            elif inter.component.custom_id == "clear_announcements_button":
                try:
                    channel = self.bot.get_channel(
                        guild.announcement_channel_id
                    ) or await self.bot.fetch_channel(guild.announcement_channel_id)
                except:
                    channel = None
                guild.announcement_channel_id = 0
                guild.patch_notes = False
                guild.major_order_updates = False
                guild.personal_order_updates = False
                guild.detailed_dispatches = False
                guild.save_changes()
                if channel:
                    for (
                        channels
                    ) in (
                        self.bot.interface_handler.news_feeds.channels_dict.copy().values()
                    ):
                        if channel in channels:
                            channels.remove(channel)
                action_rows[1].clear_items()
                action_rows[1].append_item(
                    Setup.PatchNotes.PatchNotesButton(language_json=guild_language)
                )
                action_rows[1].append_item(
                    Setup.MajorOrderUpdates.MajorOrderUpdatesButton(
                        language_json=guild_language
                    )
                )
                action_rows[1].append_item(
                    Setup.PersonalOrder.PersonalOrderUpdatesButton(
                        language_json=guild_language
                    )
                )
                action_rows[1].append_item(
                    Setup.DetailedDispatches.DetailedDispatchesButton(
                        language_json=guild_language
                    )
                )
                self.reset_row_1(action_rows[0])
                await inter.edit_original_response(
                    embed=SetupCommandEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
                return
        elif "map" in inter.component.custom_id:
            if inter.component.custom_id == "map_button":
                self.clear_extra_buttons(action_rows)
                action_rows.append(
                    ActionRow(
                        Setup.Map.ClearMapButton(language_json=guild_language)
                        if 0
                        not in (
                            guild.map_channel_id,
                            guild.map_message_id,
                        )
                        else Setup.Map.SetMapButton(language_json=guild_language)
                    )
                )
                self.reset_row_1(action_rows[0])
                action_rows[0].pop(2)
                action_rows[0].insert_item(
                    2, Setup.Map.MapButton(language_json=guild_language, selected=True)
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
                guild.map_channel_id = 0
                guild.map_message_id = 0
                guild.save_changes()
                self.bot.interface_handler.maps = [
                    message
                    for message in self.bot.interface_handler.maps.copy()
                    if message.guild.id != inter.guild_id
                ]
                self.reset_row_1(action_rows[0])
                await inter.edit_original_response(
                    embed=SetupCommandEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
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
                self.reset_row_1(action_rows[0])
                action_rows[0].pop(3)
                action_rows[0].insert_item(
                    3,
                    Setup.Language.LanguageButton(
                        language_json=guild_language, selected=True
                    ),
                )
                try:
                    await inter.edit_original_response(
                        embed=SetupCommandEmbed(
                            guild, self.bot.json_dict["languages"][guild.language]
                        ),
                        components=action_rows,
                    )
                except Exception as e:
                    self.bot.logger.error(f"ERROR SetupCog | {e}")
                return
        elif inter.component.custom_id == "patch_notes_button":
            if guild.patch_notes:  # want to disable
                channel = self.bot.get_channel(
                    guild.announcement_channel_id
                ) or await self.bot.fetch_channel(guild.announcement_channel_id)
                self.bot.interface_handler.news_feeds.channels_dict["Patch"].remove(
                    channel
                )
                guild.patch_notes = False
                guild.save_changes()
                action_rows[1].pop(0)
                action_rows[1].insert_item(
                    0, Setup.PatchNotes.PatchNotesButton(language_json=guild_language)
                )
                action_rows[1][0].disabled = False
                await inter.edit_original_response(
                    embed=SetupCommandEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
                return
            else:  # want to enable
                try:
                    channel = self.bot.get_channel(
                        guild.announcement_channel_id
                    ) or await self.bot.fetch_channel(guild.announcement_channel_id)
                except NotFound as e:
                    await inter.send(
                        "There was an issue finding your announcements channel.\nApologies for the inconvenience",
                        ephemeral=True,
                    )
                    return
                self.bot.interface_handler.news_feeds.channels_dict["Patch"].append(
                    channel
                )
                guild.patch_notes = True
                guild.save_changes()
                action_rows[1].pop(0)
                action_rows[1].insert_item(
                    0,
                    Setup.PatchNotes.PatchNotesButton(
                        language_json=guild_language, enabled=True
                    ),
                )
                action_rows[1][0].disabled = False
                await inter.edit_original_response(
                    embed=SetupCommandEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
                return
        elif inter.component.custom_id == "major_order_updates_button":
            if guild.major_order_updates:  # want to disable
                channel = self.bot.get_channel(
                    guild.announcement_channel_id
                ) or await self.bot.fetch_channel(guild.announcement_channel_id)
                guild.major_order_updates = False
                guild.save_changes()
                self.bot.interface_handler.news_feeds.channels_dict["MO"].remove(
                    channel
                )
                action_rows[1].pop(1)
                action_rows[1].insert_item(
                    1,
                    Setup.MajorOrderUpdates.MajorOrderUpdatesButton(
                        language_json=guild_language
                    ),
                )
                action_rows[1].children[1].disabled = False
                await inter.edit_original_response(
                    embed=SetupCommandEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
                return
            else:  # want to enable
                try:
                    channel = self.bot.get_channel(
                        guild.announcement_channel_id
                    ) or await self.bot.fetch_channel(guild.announcement_channel_id)
                except NotFound:
                    await inter.send(
                        "Your announcements channel could not be found. Please reset it.",
                        ephemeral=True,
                    )
                    return
                self.bot.interface_handler.news_feeds.channels_dict["MO"].append(
                    channel
                )
                guild.major_order_updates = True
                guild.save_changes()
                action_rows[1].pop(1)
                action_rows[1].insert_item(
                    1,
                    Setup.MajorOrderUpdates.MajorOrderUpdatesButton(
                        language_json=guild_language, enabled=True
                    ),
                )
                action_rows[1].children[1].disabled = False
                await inter.edit_original_response(
                    embed=SetupCommandEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
                return
        elif inter.component.custom_id == "personal_order_updates_button":
            if guild.personal_order_updates:  # want to disable
                channel = self.bot.get_channel(
                    guild.announcement_channel_id
                ) or await self.bot.fetch_channel(guild.announcement_channel_id)
                guild.personal_order_updates = False
                guild.save_changes()
                self.bot.interface_handler.news_feeds.channels_dict["PO"].remove(
                    channel
                )
                action_rows[1].pop(2)
                action_rows[1].insert_item(
                    2,
                    Setup.PersonalOrder.PersonalOrderUpdatesButton(
                        language_json=guild_language
                    ),
                )
                action_rows[1].children[2].disabled = False
                await inter.edit_original_response(
                    embed=SetupCommandEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
                return
            else:  # want to enable
                try:
                    channel = self.bot.get_channel(
                        guild.announcement_channel_id
                    ) or await self.bot.fetch_channel(guild.announcement_channel_id)
                except NotFound:
                    await inter.send(
                        "Your announcements channel could not be found. Please reset it.",
                        ephemeral=True,
                    )
                    return
                self.bot.interface_handler.news_feeds.channels_dict["PO"].append(
                    channel
                )
                guild.personal_order_updates = True
                guild.save_changes()
                action_rows[1].pop(2)
                action_rows[1].insert_item(
                    2,
                    Setup.PersonalOrder.PersonalOrderUpdatesButton(
                        language_json=guild_language, enabled=True
                    ),
                )
                action_rows[1].children[2].disabled = False
                await inter.edit_original_response(
                    embed=SetupCommandEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
                return
        elif inter.component.custom_id == "detailed_dispatches_updates_button":
            if guild.detailed_dispatches:  # want to disable
                channel = self.bot.get_channel(
                    guild.announcement_channel_id
                ) or await self.bot.fetch_channel(guild.announcement_channel_id)
                guild.detailed_dispatches = False
                guild.save_changes()
                try:
                    self.bot.interface_handler.news_feeds.channels_dict[
                        "DetailedDispatches"
                    ].remove(channel)
                except:
                    pass
                action_rows[1].pop(3)
                action_rows[1].insert_item(
                    3,
                    Setup.DetailedDispatches.DetailedDispatchesButton(
                        language_json=guild_language
                    ),
                )
                action_rows[1].children[3].disabled = False
                await inter.edit_original_response(
                    embed=SetupCommandEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
                return
            else:  # want to enable
                try:
                    channel = self.bot.get_channel(
                        guild.announcement_channel_id
                    ) or await self.bot.fetch_channel(guild.announcement_channel_id)
                except NotFound:
                    await inter.send(
                        "Your announcements channel could not be found. Please reset it.",
                        ephemeral=True,
                    )
                    return
                self.bot.interface_handler.news_feeds.channels_dict[
                    "DetailedDispatches"
                ].append(channel)
                guild.detailed_dispatches = True
                guild.save_changes()
                action_rows[1].pop(3)
                action_rows[1].insert_item(
                    3,
                    Setup.DetailedDispatches.DetailedDispatchesButton(
                        language_json=guild_language, enabled=True
                    ),
                )
                action_rows[1].children[3].disabled = False
                await inter.edit_original_response(
                    embed=SetupCommandEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
                return

    @commands.Cog.listener("on_dropdown")
    async def on_dropdowns(self, inter: MessageInteraction):
        allowed_ids = {
            "dashboard_channel_select",
            "announcements_channel_select",
            "map_channel_select",
            "language_select",
        }
        if inter.component.custom_id not in allowed_ids:
            return
        await inter.response.defer()
        action_rows = ActionRow.rows_from_message(inter.message)
        guild = GWWGuild.get_by_id(inter.guild_id)
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
                    self.bot.data,
                    guild.language,
                    self.bot.json_dict,
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
                guild.dashboard_channel_id = dashboard_channel.id
                guild.dashboard_message_id = message.id
                guild.save_changes()
                self.bot.interface_handler.dashboards.append(message)
                embed = SetupCommandEmbed(guild, guild_language)
                self.clear_extra_buttons(action_rows)
                self.reset_row_1(action_rows[0])
                await inter.edit_original_response(embed=embed, components=action_rows)
        elif inter.component.custom_id == "announcements_channel_select":
            try:
                announcement_channel = self.bot.get_channel(
                    inter.values[0]
                ) or await self.bot.fetch_channel(inter.values[0])
            except:
                await inter.send(
                    guild_language["setup"]["cant_find_channel"],
                    ephemeral=True,
                )
                return

            my_permissions = announcement_channel.permissions_for(inter.guild.me)
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
                guild.announcement_channel_id = announcement_channel.id
                guild.save_changes()
                self.bot.interface_handler.news_feeds.channels_dict["Generic"].append(
                    announcement_channel
                )
                embed = SetupCommandEmbed(guild, guild_language)
                self.clear_extra_buttons(action_rows)
                self.reset_row_1(action_rows[0])
                action_rows[1].children[0].disabled = False
                action_rows[1].children[1].disabled = False
                action_rows[1].children[2].disabled = False
                action_rows[1].children[3].disabled = False
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
                self.reset_row_1(action_rows[0])
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
                    await inter.send(
                        "Generating map, please wait...",
                        delete_after=12,
                        ephemeral=True,
                    )
                    await self.bot.maps.update_base_map(
                        planets=self.bot.data.planets,
                        assignment=self.bot.data.assignment,
                        campaigns=self.bot.data.campaigns,
                        dss=self.bot.data.dss,
                    )
                    self.bot.maps.localize_map(
                        language_code_short=guild_language["code"],
                        language_code_long=guild_language["code_long"],
                        planets=self.bot.data.planets,
                        active_planets=[
                            campaign.planet.index
                            for campaign in self.bot.data.campaigns
                        ],
                        dss=self.bot.data.dss,
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
                guild.map_channel_id = map_channel.id
                guild.map_message_id = message.id
                guild.save_changes()
                self.bot.interface_handler.maps.append(message)
                embed = SetupCommandEmbed(guild, guild_language)
                await inter.edit_original_response(embed=embed, components=action_rows)
        elif inter.component.custom_id == "language_select":
            guild.language = inter.values[0].lower()
            guild.save_changes()
            guild_language = self.bot.json_dict["languages"][guild.language]
            embed = SetupCommandEmbed(
                guild, self.bot.json_dict["languages"][guild.language]
            )
            await inter.edit_original_response(
                embed=embed,
                components=[
                    (
                        ActionRow(
                            Setup.Dashboard.DashboardButton(
                                language_json=guild_language
                            ),
                            Setup.Announcements.AnnouncementsButton(
                                language_json=guild_language
                            ),
                            Setup.Map.MapButton(language_json=guild_language),
                            Setup.Language.LanguageButton(language_json=guild_language),
                        )
                    ),
                    (
                        ActionRow(
                            Setup.PatchNotes.PatchNotesButton(
                                language_json=guild_language, enabled=guild.patch_notes
                            ),
                            Setup.MajorOrderUpdates.MajorOrderUpdatesButton(
                                language_json=guild_language,
                                enabled=guild.major_order_updates,
                            ),
                            Setup.PersonalOrder.PersonalOrderUpdatesButton(
                                language_json=guild_language,
                                enabled=guild.personal_order_updates,
                            ),
                            Setup.DetailedDispatches.DetailedDispatchesButton(
                                language_json=guild_language,
                                enabled=guild.detailed_dispatches,
                            ),
                        )
                    ),
                ],
            )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(SetupCog(bot))
