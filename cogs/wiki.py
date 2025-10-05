from random import choice
from re import findall
from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    InteractionContextTypes,
    InteractionTimedOut,
    MessageInteraction,
    NotFound,
)
from disnake.ext import commands
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.dbv2 import GWWGuild, GWWGuilds
from utils.wiki import Wiki


class WikiCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(
        description="Browse the GWW's wiki",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns information the following subjects:\n - DSS\n - Enemies\n - Warbonds\n - Equipment",
            "example_usage": "**`/wiki`** would return a menu you can click through.",
        },
    )
    async def wiki(
        self,
        inter: AppCmdInter,
    ):
        try:
            await inter.response.defer(ephemeral=True)
        except (NotFound, InteractionTimedOut):
            await inter.channel.send(
                "There was an error with that command, please try again.",
                delete_after=5,
            )
            return
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name}"
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
        embed = Wiki.Embeds.WikiHomeEmbed(
            language_json=guild_language["wiki"]["embeds"]["WikiHomeEmbed"]
        )
        components = Wiki.Buttons.main_menu_action_rows(language_json=guild_language)
        await inter.send(embed=embed, components=components, ephemeral=True)

    @commands.Cog.listener("on_button_click")
    async def on_button_clicks(self, inter: MessageInteraction):
        allowed_ids = {
            "MainMenuButton",
            "DSSButton",
            "EnemiesHomeButton",
            "AutomatonButton",
            "IlluminateButton",
            "TerminidsButton",
            "WarbondButton",
            "_prev_page",
            "_next_page",
            "EquipmentHomeButton",
            "WeaponsHomeButton",
            "PrimaryWeaponsButton",
            "SecondaryWeaponsButton",
            "GrenadesButton",
            "BoostersButton",
            "StratagemsButton",
        }
        comp_id = inter.component.custom_id
        if comp_id not in allowed_ids and comp_id[-10:] not in allowed_ids:
            return
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
        if comp_id == "MainMenuButton":
            embed = Wiki.Embeds.WikiHomeEmbed(
                language_json=guild_language["wiki"]["embeds"]["WikiHomeEmbed"]
            )
            components = Wiki.Buttons.main_menu_action_rows(
                language_json=guild_language
            )
            await inter.response.edit_message(
                embed=embed, components=components, attachments=None
            )
            return
        elif comp_id == "DSSButton":
            embed = Wiki.Embeds.DSSEmbed(
                dss_data=self.bot.data.dss,
                language_json=guild_language,
            )
            components = Wiki.Buttons.dss_action_rows(language_json=guild_language)
            await inter.response.edit_message(embed=embed, components=components)
            return
        elif comp_id == "EnemiesHomeButton":
            embed = Wiki.Embeds.EnemyHomeEmbed(
                language_json=guild_language["wiki"]["embeds"]["EnemyHomeEmbed"]
            )
            components = Wiki.Buttons.enemy_home_rows(language_json=guild_language)
            await inter.response.edit_message(
                embed=embed, components=components, attachments=None
            )
            return
        elif comp_id == "AutomatonButton":
            embed = Wiki.Embeds.EnemyPageEmbed(
                language_json=guild_language["wiki"]["embeds"]["EnemyPageEmbed"],
                species_info={
                    "name": "Trooper",
                    "info": self.bot.json_dict["enemies"]["automaton"]["Trooper"],
                },
                faction="Automaton",
                variation=False,
            )
            components = Wiki.Buttons.enemy_page_rows(
                language_json=guild_language,
                faction_json=self.bot.json_dict["enemies"]["automaton"],
                species="Trooper",
            )
            await inter.response.edit_message(embed=embed, components=components)
            return
        elif comp_id == "IlluminateButton":
            embed = Wiki.Embeds.EnemyPageEmbed(
                language_json=guild_language["wiki"]["embeds"]["EnemyPageEmbed"],
                species_info={
                    "name": "Voteless",
                    "info": self.bot.json_dict["enemies"]["illuminate"]["Voteless"],
                },
                faction="Illuminate",
                variation=False,
            )
            components = Wiki.Buttons.enemy_page_rows(
                language_json=guild_language,
                faction_json=self.bot.json_dict["enemies"]["illuminate"],
                species="Voteless",
            )
            await inter.response.edit_message(embed=embed, components=components)
            return
        elif comp_id == "TerminidsButton":
            embed = Wiki.Embeds.EnemyPageEmbed(
                language_json=guild_language["wiki"]["embeds"]["EnemyPageEmbed"],
                species_info={
                    "name": "Scavenger",
                    "info": self.bot.json_dict["enemies"]["terminids"]["Scavenger"],
                },
                faction="Terminids",
                variation=False,
            )
            components = Wiki.Buttons.enemy_page_rows(
                language_json=guild_language,
                faction_json=self.bot.json_dict["enemies"]["terminids"],
                species="Scavenger",
            )
            await inter.response.edit_message(embed=embed, components=components)
            return
        elif comp_id == "WarbondButton":
            latest_warbond_info = next(
                reversed(self.bot.json_dict["warbonds"]["index"].values())
            )
            warbond_info = (
                latest_warbond_info["id"],
                latest_warbond_info["name"],
                self.bot.json_dict["warbonds"][latest_warbond_info["id"]],
            )
            embed = Wiki.Embeds.WarbondEmbed(
                language_json=guild_language["wiki"]["embeds"]["WarbondEmbed"],
                warbond_info=warbond_info,
                json_dict=self.bot.json_dict,
                page=1,
            )
            components = Wiki.Buttons.warbond_page_rows(
                language_json=guild_language,
                warbond_name=latest_warbond_info["id"],
                clean_warbond_names=[
                    warbond["name"]
                    for warbond in self.bot.json_dict["warbonds"]["index"].values()
                ],
                first_page=True,
            )
            await inter.response.edit_message(embed=embed, components=components)
            return
        elif comp_id[:-10] in self.bot.json_dict["warbonds"]:
            warbond_name = comp_id[:-10]
            clean_warbond_name = [
                warbond_info["name"]
                for warbond_info in self.bot.json_dict["warbonds"]["index"].values()
                if warbond_info["id"] == warbond_name
            ][0]
            warbond_info = (
                warbond_name,
                clean_warbond_name,
                self.bot.json_dict["warbonds"][comp_id[:-10]],
            )
            page_count = [int(i) for i in warbond_info[2]]
            current_page = int(findall(r"\d+", inter.message.embeds[0].description)[0])
            new_page = (
                current_page + 1
                if comp_id == f"{warbond_name}_next_page"
                else current_page - 1
            )
            components = Wiki.Buttons.warbond_page_rows(
                language_json=guild_language,
                warbond_name=warbond_name,
                clean_warbond_names=[
                    warbond["name"]
                    for warbond in self.bot.json_dict["warbonds"]["index"].values()
                ],
                first_page=new_page == page_count[0],
                last_page=new_page == page_count[-1],
            )
            embed = Wiki.Embeds.WarbondEmbed(
                language_json=guild_language["wiki"]["embeds"]["WarbondEmbed"],
                warbond_info=warbond_info,
                json_dict=self.bot.json_dict,
                page=new_page,
            )
            await inter.response.edit_message(
                embed=embed,
                components=components,
            )
            return
        elif comp_id == "EquipmentHomeButton":
            embed = Wiki.Embeds.EquipmentHomeEmbed(
                language_json=guild_language["wiki"]["embeds"]["EquipmentHomeEmbed"]
            )
            components = Wiki.Buttons.equipment_home_rows(language_json=guild_language)
            await inter.response.edit_message(
                embed=embed, components=components, attachments=None
            )
            return
        elif comp_id == "WeaponsHomeButton":
            embed = Wiki.Embeds.WeaponsHomeEmbed(
                language_json=guild_language["wiki"]["embeds"]["WeaponsHomeEmbed"]
            )
            components = Wiki.Buttons.weapons_home_rows(language_json=guild_language)
            await inter.response.edit_message(
                embed=embed, components=components, attachments=None
            )
            return
        elif comp_id == "PrimaryWeaponsButton":
            primaries = {
                item["name"]: item
                for item in self.bot.json_dict["items"]["primary_weapons"].values()
            }
            first_weapon: tuple[str, dict] = list(primaries.items())[0]
            embed = Wiki.Embeds.PrimaryWeaponsEmbed(
                language_json=guild_language["wiki"]["embeds"]["PrimaryWeaponsEmbed"],
                weapon_info=first_weapon,
            )
            if not embed.image_set:
                await self.bot.channels.moderator_channel.send(
                    f"# <@{self.bot.owner.id}> :warning:\nImage missing for **weapon primary __{first_weapon[0]}__** {first_weapon[0].replace(' ', '-').replace('&', 'n')}.png"
                )
            components = Wiki.Buttons.primary_weapon_rows(
                language_json=guild_language,
                weapon_names=sorted([name for name in primaries.keys()]),
                main_weapon_name=first_weapon[0],
            )
            await inter.response.edit_message(embed=embed, components=components)
            return
        elif comp_id == "SecondaryWeaponsButton":
            secondaries = {
                item["name"]: item
                for item in self.bot.json_dict["items"]["secondary_weapons"].values()
            }
            first_weapon: tuple[str, dict] = list(secondaries.items())[0]
            embed = Wiki.Embeds.SecondaryWeaponsEmbed(
                language_json=guild_language["wiki"]["embeds"]["SecondaryWeaponsEmbed"],
                weapon_info=first_weapon,
            )
            if not embed.image_set:
                await self.bot.channels.moderator_channel.send(
                    f"# <@{self.bot.owner.id}> :warning:\nImage missing for **weapon secondary __{first_weapon[0]}__** {first_weapon[0].replace(' ', '-').replace('/', '-')}.png"
                )
            components = Wiki.Buttons.secondary_weapon_rows(
                language_json=guild_language,
                weapon_names=sorted([name for name in secondaries.keys()]),
                main_weapon_name=first_weapon[0],
            )
            await inter.response.edit_message(embed=embed, components=components)
            return
        elif comp_id == "GrenadesButton":
            grenades = {
                item["name"]: item
                for item in self.bot.json_dict["items"]["grenades"].values()
            }
            first_grenade: tuple[str, dict] = list(grenades.items())[0]
            embed = Wiki.Embeds.GrenadesEmbed(
                language_json=guild_language["wiki"]["embeds"]["GrenadesEmbed"],
                grenade_info=first_grenade,
            )
            if not embed.image_set:
                await self.bot.channels.moderator_channel.send(
                    f"# <@{self.bot.owner.id}> :warning:\nImage missing for **weapon grenades __{first_grenade[0]}__** {first_grenade[0].replace(' ', '-')}.png"
                )
            components = Wiki.Buttons.grenades_rows(
                language_json=guild_language,
                weapon_names=sorted([name for name in grenades.keys()]),
                main_grenade_name=first_grenade[0],
            )
            await inter.response.edit_message(embed=embed, components=components)
            return
        elif comp_id == "BoostersButton":
            boosters = {
                item["name"]: item
                for item in self.bot.json_dict["items"]["boosters"].values()
            }
            first_booster: tuple[str, dict] = list(boosters.items())[0]
            embed = Wiki.Embeds.BoostersEmbed(booster_info=first_booster)
            if not embed.image_set:
                await self.bot.channels.moderator_channel.send(
                    f" <@{self.bot.owner.id}> :warning:\nImage missing for **booster __{first_booster[0]}__** {first_booster[0].replace(' ', '_')}.png"
                )
            components = Wiki.Buttons.boosters_rows(
                language_json=guild_language,
                booster_names=sorted([name for name in boosters.keys()]),
            )
            await inter.response.edit_message(embed=embed, components=components)
            return
        elif comp_id == "StratagemsButton":
            stratagem_info = choice(
                [
                    (s_name, s_item_dict)
                    for s_dict in self.bot.json_dict["stratagems"].values()
                    for s_name, s_item_dict in s_dict.items()
                ]
            )
            embed = Wiki.Embeds.StratagemsEmbed(
                language_json=guild_language["wiki"]["embeds"]["StratagemsEmbed"],
                stratagem_info=stratagem_info,
            )
            if not embed.image_set:
                strat_name = (
                    stratagem_info[0]
                    .replace("/", "_")
                    .replace(" ", "_")
                    .replace('"', "")
                )
                await self.bot.channels.moderator_channel.send(
                    f"# <@{self.bot.owner.id}> :warning:\nImage missing for **stratagem `{stratagem_info[0]}     -     {strat_name}.png`**"
                )
            components = Wiki.Buttons.stratagems_rows(
                language_json=guild_language,
                stratagem_names=sorted(
                    [
                        s_name
                        for s_dict in self.bot.json_dict["stratagems"].values()
                        for s_name in s_dict
                    ]
                ),
            )
            await inter.response.edit_message(embed=embed, components=components)
            return

    @commands.Cog.listener("on_dropdown")
    async def on_dropdowns(self, inter: MessageInteraction):
        allowed_ids = {
            "EnemyDropdown",
            "WarbondDropdown",
            "PrimaryWeaponsDropdown",
            "SecondaryWeaponsDropdown",
            "GrenadesDropdown",
            "BoostersDropdown",
            "StratagemsDropdown",
        }
        comp_id = inter.component.custom_id
        if comp_id not in allowed_ids and comp_id[:-1] not in allowed_ids:
            return
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
        if comp_id == "EnemyDropdown":
            enemy_name = inter.values[0]
            factions = {
                "Automaton": self.bot.json_dict["enemies"]["automaton"],
                "Illuminate": self.bot.json_dict["enemies"]["illuminate"],
                "Terminids": self.bot.json_dict["enemies"]["terminids"],
            }
            enemy_json = None
            for faction, faction_json in factions.items():
                base_enemies = set(faction_json.keys())
                variant_enemies = {
                    variant_name: base_enemy_name
                    for base_enemy_name, enemy_json in faction_json.items()
                    if enemy_json["variations"]
                    for variant_name in enemy_json["variations"]
                }
                if enemy_name in base_enemies:
                    enemy_json = faction_json.get(enemy_name, {})
                    variant = False
                elif enemy_name in variant_enemies:
                    enemy_json = faction_json.get(variant_enemies[enemy_name])[
                        "variations"
                    ][enemy_name]
                    variant = True
                if enemy_json:
                    embed = Wiki.Embeds.EnemyPageEmbed(
                        language_json=guild_language["wiki"]["embeds"][
                            "EnemyPageEmbed"
                        ],
                        species_info={"name": enemy_name, "info": enemy_json},
                        faction=faction,
                        variation=variant,
                    )
                    break
            components = Wiki.Buttons.enemy_page_rows(
                language_json=guild_language,
                faction_json=faction_json,
                species=enemy_name,
            )
            attachments = inter.message.attachments
            if not embed.image_set:
                attachments = None
            await inter.response.edit_message(
                embed=embed, components=components, attachments=attachments
            )
            return
        elif comp_id == "WarbondDropdown":
            clean_warbond_name = inter.values[0]
            warbond_name = clean_warbond_name.replace(" ", "_").replace("'", "").lower()
            warbond_info = (
                warbond_name,
                clean_warbond_name,
                self.bot.json_dict["warbonds"][warbond_name],
            )
            components = Wiki.Buttons.warbond_page_rows(
                language_json=guild_language,
                warbond_name=warbond_name,
                clean_warbond_names=[
                    warbond["name"]
                    for warbond in self.bot.json_dict["warbonds"]["index"].values()
                ],
                first_page=True,
            )
            embed = Wiki.Embeds.WarbondEmbed(
                language_json=guild_language["wiki"]["embeds"]["WarbondEmbed"],
                warbond_info=warbond_info,
                json_dict=self.bot.json_dict,
                page=1,
            )
            await inter.response.edit_message(
                embed=embed,
                components=components,
            )
            return
        elif comp_id[:-1] == "PrimaryWeaponsDropdown":
            primary_names = sorted(
                [
                    item["name"]
                    for item in self.bot.json_dict["items"]["primary_weapons"].values()
                ]
            )
            weapon_name = inter.values[0]
            weapon_json = [
                primary
                for primary in self.bot.json_dict["items"]["primary_weapons"].values()
                if primary["name"] == weapon_name
            ][0]
            weapon_info = (weapon_name, weapon_json)
            embed = Wiki.Embeds.PrimaryWeaponsEmbed(
                language_json=guild_language["wiki"]["embeds"]["PrimaryWeaponsEmbed"],
                weapon_info=weapon_info,
            )
            if not embed.image_set:
                await self.bot.channels.moderator_channel.send(
                    f"# <@{self.bot.owner.id}> :warning:\nImage missing for **weapon primary __{weapon_info[0]}__** {weapon_info[0].replace(' ', '-').replace('&', 'n')}.png"
                )
            components = Wiki.Buttons.primary_weapon_rows(
                language_json=guild_language,
                weapon_names=sorted(primary_names),
                main_weapon_name=weapon_name,
            )
            await inter.response.edit_message(
                embed=embed, components=components, attachments=None
            )
            return
        elif comp_id[:-1] == "SecondaryWeaponsDropdown":
            secondary_names = sorted(
                [
                    item["name"]
                    for item in self.bot.json_dict["items"][
                        "secondary_weapons"
                    ].values()
                ]
            )
            weapon_name = inter.values[0]
            weapon_json = [
                secondary
                for secondary in self.bot.json_dict["items"][
                    "secondary_weapons"
                ].values()
                if secondary["name"] == weapon_name
            ][0]
            weapon_info = (weapon_name, weapon_json)
            embed = Wiki.Embeds.SecondaryWeaponsEmbed(
                language_json=guild_language["wiki"]["embeds"]["SecondaryWeaponsEmbed"],
                weapon_info=weapon_info,
            )
            if not embed.image_set:
                await self.bot.channels.moderator_channel.send(
                    f"# <@{self.bot.owner.id}> :warning:\nImage missing for **weapon secondary __{weapon_info[0]}__** {weapon_info[0].replace(' ', '-').replace('/', '-')}.png"
                )
            components = Wiki.Buttons.secondary_weapon_rows(
                language_json=guild_language,
                weapon_names=sorted(secondary_names),
                main_weapon_name=weapon_name,
            )
            await inter.response.edit_message(
                embed=embed, components=components, attachments=None
            )
            return
        elif comp_id[:-1] == "GrenadesDropdown":
            grenade_names = sorted(
                [
                    item["name"]
                    for item in self.bot.json_dict["items"]["grenades"].values()
                ]
            )
            grenade_name = inter.values[0]
            grenade_json = [
                grenade
                for grenade in self.bot.json_dict["items"]["grenades"].values()
                if grenade["name"] == grenade_name
            ][0]
            grenade_info = (grenade_name, grenade_json)
            embed = Wiki.Embeds.GrenadesEmbed(
                language_json=guild_language["wiki"]["embeds"]["GrenadesEmbed"],
                grenade_info=grenade_info,
            )
            if not embed.image_set:
                await self.bot.channels.moderator_channel.send(
                    f" <@{self.bot.owner.id}> :warning:\nImage missing for **weapon grenade __{grenade_name}__** {grenade_name.replace(' ', '-')}.png"
                )
            components = Wiki.Buttons.grenades_rows(
                language_json=guild_language,
                weapon_names=sorted(grenade_names),
                main_grenade_name=grenade_name,
            )
            await inter.response.edit_message(
                embed=embed, components=components, attachments=None
            )
            return
        elif comp_id == "BoostersDropdown":
            booster_name = inter.values[0]
            booster_json = [
                booster
                for booster in self.bot.json_dict["items"]["boosters"].values()
                if booster["name"] == booster_name
            ][0]
            booster_info = (booster_name, booster_json)
            embed = Wiki.Embeds.BoostersEmbed(booster_info=booster_info)
            if not embed.image_set:
                await self.bot.channels.moderator_channel.send(
                    f" <@{self.bot.owner.id}> :warning:\nImage missing for **booster __{booster_info[0]}__** {booster_info[0].replace(' ', '_')}.png"
                )
            components = Wiki.Buttons.boosters_rows(
                language_json=guild_language,
                booster_names=sorted(
                    [
                        v["name"]
                        for v in self.bot.json_dict["items"]["boosters"].values()
                    ]
                ),
            )
            await inter.response.edit_message(
                embed=embed, components=components, attachments=None
            )
            return
        elif comp_id[:-1] == "StratagemsDropdown":
            stratagem_name = inter.values[0]
            stratagem_info = [
                (s_name, s_item_dict)
                for s_dict in self.bot.json_dict["stratagems"].values()
                for s_name, s_item_dict in s_dict.items()
                if s_name == stratagem_name
            ][0]
            embed = Wiki.Embeds.StratagemsEmbed(
                language_json=guild_language["wiki"]["embeds"]["StratagemsEmbed"],
                stratagem_info=stratagem_info,
            )
            if not embed.image_set:
                strat_name = (
                    stratagem_info[0]
                    .replace("/", "_")
                    .replace(" ", "_")
                    .replace('"', "")
                )
                await self.bot.channels.moderator_channel.send(
                    f"# <@{self.bot.owner.id}> :warning:\nImage missing for **stratagem `{stratagem_info[0]}     -     {strat_name}.png`**"
                )
            components = Wiki.Buttons.stratagems_rows(
                language_json=guild_language,
                stratagem_names=sorted(
                    [
                        s_name
                        for s_dict in self.bot.json_dict["stratagems"].values()
                        for s_name in s_dict
                    ]
                ),
            )
            await inter.response.edit_message(
                embed=embed, components=components, attachments=None
            )
            return


def setup(bot: GalacticWideWebBot):
    bot.add_cog(cog=WikiCog(bot))
