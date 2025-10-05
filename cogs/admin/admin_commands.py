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
from utils.containers import (
    CampaignChangesContainer,
    DSSChangesContainer,
    RegionChangesContainer,
    GuildContainer,
    PlanetContainers,
)
from utils.dataclasses import (
    Languages,
    CampaignChangesJson,
    DSSChangesJson,
    RegionChangesJson,
    SpecialUnits,
)
from utils.dbv2 import GWWGuild, GWWGuilds
from utils.embeds import BotInfoEmbeds, Dashboard
from utils.interactables import ConfirmButton


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
            f"{self.qualified_name} | /{inter.application_command.name} <{feature = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        match feature:
            case "Dashboard":
                await self.bot.get_cog(name="DashboardCog").dashboard_poster()
            case "Map":
                await self.bot.get_cog(name="MapCog").map_poster()
            case "MO Update":
                await self.bot.get_cog(name="MajorOrderCog").major_order_updates()
        await inter.send(content="Completed", ephemeral=True)

    def extension_names_autocomp(inter: AppCmdInter, user_input: str):
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
            f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
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
            f"{self.qualified_name} | /{inter.application_command.name} <{id_to_check = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
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
            container = GuildContainer(guild=guild, db_guild=db_guild, fetching=True)
            await inter.send(components=container, ephemeral=True)
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
            f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
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
            f"{self.qualified_name} | /{inter.application_command.name} <{feature = }> | used by <@{inter.author.id}> | @{inter.author.global_name}"
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
                seconds_to_wait = len(self.bot.data.planets) * len(Languages.all)
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
                            containers = PlanetContainers(
                                planet=planet,
                                containers_json=lang_json["containers"][
                                    "PlanetContainers"
                                ],
                                faction_json=lang_json["factions"],
                                gambit_planets=self.bot.data.gambit_planets,
                            )

                            await self.bot.waste_bin_channel.send(
                                components=containers,
                                delete_after=0.1,
                            )
                            await sleep(0.2)
                        lang_start_time = datetime.now()
                    except Exception as e:
                        error_dict[lang.short_code] = f"{planet.name} - {e}"
                        break

        if error_dict:
            for lang, error in error_dict.items():
                await inter.channel.send(
                    f"There was an issue with `{lang}` `{feature}`\n```{error}```"
                )
                return

        await inter.channel.send("Test run without errors!")

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Test v2 components",
        default_member_permissions=Permissions(administrator=True),
    )
    async def test_v2(
        self,
        inter: AppCmdInter,
        feature: str = commands.Param(
            choices=["campaign_changes", "region_changes", "dss_changes"]
        ),
        public: str = commands.Param(choices=["Yes", "No"], default="No"),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild_id, "en", [])
        else:
            guild = GWWGuild.default()
        guild_language = self.bot.json_dict["languages"][guild.language]
        match feature:
            case "campaign_changes":
                campaign_changes_container = CampaignChangesContainer(
                    json=CampaignChangesJson(
                        lang_code_long=guild_language["code_long"],
                        container=guild_language["containers"][
                            "CampaignChangesContainer"
                        ],
                        special_units=guild_language["special_units"],
                        factions=guild_language["factions"],
                    )
                )

                # test cases
                campaigns_to_skip = []

                # new liberation campaign
                if lib_camp_list := [
                    c for c in self.bot.data.campaigns if not c.planet.event
                ]:
                    lib_camp = sorted(
                        lib_camp_list,
                        key=lambda x: x.planet.stats.player_count,
                        reverse=True,
                    )[0]
                    campaigns_to_skip.append(lib_camp)
                    print("lib camp is", lib_camp.planet.name)
                    campaign_changes_container.add_new_campaign(
                        campaign=lib_camp, gambit_planets=self.bot.data.gambit_planets
                    )

                # new defence campaign
                if def_camp_list := [
                    c
                    for c in self.bot.data.campaigns
                    if c.planet.event
                    if c not in campaigns_to_skip
                ]:
                    def_camp = sorted(
                        def_camp_list,
                        key=lambda x: x.planet.stats.player_count,
                        reverse=True,
                    )[0]
                    campaigns_to_skip.append(def_camp)
                    print("def camp is", def_camp.planet.name)
                    campaign_changes_container.add_new_campaign(
                        campaign=def_camp, gambit_planets=self.bot.data.gambit_planets
                    )

                # gambit campaign
                if self.bot.data.gambit_planets:
                    if gambit_tuple := self.bot.data.gambit_planets.popitem():
                        defence_campaign = sorted(
                            [
                                c
                                for c in self.bot.data.campaigns
                                if c.planet.index == gambit_tuple[0]
                            ],
                            key=lambda x: x.planet.stats.player_count,
                            reverse=True,
                        )[0]
                        print("gambit def camp is", defence_campaign.planet.name)
                    campaign_changes_container.add_new_campaign(
                        campaign=defence_campaign,
                        gambit_planets=self.bot.data.gambit_planets,
                    )

                # regions
                if region_campaigns_list := [
                    c
                    for c in self.bot.data.campaigns
                    if c.planet.regions and c not in campaigns_to_skip
                ]:
                    region_campaign = sorted(
                        region_campaigns_list,
                        key=lambda x: x.planet.stats.player_count,
                        reverse=True,
                    )[0]
                    campaigns_to_skip.append(region_campaign)
                    print("region campaign is", region_campaign.planet.name)
                    campaign_changes_container.add_new_campaign(
                        campaign=region_campaign,
                        gambit_planets=self.bot.data.gambit_planets,
                    )

                # special units
                if special_units_campaign_list := [
                    c
                    for c in self.bot.data.campaigns
                    if SpecialUnits.get_from_effects_list(c.planet.active_effects)
                    and c not in campaigns_to_skip
                ]:
                    special_units_campaign = sorted(
                        special_units_campaign_list,
                        key=lambda x: x.planet.stats.player_count,
                        reverse=True,
                    )[0]
                    campaigns_to_skip.append(special_units_campaign)
                    print(
                        "special units campaign is",
                        special_units_campaign.planet.name,
                    )
                    campaign_changes_container.add_new_campaign(
                        campaign=special_units_campaign,
                        gambit_planets=self.bot.data.gambit_planets,
                    )

                # poi's
                if poi_campaign_list := [
                    c
                    for c in self.bot.data.campaigns
                    if 71 in [ae.id for ae in c.planet.active_effects]
                ]:
                    poi_campaign = sorted(
                        poi_campaign_list,
                        key=lambda x: x.planet.stats.player_count,
                        reverse=True,
                    )[0]
                    print(
                        "poi campaign is",
                        poi_campaign.planet.name,
                    )
                    campaign_changes_container.add_new_campaign(
                        campaign=poi_campaign,
                        gambit_planets=self.bot.data.gambit_planets,
                    )

                # lib victory
                if lib_victory_planet_list := [
                    p
                    for p in self.bot.data.planets.values()
                    if p.faction.full_name == "Humans"
                ]:
                    victory_planet = sorted(
                        lib_victory_planet_list,
                        key=lambda x: x.stats.player_count,
                        reverse=True,
                    )[0]
                    print("lib victory lib planet is", victory_planet.name)
                    campaign_changes_container.add_liberation_victory(
                        planet=victory_planet,
                        taken_from=choice(["Terminids", "Automaton", "Illuminate"]),
                    )

                # def victory
                if def_victory_planet_list := [
                    p
                    for p in self.bot.data.planets.values()
                    if p.faction.full_name == "Humans"
                ]:
                    victory_planet = sorted(
                        def_victory_planet_list,
                        key=lambda x: len(x.active_effects) + len(x.regions),
                        reverse=True,
                    )[0]
                    print("def victory planet is", victory_planet.name)
                    campaign_changes_container.add_defence_victory(
                        planet=victory_planet,
                        defended_against=choice(
                            ["Terminids", "Automaton", "Illuminate"]
                        ),
                        hours_remaining=choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
                    )

                # def loss
                if unowned_planets_list := [
                    p
                    for p in self.bot.data.planets.values()
                    if p.faction.full_name != "Humans"
                ]:
                    unowned_planet = sorted(
                        unowned_planets_list,
                        key=lambda x: len(x.active_effects) + len(x.regions),
                        reverse=True,
                    )[0]
                    print("loss planet is", unowned_planet.name)
                    campaign_changes_container.add_planet_lost(
                        planet=unowned_planet,
                    )

                await inter.send(
                    components=campaign_changes_container,
                    ephemeral=public != "Yes",
                )
                return
            case "region_changes":
                region_changes_container = RegionChangesContainer(
                    container_json=RegionChangesJson(
                        lang_code_long=self.bot.json_dict["languages"][guild.language][
                            "code_long"
                        ],
                        container=self.bot.json_dict["languages"][guild.language][
                            "containers"
                        ]["RegionChangesContainer"],
                        special_units=self.bot.json_dict["languages"][guild.language][
                            "special_units"
                        ],
                        factions=self.bot.json_dict["languages"][guild.language][
                            "factions"
                        ],
                    )
                )

                # test cases

                # new region
                if region_list := [
                    p for p in self.bot.data.planets.values() if p.regions
                ]:
                    region_planet = sorted(
                        region_list,
                        key=lambda x: x.stats.player_count,
                        reverse=True,
                    )[0]
                    region = sorted(
                        region_planet.regions.values(),
                        key=lambda x: x.players,
                        reverse=True,
                    )[0]
                    print("new region is", region.name)
                    region_changes_container.add_new_region(
                        planet=region_planet, region=region
                    )

                # region won
                if region_list := [
                    p for p in self.bot.data.planets.values() if p.regions
                ]:
                    region_planet = sorted(
                        region_list,
                        key=lambda x: x.stats.player_count,
                        reverse=True,
                    )[0]
                    region = sorted(
                        region_planet.regions.values(),
                        key=lambda x: x.players,
                        reverse=True,
                    )[0]
                    print("region won is", region.name)
                    region_changes_container.add_region_victory(
                        planet=region_planet, region=region
                    )

                await inter.send(components=region_changes_container)
            case "dss_changes":
                dss_changes_container = DSSChangesContainer(
                    json=DSSChangesJson(
                        lang_code_long=guild_language["code_long"],
                        container=guild_language["containers"]["DSSChangesContainer"],
                        special_units=guild_language["special_units"],
                    )
                )

                # test cases
                # dss moved
                dss_changes_container.dss_moved(
                    before_planet=self.bot.data.dss.planet,
                    after_planet=sorted(
                        [p for p in self.bot.data.planets.values()],
                        key=lambda x: x.stats.player_count,
                        reverse=True,
                    )[0],
                )

                # ta changes
                for ta in self.bot.data.dss.tactical_actions:
                    dss_changes_container.ta_status_changed(tactical_action=ta)

                await inter.send(components=dss_changes_container)

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Test v2 components",
        default_member_permissions=Permissions(administrator=True),
    )
    async def get_fake_guilds(
        self,
        inter: AppCmdInter,
        public: str = commands.Param(choices=["Yes", "No"], default="No"),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.critical(
            f"{self.qualified_name} | /{inter.application_command.name} | used by <@{inter.author.id}> | @{inter.author.global_name}"
        )
        gww_guiilds = GWWGuilds(fetch_all=True)
        possible_fake_guilds = []
        for gww_guild in gww_guiilds:
            if gww_guild.features == []:
                discord_guild = self.bot.get_guild(
                    gww_guild.guild_id
                ) or await self.bot.fetch_guild(gww_guild.guild_id)
                if (
                    len(discord_guild.channels) == 3
                    and discord_guild.member_count < 100
                ):
                    possible_fake_guilds.append(discord_guild)
        await inter.send(f"Possible fake guilds: {len(possible_fake_guilds)}")


def setup(bot: GalacticWideWebBot):
    bot.add_cog(cog=AdminCommandsCog(bot))
