from data.lists import CUSTOM_COLOURS
from disnake import Colour, MediaGalleryItem
from disnake.ui import Container, MediaGallery, Separator, TextDisplay
from utils.api_wrapper.models import GlobalEvent, Planet
from utils.containers import GWEContainer


class GlobalEventsContainer(Container):
    def __init__(
        self,
        lang_code: str,
        container_json: dict,
        global_event: GlobalEvent,
        planets: dict[int, Planet],
        with_expiry_time: bool = False,
        image_url: str = None,
        attachment_url: str = None,
    ):
        components = []
        if image_url:
            components.append(MediaGallery(MediaGalleryItem(image_url)))
        elif attachment_url:
            components.append(MediaGallery(MediaGalleryItem(attachment_url)))
        title = TextDisplay(
            f"# {global_event.title if global_event.title else container_json['new_event']}"
        )
        if global_event.assignment_id:
            title.content += f"\n-# Related to Assignment #{global_event.assignment_id}"
        components.extend([title, Separator()])
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
            components.append(TextDisplay(effects_text or "No effects present"))
            components.extend(
                [
                    TextDisplay(
                        f"\n### {container_json['active_on_planets']}:{specific_planets}"
                    ),
                    Separator(),
                ]
            )
        else:
            components.extend(
                [
                    TextDisplay(
                        "".join(f"\n{chunk}" for chunk in global_event.split_message)
                        or "Empty Message"
                    ),
                    Separator(),
                ]
            )

        extra_text_display = TextDisplay("")
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
