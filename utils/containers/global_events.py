from data.lists import CUSTOM_COLOURS
from disnake import Colour, ui
from utils.api_wrapper.models import GlobalEvent, Planet
from utils.dataclasses import Subfactions
from utils.mixins import ReprMixin


class GlobalEventsContainer(ui.Container, ReprMixin):
    def __init__(
        self,
        lang_code: str,
        container_json: dict,
        global_event: GlobalEvent,
        planets: dict[int, Planet],
        with_expiry_time: bool = False,
    ):
        components = []
        title = ui.TextDisplay(
            f"# {global_event.title if global_event.title else container_json['new_event']}"
        )
        components.extend([title, ui.Separator()])
        if global_event.flag == 0:
            if not global_event.planet_indices:
                specific_planets = f"\n    {container_json['all_planets']}"
            else:
                spec_planets_list = [
                    planets.get(index) for index in global_event.planet_indices
                ]
                specific_planets = "\n-# - " + "\n- ".join(
                    [p.names.get(lang_code, p.name) for p in spec_planets_list if p]
                )
            for index, effect in enumerate(global_event.effects, start=1):
                effect_component = ui.TextDisplay(
                    f"\n### {container_json['effect']} **#{index}**"
                )
                if effect.name:
                    effect_component.content += f"\n    **{effect.name}**"
                if effect.short_description:
                    effect_component.content += f"\n    {effect.short_description}"
                if not effect.name and not effect.short_description:
                    effect_component.content += (
                        f"\n    {effect.effect_description['simplified_name']}"
                    )
                if (
                    effect.found_booster
                    and effect.found_booster not in effect_component.content
                ):
                    effect_component.content += f"\n    {container_json['booster']}: **{effect.found_booster['name']}**"
                if (
                    effect.found_stratagem
                    and effect.found_stratagem not in effect_component.content
                ):
                    effect_component.content += f"\n    {container_json['stratagem']}: **{effect.found_stratagem}**"
                if (
                    effect.found_enemy
                    and effect.found_enemy not in effect_component.content
                ):
                    effect_component.content += (
                        f"\n    {container_json['enemy']}: **{effect.found_enemy}**"
                    )
                    if subfactions := [
                        sf
                        for sf in Subfactions._all
                        if sf.eng_name.lower() == effect.found_enemy.lower()
                    ]:
                        sf = subfactions[0]
                        effect_component.content += sf.emoji
                components.extend([effect_component, ui.Separator()])
            components.extend(
                [
                    ui.TextDisplay(
                        f"\n### {container_json['active_on_planets']}:{specific_planets}"
                    ),
                    ui.Separator(),
                ]
            )
        else:
            components.extend(
                [
                    ui.TextDisplay(
                        "".join(f"\n{chunk}" for chunk in global_event.split_message)
                    ),
                    ui.Separator(),
                ]
            )

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
