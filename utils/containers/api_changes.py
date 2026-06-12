from disnake import ComponentType, ui
from utils.api_wrapper.models import Planet
from utils.dataclasses import APIChanges
from utils.emojis import Emojis
from utils.interactables import HDCButton
from utils.mixins import ReprMixin
from .galactic_war_effect import GWEContainer


# DOESNT NEED LOCALIZATION
class APIChangesContainer(ui.Container, ReprMixin):
    def __init__(
        self, api_changes: list[APIChanges], planets: dict[int, Planet]
    ) -> None:
        self.container_components: list[ui.Section | ui.TextDisplay] = []

        for api_change in api_changes:
            if api_change.stat_source not in [
                "Global Resources",
                "Galactic War Effects",
                "Task",
                "Personal Order",
            ]:
                old_stat = getattr(api_change.old_object, api_change.property)
                new_stat = getattr(api_change.new_object, api_change.property)
            match api_change.stat_source:
                case "Global Resources":
                    self.container_components.append(
                        ui.TextDisplay(
                            f"## CHANGES TO GLOBAL RESOURCES\nBefore:\n```py\n{api_change.old_object}```\n\nAfter:\n```py\n{api_change.new_object}```"
                        )
                    )
                case "Galactic War Effects":
                    content = ""
                    if effects_removed := [
                        gwe
                        for id, gwe in api_change.old_object.items()
                        if id not in api_change.new_object
                    ]:
                        content += "\n### Galactic Effect(s) Removed ❌"
                        for gwe in effects_removed:
                            gwe_container = GWEContainer(gwe, [], False, False)
                            gwe_content = (
                                "\n"
                                + gwe_container.components[0].content
                                + gwe_container.components[1].content
                                + "\n"
                            )
                            content += gwe_content

                    if effects_added := [
                        gwe
                        for id, gwe in api_change.new_object.items()
                        if id not in api_change.old_object
                    ]:
                        content += "\n### Galactic Effect(s) Added :white_check_mark:"
                        for gwe in effects_added:
                            gwe_container = GWEContainer(gwe, [], False, False)
                            gwe_content = (
                                "\n"
                                + gwe_container.components[0].content
                                + gwe_container.components[1].content
                                + "\n"
                            )
                            content += gwe_content

                    if effects_removed or effects_added:
                        self.container_components.append(ui.TextDisplay(content))
                case "Task":
                    self.container_components.append(
                        ui.TextDisplay(
                            f"## Update to **{api_change.stat_name}**\n    Target for task **#{api_change.property}**\n        **{api_change.old_object.target:,} {Emojis.Stratagems.right} {api_change.new_object.target:,}**"
                        )
                    )
                case "Personal Order":
                    self.container_components.append(
                        ui.TextDisplay(
                            f"## Personal Order has changed\n**{api_change.old_object.id}** {Emojis.Stratagems.right} **{api_change.new_object.id}**"
                            f"\n{api_change.stat_name}"
                        )
                    )
                case "Planet":
                    if not next(
                        (
                            s
                            for s in self.container_components
                            if s.type == ComponentType.section
                            and api_change.new_object.names.get(
                                "en-GB", api_change.new_object.name
                            )
                            in s.children[0].content
                        ),
                        None,
                    ):
                        self.container_components.append(
                            ui.Section(
                                ui.TextDisplay(
                                    f"## Update to **{api_change.new_object.names.get('en-GB', api_change.new_object.name)}** {api_change.new_object.faction.emoji}{api_change.new_object.exclamations}"
                                ),
                                accessory=HDCButton(
                                    label=api_change.new_object.names.get(
                                        "en-GB", api_change.new_object.name
                                    ),
                                    link=f"https://helldiverscompanion.com/#hellpad/planets/{api_change.new_object.index}",
                                ),
                            )
                        )
                    match api_change.property:
                        case "position":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"Planet has __**moved**__"
                                    f"\n**{old_stat['x']}, {old_stat['y']}**"
                                    f"\n                         {Emojis.Stratagems.down}"
                                    f"\n**{new_stat['x']}, {new_stat['y']}**"
                                    f"\n**({(new_stat['x'] - (old_stat['x'])):+.8f}, {(new_stat['y'] - (old_stat['y'])):+.8f})**"
                                )
                            )
                        case "waypoints":
                            content = ""
                            if waypoints_removed := list(set(old_stat) - set(new_stat)):
                                content += "\n### Waypoint(s) Removed ❌"
                                for wp in waypoints_removed:
                                    planet = planets.get(wp)
                                    if planet:
                                        content += f"\n-# - **{planet.names.get('en-GB', planet.name)}**"
                                    else:
                                        content += f"\n-# - **UNKNOWN PLANET**"
                            if waypoints_added := list(set(new_stat) - set(old_stat)):
                                content += "\n### Waypoint(s) Added :white_check_mark:"
                                for wp in waypoints_added:
                                    planet = planets.get(wp)
                                    if planet:
                                        content += f"\n-# - **{planet.names.get('en-GB', planet.name)}**"
                                    else:
                                        content += f"\n-# - **UNKNOWN PLANET**"
                            if waypoints_added or waypoints_removed:
                                self.container_components.append(
                                    ui.TextDisplay(content)
                                )
                        case "max_health":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"**Max health** has changed from:\n**{old_stat:,}** {Emojis.Stratagems.right} **{new_stat:,}** | {(new_stat - old_stat):+,}"
                                )
                            )
                        case "faction":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"**Owner** has changed from:\n{old_stat.emoji} **{old_stat.full_name}** {Emojis.Stratagems.right} **{new_stat.full_name}** {new_stat.emoji}"
                                )
                            )
                        case "regen_perc_per_hour":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"**Regen** has changed from:\n**{old_stat:+.2%}**/hr {Emojis.Stratagems.right} **{new_stat:+.2%}**/hr"
                                )
                            )
                        case "dss_in_orbit":
                            if new_stat == True:
                                self.container_components.append(
                                    ui.TextDisplay(
                                        "DSS is **now in orbit** :white_check_mark:"
                                    )
                                )
                            else:
                                self.container_components.append(
                                    ui.TextDisplay("DSS is **no longer in orbit** ❌")
                                )
                        case "active_effects":
                            if effects_removed := [
                                gwe for gwe in old_stat if gwe not in new_stat
                            ]:
                                text_display = ui.TextDisplay(
                                    f"### Effect(s) __removed__ ❌"
                                )
                                for effect in effects_removed:
                                    gwe_container = GWEContainer(
                                        effect, [], False, False
                                    )
                                    gwe_content = (
                                        "\n"
                                        + gwe_container.components[0].content
                                        + gwe_container.components[1].content
                                        + "\n"
                                    )
                                    text_display.content += gwe_content
                                self.container_components.append(text_display)

                            if effects_added := [
                                gwe for gwe in new_stat if gwe not in old_stat
                            ]:
                                text_display = ui.TextDisplay(
                                    f"### Effect(s) __added__ :white_check_mark:"
                                )
                                for effect in effects_added:
                                    gwe_container = GWEContainer(
                                        effect, [], False, False
                                    )
                                    gwe_content = (
                                        "\n"
                                        + gwe_container.components[0].content
                                        + gwe_container.components[1].content
                                        + "\n"
                                    )
                                    text_display.content += gwe_content
                                self.container_components.append(text_display)
                        case "sector":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"__**Sector has changed**__:\n**{old_stat}** {Emojis.Stratagems.right} **{new_stat}**"
                                )
                            )
                        case _:
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"U - **{api_change.stat_name}** has changed from:\n**{old_stat}** {Emojis.Stratagems.right} **{new_stat}**"
                                )
                            )
                case "Region":
                    if not next(
                        (
                            s
                            for s in self.container_components
                            if s.type == ComponentType.section
                            and api_change.new_object.name in s.children[0].content
                        ),
                        None,
                    ):
                        self.container_components.append(
                            ui.Section(
                                ui.TextDisplay(
                                    f"## Update for {api_change.new_object.emoji} {api_change.new_object.type.name.replace('_', ' ').title()} {api_change.new_object.name} on {api_change.new_object.planet.names.get('en-GB', api_change.new_object.planet.name)}{api_change.new_object.planet.faction.emoji}{api_change.new_object.planet.exclamations}"
                                ),
                                accessory=HDCButton(
                                    label=api_change.new_object.planet.names.get(
                                        "en-GB", api_change.new_object.planet.name
                                    ),
                                    link=f"https://helldiverscompanion.com/#hellpad/planets/{api_change.new_object.planet.index}",
                                ),
                            )
                        )
                    match api_change.property:
                        case "owner":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"**Owner** has changed from:\n{old_stat.emoji} **{old_stat.full_name}** {Emojis.Stratagems.right} **{new_stat.full_name}** {new_stat.emoji}"
                                )
                            )
                        case "max_health":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"**Max health** has changed from:\n**{old_stat:,}** {Emojis.Stratagems.right} **{new_stat:,}** | {(new_stat - old_stat):+,}"
                                )
                            )
                        case "regen_perc_per_hour":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"**Regen** has changed from:\n**{old_stat:+.2%}**/hr {Emojis.Stratagems.right} **{new_stat:+.2%}**/hr"
                                )
                            )
                        case "is_available":
                            if new_stat == True:
                                self.container_components.append(
                                    ui.TextDisplay(
                                        f"Is **now available** :white_check_mark:"
                                    )
                                )
                            else:
                                self.container_components.append(
                                    ui.TextDisplay(f"Is **no longer available** ❌")
                                )
                        case "damage_multiplier":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"Damage multiplier has changed from:\n**{old_stat}x** {Emojis.Stratagems.right} **{new_stat}x**"
                                )
                            )
                        case _:
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"{api_change.stat_name} has changed from:\n**{old_stat}** {Emojis.Stratagems.right} **{new_stat}**"
                                )
                            )
            self.container_components.append(ui.Separator())
        super().__init__(*self.container_components)
