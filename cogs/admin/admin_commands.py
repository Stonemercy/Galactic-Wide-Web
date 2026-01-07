from typing import TYPE_CHECKING
from disnake import (
    AppCmdInter,
    HTTPException,
    InteractionTimedOut,
    MessageInteraction,
    NotFound,
    Permissions,
    ui,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from re import search
from utils.checks import wait_for_startup
from utils.containers import GuildContainer
from utils.dataclasses import Config
from utils.dbv2 import GWWGuilds
from utils.embeds import BotInfoEmbeds
from utils.interactables import ConfirmButton

if TYPE_CHECKING:
    from utils.dbv2 import GWWGuild


class AdminCommandsCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=[Config.SUPPORT_SERVER_ID],
        description="Forces the choice to update ASAP",
        default_member_permissions=Permissions(administrator=True),
    )
    async def force_update_feature(
        self,
        inter: AppCmdInter,
        feature: str = commands.Param(
            choices=["Dashboard", "Map", "MO Update", "PO Update"]
        ),
    ) -> None:
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} <{feature = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        match feature:
            case "Dashboard":
                await self.bot.get_cog(name="DashboardCog").dashboard_poster()
            case "Map":
                await self.bot.get_cog(name="MapCog").map_poster()
            case "MO Update":
                await self.bot.get_cog(name="MajorOrderCog").major_order_updates()
            case "PO Update":
                await self.bot.get_cog(name="PersonalOrderCog").personal_order_updates()
        await inter.send(content="Completed", ephemeral=True)

    def extension_names_autocomp(inter: AppCmdInter, user_input: str) -> list[str]:
        """Returns the name of each cog currently loaded"""
        if not inter.bot.extensions:
            return []
        return [
            ext.split(".")[-1]
            for ext in list(inter.bot.extensions.keys())
            if user_input.lower() in ext.lower()
        ][:25]

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=[Config.SUPPORT_SERVER_ID],
        description="Reload an extension",
        default_member_permissions=Permissions(administrator=True),
    )
    async def reload_extension(
        self,
        inter: AppCmdInter,
        file_name: str = commands.Param(
            autocomplete=extension_names_autocomp,
        ),
    ) -> None:
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} <{file_name = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
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
            content=f":warning: No matching extension found for `{file_name}` in `cogs/` or `cogs/admin/`.",
            ephemeral=True,
        )

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=[Config.SUPPORT_SERVER_ID],
        description="Get a guild's info",
        default_member_permissions=Permissions(administrator=True),
    )
    async def get_guild(
        self, inter: AppCmdInter, id_to_check: int = commands.Param(large=True)
    ) -> None:
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} <{id_to_check = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        all_guilds = GWWGuilds(fetch_all=True)
        filtered_guild_list: list[GWWGuild] = [
            g
            for g in all_guilds
            if g.guild_id == id_to_check
            or id_to_check
            in (v for f in g.features for v in (f.channel_id, f.message_id) if v)
        ]
        if filtered_guild_list != []:
            db_guild = filtered_guild_list[0]
            discord_guild = self.bot.get_guild(
                db_guild.guild_id
            ) or await self.bot.fetch_guild(db_guild.guild_id)
            container = GuildContainer(
                guild=discord_guild, db_guild=db_guild, fetching=True
            )
            await inter.send(components=container, ephemeral=True)
        else:
            await inter.send(
                f"Didn't find a guild with ID `{id_to_check}` in use", ephemeral=True
            )
            return

    @commands.Cog.listener("on_button_click")
    async def on_button_clicks(self, inter: MessageInteraction) -> None:
        allowed_ids = {
            "leave_guild_button",
            "reset_guild_button",
            "leave_confirm_button",
            "reset_confirm_button",
        }
        if inter.component.custom_id not in allowed_ids:
            return
        try:
            await inter.response.defer()
        except (NotFound, InteractionTimedOut):
            await inter.channel.send(
                "There was an error with this interaction, please try again.",
                delete_after=5,
            )
            return
        guild_id_text_display: str = (
            inter.message.components[0].children[0].children[0].content
        )
        guild_id: int = int(
            search(r"Guild ID:\s*(\d+)", guild_id_text_display).group(1)
        )
        discord_guild = self.bot.get_guild(guild_id) or await self.bot.fetch_guild(
            guild_id
        )
        if inter.component.custom_id == "leave_guild_button":
            await inter.edit_original_response(
                components=[ui.components_from_message(inter.message)[0]]
                + [ui.ActionRow(ConfirmButton("leave", discord_guild))]
            )
        elif inter.component.custom_id == "reset_guild_button":
            await inter.edit_original_response(
                components=[ui.components_from_message(inter.message)[0]]
                + [ui.ActionRow(ConfirmButton("reset", discord_guild))]
            )
        elif "confirm_button" in inter.component.custom_id:
            split_button_id = inter.component.custom_id.split("_")
            db_guild: GWWGuild = GWWGuilds.get_specific_guild(id=guild_id)
            try:
                for interface_list in self.bot.interface_handler.lists.values():
                    interface_list.remove_entry(guild_id_to_remove=guild_id)
            except:
                pass
            match split_button_id[0]:
                case "leave":
                    try:
                        await discord_guild.leave()
                    except HTTPException as e:
                        await inter.send(
                            f"There was an error:\n```py\n{e}\n```", ephemeral=True
                        )
                        return
                    await inter.send(
                        content=f"Successfully left **{discord_guild.name}**",
                        ephemeral=True,
                    )
                case "reset":
                    try:
                        db_guild.reset()
                    except Exception as e:
                        await inter.send(
                            f"There was an error:\n```py\n{e}\n```", ephemeral=True
                        )
                        return
            await inter.edit_original_response(
                components=GuildContainer(
                    guild=discord_guild, db_guild=db_guild, fetching=True
                )
            )

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=[Config.SUPPORT_SERVER_ID],
        description="Get info about the bot",
        default_member_permissions=Permissions(administrator=True),
    )
    async def get_bot_info(self, inter: AppCmdInter) -> None:
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        embeds = BotInfoEmbeds(bot=self.bot)
        await inter.send(embeds=embeds, ephemeral=True)

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=[Config.SUPPORT_SERVER_ID],
        description="Get possible fake guilds",
        default_member_permissions=Permissions(administrator=True),
    )
    async def get_fake_guilds(
        self,
        inter: AppCmdInter,
        public: str = commands.Param(choices=["Yes", "No"], default="No"),
    ) -> None:
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        gww_guilds = GWWGuilds(fetch_all=True)
        possible_fake_guilds = []
        for gww_guild in gww_guilds:
            if gww_guild.features == []:
                discord_guild = self.bot.get_guild(
                    gww_guild.guild_id
                ) or await self.bot.fetch_guild(gww_guild.guild_id)
                if (
                    len(discord_guild.text_channels) == 3
                    and discord_guild.member_count < 100
                ):
                    possible_fake_guilds.append(discord_guild)
        await inter.send(f"Possible fake guilds: {len(possible_fake_guilds)}")


def setup(bot: GalacticWideWebBot) -> None:
    bot.add_cog(AdminCommandsCog(bot))
