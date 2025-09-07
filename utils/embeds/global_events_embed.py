from data.lists import custom_colours
from disnake import Colour, Embed
from utils.data import GlobalEvent
from utils.mixins import EmbedReprMixin


class GlobalEventsEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        language_json: dict,
        planet_names_json: dict,
        global_event: GlobalEvent,
    ):
        super().__init__(
            title=global_event.title, colour=Colour.from_rgb(*custom_colours["MO"])
        )
        if global_event.flag == 0:
            specific_planets = "\n- ".join(
                [
                    planet_names_json[str(index)]["names"][language_json["code_long"]]
                    for index in global_event.planet_indices
                ]
            )
            if not specific_planets:
                specific_planets = language_json["GlobalEventsEmbed"]["all"]
            for effect in global_event.effects:
                if "UNKNOWN" in effect.planet_effect["name"]:
                    self.add_field(
                        f"UNKNOWN effect (ID {effect.id})",
                        (
                            f"{effect.effect_description['simplified_name']}"
                            f"{language_json['GlobalEventsEmbed']['active_on_planets'].format(planets=specific_planets)}"
                        ),
                        inline=False,
                    )
                    if effect.found_enemy:
                        self.add_field(
                            language_json["GlobalEventsEmbed"]["enemy_identified"],
                            effect.found_enemy,
                            inline=False,
                        )
                    if effect.found_stratagem:
                        self.add_field(
                            language_json["GlobalEventsEmbed"]["strat_identified"],
                            effect.found_stratagem,
                            inline=False,
                        )
                    if effect.found_booster:
                        self.add_field(
                            language_json["GlobalEventsEmbed"]["booster_identified"],
                            effect.found_stratagem,
                            inline=False,
                        )
                else:
                    self.add_field(
                        effect.planet_effect["name"],
                        f"-# {effect.planet_effect['description']}{language_json['GlobalEventsEmbed']['active_on_planets'].format(planets=specific_planets)}",
                        inline=False,
                    )
        else:
            for chunk in global_event.split_message:
                self.add_field("", chunk, inline=False)

        self.add_field(language_json["ends"], f"<t:{global_event.expire_time}:R>")

        self.set_footer(
            text=language_json["message"].format(message_id=global_event.id)
        )
