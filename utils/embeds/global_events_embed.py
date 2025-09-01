from data.lists import custom_colours
from disnake import Colour, Embed
from utils.data import GlobalEvent, Planets
from utils.mixins import EmbedReprMixin


class GlobalEventsEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        planets: Planets,
        language_json: dict,
        planet_effects_json: dict,
        global_event: GlobalEvent,
    ):
        super().__init__(
            title=global_event.title, colour=Colour.from_rgb(*custom_colours["MO"])
        )
        if global_event.flag == 0:
            specific_planets = "\n- ".join(
                [planets[index].name for index in global_event.planet_indices]
            )
            if not specific_planets:
                specific_planets = "All"
            for effect_id in global_event.effect_ids:
                effect = planet_effects_json.get(str(effect_id), None)
                if not effect:
                    self.add_field(
                        f"UNKNOWN effect (ID {effect_id})",
                        f"-# Now active of the following planet(s):\n- {specific_planets}",
                        inline=False,
                    )
                else:
                    self.add_field(
                        effect["name"],
                        f"-# {effect['description']}\n-# Now active on the following planet(s):\n- {specific_planets}",
                        inline=False,
                    )
        else:
            for chunk in global_event.split_message:
                self.add_field("", chunk, inline=False)

        self.set_footer(
            text=language_json["message"].format(message_id=global_event.id)
        )
