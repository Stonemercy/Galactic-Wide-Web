from datetime import datetime
from disnake import AppCmdInter, Permissions
from disnake.ext import commands
from main import GalacticWideWebBot
from os import getenv
from utils.checks import wait_for_startup
from utils.db import FeedbackUser


SUPPORT_SERVER_ID = [int(getenv("SUPPORT_SERVER"))]


class AdminCommandsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Forces dashboards to update ASAP",
        default_member_permissions=Permissions(administrator=True),
    )
    async def force_update_dashboards(self, inter: AppCmdInter):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        update_start = datetime.now()
        dashboards_updated = await self.bot.get_cog("DashboardCog").dashboard()
        await inter.send(
            f"Forced updates of {dashboards_updated} dashboards in {(datetime.now() - update_start).total_seconds():.2f} seconds",
            ephemeral=True,
        )

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Forces maps to update ASAP",
        default_member_permissions=Permissions(administrator=True),
    )
    async def force_update_maps(self, inter: AppCmdInter):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        update_start = datetime.now()
        maps_updated = await self.bot.get_cog("MapCog").map_poster()
        await inter.send(
            f"Forced updates of {maps_updated} maps in {(datetime.now() - update_start).total_seconds():.2f} seconds",
            ephemeral=True,
        )

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Forces MO updates to be sent ASAP",
        default_member_permissions=Permissions(administrator=True),
    )
    async def force_mo_update(self, inter: AppCmdInter):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        if not self.bot.data.assignment:
            return await inter.send("No assignment data available", ephemeral=True)
        update_start = datetime.now()
        updates_sent = await self.bot.get_cog("AnnouncementsCog").major_order_updates(
            force=True
        )
        text = f"Forced updates of {updates_sent} MO updates in {(datetime.now() - update_start).total_seconds():.2f} seconds"
        self.bot.logger.info(text)
        await inter.send(text, ephemeral=True)

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Unban someone you accidentally banned from giving feedback",
        default_member_permissions=Permissions(administrator=True),
    )
    async def feedback_unban(
        self,
        inter: AppCmdInter,
        user_id: int = commands.Param(
            description="The ID of the user you want to unban", large=True
        ),
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} <{user_id = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        feedback_user = FeedbackUser.get_by_id(user_id)
        if not feedback_user.banned:
            return await inter.send("That user isn't banned", ephemeral=True)
        else:
            feedback_user.banned = True
            feedback_user.save_changes()
            await inter.send(f"Unbanned <@{user_id}>", ephemeral=True)

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Provide the reason for a ban",
        default_member_permissions=Permissions(administrator=True),
    )
    async def feedback_ban_reason(
        self,
        inter: AppCmdInter,
        user_id: int = commands.Param(
            description="The ID of a banned user you want to add a reason to",
            large=True,
        ),
        reason: str = commands.Param(description="The reason they are banned"),
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} <{user_id = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        feedback_user = FeedbackUser.get_by_id(user_id)
        if not feedback_user.banned:
            return await inter.send("That user isn't banned", ephemeral=True)
        else:
            feedback_user.reason = reason
            feedback_user.save_changes()
            await inter.send(f"Reason set for <@{user_id}>:\n{reason}", ephemeral=True)

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Un-mark a user as good",
        default_member_permissions=Permissions(administrator=True),
    )
    async def not_good_feedback(
        self,
        inter: AppCmdInter,
        user_id: int = commands.Param(
            description="Remove the good feedback tag from a user", large=True
        ),
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} <{user_id = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        feedback_user = FeedbackUser.get_by_id(user_id)
        if not feedback_user.good_feedback:
            return await inter.send("That user isn't a good user", ephemeral=True)
        else:
            feedback_user.good_feedback = False
            feedback_user.save_changes()
            await inter.send(f"<@{user_id}> removed from good feedback", ephemeral=True)

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Reload an extension",
        default_member_permissions=Permissions(administrator=True),
    )
    async def reload_extension(
        self,
        inter: AppCmdInter,
        ext: str = commands.Param(description="The extension to reload"),
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} <{ext = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        admin_ext = f"cogs.admin.{ext}"
        ext = f"cogs.{ext}"
        if ext not in [
            extension for extension in self.bot.extensions.keys()
        ] and admin_ext not in [extension for extension in self.bot.extensions.keys()]:
            return await inter.send("Extension not found", ephemeral=True)
        else:
            ext = admin_ext
        try:
            self.bot.reload_extension(ext)
            return await inter.send(f"Reloaded the `{ext}` extension", ephemeral=True)
        except Exception as e:
            return await inter.send(f"Error:\n{e}", ephemeral=True)

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Get Data",
        default_member_permissions=Permissions(administrator=True),
    )
    async def get_data(
        self,
        inter: AppCmdInter,
    ):
        await inter.send(
            (
                f"# Dashboard messages:\n- Length: {len(self.bot.dashboard_messages)}\n- Type: {type(self.bot.dashboard_messages)}\n\n"
                f"# Announcement channels:\n- Length: {len(self.bot.announcement_channels)}\n- Type: {type(self.bot.announcement_channels)}\n\n"
                f"# Patch Channels:\n- Length: {len(self.bot.patch_channels)}\n- Type: {type(self.bot.patch_channels)}\n\n"
                f"# Major Order channels:\n- Length: {len(self.bot.major_order_channels)}\n- Type: {type(self.bot.major_order_channels)}\n\n"
                f"# Map messages:\n- Length: {len(self.bot.map_messages)}\n- Type: {type(self.bot.map_messages)}\n\n"
            )
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(AdminCommandsCog(bot))
