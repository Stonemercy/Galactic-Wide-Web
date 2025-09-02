from asyncio import sleep
from datetime import datetime
from disnake import (
    AppCmdInter,
    Guild,
    HTTPException,
    InteractionTimedOut,
    MessageInteraction,
    NotFound,
    Permissions,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from os import getenv
from random import choice
from utils.checks import wait_for_startup
from utils.dataclasses import Languages
from utils.dbv2 import GWWGuild, GWWGuilds
from utils.embeds import BotInfoEmbeds, Dashboard, GuildEmbed, PlanetEmbeds
from utils.interactables import (
    ConfirmButton,
    HDCButton,
    LeaveGuildButton,
    ResetGuildButton,
    WikiButton,
)


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
                await self.bot.get_cog(name="MajorOrderCog").major_order_updates()
                text = f"Forced updates of {len(self.bot.interface_handler.major_order_updates)} MO updates in {(datetime.now() - update_start).total_seconds():.2f} seconds"
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
            content=f":warning: No matching extension found for `{file_name}` in `cogs/` or `cogs/admin/`.",
            ephemeral=True,
        )

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Fake an event for the bot",
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
                await inter.send("Event not configured", ephemeral=True)

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Reset a guild in the DB",
        default_member_permissions=Permissions(administrator=True),
    )
    async def get_guild(
        self, inter: AppCmdInter, id_to_check: int = commands.Param(large=True)
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            msg=f"{self.qualified_name} | /{inter.application_command.name} <{id_to_check = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        all_guilds = GWWGuilds(fetch_all=True)
        filtered_guild_list = [
            g
            for g in all_guilds
            if g.guild_id == id_to_check
            or id_to_check
            in [v for f in g.features for v in (f.channel_id, f.message_id) if v]
        ]
        if filtered_guild_list != []:
            db_guild = filtered_guild_list[0]
            guild = self.bot.get_guild(db_guild.guild_id) or await self.bot.fetch_guild(
                db_guild.guild_id
            )
            embed = GuildEmbed(guild=guild, db_guild=db_guild)
            components = [LeaveGuildButton(), ResetGuildButton()]
            await inter.send(embed=embed, components=components, ephemeral=True)
        else:
            await inter.send(
                f"Didn't find a guild with ID `{id_to_check}` in use", ephemeral=True
            )
            return

    @commands.Cog.listener("on_button_click")
    async def on_button_clicks(self, inter: MessageInteraction):
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
        guild_id = int(inter.message.embeds[0].fields[0].value[3:])
        discord_guild = self.bot.get_guild(guild_id) or await self.bot.fetch_guild(
            guild_id
        )
        if inter.component.custom_id == "leave_guild_button":
            await inter.edit_original_response(
                components=[ConfirmButton("leave", discord_guild)]
            )
        elif inter.component.custom_id == "reset_guild_button":
            await inter.edit_original_response(
                components=[ConfirmButton("reset", discord_guild)]
            )
        elif "confirm_button" in inter.component.custom_id:
            split_button_id = inter.component.custom_id.split("_")
            db_guild: GWWGuild = GWWGuilds.get_specific_guild(id=guild_id)
            try:
                for list in self.bot.interface_handler.lists.values():
                    list.remove_entry(guild_id_to_remove=guild_id)
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
                    components = None
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
                    await inter.send(
                        content=f"Successfully reset **{discord_guild.name}**'s settings",
                        ephemeral=True,
                    )
                    components = [LeaveGuildButton(), ResetGuildButton()]
            await inter.edit_original_response(
                embed=GuildEmbed(guild=discord_guild, db_guild=db_guild),
                components=components,
            )

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Get info from the bot",
        default_member_permissions=Permissions(administrator=True),
    )
    async def get_bot_info(
        self,
        inter: AppCmdInter,
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            msg=f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        embeds = BotInfoEmbeds(bot=self.bot)
        await inter.send(embeds=embeds, ephemeral=True)

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Test a feature",
        default_member_permissions=Permissions(administrator=True),
    )
    async def test_feature(
        self,
        inter: AppCmdInter,
        feature: str = commands.Param(choices=["dashboard", "planets"]),
    ):
        await inter.response.defer(ephemeral=True)
        self.bot.logger.critical(
            msg=f"{self.qualified_name} | /{inter.application_command.name} <{feature = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        error_dict = {}
        match feature:
            case "dashboard":
                for lang in Languages.all:
                    try:
                        dashboard = Dashboard(
                            data=self.bot.data,
                            language_code=lang.short_code,
                            json_dict=self.bot.json_dict,
                        )
                        compact_level = 0
                        while dashboard.character_count() > 6000 and compact_level < 2:
                            compact_level += 1
                            dashboard = Dashboard(
                                data=self.bot.data,
                                language_code=lang.short_code,
                                json_dict=self.bot.json_dict,
                                compact_level=compact_level,
                            )
                        await inter.send(
                            content=lang.full_name,
                            embeds=dashboard.embeds,
                            ephemeral=True,
                            delete_after=0.1,
                        )
                    except Exception as e:
                        error_dict[lang.short_code] = e

            case "planets":
                start_time = datetime.now()
                seconds_to_wait = len(self.bot.data.planets) * len(Languages.all) * 0.6
                await inter.send(
                    f"Testing planets, should be done <t:{int(start_time.timestamp() + seconds_to_wait)}:R>",
                    ephemeral=True,
                )
                lang_start_time = datetime.now()
                for lang in Languages.all:
                    self.bot.logger.info(
                        f"Starting {lang.full_name} after {(datetime.now() - lang_start_time).total_seconds():.2f} seconds"
                    )
                    try:
                        lang_json = self.bot.json_dict["languages"][lang.short_code]
                        for planet in self.bot.data.planets.values():
                            self.bot.logger.info(
                                f"Trying #{planet.index} {planet.name} for {lang.full_name}"
                            )
                            planet_name = [
                                planet_names
                                for planet_names in self.bot.json_dict[
                                    "planets"
                                ].values()
                                if planet_names["name"].lower() == planet.name.lower()
                            ][0]["names"][lang.long_code]
                            planet_changes = self.bot.data.liberation_changes.get_entry(
                                planet.index
                            )
                            embeds = PlanetEmbeds(
                                planet_name=planet_name,
                                planet=planet,
                                language_json=lang_json,
                                liberation_change=planet_changes,
                                region_changes=self.bot.data.region_changes,
                                total_players=self.bot.data.total_players,
                            )

                            if not embeds[0].image_set:
                                await self.bot.moderator_channel.send(
                                    f"# <@{self.bot.owner.id}> :warning:\nImage missing for biome of **planet __{planet}__** {planet.biome} {planet.biome['name'].lower().replace(' ', '_')}.png"
                                )
                            await self.bot.waste_bin_channel.send(
                                embeds=embeds,
                                components=[
                                    WikiButton(
                                        link=f"https://helldivers.wiki.gg/wiki/{planet.name.replace(' ', '_')}"
                                    ),
                                    HDCButton(
                                        link=f"https://helldiverscompanion.com/#hellpad/planets/{planet.index}"
                                    ),
                                ],
                                delete_after=0.1,
                            )
                            await sleep(0.2)
                        lang_start_time = datetime.now()
                    except Exception as e:
                        error_dict[lang.short_code] = e
                        break

        if error_dict:
            for lang, error in error_dict.items():
                await inter.channel.send(
                    f"There was an issue with `{lang}` `{feature}`\n```{error}```"
                )
                return

        await inter.channel.send("Test run without errors!")


def setup(bot: GalacticWideWebBot):
    bot.add_cog(cog=AdminCommandsCog(bot))
