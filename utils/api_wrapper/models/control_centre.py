from datetime import datetime
from utils.dataclasses.enums import ControlCentreStatus
from utils.dataclasses.factions import Faction, Factions
from utils.emojis import Emojis
from utils.functions import arrowhead_format


class ControlCentre:
    def __init__(
        self, raw_control_centre_data: dict, json_dict: dict, war_time: int
    ) -> None:
        self.raw_data = raw_control_centre_data
        self.episodes: list[ControlCentre.Episode] = [
            ControlCentre.Episode(r, json_dict, war_time)
            for r in raw_control_centre_data.get("episodes", [])
        ]

    def images_required(
        self,
        episode_id: int = None,
        need_episode: bool = True,
        phase_id: int = None,
    ):
        episodes = [e for e in self.episodes]
        if episode_id != None:
            episodes = [e for e in episodes.copy() if e.id == episode_id]
        phases = [p for e in episodes for p in e.phases]
        if phase_id != None:
            phases = [p for p in phases.copy() if p.id == phase_id]
        return set(
            [
                p.outro_image_id or p.intro_image_id
                for p in phases
                if p.outro_image_id or p.intro_image_id
            ]
            + ([e.image_id for e in episodes if e.image_id] if need_episode else [])
        )

    class Episode:
        def __init__(
            self, raw_episode_data: dict, json_dict: dict, war_time: int
        ) -> None:
            self.id: int = raw_episode_data.get("id32", 0)
            self.title: str = raw_episode_data.get("title", "Undefined Title")
            self.description: str = arrowhead_format(
                raw_episode_data.get("description", "")
            )
            self.intro_message: str = arrowhead_format(
                raw_episode_data.get("introMessage", "")
            )
            self.outro_message: str = arrowhead_format(
                raw_episode_data.get("outroMessage", "")
            )
            self._race: int = raw_episode_data.get("race", 0)
            self.faction: Faction = Factions.get_from_identifier(number=self._race)
            self.start_time: int = war_time + raw_episode_data.get("startWarTime", 0)
            self.start_time_datetime: datetime = datetime.fromtimestamp(self.start_time)
            self.end_time: int = war_time + raw_episode_data.get("endWarTime", 0)
            self.end_time_datetime: datetime = datetime.fromtimestamp(self.end_time)
            self._status: int = raw_episode_data.get("status", 0)
            self.status: ControlCentreStatus = ControlCentreStatus(self._status)
            self.phases: list[ControlCentre.Episode.Phase] = [
                ControlCentre.Episode.Phase(r, json_dict)
                for r in raw_episode_data.get("phases", [])
            ]
            self.rewards: list[ControlCentre.Episode.Reward] = [
                ControlCentre.Episode.Reward(r, json_dict)
                for r in raw_episode_data.get("rewards", [])
            ]
            self.image_id: int = raw_episode_data.get("bannerImageId32", 0)
            """default: 0"""

        def __eq__(self, value):
            return self.id == value.id

        class Phase:
            def __init__(self, raw_phase_data: dict, json_dict: dict) -> None:
                """Organised data for an Episode's Phase"""
                self.id: int = raw_phase_data.get("id32", 0)
                self.intro_title: str = raw_phase_data.get("introTitle", "")
                self.intro_message: str = arrowhead_format(
                    raw_phase_data.get("introMessage", "")
                )
                self.outro_title: str = raw_phase_data.get("outroTitle", "")
                self.outro_message: str = arrowhead_format(
                    raw_phase_data.get("outroMessage", "")
                )
                self._status: int = raw_phase_data.get("status", 0)
                self.status: ControlCentreStatus = ControlCentreStatus(self._status)
                self.entries: list = raw_phase_data.get("entries", [])
                self.rewards: list[ControlCentre.Episode.Reward] = [
                    ControlCentre.Episode.Reward(r, json_dict)
                    for r in raw_phase_data.get("rewards", [])
                ]
                self.intro_image_id: int = raw_phase_data.get("introMediaId32", 0)
                self.outro_image_id: int = raw_phase_data.get("outroMediaId32", 0)

            def __eq__(self, value):
                return self.id == value.id

        class Reward:
            def __init__(self, raw_reward_data: dict, json_dict: dict) -> None:
                self.id: int = raw_reward_data.get("mixId", 0)
                self.amount: int = raw_reward_data.get("amount", 1)
                self.item_name: str = (
                    json_dict["items"]["rewards"].get(str(self.id))
                    or json_dict["items"]["items"].get(str(self.id), {}).get("type", None)
                    or json_dict["strings"].get(str(self.id))
                    or "Unknown Item"
                )
                self.item_type = "" or json_dict["items"]["items"].get(
                    str(self.id), {}
                ).get("type", "")
                self.emoji: str = getattr(
                    Emojis.Items,
                    (self.item_type or self.item_name).replace(" ", "_").lower(),
                    "",
                )

            def __eq__(self, value):
                return self.id == value.id
