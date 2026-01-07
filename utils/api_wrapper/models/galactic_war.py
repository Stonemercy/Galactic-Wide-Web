from disnake import Colour
from ...mixins import GWEReprMixin, ReprMixin
from ...dataclasses import Faction, Factions
from ...functions import dispatch_format
from ...functions.health_bar import health_bar
from ..services.tracking_service import TrackerEntry
from data.lists import stratagem_id_dict


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


GLOBAL_RESOURCES_DICT = {
    1754540810: AcquiredE711,
}


class GalacticWarEffect(GWEReprMixin):
    __slots__ = (
        "id",
        "gameplay_effect_id32",
        "effect_type",
        "flags",
        "name_hash",
        "fluff_description_hash",
        "long_description_hash",
        "short_description_hash",
        "values_dict",
        "effect_description",
        "planet_effect",
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
    )

    def __init__(self, gwa: dict, json_dict: dict) -> None:
        """Organised data for a galactic war effect"""
        self.id: int = gwa["id"]
        self.gameplay_effect_id32: int = gwa["gameplayEffectId32"]
        self.effect_type: int = gwa["effectType"]
        self.flags: int = gwa["flags"]
        self.name_hash: int = gwa["nameHash"]
        self.fluff_description_hash: int = gwa["descriptionFluffHash"]
        self.long_description_hash: int = gwa["descriptionGamePlayLongHash"]
        self.short_description_hash: int = gwa["descriptionGamePlayShortHash"]
        self.values_dict: dict = dict(zip(gwa["valueTypes"], gwa["values"]))
        self.effect_description: dict = json_dict["galactic_war_effects"].get(
            str(gwa["effectType"]),
            {"name": "UNKNOWN", "simplified_name": "", "description": ""},
        )
        self.planet_effect: dict | None = json_dict["planet_effects"].get(
            str(self.id),
            {
                "name": f"UNKNOWN [{self.id}]",
                "description_long": "",
                "description_short": "",
            },
        )
        self.count = self.percent = self.faction = self.mix_id = self.value5 = (
            self.DEPRECATED_enemy_group
        ) = self.DEPRECATED_item_package = self.value8 = self.value9 = (
            self.reward_multiplier_id
        ) = self.value11 = self.item_tag = self.hash_id = self.planet_body_type = (
            self.value15
        ) = self.resource_hash = self.found_enemy = self.found_stratagem = (
            self.found_booster
        ) = None

        if count := self.values_dict.get(1):
            self.count: int | float = count
        if percent := self.values_dict.get(2):
            self.percent: int | float = percent
        if faction := self.values_dict.get(3):
            self.faction: Faction | None = Factions.get_from_identifier(number=faction)
        if mix_id := self.values_dict.get(4):
            self.mix_id: int = mix_id
            if stratagem := stratagem_id_dict.get(self.mix_id):
                self.found_stratagem: str = stratagem
            elif booster := json_dict["items"]["boosters"].get(str(self.mix_id), {}):
                self.found_booster: dict = booster
        if value5 := self.values_dict.get(5):
            self.value5 = value5
            print(f"VALUE5 USED: {self.id} {self.value5 = }")
        if DEPRECATED_enemy_group := self.values_dict.get(6):
            self.DEPRECATED_enemy_group = DEPRECATED_enemy_group
        if DEPRECATED_item_package := self.values_dict.get(7):
            self.DEPRECATED_item_package = DEPRECATED_item_package
        if value8 := self.values_dict.get(8):
            self.value8 = value8
            print(f"VALUE8 USED: {self.id} {self.value8 = }")
        if value9 := self.values_dict.get(9):
            self.value9 = value9
            print(f"VALUE9 USED: {self.id} {self.value9 = }")
        if reward_multiplier_id := self.values_dict.get(10):
            # refer to: /api/Mission/RewardEntries
            self.reward_multiplier_id = reward_multiplier_id
        if value11 := self.values_dict.get(11):
            self.value11 = value11
            print(f"VALUE11 USED: {self.id} {self.value11 = }")
        if item_tag := self.values_dict.get(12):
            # or item group; gets used in /Progression/Items
            self.item_tag = item_tag
        if hash_id := self.values_dict.get(13):
            self.hash_id = hash_id
            if enemy := json_dict["enemy_ids"].get(str(self.hash_id), None):
                self.found_enemy: str = enemy
        if planet_body_type := self.values_dict.get(14):
            # BlackHole = 1, UNKNOWN = 2
            self.planet_body_type = planet_body_type
        if value15 := self.values_dict.get(15):
            # might be a boolean flag, only used with game_OperationModToggle so far
            self.value15 = value15
        if resource_hash := self.values_dict.get(16):
            # murmur2 resource hash
            self.resource_hash = resource_hash
            if enemy := json_dict["enemy_ids"].get(str(self.resource_hash), None):
                self.found_enemy = enemy

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
        self.title: str = dispatch_format(raw_global_event_data.get("title", ""))
        self.message: str = dispatch_format(
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
