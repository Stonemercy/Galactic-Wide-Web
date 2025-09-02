from data.lists import (
    custom_colours,
    emotes_list,
    player_cards_list,
    stratagem_permit_list,
    titles_list,
    victory_poses_list,
)
from disnake import Colour, Embed, File, ButtonStyle, SelectOption
from disnake.ui import Button, StringSelect, ActionRow
from utils.data import DSS
from utils.dataclasses import Factions, WarbondImages
from utils.emojis import Emojis
from utils.functions import health_bar
from utils.mixins import EmbedReprMixin, ReprMixin


class Wiki:
    class Buttons:
        class WikiGGButton(Button, ReprMixin):
            def __init__(
                self,
                language_json: dict,
                link: str = "https://helldivers.wiki.gg/wiki/Helldivers_Wiki",
            ):
                super().__init__(
                    style=ButtonStyle.link,
                    label=language_json["label"],
                    url=link,
                    emoji=Emojis.Icons.wiki,
                )

        class HDCButton(Button):
            def __init__(self, link: str = "https://helldiverscompanion.com/"):
                super().__init__(
                    style=ButtonStyle.link,
                    label="Helldivers Companion",
                    url=link,
                    emoji=Emojis.Icons.hdc,
                )

        class MainMenuButton(Button, ReprMixin):
            def __init__(self, language_json: dict, disabled: bool = False):
                super().__init__(
                    label=language_json["label"],
                    disabled=disabled,
                    custom_id="MainMenuButton",
                    emoji=Emojis.Wiki.main_menu,
                    style=ButtonStyle.primary,
                )

        class DSSButton(Button, ReprMixin):
            def __init__(self, language_json: dict, disabled: bool = False):
                super().__init__(
                    label=language_json["label"],
                    disabled=disabled,
                    custom_id="DSSButton",
                    emoji=Emojis.DSS.icon,
                    style=ButtonStyle.blurple,
                )

        class EnemiesHomeButton(Button, ReprMixin):
            def __init__(self, language_json: dict, disabled: bool = False):
                super().__init__(
                    label=language_json["label"],
                    disabled=disabled,
                    custom_id="EnemiesHomeButton",
                    style=ButtonStyle.danger,
                    emoji=Emojis.Wiki.enemies,
                )

        class WarbondButton(Button, ReprMixin):
            def __init__(self, language_json: dict, disabled: bool = False):
                super().__init__(
                    label=language_json["label"],
                    disabled=disabled,
                    custom_id="WarbondButton",
                    style=ButtonStyle.primary,
                    emoji=Emojis.Wiki.warbond,
                )

        class WarbondPreviousPageButton(Button, ReprMixin):
            def __init__(
                self, language_json: dict, warbond_name: str, disabled: bool = False
            ):
                super().__init__(
                    label=language_json["label"],
                    disabled=disabled,
                    custom_id=f"{warbond_name}_prev_page",
                    emoji=Emojis.Stratagems.left,
                    style=ButtonStyle.success,
                )

        class WarbondNextPageButton(Button, ReprMixin):
            def __init__(
                self, language_json: dict, warbond_name: str, disabled: bool = False
            ):
                super().__init__(
                    label=language_json["label"],
                    disabled=disabled,
                    custom_id=f"{warbond_name}_next_page",
                    emoji=Emojis.Stratagems.right,
                    style=ButtonStyle.success,
                )

        class AutomatonButton(Button, ReprMixin):
            def __init__(self, label_text: str, disabled: bool = False):
                super().__init__(
                    label=label_text,
                    disabled=disabled,
                    custom_id="AutomatonButton",
                    emoji=Emojis.Factions.automaton,
                )

        class IlluminateButton(Button, ReprMixin):
            def __init__(self, label_text: str, disabled: bool = False):
                super().__init__(
                    label=label_text,
                    disabled=disabled,
                    custom_id="IlluminateButton",
                    emoji=Emojis.Factions.illuminate,
                )

        class TerminidsButton(Button, ReprMixin):
            def __init__(self, label_text: str, disabled: bool = False):
                super().__init__(
                    label=label_text,
                    disabled=disabled,
                    custom_id="TerminidsButton",
                    emoji=Emojis.Factions.terminids,
                )

        class EquipmentHomeButton(Button, ReprMixin):
            def __init__(self, language_json: dict, disabled: bool = False):
                super().__init__(
                    label=language_json["label"],
                    disabled=disabled,
                    custom_id="EquipmentHomeButton",
                    emoji=Emojis.Wiki.equipment,
                )

        class WeaponsHomeButton(Button, ReprMixin):
            def __init__(self, language_json: dict):
                super().__init__(
                    label=language_json["label"],
                    custom_id="WeaponsHomeButton",
                    emoji=Emojis.Wiki.weapons,
                )

        class PrimaryWeaponsButton(Button, ReprMixin):
            def __init__(self, language_json: dict):
                super().__init__(
                    label=language_json["label"],
                    custom_id="PrimaryWeaponsButton",
                    emoji=Emojis.Wiki.primary,
                )

        class SecondaryWeaponsButton(Button, ReprMixin):
            def __init__(self, language_json: dict):
                super().__init__(
                    label=language_json["label"],
                    custom_id="SecondaryWeaponsButton",
                    emoji=Emojis.Wiki.secondary,
                )

        class GrenadesButton(Button, ReprMixin):
            def __init__(self, language_json: dict):
                super().__init__(
                    label=language_json["label"],
                    custom_id="GrenadesButton",
                    emoji=Emojis.Wiki.grenade,
                )

        class BoostersButton(Button, ReprMixin):
            def __init__(self, language_json: dict):
                super().__init__(
                    label=language_json["label"],
                    custom_id="BoostersButton",
                    emoji=Emojis.Wiki.booster,
                )

        class StratagemsButton(Button, ReprMixin):
            def __init__(self, language_json: dict):
                super().__init__(
                    label=language_json["label"],
                    custom_id="StratagemsButton",
                    emoji=Emojis.Wiki.stratagem,
                )

        def main_menu_action_rows(language_json: dict) -> list[ActionRow, ActionRow]:
            return [
                ActionRow(
                    Wiki.Buttons.MainMenuButton(
                        language_json=language_json["wiki"]["buttons"][
                            "MainMenuButton"
                        ],
                        disabled=True,
                    )
                ),
                ActionRow(
                    Wiki.Buttons.DSSButton(
                        language_json=language_json["wiki"]["buttons"]["DSSButton"]
                    ),
                    Wiki.Buttons.EnemiesHomeButton(
                        language_json=language_json["wiki"]["buttons"][
                            "EnemiesHomeButton"
                        ]
                    ),
                    Wiki.Buttons.WarbondButton(
                        language_json=language_json["wiki"]["buttons"]["WarbondButton"]
                    ),
                    Wiki.Buttons.EquipmentHomeButton(
                        language_json=language_json["wiki"]["buttons"][
                            "EquipmentHomeButton"
                        ]
                    ),
                ),
            ]

        def dss_action_rows(language_json: dict) -> list[ActionRow, ActionRow]:
            return [
                ActionRow(
                    Wiki.Buttons.MainMenuButton(
                        language_json=language_json["wiki"]["buttons"]["MainMenuButton"]
                    )
                ),
                ActionRow(
                    Wiki.Buttons.WikiGGButton(
                        language_json=language_json["wiki"]["buttons"]["WikiGGButton"],
                        link=f"https://helldivers.wiki.gg/wiki/Democracy_Space_Station",
                    ),
                    Wiki.Buttons.HDCButton(
                        link="https://helldiverscompanion.com/#hellpad/stations"
                    ),
                ),
            ]

        def enemy_home_rows(language_json: dict) -> list[ActionRow, ActionRow]:
            return [
                ActionRow(
                    Wiki.Buttons.MainMenuButton(
                        language_json=language_json["wiki"]["buttons"]["MainMenuButton"]
                    )
                ),
                ActionRow(
                    Wiki.Buttons.AutomatonButton(
                        label_text=language_json["factions"]["Automaton"]
                    ),
                    Wiki.Buttons.IlluminateButton(
                        label_text=language_json["factions"]["Illuminate"]
                    ),
                    Wiki.Buttons.TerminidsButton(
                        label_text=language_json["factions"]["Terminids"]
                    ),
                ),
            ]

        def enemy_page_rows(
            language_json: dict, faction_json: dict, species: str
        ) -> list[ActionRow, ActionRow]:
            return [
                ActionRow(
                    Wiki.Buttons.MainMenuButton(
                        language_json=language_json["wiki"]["buttons"]["MainMenuButton"]
                    ),
                    Wiki.Buttons.EnemiesHomeButton(
                        language_json=language_json["wiki"]["buttons"][
                            "EnemiesHomeButton"
                        ]
                    ),
                    Wiki.Buttons.WikiGGButton(
                        language_json=language_json["wiki"]["buttons"]["WikiGGButton"],
                        link=f"https://helldivers.wiki.gg/wiki/{species.replace(' ', '_')}",
                    ),
                ),
                ActionRow(Wiki.Dropdowns.EnemyDropdown(faction_json=faction_json)),
            ]

        def warbond_page_rows(
            language_json: dict,
            warbond_name: str,
            clean_warbond_names: list[str],
            first_page: bool = False,
            last_page: bool = False,
        ) -> list[ActionRow]:
            return [
                ActionRow(
                    Wiki.Buttons.MainMenuButton(
                        language_json=language_json["wiki"]["buttons"]["MainMenuButton"]
                    ),
                    Wiki.Buttons.WikiGGButton(
                        language_json=language_json["wiki"]["buttons"]["WikiGGButton"],
                        link="https://helldivers.wiki.gg/wiki/Warbonds",
                    ),
                ),
                ActionRow(
                    Wiki.Buttons.WarbondPreviousPageButton(
                        language_json=language_json["wiki"]["buttons"][
                            "WarbondPreviousPageButton"
                        ],
                        warbond_name=warbond_name,
                        disabled=first_page,
                    ),
                    Wiki.Buttons.WarbondNextPageButton(
                        language_json=language_json["wiki"]["buttons"][
                            "WarbondNextPageButton"
                        ],
                        warbond_name=warbond_name,
                        disabled=last_page,
                    ),
                ),
                ActionRow(
                    Wiki.Dropdowns.WarbondDropdown(warbond_names=clean_warbond_names)
                ),
            ]

        def equipment_home_rows(language_json: dict) -> list[ActionRow]:
            return [
                ActionRow(
                    Wiki.Buttons.MainMenuButton(
                        language_json=language_json["wiki"]["buttons"]["MainMenuButton"]
                    )
                ),
                ActionRow(
                    Wiki.Buttons.WeaponsHomeButton(
                        language_json=language_json["wiki"]["buttons"][
                            "WeaponsHomeButton"
                        ]
                    ),
                    Wiki.Buttons.BoostersButton(
                        language_json=language_json["wiki"]["buttons"]["BoostersButton"]
                    ),
                    Wiki.Buttons.StratagemsButton(
                        language_json=language_json["wiki"]["buttons"][
                            "StratagemsButton"
                        ]
                    ),
                ),
            ]

        def weapons_home_rows(language_json: dict) -> list[ActionRow]:
            return [
                ActionRow(
                    Wiki.Buttons.MainMenuButton(
                        language_json=language_json["wiki"]["buttons"]["MainMenuButton"]
                    ),
                    Wiki.Buttons.EquipmentHomeButton(
                        language_json=language_json["wiki"]["buttons"][
                            "EquipmentHomeButton"
                        ]
                    ),
                ),
                ActionRow(
                    Wiki.Buttons.PrimaryWeaponsButton(
                        language_json=language_json["wiki"]["buttons"][
                            "PrimaryWeaponsButton"
                        ]
                    ),
                    Wiki.Buttons.SecondaryWeaponsButton(
                        language_json=language_json["wiki"]["buttons"][
                            "SecondaryWeaponsButton"
                        ]
                    ),
                    Wiki.Buttons.GrenadesButton(
                        language_json=language_json["wiki"]["buttons"]["GrenadesButton"]
                    ),
                ),
            ]

        def primary_weapon_rows(
            language_json: dict, weapon_names: list[str], main_weapon_name: str
        ) -> list[ActionRow]:
            weapon_name_batches = [
                weapon_names[i : i + 25] for i in range(0, len(weapon_names), 25)
            ]
            weapon_dropdowns = [
                ActionRow(
                    Wiki.Dropdowns.PrimaryWeaponsDropdown(
                        weapon_names=weapon_names_batch, num=index
                    )
                )
                for index, weapon_names_batch in enumerate(weapon_name_batches, start=1)
            ]
            return [
                ActionRow(
                    Wiki.Buttons.MainMenuButton(
                        language_json=language_json["wiki"]["buttons"]["MainMenuButton"]
                    ),
                    Wiki.Buttons.EquipmentHomeButton(
                        language_json=language_json["wiki"]["buttons"][
                            "EquipmentHomeButton"
                        ]
                    ),
                    Wiki.Buttons.WeaponsHomeButton(
                        language_json=language_json["wiki"]["buttons"][
                            "WeaponsHomeButton"
                        ]
                    ),
                    Wiki.Buttons.WikiGGButton(
                        language_json=language_json["wiki"]["buttons"]["WikiGGButton"],
                        link=f"https://helldivers.wiki.gg/wiki/{main_weapon_name.replace(' ', '_')}",
                    ),
                ),
            ] + weapon_dropdowns

        def secondary_weapon_rows(
            language_json: dict, weapon_names: list[str], main_weapon_name: str
        ) -> list[ActionRow]:
            weapon_name_batches = [
                weapon_names[i : i + 25] for i in range(0, len(weapon_names), 25)
            ]
            weapon_dropdowns = [
                ActionRow(
                    Wiki.Dropdowns.SecondaryWeaponsDropdown(
                        weapon_names=weapon_names_batch, num=index
                    )
                )
                for index, weapon_names_batch in enumerate(weapon_name_batches, start=1)
            ]
            return [
                ActionRow(
                    Wiki.Buttons.MainMenuButton(
                        language_json=language_json["wiki"]["buttons"]["MainMenuButton"]
                    ),
                    Wiki.Buttons.EquipmentHomeButton(
                        language_json=language_json["wiki"]["buttons"][
                            "EquipmentHomeButton"
                        ]
                    ),
                    Wiki.Buttons.WeaponsHomeButton(
                        language_json=language_json["wiki"]["buttons"][
                            "WeaponsHomeButton"
                        ]
                    ),
                    Wiki.Buttons.WikiGGButton(
                        language_json=language_json["wiki"]["buttons"]["WikiGGButton"],
                        link=f"https://helldivers.wiki.gg/wiki/{main_weapon_name.replace(' ', '_')}",
                    ),
                ),
            ] + weapon_dropdowns

        def grenades_rows(
            language_json: dict, weapon_names: list[str], main_grenade_name: str
        ) -> list[ActionRow]:
            grenade_names_batches = [
                weapon_names[i : i + 25] for i in range(0, len(weapon_names), 25)
            ]
            weapon_dropdowns = [
                ActionRow(
                    Wiki.Dropdowns.GrenadesDropdown(
                        grenade_names=grenade_names_batch, num=index
                    )
                )
                for index, grenade_names_batch in enumerate(
                    grenade_names_batches, start=1
                )
            ]
            return [
                ActionRow(
                    Wiki.Buttons.MainMenuButton(
                        language_json=language_json["wiki"]["buttons"]["MainMenuButton"]
                    ),
                    Wiki.Buttons.EquipmentHomeButton(
                        language_json=language_json["wiki"]["buttons"][
                            "EquipmentHomeButton"
                        ]
                    ),
                    Wiki.Buttons.WeaponsHomeButton(
                        language_json=language_json["wiki"]["buttons"][
                            "WeaponsHomeButton"
                        ]
                    ),
                    Wiki.Buttons.WikiGGButton(
                        language_json=language_json["wiki"]["buttons"]["WikiGGButton"],
                        link=f"https://helldivers.wiki.gg/wiki/{main_grenade_name.replace(' ', '_')}",
                    ),
                ),
            ] + weapon_dropdowns

        def boosters_rows(
            language_json: dict, booster_names: list[str]
        ) -> list[ActionRow]:
            return [
                ActionRow(
                    Wiki.Buttons.MainMenuButton(
                        language_json=language_json["wiki"]["buttons"]["MainMenuButton"]
                    ),
                    Wiki.Buttons.EquipmentHomeButton(
                        language_json=language_json["wiki"]["buttons"][
                            "EquipmentHomeButton"
                        ]
                    ),
                ),
                ActionRow(Wiki.Dropdowns.BoostersDropdown(booster_names=booster_names)),
            ]

        def stratagems_rows(
            language_json: dict, stratagem_names: list[str]
        ) -> list[ActionRow]:
            stratagem_name_batches = [
                stratagem_names[i : i + 25] for i in range(0, len(stratagem_names), 25)
            ]
            stratagem_dropdowns = [
                ActionRow(
                    Wiki.Dropdowns.StratagemsDropdown(
                        stratagem_names=stratagem_name_batch, num=index
                    )
                )
                for index, stratagem_name_batch in enumerate(
                    stratagem_name_batches, start=1
                )
            ]
            return [
                ActionRow(
                    Wiki.Buttons.MainMenuButton(
                        language_json=language_json["wiki"]["buttons"]["MainMenuButton"]
                    ),
                    Wiki.Buttons.EquipmentHomeButton(
                        language_json=language_json["wiki"]["buttons"][
                            "EquipmentHomeButton"
                        ]
                    ),
                ),
            ] + stratagem_dropdowns

    class Embeds:
        class WikiHomeEmbed(Embed, EmbedReprMixin):
            def __init__(self, language_json: dict):
                super().__init__(
                    title=language_json["title"],
                    colour=Colour.from_rgb(*custom_colours["MO"]),
                )
                self.add_field(
                    Emojis.DSS.icon + language_json["dss_name"],
                    language_json["dss_value"],
                    inline=False,
                )
                self.add_field(
                    Emojis.Wiki.enemies + language_json["enemies_name"],
                    language_json["enemies_value"],
                    inline=False,
                )
                self.add_field(
                    Emojis.Wiki.warbond + language_json["warbonds_name"],
                    language_json["warbonds_value"],
                    inline=False,
                )
                self.add_field(
                    Emojis.Wiki.equipment + language_json["equipment_name"],
                    language_json["equipment_value"],
                    inline=False,
                )

        class DSSEmbed(Embed, EmbedReprMixin):
            def __init__(self, language_json: dict, dss_data: DSS):
                super().__init__(
                    title=language_json["title"],
                    colour=Colour.from_rgb(r=38, g=156, b=182),
                )
                if dss_data.flags == 2:
                    self.add_field("The DSS is currently unavailable.", "")
                    self.colour = Colour.brand_red()
                    return
                self.description = language_json["stationed_at"].format(
                    planet=dss_data.planet.name,
                    faction_emoji=getattr(
                        Emojis.Factions, dss_data.planet.current_owner.full_name.lower()
                    ),
                )
                self.description += language_json["next_move"].format(
                    timestamp=f"<t:{int(dss_data.move_timer_datetime.timestamp())}:R>"
                )
                self.set_thumbnail(
                    "https://cdn.discordapp.com/attachments/1212735927223590974/1312446626975187065/DSS.png?ex=674c86ab&is=674b352b&hm=3184fde3e8eece703b0e996501de23c89dc085999ebff1a77009fbee2b09ccad&"
                ).set_image(
                    "https://cdn.discordapp.com/attachments/1212735927223590974/1312448218398986331/dss.jpg?ex=674c8827&is=674b36a7&hm=def01cbdf1920b85617b1028a95ec982484c70a5cf9bed14b9072319fd018246&"
                )
                for tactical_action in dss_data.tactical_actions:
                    tactical_action: DSS.TacticalAction
                    status = {
                        0: "inactive",
                        1: "preparing",
                        2: "active",
                        3: "on_cooldown",
                    }[tactical_action.status]
                    if status == "preparing":
                        cost = ""
                        for ta_cost in tactical_action.cost:
                            submittable_formatted = language_json[
                                "max_submitable"
                            ].format(
                                emoji=getattr(
                                    Emojis.Items,
                                    ta_cost.item.replace(" ", "_").lower(),
                                ),
                                number=f"{ta_cost.max_per_seconds[0]:,}",
                                item=ta_cost.item,
                                hours=f"{ta_cost.max_per_seconds[1]/3600:.0f}",
                            )
                            ta_cost_health_bar = health_bar(
                                ta_cost.progress,
                                "MO" if ta_cost.progress != 1 else "Humans",
                            )
                            cost = (
                                f"{submittable_formatted}\n"
                                f"{ta_cost_health_bar}\n"
                                f"`{ta_cost.progress:^25.2%}`"
                            )
                    elif status == "active":
                        cost = f"{language_json['ends']} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
                    elif status == "on_cooldown":
                        cost = f"{language_json['off_cooldown'].capitalize()} <t:{int(tactical_action.status_end_datetime.timestamp())}:R>"
                    else:
                        continue
                    ta_long_description = tactical_action.strategic_description.replace(
                        ". ", ".\n-# "
                    )
                    self.add_field(
                        f"{getattr(Emojis.DSS, tactical_action.name.replace(' ', '_').lower())} {tactical_action.name.title()}",
                        (
                            f"{language_json['status']}: **{language_json[status].capitalize()}**\n"
                            f"-# {ta_long_description}\n"
                            f"{cost}\n\u200b\n"
                        ),
                        inline=False,
                    )

        class EnemyHomeEmbed(Embed):
            def __init__(self, language_json: dict):
                super().__init__(
                    title=language_json["title"],
                    colour=Colour.light_gray(),
                )

        class EnemyPageEmbed(Embed, EmbedReprMixin):
            def __init__(
                self,
                language_json: dict,
                species_info: dict,
                faction: str,
                variation: bool,
            ):
                super().__init__(
                    colour=Colour.from_rgb(
                        *Factions.get_from_identifier(name=faction).colour
                    ),
                    title=species_info["name"],
                    description=species_info["info"]["desc"],
                )
                file_name = species_info["name"].replace(" ", "_")
                start_emoji = getattr(
                    Emojis.Difficulty, f"difficulty{species_info['info']['start']}"
                )
                self.add_field(
                    language_json["introduced"],
                    f"{language_json['difficulty']} {species_info['info']['start']} {start_emoji}",
                    inline=False,
                ).add_field(
                    language_json["tactics"],
                    species_info["info"]["tactics"],
                    inline=False,
                ).add_field(
                    language_json["weak_spots"],
                    species_info["info"]["weak spots"],
                    inline=False,
                )
                variations = ""
                if not variation and species_info["info"]["variations"] != None:
                    for i in species_info["info"]["variations"]:
                        variations += f"\n- {i}"
                    self.add_field(language_json["variations"], variations)
                try:
                    self.set_thumbnail(
                        file=File(
                            f"resources/enemies/{faction.lower()}/{file_name}.png"
                        )
                    )
                    self.image_set = True
                except Exception as e:
                    self.image_set = False
                    self.error = e

        class WarbondEmbed(Embed, EmbedReprMixin):
            def __init__(
                self,
                language_json: dict,
                warbond_info: tuple,
                json_dict: dict,
                page: int,
            ):
                warbond_name: str = warbond_info[0]
                clean_warbond_name: str = warbond_info[1]
                warbond_data: dict = warbond_info[2]
                warbond_page = warbond_data[str(page)]
                formatted_index = {
                    warbond["id"]: warbond
                    for warbond in json_dict["warbonds"]["index"].values()
                }
                cost = formatted_index[warbond_name]["credits_to_unlock"]
                super().__init__(
                    colour=Colour.blue(),
                    title=clean_warbond_name,
                    description=(
                        f"{language_json['page']} {page}/{list(warbond_data.keys())[-1]}\n"
                        f"{language_json['cost_to_unlock']}: **{cost}** {Emojis.Items.super_credits}\n"
                        f"{language_json['medals_to_unlock']}: **{warbond_page['medals_to_unlock'] }** {Emojis.Items.medal}\n"
                    ),
                )
                self.set_image(url=WarbondImages.get(name=clean_warbond_name))
                item_number = 1
                for item in warbond_page["items"]:
                    if armor := json_dict["items"]["armor"].get(
                        str(item["item_id"]), None
                    ):
                        self.add_field(
                            f"{armor['name']}",
                            (
                                f"{language_json['type']}: **{language_json['armor']}**\n"
                                f"{language_json['slot']}: **{armor['slot']}** {getattr(Emojis.Armour, armor['slot'].lower())}\n"
                                f"{language_json['armor_rating']}: **{armor['armor_rating']}**\n"
                                f"{language_json['speed']}: **{armor['speed']}**\n"
                                f"{language_json['stamina_regen']}: **{armor['stamina_regen']}**\n"
                                f"{language_json['passive']}: **{armor['passive']['name']}**\n"
                                f"{language_json['medal_cost']}: **{item['medal_cost']} {Emojis.Items.medal}**\n\n"
                            ),
                        )
                    elif primary := json_dict["items"]["primary_weapons"].get(
                        str(item["item_id"]), None
                    ):
                        self.add_field(
                            f"{primary['name']}",
                            (
                                f"{language_json['type']}: **{language_json['primary']}**\n"
                                f"{language_json['weapon_type']}: **{primary['type']}**\n"
                                f"{language_json['damage']}: **{primary['damage']}**\n"
                                f"{language_json['capacity']}: **{primary['capacity']}**\n"
                                f"{language_json['recoil']}: **{primary['recoil']}**\n"
                                f"{language_json['fire_rate']}: **{primary['fire_rates']}**\n"
                                f"{language_json['medal_cost']}: **{item['medal_cost']} {Emojis.Items.medal}**\n\n"
                            ),
                        )
                    elif secondary := json_dict["items"]["secondary_weapons"].get(
                        str(item["item_id"]), None
                    ):
                        self.add_field(
                            f"{secondary['name']}",
                            (
                                f"{language_json['type']}: **{language_json['secondary']}**\n"
                                f"{language_json['damage']}: **{secondary['damage']}**\n"
                                f"{language_json['capacity']}: **{secondary['capacity']}**\n"
                                f"{language_json['recoil']}: **{secondary['recoil']}**\n"
                                f"{language_json['fire_rate']}: **{secondary['fire_rate']}**\n"
                                f"{language_json['medal_cost']}: **{item['medal_cost']} {Emojis.Items.medal}**\n\n"
                            ),
                        )
                    elif grenade := json_dict["items"]["grenades"].get(
                        str(item["item_id"]), None
                    ):
                        self.add_field(
                            f"{grenade['name']}",
                            (
                                f"{language_json['type']}: **{language_json['grenade']}**\n"
                                f"{language_json['damage']}: **{grenade['damage']}**\n"
                                f"{language_json['penetration']}: **{grenade['penetration']}**\n"
                                f"{language_json['radius']}: **{grenade['outer_radius']}**\n"
                                f"{language_json['fuse_time']}: **{grenade['fuse_time']}**\n"
                                f"{language_json['medal_cost']}: **{item['medal_cost']} {Emojis.Items.medal}**\n\n"
                            ),
                        )
                    elif (
                        "Super Credits"
                        in json_dict["items"]["item_names"][str(item["item_id"])][
                            "name"
                        ]
                    ):
                        self.add_field(
                            f"{json_dict['items']['item_names'][str(item['item_id'])]['name']} {Emojis.Items.super_credits}",
                            f"{language_json['medal_cost']}: **{item['medal_cost']} {Emojis.Items.medal}**",
                        )
                    elif (
                        json_dict["items"]["item_names"][str(item["item_id"])]["name"]
                        in emotes_list
                    ):
                        self.add_field(
                            f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                            (
                                f"{language_json['type']}: {language_json['emote']}\n"
                                f"{language_json['medal_cost']}: **{item['medal_cost']} {Emojis.Items.medal}**"
                            ),
                        )
                    elif (
                        json_dict["items"]["item_names"][str(item["item_id"])]["name"]
                        in victory_poses_list
                    ):
                        self.add_field(
                            f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                            (
                                f"{language_json['type']}: {language_json['victory_pose']}\n"
                                f"{language_json['medal_cost']}: **{item['medal_cost']} {Emojis.Items.medal}**"
                            ),
                        )
                    elif (
                        json_dict["items"]["item_names"][str(item["item_id"])]["name"]
                        in player_cards_list
                    ):
                        self.add_field(
                            f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                            (
                                f"{language_json['type']}: {language_json['player_card']}\n"
                                f"{language_json['medal_cost']}: **{item['medal_cost']} {Emojis.Items.medal}**"
                            ),
                        )
                    elif str(item["item_id"]) in json_dict["items"]["boosters"]:
                        self.add_field(
                            f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                            (
                                f"{language_json['type']}: {language_json['booster']}\n"
                                f"{language_json['medal_cost']}: **{item['medal_cost']} {Emojis.Items.medal}**"
                            ),
                        )
                    elif (
                        json_dict["items"]["item_names"][str(item["item_id"])]["name"]
                        in titles_list
                    ):
                        self.add_field(
                            f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                            (
                                f"{language_json['type']}: {language_json['title']}\n"
                                f"{language_json['medal_cost']}: **{item['medal_cost']} {Emojis.Items.medal}**"
                            ),
                        )
                    elif (
                        json_dict["items"]["item_names"][str(item["item_id"])]["name"]
                        in stratagem_permit_list
                    ):
                        self.add_field(
                            f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                            (
                                f"{language_json['type']}: {language_json['stratagem_permit']}\n"
                                f"{language_json['medal_cost']}: **{item['medal_cost']} {Emojis.Items.medal}**"
                            ),
                        )
                    else:
                        self.add_field(
                            f"{json_dict['items']['item_names'][str(item['item_id'])]['name']}",
                            f"{language_json['medal_cost']}: **{item['medal_cost']} {Emojis.Items.medal}**",
                        )
                    if item_number % 2 == 0:
                        self.add_field("", "")
                    item_number += 1

        class EquipmentHomeEmbed(Embed, EmbedReprMixin):
            def __init__(self, language_json: dict):
                super().__init__(
                    title=language_json["title"],
                    colour=Colour.dark_gray(),
                )
                self.add_field(
                    language_json["weapons_name"],
                    language_json["weapons_value"],
                    inline=False,
                )
                self.add_field(
                    language_json["boosters_name"],
                    language_json["boosters_value"],
                    inline=False,
                )
                self.add_field(
                    language_json["stratagems_name"],
                    language_json["stratagems_value"],
                    inline=False,
                )

        class WeaponsHomeEmbed(Embed, EmbedReprMixin):
            def __init__(self, language_json: dict):
                super().__init__(
                    title=language_json["title"],
                    colour=Colour.light_gray(),
                )
                self.add_field(
                    name=language_json["primary_weapons_name"],
                    value=language_json["primary_weapons_value"],
                    inline=False,
                )
                self.add_field(
                    name=language_json["secondary_weapons_name"],
                    value=language_json["secondary_weapons_value"],
                    inline=False,
                )
                self.add_field(
                    name=language_json["grenades_name"],
                    value=language_json["grenades_value"],
                    inline=False,
                )

        class PrimaryWeaponsEmbed(Embed, EmbedReprMixin):
            def __init__(
                self,
                language_json: dict,
                weapon_info: tuple[str, dict],
            ):
                weapon_name, weapon_json = weapon_info
                super().__init__(
                    colour=Colour.blue(),
                    title=weapon_name,
                    description=weapon_json["description"],
                )
                gun_fire_modes = ""
                for i in weapon_json["fire_modes"]:
                    gun_fire_modes += f"\n- **{i}**"

                features = ""
                for i in weapon_json["traits"]:
                    if i != 0:
                        features += f"\n- **{i}**"
                    else:
                        features = "\n- None"
                if 9 in weapon_json["traits"]:
                    weapon_json["capacity"] = language_json["constant_fire"].format(
                        number=weapon_json["capacity"]
                    )
                if weapon_json["capacity"] == 999:
                    weapon_json["capacity"] = "**∞**"
                information = ""
                information += language_json["type"].format(type=weapon_json["type"])
                information += language_json["damage"].format(
                    damage=weapon_json["damage"]
                )
                information += language_json["fire_rate"].format(
                    fire_rate=weapon_json["fire_rates"]
                )
                information += language_json["dps"].format(
                    dps=f'{((weapon_json["damage"] * weapon_json["fire_rates"][-1]) / 60):.2f}'
                )
                information += language_json["capacity"].format(
                    capacity=weapon_json["capacity"],
                )
                information += language_json["fire_modes"].format(
                    fire_modes=gun_fire_modes
                )
                information += language_json["features"].format(features=features)
                self.add_field(
                    language_json["information_title"],
                    information,
                )
                try:
                    self.set_thumbnail(
                        file=File(
                            f"resources/weapons/{weapon_json['name'].replace(' ', '-').replace('&', 'n')}.png"
                        )
                    )
                    self.image_set = True
                except:
                    self.image_set = False

        class SecondaryWeaponsEmbed(Embed, EmbedReprMixin):
            def __init__(
                self,
                language_json: dict,
                weapon_info: tuple[str, dict],
            ):
                weapon_name, weapon_json = weapon_info
                super().__init__(
                    colour=Colour.blue(),
                    title=weapon_name,
                    description=weapon_json["description"],
                )
                gun_fire_modes = ""
                for i in weapon_json["fire_modes"]:
                    gun_fire_modes += f"\n- **{i}**"

                features = ""
                for i in weapon_json["traits"]:
                    if i != 0:
                        features += f"\n- **{i}**"
                    else:
                        features = "\n- None"

                if 9 in weapon_json["traits"]:
                    weapon_json["capacity"] = language_json["constant_fire"].format(
                        number=weapon_json["capacity"]
                    )
                if weapon_json["capacity"] == 999:
                    weapon_json["capacity"] = "**∞**"
                information = ""
                information += language_json["damage"].format(
                    damage=weapon_json["damage"]
                )
                information += language_json["fire_rate"].format(
                    fire_rate=weapon_json["fire_rates"]
                )
                information += language_json["dps"].format(
                    dps=f'{((weapon_json["damage"] * weapon_json["fire_rates"][-1]) / 60):.2f}'
                )
                information += language_json["capacity"].format(
                    capacity=weapon_json["capacity"],
                )
                information += language_json["fire_modes"].format(
                    fire_modes=gun_fire_modes
                )
                information += language_json["features"].format(features=features)
                self.add_field(
                    language_json["information_title"],
                    information,
                )
                try:
                    self.set_thumbnail(
                        file=File(
                            f"resources/weapons/{weapon_json['name'].replace(' ', '-').replace('/', '-')}.png"
                        )
                    )
                    self.image_set = True
                except:
                    self.image_set = False

        class GrenadesEmbed(Embed, EmbedReprMixin):
            def __init__(
                self,
                language_json: dict,
                grenade_info: tuple[str, dict],
            ):
                grenade_name, grenade_json = grenade_info
                super().__init__(
                    colour=Colour.blue(),
                    title=grenade_name,
                    description=grenade_json["description"],
                )
                information = ""
                information += language_json["damage"].format(
                    damage=grenade_json["damage"]
                )
                information += language_json["fuse_time"].format(
                    fuse_time=grenade_json["fuse_time"]
                )
                information += language_json["penetration"].format(
                    penetration=grenade_json["penetration"]
                )
                information += language_json["radius"].format(
                    radius=grenade_json["outer_radius"]
                )

                self.add_field(
                    language_json["information_title"],
                    information,
                )
                try:
                    self.set_thumbnail(
                        file=File(
                            f"resources/weapons/{grenade_json['name'].replace(' ', '-')}.png"
                        )
                    )
                    self.image_set = True
                except:
                    self.image_set = False

        class BoostersEmbed(Embed, EmbedReprMixin):
            def __init__(self, booster_info: tuple[str, dict]):
                booster_name, booster_json = booster_info
                super().__init__(
                    colour=Colour.blue(),
                    title=booster_name,
                    description=booster_json["description"],
                )
                try:
                    self.set_thumbnail(
                        file=File(
                            f"resources/boosters/{booster_name.replace(' ', '_')}.png"
                        )
                    )
                    self.image_set = True
                except:
                    self.image_set = False

        class StratagemsEmbed(Embed, EmbedReprMixin):
            def __init__(
                self,
                language_json: dict,
                stratagem_info: tuple[str, dict],
            ):
                stratagem_name, stratagem_json = stratagem_info
                super().__init__(title=stratagem_name, colour=Colour.brand_green())
                key_inputs = ""
                for key in stratagem_json["keys"]:
                    key_inputs += getattr(Emojis.Stratagems, key)
                self.add_field(
                    language_json["key_input"],
                    key_inputs,
                    inline=False,
                )
                self.add_field(
                    language_json["uses"],
                    stratagem_json["uses"],
                    inline=False,
                )
                self.add_field(
                    language_json["cooldown"],
                    f"{stratagem_json['cooldown']} seconds ({(stratagem_json['cooldown']/60):.2f} minutes)",
                )
                try:
                    self.set_thumbnail(
                        file=File(
                            f"resources/stratagems/{stratagem_name.replace('/', '_').replace(' ', '_')}.png"
                        )
                    )
                    self.image_set = True
                except:
                    self.image_set = False

    class Dropdowns:
        class EnemyDropdown(StringSelect, ReprMixin):
            def __init__(self, faction_json: dict):
                super().__init__(
                    custom_id="EnemyDropdown",
                    options=[SelectOption(label=enemy) for enemy in faction_json.keys()]
                    + [
                        SelectOption(label=variant_name)
                        for json in faction_json.values()
                        if json["variations"] != None
                        for variant_name in json["variations"].keys()
                    ],
                )

        class WarbondDropdown(StringSelect, ReprMixin):
            def __init__(self, warbond_names: list[str]):
                super().__init__(
                    custom_id="WarbondDropdown",
                    options=[SelectOption(label=warbond) for warbond in warbond_names],
                )

        class PrimaryWeaponsDropdown(StringSelect, ReprMixin):
            def __init__(self, weapon_names: list[str], num: int):
                super().__init__(
                    custom_id=f"PrimaryWeaponsDropdown{num}",
                    options=[SelectOption(label=warbond) for warbond in weapon_names],
                )

        class SecondaryWeaponsDropdown(StringSelect, ReprMixin):
            def __init__(self, weapon_names: list[str], num: int):
                super().__init__(
                    custom_id=f"SecondaryWeaponsDropdown{num}",
                    options=[SelectOption(label=warbond) for warbond in weapon_names],
                )

        class GrenadesDropdown(StringSelect, ReprMixin):
            def __init__(self, grenade_names: list[str], num: int):
                super().__init__(
                    custom_id=f"GrenadesDropdown{num}",
                    options=[SelectOption(label=warbond) for warbond in grenade_names],
                )

        class BoostersDropdown(StringSelect, ReprMixin):
            def __init__(self, booster_names: list[str]):
                super().__init__(
                    custom_id=f"BoostersDropdown",
                    options=[SelectOption(label=warbond) for warbond in booster_names],
                )

        class StratagemsDropdown(StringSelect, ReprMixin):
            def __init__(self, stratagem_names: list[str], num: int):
                super().__init__(
                    custom_id=f"StratagemsDropdown{num}",
                    options=[
                        SelectOption(label=warbond) for warbond in stratagem_names
                    ],
                )
