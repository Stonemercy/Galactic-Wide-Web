from disnake import Colour, Embed
from data.lists import CUSTOM_COLOURS
from utils.api_wrapper.models import PersonalOrder
from utils.dataclasses import AssignmentImages
from utils.emojis import Emojis
from utils.mixins import EmbedReprMixin


class PersonalOrderCommandEmbed(Embed, EmbedReprMixin):
    def __init__(self, personal_order: PersonalOrder, json_dict: dict):
        super().__init__(
            title="PERSONAL ORDER",
            colour=Colour.from_rgb(*CUSTOM_COLOURS["MO"]),
        )

        self.set_thumbnail(url=AssignmentImages.get(8))

        for task in personal_order.tasks:
            if task.type == 2:  # Extract with {number} {items}
                if task.mix_id:
                    item = json_dict["items"]["item_names"].get(
                        str(task.mix_id), {"name": "UNKNOWN"}
                    )
                    item = item["name"]
                    full_objective = f"Successfully extract with {task.values[2]} {item}s {getattr(Emojis.Items, item.replace(' ', '_').lower(), '')}"
                else:
                    full_objective = (
                        f"Successfully extract from with {task.values[2]} **UNMAPPED**s"
                    )
                self.add_field(full_objective, "", inline=False)
            elif task.type == 3:  # Kill {number} {species} {stratagem}
                full_objective = f"Kill {task.values[2]} "
                if enemy := task.found_enemy:
                    if enemy[-1] == "s":
                        full_objective += enemy
                    else:
                        full_objective += f"{enemy}s"
                else:
                    full_objective += (
                        task.faction.full_name if task.faction else "Enemies"
                    )
                if task.found_stratagem:
                    full_objective += (
                        f" with the {task.found_stratagem}" if task.values[5] else ""
                    )
                self.add_field(
                    full_objective,
                    "",
                    inline=False,
                )
            elif task.type == 4:  # Complete {number} {tier} objectives
                objective_type = {1: "primary", 2: "secondary"}[task.values[3]]
                full_objective = (
                    f"Complete {task.values[2]} {objective_type} objectives"
                )
                self.add_field(
                    full_objective,
                    "",
                    inline=False,
                )
            elif (
                task.type == 7
            ):  # Extract from successful mission {faction} {number} times
                faction_text = ""
                faction = {
                    1: "Humans",
                    2: "Terminids",
                    3: "Automaton",
                    4: "Illuminate",
                }.get(task.values[0], None)
                if faction:
                    faction_text = f"against {faction} "
                full_objective = f"Extract from a successful Mission {faction_text}{task.values[2]} times"
                self.add_field(
                    full_objective,
                    "",
                    inline=False,
                )

        for reward in personal_order.rewards:
            self.add_field("Reward", f"{reward.amount} Medals {Emojis.Items.medal}")

        self.add_field(
            "Ends", f"<t:{int(personal_order.expiration_datetime.timestamp())}:R>"
        )
