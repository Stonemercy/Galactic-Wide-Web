from data.lists import STRATAGEM_ID_DICT, STRATAGEM_CAT_DICT
from datetime import datetime, timezone
from disnake import Colour
from utils.api_wrapper.services.tracking_service import TrackerEntry
from utils.dataclasses import Faction, Factions
from utils.functions import arrowhead_format
from utils.functions.health_bar import health_bar
from utils.mixins import GWEReprMixin, ReprMixin


class GlobalResource(ReprMixin):
    __slots__ = (
        "id",
        "current_value",
        "max_value",
        "perc",
        "tracker",
        "name",
        "description",
        "embed_colour",
    )

    def __init__(self, raw_global_resource_data: dict) -> None:
        """Organised data of a global resource"""
        self.id: int = raw_global_resource_data["id32"]
        self.current_value: int = raw_global_resource_data["currentValue"]
        self.max_value: int = raw_global_resource_data["maxValue"]
        self.perc: float = self.current_value / self.max_value
        self.tracker: TrackerEntry | None = None
        self.name: str = ""
        self.description: str = ""
        self.embed_colour: Colour = Colour.dark_embed()
        self.health_bar_colour: Faction | str = Factions.humans

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, value):
        if not isinstance(value, type(self)):
            return False
        return self.id == value.id

    @property
    def get_health_bar(self):
        return health_bar(
            perc=self.perc,
            faction=self.health_bar_colour,
            anim=(
                True
                if self.tracker and self.tracker.change_rate_per_hour != 0
                else False
            ),
            increasing=(
                True
                if self.tracker and self.tracker.change_rate_per_hour > 0
                else False
            ),
        )

    @staticmethod
    def from_id(raw_gr_data: dict):
        return GLOBAL_RESOURCES_DICT.get(raw_gr_data["id32"], GlobalResource)(
            raw_global_resource_data=raw_gr_data
        )


class AcquiredE711(GlobalResource):
    def __init__(self, raw_global_resource_data):
        super().__init__(raw_global_resource_data=raw_global_resource_data)
        self.name = "ACQUIRED E-711"
        self.description = (
            "E-711 is being used to synthesize Dark Fluid to fire the Star of Peace"
        )
        self.embed_colour = Colour.yellow()
        self.health_bar_colour = "MO"


class ForcesInReserve(GlobalResource):
    def __init__(self, raw_global_resource_data):
        super().__init__(raw_global_resource_data=raw_global_resource_data)
        self.name = "FORCES IN RESERVE"
        self.description = "-# Remaining forces left in the reserve.\n-# **Every** Helldiver death reduces this."
        self.embed_colour = Colour.from_rgb(*Factions.humans.colour)
        self.health_bar_colour = Factions.humans


GLOBAL_RESOURCES_DICT = {
    1754540810: AcquiredE711,
    1053905445: ForcesInReserve,
}


class GalacticWarEffect(GWEReprMixin):
    __slots__ = (
        "id",
        "gameplay_effect_id32",
        "effect_type",
        "flags",
        "name_hash",
        "name",
        "fluff_description_hash",
        "fluff_description",
        "long_description_hash",
        "long_description",
        "short_description_hash",
        "short_description",
        "values_list",
        "effect_description",
        "count",
        "percent",
        "faction",
        "mix_id",
        "value5",
        "DEPRECATED_enemy_group",
        "DEPRECATED_item_package",
        "value8",
        "value9",
        "reward_multiplier_id",
        "value11",
        "item_tag",
        "hash_id",
        "planet_body_type",
        "value15",
        "resource_hash",
        "resource",
        "stratagem_category",
    )

    def __init__(self, gwa: dict, json_dict: dict) -> None:
        """Organised data for a galactic war effect"""
        self.count = self.percent = self.faction = self.mix_id = self.value5 = (
            self.DEPRECATED_enemy_group
        ) = self.DEPRECATED_item_package = self.value8 = self.value9 = (
            self.reward_multiplier_id
        ) = self.value11 = self.item_tag = self.hash_id = self.planet_body_type = (
            self.value15
        ) = self.resource_hash = self.found_enemy = self.found_stratagem = (
            self.found_booster
        ) = self.fluff_description = self.name = self.long_description = (
            self.short_description
        ) = self.resource = self.stratagem_category = None
        self.id: int = gwa["id"]
        self.gameplay_effect_id32: int = gwa["gameplayEffectId32"]
        self.effect_type: int = gwa["effectType"]
        self.flags: int = gwa["flags"]
        self.name_hash: int = gwa["nameHash"]
        self.fluff_description_hash: int = gwa["descriptionFluffHash"]
        self.long_description_hash: int = gwa["descriptionGamePlayLongHash"]
        self.short_description_hash: int = gwa["descriptionGamePlayShortHash"]
        self.values_list: list = list(zip(gwa["valueTypes"], gwa["values"]))
        self.effect_description: dict = json_dict["galactic_war_effects"].get(
            str(gwa["effectType"]),
            {"name": "UNKNOWN", "simplified_name": "", "description": ""},
        )
        for value_type, value in self.values_list:
            match value_type:
                case 1:
                    if (
                        len([v[0] == 1 for v in self.values_list]) > 1
                        and self.effect_type == 36
                        and not self.stratagem_category
                    ):
                        self.stratagem_category = STRATAGEM_CAT_DICT.get(value)
                    else:
                        self.count: int | float = value
                case 2:
                    self.percent: int | float = value
                case 3:
                    self.faction: Faction | None = Factions.get_from_identifier(
                        number=value
                    )
                case 4:
                    self.mix_id: int = value
                    if stratagem := STRATAGEM_ID_DICT.get(self.mix_id):
                        self.found_stratagem: str = stratagem
                    elif booster := json_dict["items"]["boosters"].get(
                        str(self.mix_id), {}
                    ):
                        self.found_booster: str = booster["name"]
                case 5:
                    self.value5 = value
                    print(f"VALUE5 (AssaultType) USED: {self.id} {self.value5 = }")
                case 6:
                    self.DEPRECATED_enemy_group = value
                    print(
                        f"DEPRECATED_enemy_group USED: {self.id} {self.DEPRECATED_enemy_group = }"
                    )
                case 7:
                    self.DEPRECATED_item_package = value
                case 8:
                    self.value8 = value
                    print(
                        f"VALUE8 (StoreWideDiscountId) USED: {self.id} {self.value8 = }"
                    )
                case 9:
                    self.value9 = value
                    print(f"VALUE9 (BadgeId) USED: {self.id} {self.value9 = }")
                case 10:
                    # refer to: /api/Mission/RewardEntries
                    self.reward_multiplier_id = value
                case 11:
                    self.value11 = value
                    print(f"VALUE11 (BadgeGroupId) USED: {self.id} {self.value11 = }")
                case 12:
                    # or item group; gets used in /Progression/Items
                    self.item_tag = value
                    print(f"item_tag USED: {self.id} {self.item_tag = }")
                case 13:
                    self.hash_id = value
                    if enemy := json_dict["enemy_ids"].get(str(self.hash_id), None):
                        self.found_enemy: str = enemy
                case 14:
                    # BlackHole = 1, UNKNOWN = 2
                    self.planet_body_type = value
                case 15:
                    # might be a boolean flag, only used with game_OperationModToggle so far
                    self.value15 = value
                case 16:
                    # murmur2 resource hash
                    self.resource_hash = value
                    if enemy := json_dict["enemy_ids"].get(
                        str(self.resource_hash), None
                    ):
                        self.found_enemy = enemy

        if self.name_hash:
            self.name = json_dict["strings"].get(str(self.name_hash))
        if self.fluff_description_hash:
            self.fluff_description = json_dict["strings"].get(
                str(self.fluff_description_hash)
            )
        if self.long_description_hash:
            self.long_description = json_dict["strings"].get(
                str(self.long_description_hash)
            )
        if self.short_description_hash:
            short_desc = json_dict["strings"].get(str(self.short_description_hash))
            if short_desc:
                value = iter(
                    i
                    for i in [
                        self.found_stratagem,
                        self.found_enemy,
                        self.found_booster,
                        self.percent,
                        self.count,
                    ]
                    if i
                )
                short_desc = arrowhead_format(short_desc)
                if "#V_ONE" in short_desc:
                    short_desc = short_desc.replace(
                        "#V_ONE", str(next(value, "NOT FOUND"))
                    )
                if "#V_TWO" in short_desc:
                    short_desc = short_desc.replace(
                        "#V_TWO", str(next(value, "NOT FOUND"))
                    )
                short_desc = short_desc.replace("\n", " ")
                self.short_description = short_desc

    def __hash__(self):
        return hash((self.id))

    def __eq__(self, value):
        if not isinstance(value, type(self)):
            return False
        return self.id == value.id


class GlobalEvent(ReprMixin):
    __slots__ = (
        "id",
        "title",
        "message",
        "faction",
        "flag",
        "assignment_id",
        "effects",
        "planet_indices",
        "expire_time",
    )

    def __init__(
        self,
        raw_global_event_data: dict,
        war_time: float,
        war_effect_list: dict[int, GalacticWarEffect],
    ) -> None:
        """Organised data of a global event"""
        self.id: int = raw_global_event_data["eventId"]
        self.title: str = arrowhead_format(raw_global_event_data.get("title", ""))
        self.message: str = arrowhead_format(
            text=raw_global_event_data.get("message", "")
        )
        self.faction: Faction = Factions.get_from_identifier(
            number=raw_global_event_data["race"]
        )
        self.flag: int = raw_global_event_data["flag"]
        self.assignment_id: int = raw_global_event_data["assignmentId32"]
        self.effects: list[GalacticWarEffect] = [
            war_effect_list.get(effect_id)
            for effect_id in raw_global_event_data["effectIds"]
        ]
        self.planet_indices: list[int] = raw_global_event_data["planetIndices"]
        self.expire_time: int = raw_global_event_data["expireTime"] + war_time
        self.intro_image_id: int = raw_global_event_data.get("introMediaId32", 0)
        self.outro_image_id: int = raw_global_event_data.get("outroMediaId32", 0)

    @property
    def split_message(self) -> list[str]:
        """Returns the message split into chunks with character lengths of 1024 or less"""
        sentences = self.message.split(sep="\n")
        formatted_sentences = [
            f"-# {sentence}" for sentence in sentences if sentence != ""
        ]
        chunks = []
        current_chunk = ""
        for sentence in formatted_sentences:
            if len(current_chunk) + len(sentence) + 2 <= 1024:
                current_chunk += sentence + "\n\n"
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence + "\n\n"
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks
