from data.lists import CUSTOM_COLOURS
from disnake import Colour, ui
from utils.api_wrapper.models import GlobalEvent, Planet
from utils.mixins import ReprMixin


class GlobalEventsContainer(ui.Container, ReprMixin):
    def __init__(
        self,
        long_lang_code: str,
        container_json: dict,
        global_event: GlobalEvent,
        planets: dict[int, Planet],
        with_expiry_time: bool = False,
    ):
        components = []
        text_display = ui.TextDisplay(
            f"# {global_event.title if global_event.title else 'New Global Event'}"
        )
        if global_event.flag == 0:
            if not global_event.planet_indices:
                specific_planets = container_json["all_planets"]
            else:
                spec_planets_list = [
                    planets.get(index) for index in global_event.planet_indices
                ]
                specific_planets = "\n-# " + "\n- ".join(
                    [p.name for p in spec_planets_list if p]
                )
            for effect in global_event.effects:
                if "UNKNOWN" in effect.planet_effect["name"]:
                    text_display.content += f"\nUNKNOWN effect (ID {effect.id})\n{effect.effect_description['simplified_name']}{container_json['active_on_planets'].format(planets=specific_planets)}"
                    if effect.found_enemy:
                        text_display.content += f"\n{container_json['enemy_identified']}: {effect.found_enemy}"
                    if effect.found_stratagem:
                        text_display.content += f"\n{container_json['strat_identified']}: {effect.found_stratagem}"
                    if effect.found_booster:
                        text_display.content += f"\n{container_json['booster_identified']}: {effect.found_stratagem}"
                else:
                    text_display.content += f"\n{effect.planet_effect['name']}"
                    if effect.planet_effect["description_long"]:
                        text_display.content += (
                            f"\n-# {effect.planet_effect['description_long']}"
                        )
                    if effect.planet_effect["description_short"]:
                        if effect.effect_type == 32:
                            effect.planet_effect["description_short"] = (
                                effect.planet_effect["description_short"].replace(
                                    "#V_ONE", effect.found_stratagem
                                )
                            )
                        text_display.content += (
                            f"\n-# {effect.planet_effect['description_short']}"
                        )
                    text_display.content += f"{container_json['active_on_planets'].format(planets=specific_planets)}"
        else:
            for chunk in global_event.split_message:
                text_display.content += f"\n{chunk}"
        components.extend([text_display, ui.Separator()])

        extra_text_display = ui.TextDisplay("")
        if with_expiry_time:
            extra_text_display.content += (
                f"-# {container_json['expires']} <t:{global_event.expire_time}:R>"
            )

        extra_text_display.content += (
            f"\n-# {container_json['global_event']} #{global_event.id}"
        )
        components.append(extra_text_display)

        super().__init__(
            *components, accent_colour=Colour.from_rgb(*CUSTOM_COLOURS["MO"])
        )
