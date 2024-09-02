from asyncio import sleep
from datetime import datetime
from os import getenv
from disnake import AppCmdInter, Permissions
from disnake.ext import commands
from helpers.db import Feedback, Guilds
from helpers.embeds import AnnouncementEmbed
from main import GalacticWideWebBot


SUPPORT_SERVER = [int(getenv("SUPPORT_SERVER"))]


class AdminCommandsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    def owner_only():
        def predicate(inter: AppCmdInter):
            return inter.author.id == inter.bot.owner_id

        return commands.check(predicate)

    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: AppCmdInter, error):
        if isinstance(error, commands.CheckFailure):
            return await inter.send(
                f"You need to be the owner of {inter.guild.me.mention} to use this command."
            )
        raise error

    @owner_only()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER,
        description="Forces dashboards to update ASAP",
        default_member_permissions=Permissions(administrator=True),
    )
    async def force_update_dashboard(self, inter: AppCmdInter):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"AdminCommandsCog, {inter.application_command.name} command used by {inter.author.id} - {inter.author.name}"
        )
        update_start = datetime.now()
        dashboards_updated = await self.bot.get_cog("DashboardCog").dashboard(
            force=True
        )
        text = f"Forced updates of {dashboards_updated} dashboards in {(datetime.now() - update_start).total_seconds():.2f} seconds"
        self.bot.logger.info(text)
        await inter.send(text, ephemeral=True)

    @owner_only()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER,
        description="Forces maps to update ASAP",
        default_member_permissions=Permissions(administrator=True),
    )
    async def force_update_maps(self, inter: AppCmdInter):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"AdminCommandsCog, {inter.application_command.name} command used by {inter.author.id} - {inter.author.name}"
        )
        update_start = datetime.now()
        maps_updated = await self.bot.get_cog("MapCog").map_poster(force=True)
        text = f"Forced updates of {maps_updated} maps in {(datetime.now() - update_start).total_seconds():.2f} seconds"
        self.bot.logger.info(text)
        await inter.send(text, ephemeral=True)

    @owner_only()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER,
        description="Send out the prepared announcement",
        default_member_permissions=Permissions(administrator=True),
    )
    async def send_announcement(self, inter: AppCmdInter, test: bool):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"AdminCommandsCog, {inter.application_command.name} command used by {inter.author.id} - {inter.author.name}"
        )
        update_start = datetime.now()
        languages = Guilds.get_used_languages()
        embeds = {lang: AnnouncementEmbed() for lang in languages}
        if test == True:
            return await inter.send(embed=embeds["en"], ephemeral=True)
        chunked_channels = [
            self.bot.announcement_channels[i : i + 50]
            for i in range(0, len(self.bot.announcement_channels), 50)
        ]
        for chunk in chunked_channels:
            for channel in chunk:
                self.bot.loop.create_task(
                    self.bot.get_cog("AnnouncementsCog").send_embed(
                        channel, embeds, "Announcement"
                    )
                )
            await sleep(1.025)
        await inter.send(
            f"Attempted to send out an announcement to {len(self.bot.announcement_channels)} channels in {(datetime.now() - update_start).total_seconds():.2f} seconds",
            ephemeral=True,
        )

    @owner_only()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER,
        description="Unban someone you accidentally banned from giving feedback",
        default_member_permissions=Permissions(administrator=True),
    )
    async def feedback_unban(self, inter: AppCmdInter, user_id):
        self.bot.logger.critical(
            f"AdminCommandsCog, {inter.application_command.name}: {user_id} command used by {inter.author.id} - {inter.author.name}"
        )
        user = Feedback.get_user(user_id)
        if not user:
            return await inter.send("That user doesn't exist in the db", ephemeral=True)
        elif user[1] == False:
            return await inter.send("That user isn't banned", ephemeral=True)
        Feedback.unban_user(user_id)
        await inter.send(f"Unbanned {user_id}", ephemeral=True)

    @owner_only()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER,
        description="Provide the reason for a ban",
        default_member_permissions=Permissions(administrator=True),
    )
    async def feedback_ban_reason(self, inter: AppCmdInter, user_id, reason):
        self.bot.logger.critical(
            f"AdminCommandsCog, {inter.application_command.name}: {user_id}, {reason} command used by {inter.author.id} - {inter.author.name}"
        )
        user = Feedback.get_user(user_id)
        if not user:
            return await inter.send("That user doesn't exist in the db", ephemeral=True)
        elif user[1] == False:
            return await inter.send("That user isn't banned", ephemeral=True)
        Feedback.set_reason(user_id, reason)
        await inter.send(f"Reason set for {user_id}:\n{reason}", ephemeral=True)

    @owner_only()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER,
        description="Un-mark a user as good",
        default_member_permissions=Permissions(administrator=True),
    )
    async def not_good_feedback(self, inter: AppCmdInter, user_id):
        self.bot.logger.critical(
            f"AdminCommandsCog, {inter.application_command.name}: {user_id} command used by {inter.author.id} - {inter.author.name}"
        )
        user = Feedback.get_user(user_id)
        if not user:
            return await inter.send("That user doesn't exist in the db", ephemeral=True)
        elif user[3] == False:
            return await inter.send("That user isn't a good user", ephemeral=True)
        Feedback.not_good_user(user_id)
        await inter.send(f"User **{user_id}** set as not-good feedback", ephemeral=True)

    @owner_only()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER,
        description="Reload a cog",
        default_member_permissions=Permissions(administrator=True),
    )
    async def reload_extension(self, inter: AppCmdInter, ext: str):
        self.bot.logger.critical(
            f"AdminCommandsCog, {inter.application_command.name}: {ext} command used by {inter.author.id} - {inter.author.name}"
        )
        admin_ext = f"cogs.admin.{ext}"
        ext = f"cogs.{ext}"
        if ext not in [extension for extension in self.bot.extensions.keys()]:
            if admin_ext not in [extension for extension in self.bot.extensions.keys()]:
                return await inter.send("Extension not found", ephemeral=True)
            else:
                ext = admin_ext
        try:
            self.bot.reload_extension(ext)
            return await inter.send(f"Reloaded the `{ext}` extension", ephemeral=True)
        except Exception as e:
            return await inter.send(f"Error:\n{e}")


def setup(bot: GalacticWideWebBot):
    bot.add_cog(AdminCommandsCog(bot))
