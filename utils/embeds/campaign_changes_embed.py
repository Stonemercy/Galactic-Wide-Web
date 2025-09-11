from disnake import Colour, Embed
from utils.dataclasses import SpecialUnits
from utils.data import DSS, Campaign, Planet
from utils.emojis import Emojis
from utils.mixins import EmbedReprMixin


class CampaignChangesEmbed(Embed, EmbedReprMixin):
    def __init__(self, language_json: dict, planet_names_json: dict):
        self.language_json = language_json
        self.planet_names_json = planet_names_json
        super().__init__(
            title=f"{Emojis.Decoration.left_banner} {self.language_json['CampaignEmbed']['title']} {Emojis.Decoration.right_banner}",
            colour=Colour.brand_red(),
        )
        self.add_field(
            self.language_json["CampaignEmbed"]["victories"], "", inline=False
        )
        self.add_field(
            self.language_json["CampaignEmbed"]["planets_lost"], "", inline=False
        )
        self.add_field(
            self.language_json["CampaignEmbed"]["new_battles"], "", inline=False
        )
        self.add_field(
            self.language_json["dss"]["title"] + " " + Emojis.DSS.icon,
            "",
            inline=False,
        )
        self.add_field(
            self.language_json["CampaignEmbed"]["invasions"], "", inline=False
        )

    def add_new_campaign(self, campaign: Campaign, time_remaining: str | None):
        description = self.fields[2].value
        exclamation = campaign.planet.exclamations
        if campaign.planet.event and time_remaining:
            def_level_exc = {
                0: "",
                5: "!",
                20: "!!",
                33: "!!!",
                50: " :warning:",
                100: " :skull:",
                250: " :skull_crossbones:",
            }
            key = [
                key
                for key in def_level_exc.keys()
                if key <= campaign.planet.event.level
            ][-1]
            def_level_exc = def_level_exc[key]
            match campaign.planet.event.type:
                case 1:
                    description += self.language_json["CampaignEmbed"][
                        "defend_planet"
                    ].format(
                        planet=self.planet_names_json[str(campaign.planet.index)][
                            "names"
                        ][self.language_json["code_long"]],
                        faction_emoji=getattr(
                            Emojis.Factions, campaign.faction.full_name.lower()
                        ),
                        exclamation=exclamation,
                    )
                    description += self.language_json["CampaignEmbed"][
                        "invasion_level"
                    ].format(
                        level=campaign.planet.event.level, exclamation=def_level_exc
                    )
                    description += (
                        f"> *{self.language_json['ends']} {time_remaining}*\n"
                    )
                    if campaign.planet.feature:
                        description += f"> -# {self.language_json['CampaignEmbed']['feature']}: {campaign.planet.feature}\n"
            for special_unit in SpecialUnits.get_from_effects_list(
                active_effects=campaign.planet.active_effects
            ):
                description += f"> -# {self.language_json['CampaignEmbed']['special_unit']}: **{self.language_json['special_units'][special_unit[0]]}** {special_unit[1]}\n"
        else:
            description += self.language_json["CampaignEmbed"]["liberate"].format(
                planet=self.planet_names_json[str(campaign.planet.index)]["names"][
                    self.language_json["code_long"]
                ],
                faction_emoji=getattr(
                    Emojis.Factions, campaign.faction.full_name.lower()
                ),
                exclamation=exclamation,
            )
            if campaign.planet.feature:
                description += f"-# {self.language_json['CampaignEmbed']['feature']}: {campaign.planet.feature}\n"
            for special_unit in SpecialUnits.get_from_effects_list(
                active_effects=campaign.planet.active_effects
            ):
                description += f"-# {self.language_json['CampaignEmbed']['special_unit']}: **{self.language_json['special_units'][special_unit[0]]}** {special_unit[1]}\n"
        self.set_field_at(2, self.fields[2].name, description, inline=False)

    def add_campaign_victory(self, planet: Planet, taken_from: str):
        description = self.fields[0].value
        description += self.language_json["CampaignEmbed"]["been_liberated"].format(
            emoji=Emojis.Icons.victory,
            planet=self.planet_names_json[str(planet.index)]["names"][
                self.language_json["code_long"]
            ],
            faction=self.language_json["factions"][taken_from],
            faction_emoji=getattr(Emojis.Factions, taken_from.lower()),
            exclamation=planet.exclamations,
        )
        if planet.feature:
            description += f"-# {self.language_json['CampaignEmbed']['feature']}: {planet.feature}\n"
        for special_unit in SpecialUnits.get_from_effects_list(
            active_effects=planet.active_effects
        ):
            description += f"-# {self.language_json['CampaignEmbed']['special_unit']}: **{self.language_json['special_units'][special_unit[0]]}** {special_unit[1]}\n"
        self.set_field_at(0, self.fields[0].name, description, inline=False)

    def add_def_victory(self, planet: Planet, hours_left: float):
        description = self.fields[0].value
        description += self.language_json["CampaignEmbed"]["been_defended"].format(
            emoji=Emojis.Icons.victory,
            planet=self.planet_names_json[str(planet.index)]["names"][
                self.language_json["code_long"]
            ],
            exclamation=planet.exclamations,
        )
        if hours_left != 0.0:
            description += f" with **{hours_left:.0f}** hours remaining\n"
        if planet.feature:
            description += f"-# {self.language_json['CampaignEmbed']['feature']}: {planet.feature}\n"
        for special_unit in SpecialUnits.get_from_effects_list(
            active_effects=planet.active_effects
        ):
            description += f"-# {self.language_json['CampaignEmbed']['special_unit']}: **{self.language_json['special_units'][special_unit[0]]}** {special_unit[1]}\n"
        self.set_field_at(0, self.fields[0].name, description, inline=False)

    def add_planet_lost(self, planet: Planet):
        description = self.fields[1].value
        description += self.language_json["CampaignEmbed"]["been_lost"].format(
            planet=self.planet_names_json[str(planet.index)]["names"][
                self.language_json["code_long"]
            ],
            faction=self.language_json["factions"][planet.current_owner.full_name],
            faction_emoji=getattr(
                Emojis.Factions, planet.current_owner.full_name.lower()
            ),
            exclamation=planet.exclamations,
        )
        if planet.feature:
            description += f"-# {self.language_json['CampaignEmbed']['feature']}: {planet.feature}\n"
        for special_unit in SpecialUnits.get_from_effects_list(
            active_effects=planet.active_effects
        ):
            description += f"-# {self.language_json['CampaignEmbed']['special_unit']}: **{self.language_json['special_units'][special_unit[0]]}** {special_unit[1]}\n"
        self.set_field_at(1, self.fields[1].name, description, inline=False)

    def add_invasion_over(
        self, planet: Planet, faction: str, hours_left: int, win_status: bool = False
    ):
        name = self.fields[4].name
        description = self.fields[4].value
        description += self.language_json["CampaignEmbed"]["invasion_over"].format(
            planet=self.planet_names_json[str(planet.index)]["names"][
                self.language_json["code_long"]
            ],
            faction_emoji=getattr(
                Emojis.Factions, planet.current_owner.full_name.lower()
            ),
            exclamation=planet.exclamations,
        )
        if not win_status:
            description += self.language_json["CampaignEmbed"][
                "no_territory_change"
            ].format(
                faction=self.language_json["factions"][faction],
                faction_emoji=getattr(Emojis.Factions, faction.lower()),
            )
        else:
            description += self.language_json["CampaignEmbed"][
                "with_time_remaining"
            ].format(
                faction=self.language_json["factions"][faction],
                faction_emoji=getattr(Emojis.Factions, faction.lower()),
                hours=f"{hours_left:.2f}",
            )
        if planet.feature:
            description += f"-# {self.language_json['CampaignEmbed']['feature']}: {planet.feature}\n"
        for special_unit in SpecialUnits.get_from_effects_list(
            active_effects=planet.active_effects
        ):
            description += f"-# {self.language_json['CampaignEmbed']['special_unit']}: **{self.language_json['special_units'][special_unit[0]]}** {special_unit[1]}\n"
        self.set_field_at(4, name, description, inline=False)

    def remove_empty(self):
        for field in self.fields.copy():
            if field.value == "":
                self.remove_field(self.fields.index(field))

    def dss_moved(self, before_planet: Planet, after_planet: Planet):
        description = self.fields[3].value
        exclamation1 = before_planet.exclamations
        exclamation2 = after_planet.exclamations
        description += self.language_json["CampaignEmbed"]["dss"]["has_moved"].format(
            planet1=self.planet_names_json[str(before_planet.index)]["names"][
                self.language_json["code_long"]
            ],
            faction_emoji1=getattr(
                Emojis.Factions, before_planet.current_owner.full_name.lower()
            ),
            exclamation1=exclamation1,
            planet2=self.planet_names_json[str(after_planet.index)]["names"][
                self.language_json["code_long"]
            ],
            faction_emoji2=getattr(
                Emojis.Factions, after_planet.current_owner.full_name.lower()
            ),
            exclamation2=exclamation2,
        )
        if after_planet.feature:
            description += f"-# {self.language_json['CampaignEmbed']['feature']}: {after_planet.feature}\n"
        self.set_field_at(3, self.fields[3].name, description, inline=False)

    def ta_status_changed(self, tactical_action: DSS.TacticalAction):
        statuses = {0: "active", 1: "preparing", 2: "active", 3: "on_cooldown"}
        description = self.fields[3].value
        description += self.language_json["CampaignEmbed"]["dss"][
            "ta_status_change"
        ].format(
            emoji=getattr(Emojis.DSS, tactical_action.name.replace(" ", "_").lower()),
            ta_name=self.language_json["dashboard"]["DSSEmbed"]["tactical_actions"][
                tactical_action.name
            ]["name"],
            status=self.language_json["dashboard"]["DSSEmbed"][
                statuses.get(tactical_action.status, "active")
            ],
        )
        self.set_field_at(3, self.fields[3].name, description, inline=False)
