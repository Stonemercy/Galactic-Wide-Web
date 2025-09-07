from disnake import Colour, Embed
from utils.data import Planet
from utils.dataclasses import SpecialUnits
from utils.emojis import Emojis
from utils.mixins import EmbedReprMixin


class RegionChangesEmbed(Embed, EmbedReprMixin):
    def __init__(self, language_json: dict, planet_names_json: dict):
        self.language_json = language_json
        self.planet_names_json = planet_names_json
        super().__init__(
            title=f"{Emojis.Decoration.left_banner} {language_json['RegionLoopEmbed']['title']} {Emojis.Decoration.right_banner}",
            colour=Colour.brand_red(),
        )
        self.add_field(
            language_json["RegionLoopEmbed"]["region_victories"], "", inline=False
        )
        self.add_field(
            language_json["RegionLoopEmbed"]["regions_lost"], "", inline=False
        )
        self.add_field(
            language_json["RegionLoopEmbed"]["new_regions"], "", inline=False
        )

    def add_region_victory(
        self,
        planet: Planet,
        region: Planet.Region,
        taken_from: str,
    ):
        description = self.fields[0].value
        description += self.language_json["RegionLoopEmbed"]["region_victory"].format(
            emoji=Emojis.Icons.victory,
            region_name=region.name,
            planet_name=self.planet_names_json[str(planet.index)]["names"][
                self.language_json["code_long"]
            ],
            faction=self.language_json["factions"][taken_from],
            faction_emoji=getattr(Emojis.Factions, taken_from.lower()),
            exclamations=planet.exclamations,
        )
        if planet.feature:
            description += f"\n-# {self.language_json['RegionLoopEmbed']['feature']}: {planet.feature}"
        for special_unit in SpecialUnits.get_from_effects_list(
            active_effects=planet.active_effects
        ):
            description += f"\n-# {self.language_json['RegionLoopEmbed']['special_unit']}: **{self.language_json['special_units'][special_unit[0]]}** {special_unit[1]}"
        self.set_field_at(0, self.fields[0].name, description, inline=False)

    def add_region_lost(self, planet: Planet, region: Planet.Region, taken_by: str):
        description = self.fields[0].value
        desctiption += self.language_json["RegionLoopEmbed"]["region_lost"].format(
            region_name=region.name,
            planet_name=self.planet_names_json[str(planet.index)]["names"][
                self.language_json["code_long"]
            ],
            faction=self.language_json["factions"][taken_by],
            faction_emoji=getattr(Emojis.Factions, taken_by.lower()),
            exclamations=planet.exclamations,
        )
        if planet.feature:
            description += f"\n-# {self.language_json['RegionLoopEmbed']['feature']}: {planet.feature}"
        for special_unit in SpecialUnits.get_from_effects_list(
            active_effects=planet.active_effects
        ):
            description += f"\n-# {self.language_json['RegionLoopEmbed']['special_unit']}: **{self.language_json['special_units'][special_unit[0]]}** {special_unit[1]}"
        self.set_field_at(0, self.fields[0].name, description, inline=False)

    def add_new_region_appeared(self, planet: Planet, region: Planet.Region):
        description = self.fields[2].value
        description += self.language_json["RegionLoopEmbed"]["new_region"].format(
            faction_emoji=getattr(Emojis.Factions, region.owner.full_name.lower()),
            planet_name=self.planet_names_json[str(planet.index)]["names"][
                self.language_json["code_long"]
            ],
            region_type=region.type,
            exclamations=planet.exclamations,
            region_name=region.name,
            region_emoji=getattr(
                getattr(Emojis.RegionIcons, region.owner.full_name), f"_{region.size}"
            ),
        )
        if region.description:
            description += f"\n-# {region.description}"
        if planet.feature:
            description += f"\n-# {self.language_json['RegionLoopEmbed']['feature']}: {planet.feature}"
        for special_unit in SpecialUnits.get_from_effects_list(
            active_effects=planet.active_effects
        ):
            description += f"\n-# {self.language_json['RegionLoopEmbed']['special_unit']}: **{self.language_json['special_units'][special_unit[0]]}** {special_unit[1]}"
        self.set_field_at(2, self.fields[2].name, description, inline=False)

    def remove_empty(self):
        for field in self.fields.copy():
            if field.value == "":
                self.remove_field(self.fields.index(field))
