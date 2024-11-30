from disnake import (
    AppCmdInter,
    ButtonStyle,
    File,
    MessageInteraction,
    Permissions,
)
from disnake.ext import commands
from disnake.ui import ActionRow
from main import GalacticWideWebBot
from utils.interactables import Setup
from utils.checks import wait_for_startup
from utils.db import GuildRecord, GuildsDB
from utils.embeds import Dashboard, SetupEmbed
from utils.functions import dashboard_maps


class SetupCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.dashboard_perms_needed = Permissions(
            send_messages=True,
            view_channel=True,
            attach_files=True,
            embed_links=True,
            use_external_emojis=True,
        )
        self.annnnouncement_perms_needed = Permissions(
            view_channel=True,
            send_messages=True,
            embed_links=True,
            use_external_emojis=True,
        )
        self.map_perms_needed = Permissions(
            view_channel=True, send_messages=True, embed_links=True, attach_files=True
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
        dm_permission=False,
    )
    async def setup(
        self,
        inter: AppCmdInter,
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name}"
        )
        guild_in_db: GuildRecord = GuildsDB.get_info(inter.guild_id)
        if not guild_in_db:
            guild_in_db = GuildsDB.insert_new_guild(inter.guild_id)
        guild_language = self.bot.json_dict["languages"][guild_in_db.language]
        embed = SetupEmbed(guild_record=guild_in_db, language_json=guild_language)
        row1 = (
            ActionRow()
            .append_item(Setup.Dashboard.DashboardButton())
            .append_item(Setup.Announcements.AnnouncementsButton())
            .append_item(Setup.Map.MapButton())
            .append_item(Setup.Language.LanguageButton())
        )
        row2 = (
            ActionRow()
            .append_item(Setup.PatchNotes.PatchNotesButton(guild_in_db.patch_notes))
            .append_item(
                Setup.MajorOrderUpdates.MajorOrderUpdatesButton(
                    guild_in_db.major_order_updates
                )
            )
        )
        components = [row1, row2]
        if guild_in_db.announcement_channel_id != 0:
            components[1][0].disabled = False
            components[1][1].disabled = False
        await inter.send(embed=embed, components=components)

    @commands.Cog.listener("on_button_click")
    async def ban_listener(self, inter: MessageInteraction):
        action_rows = ActionRow.rows_from_message(inter.message)
        guild_in_db: GuildRecord = GuildsDB.get_info(inter.guild.id)
        if "dashboard" in inter.component.custom_id:
            self.clear_extra_buttons(action_rows)
            if inter.component.custom_id == "dashboard_button":
                dashboard_row = ActionRow()
                if 0 not in (
                    guild_in_db.dashboard_channel_id,
                    guild_in_db.dashboard_message_id,
                ):
                    dashboard_row.append_item(Setup.Dashboard.ClearDashboardButton())
                else:
                    dashboard_row.append_item(Setup.Dashboard.SetDashboardButton())
                action_rows.append(dashboard_row)
                self.reset_row_1(action_rows[0])
                action_rows[0].pop(0)
                action_rows[0].insert_item(
                    0, Setup.Dashboard.DashboardButton(selected=True)
                )
                return await inter.response.edit_message(components=action_rows)
            elif inter.component.custom_id == "set_dashboard_button":
                dashboard_row = ActionRow(Setup.Dashboard.DashboardChannelSelect())
                action_rows.append(dashboard_row)
                return await inter.response.edit_message(components=action_rows)
            elif inter.component.custom_id == "clear_dashboard_button":
                guild_in_db = GuildsDB.update_dashboard(inter.guild.id, 0, 0)
                self.bot.dashboard_messages = [
                    message
                    for message in self.bot.dashboard_messages.copy()
                    if message.guild.id != inter.guild_id
                ]
                embed = SetupEmbed(
                    guild_in_db, self.bot.json_dict["languages"][guild_in_db.language]
                )
                self.reset_row_1(action_rows[0])
                return await inter.response.edit_message(
                    embed=embed, components=action_rows
                )
        elif "announcements" in inter.component.custom_id:
            self.clear_extra_buttons(action_rows)
            if inter.component.custom_id == "announcements_button":
                announcements_row = ActionRow()
                if guild_in_db.announcement_channel_id != 0:
                    announcements_row.append_item(
                        Setup.Announcements.ClearAnnouncementsButton()
                    )
                else:
                    announcements_row.append_item(
                        Setup.Announcements.SetAnnouncementsButton()
                    )
                action_rows.append(announcements_row)
                self.reset_row_1(action_rows[0])
                action_rows[0].pop(1)
                action_rows[0].insert_item(
                    1, Setup.Announcements.AnnouncementsButton(selected=True)
                )
                return await inter.response.edit_message(components=action_rows)
            elif inter.component.custom_id == "set_announcements_button":
                dashboard_row = ActionRow(
                    Setup.Announcements.AnnouncementsChannelSelect()
                )
                action_rows.append(dashboard_row)
                return await inter.response.edit_message(components=action_rows)
            elif inter.component.custom_id == "clear_announcements_button":
                guild_in_db = GuildsDB.update_announcement_channel(inter.guild.id, 0)
                self.bot.announcement_channels = [
                    channel
                    for channel in self.bot.announcement_channels.copy()
                    if channel.guild.id != inter.guild_id
                ]
                if guild_in_db.patch_notes:
                    guild_in_db = GuildsDB.update_patch_notes(inter.guild_id, False)
                    self.bot.patch_channels = [
                        channel
                        for channel in self.bot.patch_channels.copy()
                        if channel.guild.id != inter.guild.id
                    ]
                action_rows[1].pop(0)
                action_rows[1].append_item(Setup.PatchNotes.PatchNotesButton())
                action_rows[1].children[0].disabled = True
                action_rows[1].children[1].disabled = True
                embed = SetupEmbed(
                    guild_in_db, self.bot.json_dict["languages"][guild_in_db.language]
                )
                self.reset_row_1(action_rows[0])
                return await inter.response.edit_message(
                    embed=embed, components=action_rows
                )
        elif "map" in inter.component.custom_id:
            if inter.component.custom_id == "map_button":
                self.clear_extra_buttons(action_rows)
                map_row = ActionRow()
                if 0 not in (
                    guild_in_db.map_channel_id,
                    guild_in_db.map_message_id,
                ):
                    map_row.append_item(Setup.Map.ClearMapButton())
                else:
                    map_row.append_item(Setup.Map.SetMapButton())
                action_rows.append(map_row)
                self.reset_row_1(action_rows[0])
                action_rows[0].pop(2)
                action_rows[0].insert_item(2, Setup.Map.MapButton(selected=True))
                return await inter.response.edit_message(components=action_rows)
            elif inter.component.custom_id == "set_map_button":
                self.clear_extra_buttons(action_rows)
                map_row = ActionRow(Setup.Map.MapChannelSelect())
                action_rows.append(map_row)
                return await inter.response.edit_message(components=action_rows)
            elif inter.component.custom_id == "clear_map_button":
                self.clear_extra_buttons(action_rows)
                guild_in_db = GuildsDB.update_map(inter.guild.id, 0, 0)
                self.bot.map_messages = [
                    message
                    for message in self.bot.map_messages.copy()
                    if message.guild.id != inter.guild_id
                ]
                embed = SetupEmbed(
                    guild_in_db, self.bot.json_dict["languages"][guild_in_db.language]
                )
                self.reset_row_1(action_rows[0])
                return await inter.response.edit_message(
                    embed=embed, components=action_rows
                )
        elif "language" in inter.component.custom_id:
            if inter.component.custom_id == "language_button":
                self.clear_extra_buttons(action_rows)
                language_row = ActionRow(Setup.Language.LanguageSelect())
                action_rows.append(language_row)
                self.reset_row_1(action_rows[0])
                action_rows[0].pop(3)
                action_rows[0].insert_item(
                    3, Setup.Language.LanguageButton(selected=True)
                )
                embed = SetupEmbed(
                    guild_in_db, self.bot.json_dict["languages"][guild_in_db.language]
                )
                return await inter.response.edit_message(
                    embed=embed, components=action_rows
                )
        elif inter.component.custom_id == "patch_notes_button":
            if guild_in_db.patch_notes:  # want to disable
                channel = self.bot.get_channel(
                    guild_in_db.announcement_channel_id
                ) or await self.bot.fetch_channel(guild_in_db.announcement_channel_id)
                self.bot.patch_channels.remove(channel)
                guild_in_db = GuildsDB.update_patch_notes(inter.guild_id, False)
                self.bot.patch_channels = [
                    channel
                    for channel in self.bot.patch_channels.copy()
                    if channel.guild.id != inter.guild_id
                ]
                action_rows[1].pop(0)
                action_rows[1].append_item(Setup.PatchNotes.PatchNotesButton())
                action_rows[1].children[0].disabled = False
                embed = SetupEmbed(
                    guild_in_db, self.bot.json_dict["languages"][guild_in_db.language]
                )
                return await inter.response.edit_message(
                    embed=embed, components=action_rows
                )
            else:  # want to enable
                channel = self.bot.get_channel(
                    guild_in_db.announcement_channel_id
                ) or await self.bot.fetch_channel(guild_in_db.announcement_channel_id)
                self.bot.patch_channels.append(channel)
                guild_in_db = GuildsDB.update_patch_notes(inter.guild_id, True)
                action_rows[1].pop(0)
                action_rows[1].append_item(Setup.PatchNotes.PatchNotesButton(True))
                action_rows[1].children[0].disabled = False
                embed = SetupEmbed(
                    guild_in_db, self.bot.json_dict["languages"][guild_in_db.language]
                )
                return await inter.response.edit_message(
                    embed=embed, components=action_rows
                )
        elif inter.component.custom_id == "major_order_updates_button":
            if guild_in_db.major_order_updates:  # want to disable
                channel = self.bot.get_channel(
                    guild_in_db.announcement_channel_id
                ) or await self.bot.fetch_channel(guild_in_db.announcement_channel_id)
                self.bot.major_order_channels.remove(channel)
                guild_in_db = GuildsDB.update_mo(inter.guild_id, False)
                self.bot.major_order_channels = [
                    channel
                    for channel in self.bot.major_order_channels.copy()
                    if channel.guild.id != inter.guild_id
                ]
                action_rows[1].pop(1)
                action_rows[1].append_item(
                    Setup.MajorOrderUpdates.MajorOrderUpdatesButton()
                )
                action_rows[1].children[1].disabled = False
                embed = SetupEmbed(
                    guild_in_db, self.bot.json_dict["languages"][guild_in_db.language]
                )
                return await inter.response.edit_message(
                    embed=embed, components=action_rows
                )
            else:  # want to enable
                channel = self.bot.get_channel(
                    guild_in_db.announcement_channel_id
                ) or await self.bot.fetch_channel(guild_in_db.announcement_channel_id)
                self.bot.major_order_channels.append(channel)
                guild_in_db = GuildsDB.update_mo(inter.guild_id, True)
                action_rows[1].pop(1)
                action_rows[1].append_item(
                    Setup.MajorOrderUpdates.MajorOrderUpdatesButton(True)
                )
                action_rows[1].children[1].disabled = False
                embed = SetupEmbed(
                    guild_in_db, self.bot.json_dict["languages"][guild_in_db.language]
                )
                return await inter.response.edit_message(
                    embed=embed, components=action_rows
                )

    @commands.Cog.listener("on_dropdown")
    async def on_dropdowns(self, inter: MessageInteraction):
        action_rows = ActionRow.rows_from_message(inter.message)
        if inter.component.custom_id == "dashboard_channel_select":
            guild_in_db: GuildRecord = GuildsDB.get_info(inter.guild_id)
            guild_language = self.bot.json_dict["languages"][guild_in_db.language]
            try:
                dashboard_channel = self.bot.get_channel(
                    inter.values[0]
                ) or await self.bot.fetch_channel(inter.values[0])
            except:
                return await inter.send(
                    guild_language["setup"]["missing_perm"],
                    ephemeral=True,
                )
            dashboard_perms_have = dashboard_channel.permissions_for(
                inter.guild.me
            ).is_superset(self.dashboard_perms_needed)
            if not dashboard_perms_have:
                return await inter.send(
                    guild_language["setup"]["missing_perm"],
                    ephemeral=True,
                )
            else:
                dashboard = Dashboard(
                    self.bot.data,
                    guild_language,
                    self.bot.json_dict,
                )
                try:
                    message = await dashboard_channel.send(
                        embeds=dashboard.embeds, file=File("resources/banner.png")
                    )
                except Exception as e:
                    self.bot.logger.error(f"SetupCog | dashboard setup | {e}")
                    return await inter.send(
                        "An error has occured, I have contacted Super Earth High Command.",
                        ephemeral=True,
                    )
                guild_in_db = GuildsDB.update_dashboard(
                    inter.guild_id, dashboard_channel.id, message.id
                )
                self.bot.dashboard_messages.append(message)
                embed = SetupEmbed(guild_in_db, guild_language)
                self.clear_extra_buttons(action_rows)
                self.reset_row_1(action_rows[0])
                await inter.response.edit_message(embed=embed, components=action_rows)
        elif inter.component.custom_id == "announcements_channel_select":
            try:
                announcement_channel = self.bot.get_channel(
                    inter.values[0]
                ) or await self.bot.fetch_channel(inter.values[0])
            except:
                return await inter.send(
                    guild_language["setup"]["missing_perm"],
                    ephemeral=True,
                )
            annnnouncement_perms_have = announcement_channel.permissions_for(
                inter.guild.me
            ).is_superset(self.annnnouncement_perms_needed)
            guild_in_db: GuildRecord = GuildsDB.get_info(inter.guild_id)
            guild_language = self.bot.json_dict["languages"][guild_in_db.language]
            if not annnnouncement_perms_have:
                return await inter.send(
                    guild_language["setup"]["missing_perm"],
                    ephemeral=True,
                )
            else:
                guild_in_db = GuildsDB.update_announcement_channel(
                    inter.guild_id, announcement_channel.id
                )
                self.bot.announcement_channels.append(announcement_channel)
                embed = SetupEmbed(
                    guild_in_db, self.bot.json_dict["languages"][guild_in_db.language]
                )
                self.clear_extra_buttons(action_rows)
                self.reset_row_1(action_rows[0])
                action_rows[1].children[0].disabled = False
                action_rows[1].children[1].disabled = False
                await inter.response.edit_message(embed=embed, components=action_rows)
        elif inter.component.custom_id == "map_channel_select":
            await inter.response.defer()
            guild_in_db: GuildRecord = GuildsDB.get_info(inter.guild_id)
            guild_language = self.bot.json_dict["languages"][guild_in_db.language]
            try:
                map_channel = self.bot.get_channel(
                    inter.values[0]
                ) or await self.bot.fetch_channel(inter.values[0])
            except:
                return await inter.send(
                    guild_language["setup"]["missing_perm"],
                    ephemeral=True,
                )
            map_perms_have = map_channel.permissions_for(inter.guild.me).is_superset(
                self.map_perms_needed
            )
            if not map_perms_have:
                return await inter.send(
                    guild_language["setup"]["missing_perm"],
                    ephemeral=True,
                )
            else:
                map_embed = await dashboard_maps(
                    self.bot.data,
                    self.bot.waste_bin_channel,
                    self.bot.json_dict["planets"],
                    guild_in_db.language,
                )
                message = await map_channel.send(
                    embed=map_embed,
                )
                guild_in_db = GuildsDB.update_map(
                    inter.guild_id, map_channel.id, message.id
                )
                self.bot.map_messages.append(message)
                embed = SetupEmbed(guild_in_db, guild_language)
                self.clear_extra_buttons(action_rows)
                self.reset_row_1(action_rows[0])
                await inter.edit_original_message(embed=embed, components=action_rows)
        elif inter.component.custom_id == "language_select":
            guild_in_db = GuildsDB.update_language(
                inter.guild_id, inter.values[0].lower()
            )
            embed = SetupEmbed(
                guild_in_db, self.bot.json_dict["languages"][guild_in_db.language]
            )
            self.clear_extra_buttons(action_rows)
            self.reset_row_1(action_rows[0])
            await inter.response.edit_message(embed=embed, components=action_rows)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(SetupCog(bot))
