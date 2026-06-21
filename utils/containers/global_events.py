from .galactic_war_effect import GWEContainer
from data.lists import CUSTOM_COLOURS
from disnake import Colour, MediaGalleryItem, ui
from utils.api_wrapper.models import GlobalEvent, Planet
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
        if global_event.outtro_image_id or global_event.intro_image_id:
            components.append(
                ui.MediaGallery(
                    MediaGalleryItem(
                        f"attachment://{global_event.outtro_image_id or global_event.intro_image_id}.png"
                    )
                )
            )
        title = ui.TextDisplay(
            f"# {global_event.title if global_event.title else container_json['new_event']}"
        )
        if global_event.assignment_id:
            title.content += f"\n-# Related to Assignment #{global_event.assignment_id}"
        components.extend([title, ui.Separator()])
        if global_event.effects != []:
            if not global_event.planet_indices:
                specific_planets = f"\n    {container_json['all_planets']}"
            else:
                spec_planets_list = [
                    planets.get(index) for index in global_event.planet_indices
                ]
                specific_planets = "\n-# - " + "\n- ".join(
                    [p.names.get(lang_code, p.name) for p in spec_planets_list if p]
                )
            effects_text = ""
            for effect in global_event.effects:
                effect_container = GWEContainer(effect, [], False, False)
                gwe_content = (
                    "\n"
                    + effect_container.components[0].content
                    + effect_container.components[1].content
                    + "\n"
                )
                effects_text += gwe_content
            components.append(ui.TextDisplay(effects_text or "No effects present"))
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
                        or "Empty Message"
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
