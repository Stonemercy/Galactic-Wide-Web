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
from utils.db import GWWGuild
from utils.embeds import Dashboard, SetupEmbed
from utils.maps import Maps


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
        guild = GWWGuild.get_by_id(inter.guild_id)
        components = [
            (
                ActionRow(
                    Setup.Dashboard.DashboardButton(),
                    Setup.Announcements.AnnouncementsButton(),
                    Setup.Map.MapButton(),
                    Setup.Language.LanguageButton(),
                )
            ),
            (
                ActionRow(
                    Setup.PatchNotes.PatchNotesButton(guild.patch_notes),
                    Setup.MajorOrderUpdates.MajorOrderUpdatesButton(
                        guild.major_order_updates
                    ),
                )
            ),
        ]
        if guild.announcement_channel_id != 0:
            components[1][0].disabled = False
            components[1][1].disabled = False
        await inter.send(
            embed=SetupEmbed(
                guild=guild,
                language_json=self.bot.json_dict["languages"][guild.language],
            ),
            components=components,
        )

    @commands.Cog.listener("on_button_click")
    async def ban_listener(self, inter: MessageInteraction):
        action_rows = ActionRow.rows_from_message(inter.message)
        guild = GWWGuild.get_by_id(inter.guild_id)
        if "dashboard" in inter.component.custom_id:
            self.clear_extra_buttons(action_rows)
            if inter.component.custom_id == "dashboard_button":
                dashboard_row = ActionRow(
                    Setup.Dashboard.ClearDashboardButton()
                    if 0
                    not in (
                        guild.dashboard_channel_id,
                        guild.dashboard_message_id,
                    )
                    else Setup.Dashboard.SetDashboardButton()
                )
                action_rows.append(dashboard_row)
                self.reset_row_1(action_rows[0])
                action_rows[0].pop(0)
                action_rows[0].insert_item(
                    0, Setup.Dashboard.DashboardButton(selected=True)
                )
                return await inter.response.edit_message(components=action_rows)
            elif inter.component.custom_id == "set_dashboard_button":
                action_rows.append(ActionRow(Setup.Dashboard.DashboardChannelSelect()))
                return await inter.response.edit_message(components=action_rows)
            elif inter.component.custom_id == "clear_dashboard_button":
                guild.dashboard_channel_id = 0
                guild.dashboard_message_id = 0
                guild.save_changes()
                self.bot.dashboard_messages = [
                    message
                    for message in self.bot.dashboard_messages.copy()
                    if message.guild.id != inter.guild_id
                ]
                self.reset_row_1(action_rows[0])
                return await inter.response.edit_message(
                    embed=SetupEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
        elif "announcements" in inter.component.custom_id:
            self.clear_extra_buttons(action_rows)
            if inter.component.custom_id == "announcements_button":
                action_rows.append(
                    ActionRow(
                        Setup.Announcements.ClearAnnouncementsButton()
                        if guild.announcement_channel_id != 0
                        else Setup.Announcements.SetAnnouncementsButton()
                    )
                )
                self.reset_row_1(action_rows[0])
                action_rows[0].pop(1)
                action_rows[0].insert_item(
                    1, Setup.Announcements.AnnouncementsButton(selected=True)
                )
                return await inter.response.edit_message(components=action_rows)
            elif inter.component.custom_id == "set_announcements_button":
                action_rows.append(
                    ActionRow(Setup.Announcements.AnnouncementsChannelSelect())
                )
                return await inter.response.edit_message(components=action_rows)
            elif inter.component.custom_id == "clear_announcements_button":
                guild.announcement_channel_id = 0
                guild.patch_notes = False
                guild.major_order_updates = False
                guild.save_changes()
                self.bot.announcement_channels = [
                    channel
                    for channel in self.bot.announcement_channels.copy()
                    if channel.guild.id != inter.guild_id
                ]
                self.bot.patch_channels = [
                    channel
                    for channel in self.bot.patch_channels.copy()
                    if channel.guild.id != inter.guild.id
                ]
                self.bot.major_order_channels = [
                    channel
                    for channel in self.bot.major_order_channels.copy()
                    if channel.guild.id != inter.guild.id
                ]
                action_rows[1].clear_items()
                action_rows[1].append_item(Setup.PatchNotes.PatchNotesButton())
                action_rows[1].append_item(
                    Setup.MajorOrderUpdates.MajorOrderUpdatesButton()
                )
                self.reset_row_1(action_rows[0])
                return await inter.response.edit_message(
                    embed=SetupEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
        elif "map" in inter.component.custom_id:
            if inter.component.custom_id == "map_button":
                self.clear_extra_buttons(action_rows)
                action_rows.append(
                    ActionRow(
                        Setup.Map.ClearMapButton()
                        if 0
                        not in (
                            guild.map_channel_id,
                            guild.map_message_id,
                        )
                        else Setup.Map.SetMapButton()
                    )
                )
                self.reset_row_1(action_rows[0])
                action_rows[0].pop(2)
                action_rows[0].insert_item(2, Setup.Map.MapButton(selected=True))
                return await inter.response.edit_message(components=action_rows)
            elif inter.component.custom_id == "set_map_button":
                self.clear_extra_buttons(action_rows)
                action_rows.append(ActionRow(Setup.Map.MapChannelSelect()))
                return await inter.response.edit_message(components=action_rows)
            elif inter.component.custom_id == "clear_map_button":
                self.clear_extra_buttons(action_rows)
                guild.map_channel_id = 0
                guild.map_message_id = 0
                guild.save_changes()
                self.bot.map_messages = [
                    message
                    for message in self.bot.map_messages.copy()
                    if message.guild.id != inter.guild_id
                ]
                self.reset_row_1(action_rows[0])
                return await inter.response.edit_message(
                    embed=SetupEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
        elif "language" in inter.component.custom_id:
            if inter.component.custom_id == "language_button":
                self.clear_extra_buttons(action_rows)
                action_rows.append(ActionRow(Setup.Language.LanguageSelect()))
                self.reset_row_1(action_rows[0])
                action_rows[0].pop(3)
                action_rows[0].insert_item(
                    3, Setup.Language.LanguageButton(selected=True)
                )
                return await inter.response.edit_message(
                    embed=SetupEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
        elif inter.component.custom_id == "patch_notes_button":
            if guild.patch_notes:  # want to disable
                channel = self.bot.get_channel(
                    guild.announcement_channel_id
                ) or await self.bot.fetch_channel(guild.announcement_channel_id)
                self.bot.patch_channels = [
                    channel
                    for channel in self.bot.patch_channels.copy()
                    if channel.guild.id != inter.guild_id
                ]
                guild.patch_notes = False
                guild.save_changes()
                action_rows[1].pop(0)
                action_rows[1].insert_item(0, Setup.PatchNotes.PatchNotesButton())
                action_rows[1][0].disabled = False
                return await inter.response.edit_message(
                    embed=SetupEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
            else:  # want to enable
                channel = self.bot.get_channel(
                    guild.announcement_channel_id
                ) or await self.bot.fetch_channel(guild.announcement_channel_id)
                self.bot.patch_channels.append(channel)
                guild.patch_notes = True
                guild.save_changes()
                action_rows[1].pop(0)
                action_rows[1].insert_item(0, Setup.PatchNotes.PatchNotesButton(True))
                action_rows[1][0].disabled = False
                return await inter.response.edit_message(
                    embed=SetupEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
        elif inter.component.custom_id == "major_order_updates_button":
            if guild.major_order_updates:  # want to disable
                guild.major_order_updates = False
                guild.save_changes()
                self.bot.major_order_channels = [
                    channel
                    for channel in self.bot.major_order_channels.copy()
                    if channel.guild.id != inter.guild_id
                ]
                action_rows[1].pop(1)
                action_rows[1].insert_item(
                    1, Setup.MajorOrderUpdates.MajorOrderUpdatesButton()
                )
                action_rows[1].children[1].disabled = False
                return await inter.response.edit_message(
                    embed=SetupEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )
            else:  # want to enable
                channel = self.bot.get_channel(
                    guild.announcement_channel_id
                ) or await self.bot.fetch_channel(guild.announcement_channel_id)
                self.bot.major_order_channels.append(channel)
                guild.major_order_updates = True
                guild.save_changes()
                action_rows[1].pop(1)
                action_rows[1].insert_item(
                    1, Setup.MajorOrderUpdates.MajorOrderUpdatesButton(True)
                )
                action_rows[1].children[1].disabled = False
                return await inter.response.edit_message(
                    embed=SetupEmbed(
                        guild, self.bot.json_dict["languages"][guild.language]
                    ),
                    components=action_rows,
                )

    @commands.Cog.listener("on_dropdown")
    async def on_dropdowns(self, inter: MessageInteraction):
        if inter.component.custom_id not in (
            "dashboard_channel_select",
            "announcements_channel_select",
            "map_channel_select",
            "language_select",
        ):
            return
        action_rows = ActionRow.rows_from_message(inter.message)
        guild = GWWGuild.get_by_id(inter.guild_id)
        guild_language = self.bot.json_dict["languages"][guild.language]
        if inter.component.custom_id == "dashboard_channel_select":
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
                guild.dashboard_channel_id = dashboard_channel.id
                guild.dashboard_message_id = message.id
                guild.save_changes()
                self.bot.dashboard_messages.append(message)
                embed = SetupEmbed(guild, guild_language)
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
            if not annnnouncement_perms_have:
                return await inter.send(
                    guild_language["setup"]["missing_perm"],
                    ephemeral=True,
                )
            else:
                guild.announcement_channel_id = announcement_channel.id
                guild.save_changes()
                self.bot.announcement_channels.append(announcement_channel)
                embed = SetupEmbed(guild, guild_language)
                self.clear_extra_buttons(action_rows)
                self.reset_row_1(action_rows[0])
                action_rows[1].children[0].disabled = False
                action_rows[1].children[1].disabled = False
                await inter.response.edit_message(embed=embed, components=action_rows)
        elif inter.component.custom_id == "map_channel_select":
            await inter.response.defer()
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
                self.clear_extra_buttons(action_rows)
                self.reset_row_1(action_rows[0])
                await inter.edit_original_message(components=action_rows)
                await inter.send(
                    "Generating map, please wait...", delete_after=10, ephemeral=True
                )
                map = Maps(
                    data=self.bot.data,
                    waste_bin_channel=self.bot.waste_bin_channel,
                    planet_names_json=self.bot.json_dict["planets"],
                    languages_json_list=[guild_language],
                )
                await map.localize()
                message = await map_channel.send(
                    embed=map.embeds[guild.language],
                )
                guild.map_channel_id = map_channel.id
                guild.map_message_id = message.id
                guild.save_changes()
                self.bot.map_messages.append(message)
                embed = SetupEmbed(guild, guild_language)
                await inter.edit_original_message(embed=embed, components=action_rows)
        elif inter.component.custom_id == "language_select":
            guild.language = inter.values[0].lower()
            guild.save_changes()
            embed = SetupEmbed(guild, self.bot.json_dict["languages"][guild.language])
            self.clear_extra_buttons(action_rows)
            self.reset_row_1(action_rows[0])
            await inter.response.edit_message(embed=embed, components=action_rows)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(SetupCog(bot))
