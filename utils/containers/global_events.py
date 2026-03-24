from data.lists import CUSTOM_COLOURS, STRATAGEM_IMAGE_LINKS
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
        text_display = ui.TextDisplay(
            f"# {global_event.title if global_event.title else container_json['new_event']}"
        )
        if global_event.flag == 0:
            if not global_event.planet_indices:
                specific_planets = container_json["all_planets"]
            else:
                spec_planets_list = [
                    planets.get(index) for index in global_event.planet_indices
                ]
                specific_planets = "\n-# - " + "\n- ".join(
                    [
                        p.names.get(lang_code, str(p.index))
                        for p in spec_planets_list
                        if p
                    ]
                )
            for index, effect in enumerate(global_event.effects, start=1):
                text_display.content += (
                    f"\n### Effect **#{index}**\n    ID: **{effect.id}**"
                )
                if effect.name:
                    text_display.content += f"\n    **{effect.name}**"
                if effect.short_description:
                    text_display.content += f"\n    {effect.short_description}"
                if not effect.name and not effect.short_description:
                    text_display.content += (
                        f"\n    {effect.effect_description['simplified_name']}"
                    )
                if effect.found_booster:
                    text_display.content += (
                        f"\n    Booster: **{effect.found_booster['name']}**"
                    )
                if effect.found_stratagem:
                    text_display.content += (
                        f"\n    Stratagem: **{effect.found_stratagem}**"
                    )
                if effect.found_enemy:
                    text_display.content += f"\n    Enemy: **{effect.found_enemy}**"
                    if subfactions := [
                        sf
                        for sf in Subfactions._all
                        if sf.eng_name.lower() == effect.found_enemy.lower()
                    ]:
                        sf = subfactions[0]
                        text_display.content += sf.emoji
            text_display.content += f"\n### Effects added to:{specific_planets}"

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


class GlobalEventCommandContainer(ui.Container):
    def __init__(self, global_event: GlobalEvent, planets: dict[int, Planet]) -> None:
        self.container_components = []
        if global_event.title:
            self.container_components.extend(
                [
                    ui.TextDisplay(global_event.title),
                    ui.Separator(),
                ]
            )

        for effect in global_event.effects:
            section = ui.Section(
                ui.TextDisplay(""),
                accessory=ui.Thumbnail(
                    "https://cdn.discordapp.com/attachments/1212735927223590974/1422512588973015081/0xa92d559bf3ae174.png?ex=692eae96&is=692d5d16&hm=1a6a92832ea0b6746ec96b5cc6c6c7894be3d5bc828a8d23a89e16782947c481&"
                ),
            )
            section.children[0].content += f"\n{effect.id}"
            if effect.short_description:
                section.children[0].content += f"\n-#    {effect.short_description}"
            if not effect.name and not effect.short_description:
                section.children[
                    0
                ].content += f"\n    {effect.effect_description['simplified_name']}"
            if effect.found_booster:
                section.children[
                    0
                ].content += f"\n    Booster: **{effect.found_booster['name']}**"
            if effect.found_stratagem:
                section.children[
                    0
                ].content += f"\n    Stratagem: **{effect.found_stratagem}**"
                for stratagem in STRATAGEM_IMAGE_LINKS.keys():
                    if stratagem.lower() in effect.found_stratagem.lower():
                        section.accessory = ui.Thumbnail(
                            STRATAGEM_IMAGE_LINKS[stratagem]
                        )
            if effect.found_enemy:
                section.children[0].content += f"\n    Enemy: **{effect.found_enemy}**"
                if subfactions := [
                    sf
                    for sf in Subfactions._all
                    if sf.eng_name.lower() == effect.found_enemy.lower()
                ]:
                    sf = subfactions[0]
                    section.children[0].content += sf.emoji

            for stratagem in STRATAGEM_IMAGE_LINKS.keys():
                if stratagem.lower() in section.children[0].content.lower():
                    section.accessory = ui.Thumbnail(STRATAGEM_IMAGE_LINKS[stratagem])

            self.container_components.append(section)
            if len(global_event.effects) > 1:
                self.container_components.append(ui.Separator())

        text_display = ui.TextDisplay(f"Active on:")
        if not global_event.planet_indices:
            text_display.content += "\n**ALL PLANETS**"
        else:
            for index in global_event.planet_indices:
                text_display.content += f"\n- {planets.get(index).names['en-GB']}"
        self.container_components.append(text_display)

        self.container_components.append(
            ui.TextDisplay(f"Expires <t:{global_event.expire_time}:R>")
        )

        super().__init__(*self.container_components, accent_colour=Colour.blurple())
