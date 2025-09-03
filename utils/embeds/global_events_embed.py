from data.lists import custom_colours
from disnake import Colour, Embed
from utils.data import GlobalEvent, Planets
from utils.mixins import EmbedReprMixin


class GlobalEventsEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        planets: Planets,
        language_json: dict,
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
            for effect in global_event.effects:
                if "UNKNOWN" in effect.planet_effect["name"]:
                    self.add_field(
                        f"UNKNOWN effect (ID {effect.id})",
                        (
                            f"{effect.effect_description['simplified_name']}"
                            f"\n-# Now active of the following planet(s):\n- {specific_planets}"
                        ),
                        inline=False,
                    )
                    if effect.found_enemy:
                        self.add_field(
                            "Enemy identified", effect.found_enemy, inline=False
                        )

                else:
                    self.add_field(
                        effect.planet_effect["name"],
                        f"-# {effect.planet_effect['description']}\n-# Now active on the following planet(s):\n- {specific_planets}",
                        inline=False,
                    )
        else:
            for chunk in global_event.split_message:
                self.add_field("", chunk, inline=False)

        self.add_field("Ends", f"<t:{global_event.expire_time}:R>")

        self.set_footer(
            text=language_json["message"].format(message_id=global_event.id)
        )
