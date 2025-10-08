from disnake import ui
from utils.dataclasses import APIChanges
from utils.emojis import Emojis
from utils.interactables import HDCButton
from utils.mixins import ReprMixin


# DOESNT NEED LOCALIZATION
class APIChangesContainer(ui.Container, ReprMixin):
    def __init__(self, api_changes: list[APIChanges]) -> None:
        self.container_components: list = []

        for api_change in api_changes:
            if api_change.stat_source not in [
                "Global Resources",
                "Galactic War Effects",
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
                        for gwe in api_change.old_object
                        if gwe not in api_change.new_object
                    ]:
                        content += "\n### Galactic Effects Removed ❌"
                        for gwe in effects_removed:
                            content += f"\n {gwe.pretty_print()}"
                    if effects_added := [
                        gwe
                        for gwe in api_change.new_object
                        if gwe not in api_change.old_object
                    ]:
                        content += "\n### Galactic Effects Added :white_check_mark:"
                        for gwe in effects_added:
                            content += f"\n {gwe.pretty_print()}"
                    if effects_removed or effects_added:
                        self.container_components.append(ui.TextDisplay(content))
                case "Planet":
                    self.container_components.append(
                        ui.Section(
                            ui.TextDisplay(
                                f"## Update to **{api_change.new_object.name}** {api_change.new_object.faction.emoji}{api_change.new_object.exclamations}"
                            ),
                            accessory=HDCButton(
                                label=api_change.new_object.name,
                                link=f"https://helldiverscompanion.com/#hellpad/planets/{api_change.new_object.index}",
                            ),
                        )
                    )
                    match api_change.property:
                        case "location":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"Planet has moved from:\n**{old_stat}** {Emojis.Stratagems.right} **{new_stat}**"
                                )
                            )
                        case "waypoints":
                            if waypoints_removed := [
                                wp for wp in old_stat if wp not in new_stat
                            ]:
                                content = "### Waypoiint(s) Removed ❌"
                                for wp in waypoints_removed:
                                    content += f"\n -# - **{wp}**"
                            if waypoints_added := [
                                wp for wp in old_stat if wp not in new_stat
                            ]:
                                content = "### Waypoiint(s) Added :white_check_mark:"
                                for wp in waypoints_added:
                                    content += f"\n -# - **{wp}**"
                            if waypoints_added or waypoints_removed:
                                self.container_components.append(
                                    ui.TextDisplay(content)
                                )
                        case "max_health":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"Max health has changed from:\n**{old_stat:,}** {Emojis.Stratagems.right} **{new_stat:,}**"
                                )
                            )
                        case "faction":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"Owner has changed from:\n**{old_stat.full_name}** {old_stat.emoji} {Emojis.Stratagems.right} **{new_stat.full_name}** {old_stat.emoji}"
                                )
                            )
                        case "regen_perc_per_hour":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"Regen has changed from:\n**{old_stat:.2%}** {Emojis.Stratagems.right} **{new_stat:.2%}**"
                                )
                            )
                        case "dss_in_orbit":
                            if new_stat == True:
                                self.container_components.append(
                                    ui.TextDisplay(f"-# DSS is **now in orbit**")
                                )
                            else:
                                self.container_components.append(
                                    ui.TextDisplay(f"-# DSS is **no longer in orbit**")
                                )
                        case "active_effects":
                            if effects_removed := [
                                gwe for gwe in old_stat if gwe not in new_stat
                            ]:
                                for gwe in effects_removed:
                                    self.container_components.append(
                                        ui.TextDisplay(
                                            f"### Effect __removed__ ❌\n{gwe.pretty_print()}"
                                        )
                                    )

                            if effects_added := [
                                gwe for gwe in new_stat if gwe not in old_stat
                            ]:
                                for gwe in effects_added:
                                    self.container_components.append(
                                        ui.TextDisplay(
                                            f"### Effect __added__ :white_check_mark:\n{gwe.pretty_print()}"
                                        )
                                    )
                case "Region":
                    self.container_components.append(
                        ui.TextDisplay(
                            f"## Update for {api_change.new_object.emoji} {api_change.new_object.type} {api_change.new_object.name} on {api_change.new_object.planet.name}{api_change.new_object.planet.faction.emoji}{api_change.new_object.planet.exclamations}"
                        )
                    )
                    match api_change.property:
                        case "owner":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"Owner has changed from:\n**{old_stat.full_name}** {old_stat.emoji} {Emojis.Stratagems.right} **{new_stat.full_name}** {new_stat.emoji}"
                                )
                            )
                        case "max_health":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"Region's max health has changed from:\n**{old_stat:,}** {Emojis.Stratagems.right} **{new_stat:,}**"
                                )
                            )
                        case "regen_perc_per_hour":
                            self.container_components.append(
                                ui.TextDisplay(
                                    f"Region's regen has changed from:\n**{old_stat:.2%}** {Emojis.Stratagems.right} **{new_stat:.2%}**"
                                )
                            )
                        case "is_available":
                            if new_stat == True:
                                self.container_components.append(
                                    ui.TextDisplay(
                                        f"Region is **now available** :white_check_mark:"
                                    )
                                )
                            else:
                                self.container_components.append(
                                    ui.TextDisplay(
                                        f"Region is **no longer available** ❌"
                                    )
                                )
            self.container_components.append(ui.Separator())
        super().__init__(*self.container_components)
