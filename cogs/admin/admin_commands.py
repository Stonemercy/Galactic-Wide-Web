from datetime import datetime
from random import choice
from disnake import AppCmdInter, Guild, Permissions
from disnake.ext import commands
from main import GalacticWideWebBot
from os import execv, getenv
from sys import argv, executable
from utils.checks import wait_for_startup
from utils.db import GWWGuild


SUPPORT_SERVER_ID = [int(getenv("SUPPORT_SERVER"))]


class AdminCommandsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Forces the choice to update ASAP",
        default_member_permissions=Permissions(administrator=True),
    )
    async def force_update_feature(
        self,
        inter: AppCmdInter,
        feature: str = commands.Param(
            choices=[
                "Dashboard",
                "Map",
                "MO Update",
                # "PO Update",
            ]
        ),
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            msg=f"{self.qualified_name} | /{inter.application_command.name} <{feature = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        update_start = datetime.now()
        match feature:
            case "Dashboard":
                await self.bot.get_cog(name="DashboardCog").dashboard_poster()
                text = f"Forced updates of {len(self.bot.interface_handler.dashboards)} dashboards in {(datetime.now() - update_start).total_seconds():.2f} seconds"
            case "Map":
                await self.bot.get_cog(name="MapCog").map_poster()
                text = f"Forced updates of {len(self.bot.interface_handler.maps)} maps in {(datetime.now() - update_start).total_seconds():.2f} seconds"
            case "MO Update":
                await self.bot.get_cog(name="AnnouncementsCog").major_order_updates()
                text = f"Forced updates of {len(self.bot.interface_handler.news_feeds.channels_dict['MO'])} MO updates in {(datetime.now() - update_start).total_seconds():.2f} seconds"
            # case "PO Update":
            #     await self.bot.get_cog(name="PersonalOrderCog").personal_order_update()
            #     text = f"Forced updates of {len(self.bot.interface_handler.news_feeds.channels_dict['PO'])} PO updates in {(datetime.now() - update_start).total_seconds():.2f} seconds"
        self.bot.logger.info(msg=text)
        await inter.send(content=text, ephemeral=True)

    def extension_names_autocomp(inter: AppCmdInter, user_input: str):
        """Returns the name of each cog currently loaded"""
        return [
            ext.split(".")[-1]
            for ext in list(inter.bot.extensions.keys())
            if user_input.lower() in ext.lower()
        ][:25]

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
        file_name: str = commands.Param(
            description="The extension to reload",
            autocomplete=extension_names_autocomp,
        ),
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            msg=f"{self.qualified_name} | /{inter.application_command.name} <{file_name = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        for path in [f"cogs.{file_name}", f"cogs.admin.{file_name}"]:
            try:
                self.bot.reload_extension(name=path)
                await inter.send(
                    content=f"Successfully reloaded `{path}`", ephemeral=True
                )
                return
            except commands.ExtensionNotLoaded:
                continue
            except Exception as e:
                await inter.send(
                    content=f"Failed to reload `{path}`\n```py\n{e}```", ephemeral=True
                )
                return
        await inter.send(
            content=f":warning: No matching extension found for `{file_name}` in `cogs/` or `cogs/admin/`."
        )

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Fake a event for the bot",
        default_member_permissions=Permissions(administrator=True),
    )
    async def fake_event(
        self,
        inter: AppCmdInter,
        event: str = commands.Param(choices=["guild_join", "guild_remove"]),
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            msg=f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        match event:
            case "guild_join" | "guild_remove":
                fake_guild: Guild = choice(self.bot.guilds)
                self.bot.dispatch(event_name=event, guild=fake_guild)
                await inter.send(
                    content=f"Faked {event} for {fake_guild.name}",
                    ephemeral=True,
                    delete_after=10,
                )
            case _:
                await inter.send("Event not organsied", ephemeral=True)

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Reset a guild in the DB",
        default_member_permissions=Permissions(administrator=True),
    )
    async def reset_guild(
        self,
        inter: AppCmdInter,
        id_to_check: int = commands.Param(large=True),
        reason: str = commands.Param(default="No reason given"),
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            msg=f"{self.qualified_name} | /{inter.application_command.name} <{id_to_check = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        all_guilds = GWWGuild.get_all()
        for guild in all_guilds:
            if id_to_check in guild.ids_in_use:
                try:
                    self.bot.interface_handler.dashboards.remove_entry(
                        guild_id_to_remove=guild.id
                    )
                    self.bot.interface_handler.maps.remove_entry(
                        guild_id_to_remove=guild.id
                    )
                    self.bot.interface_handler.news_feeds.remove_entry(
                        guild_id_to_remove=guild.id
                    )
                except:
                    pass
                guild.reset()
                await inter.send(
                    f"Successfully reset guild with ID {guild.id}", ephemeral=True
                )
                guild_in_discord = self.bot.get_guild(
                    guild.id
                ) or await self.bot.fetch_guild(guild.id)
                if guild_in_discord:
                    guild_owner = (
                        guild_in_discord.owner
                        if guild_in_discord.owner
                        else self.bot.get_user(guild_in_discord.owner_id)
                        or await self.bot.fetch_user(guild_in_discord.owner_id)
                    )
                    if guild_owner:
                        await guild_owner.send(
                            f"Unfortunately there was an error on our end that resulted in your server settings (for this bot) being reset.\nReason:\n-# {reason}"
                        )
                return
        await inter.send(f"Didn't find a guild with `{id_to_check}` in it's ID's")


def setup(bot: GalacticWideWebBot):
    bot.add_cog(cog=AdminCommandsCog(bot))
