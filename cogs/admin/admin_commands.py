from datetime import datetime
from sys import argv, executable
from disnake import AppCmdInter, Colour, Embed, Permissions
from disnake.ext import commands
from main import GalacticWideWebBot
from os import execv, getenv
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
        await self.bot.get_cog("DashboardCog").dashboard_poster()
        await inter.send(
            f"Forced updates of {len(self.bot.interface_handler.dashboards)} dashboards in {(datetime.now() - update_start).total_seconds():.2f} seconds",
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
        await self.bot.get_cog("MapCog").map_poster()
        text = f"Forced updates of {len(self.bot.interface_handler.maps)} maps in {(datetime.now() - update_start).total_seconds():.2f} seconds"
        self.bot.logger.info(text)
        await inter.send(text, ephemeral=True)

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Forces MO updates to be sent ASAP",
        default_member_permissions=Permissions(administrator=True),
    )
    async def force_mo_update(self, inter: AppCmdInter, test: bool = False):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        update_start = datetime.now()
        await self.bot.get_cog("AnnouncementsCog").major_order_updates(test=test)
        text = f"Forced updates of {len(self.bot.interface_handler.news_feeds.channels_dict['MO'])} MO updates in {(datetime.now() - update_start).total_seconds():.2f} seconds"
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
        file_name: str = commands.Param(description="The extension to reload"),
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} <{file_name = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        possible_paths = [f"cogs.{file_name}", f"cogs.admin.{file_name}"]

        for path in possible_paths:
            try:
                self.bot.reload_extension(path)
                await inter.send(f"🔄 Successfully reloaded `{path}`!", ephemeral=True)
                return
            except commands.ExtensionNotLoaded:
                continue
            except Exception as e:
                await inter.send(f"❌ Failed to reload `{path}`\n```{e}```")
                return

        await inter.send(
            f"⚠️ No matching extension found for `{file_name}` in `cogs/` or `cogs/admin/`."
        )

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
        embeds = []
        for place, guild in enumerate(
            sorted(
                [guild for guild in self.bot.guilds],
                key=lambda guild: guild.member_count,
                reverse=True,
            )[:5],
            start=1,
        ):
            embed = (
                Embed(title=f"Guild #{place}", colour=Colour.brand_green())
                .add_field("Name", guild.name, inline=False)
                .add_field("Users", guild.member_count, inline=False)
                .add_field(
                    "Big guild?", {True: "Yes", False: "No"}[guild.large], inline=False
                )
                .add_field(
                    "Created",
                    f"<t:{int(guild.created_at.timestamp())}:R>",
                    inline=False,
                )
                .add_field("Owner", f"<@{guild.owner_id}>", inline=False)
                .set_thumbnail(guild.icon.url if guild.icon else None)
                .set_image(guild.banner.url if guild.banner else None)
            )
            embeds.append(embed)
        await inter.send(
            (
                f"- Dashboard messages:\n  - Amount: {len(self.bot.interface_handler.dashboards)}\n\n"
                f"- Announcement channels:\n  - Amount: {len(self.bot.interface_handler.news_feeds.channels_dict['Generic'])}\n\n"
                f"- Patch Channels:\n  - Amount: {len(self.bot.interface_handler.news_feeds.channels_dict['Patch'])}\n\n"
                f"- Major Order channels:\n  - Amount: {len(self.bot.interface_handler.news_feeds.channels_dict['MO'])}\n\n"
                f"- Personal Order channels:\n  - Amount: {len(self.bot.interface_handler.news_feeds.channels_dict['PO'])}\n\n"
                f"- Map messages:\n  - Amount: {len(self.bot.interface_handler.maps)}\n\n"
                f"- Detailed Dispatches Channels:\n  - Amount: {len(self.bot.interface_handler.news_feeds.channels_dict['DetailedDispatches'])}"
            ),
            ephemeral=True,
            embeds=embeds,
        )

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Restarts the bot",
        default_member_permissions=Permissions(administrator=True),
    )
    async def restart_bot(
        self,
        inter: AppCmdInter,
    ):
        await inter.send("Restarting the bot...", ephemeral=True)
        python = executable
        execv(python, [python] + argv)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(AdminCommandsCog(bot))
