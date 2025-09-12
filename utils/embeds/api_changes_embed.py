from disnake import Colour, Embed
from utils.data import GalacticWarEffect
from utils.dataclasses import APIChanges
from utils.emojis import Emojis
from utils.mixins import EmbedReprMixin


class APIChangesEmbed(Embed, EmbedReprMixin):
    def __init__(self, total_changes: list[APIChanges]):
        super().__init__(title="New changes in the API!", colour=Colour.brand_red())
        for change in total_changes:
            faction_emoji = (
                getattr(Emojis.Factions, change.planet.current_owner.full_name.lower())
                if not change.planet.event
                else getattr(
                    Emojis.Factions, change.planet.event.faction.full_name.lower()
                )
            )
            match change.statistic:
                case "Regen %":
                    self.add_field(
                        f"{faction_emoji} {change.planet.name}",
                        f"Planet Regeneration: **{change.before:.2%}**/hr {Emojis.Stratagems.right} **{change.after:.2%}**/hr",
                        inline=False,
                    )
                case "Max Health":
                    self.add_field(
                        f"{faction_emoji} {change.planet.name}",
                        f"Max Health: **{change.before}** {Emojis.Stratagems.right} **{change.after}**",
                        inline=False,
                    )
                case "Waypoints":
                    desctiption = "Waypoints:"
                    waypoints_removed = [
                        waypoint
                        for waypoint in change.before
                        if waypoint not in change.after
                    ]
                    waypoints_added = [
                        waypoint
                        for waypoint in change.after
                        if waypoint not in change.before
                    ]
                    if waypoints_removed:
                        wp_list = "\n  - ".join(waypoints_removed)
                        desctiption += f"\n- Removed:\n  - {wp_list}"
                    if waypoints_added:
                        wp_list = "\n  - ".join(waypoints_added)
                        desctiption += f"\n- Added:\n  - {wp_list}"
                    self.add_field(
                        f"{faction_emoji} {change.planet.name}",
                        desctiption,
                        inline=False,
                    )
                case "Location":
                    if change.planet.index == 64:
                        self.title = "Meridia has moved"
                        self.set_thumbnail(
                            url="https://cdn.discordapp.com/emojis/1331357764039086212.webp?size=96"
                        )
                    description = f"Location:\n{change.before} {Emojis.Stratagems.right} {change.after}"
                    description += f"\nChange: ({change.after[0] - change.before[0]:+.8f}, {change.after[1] - change.before[1]:+.8f})"
                    self.add_field(
                        f"{faction_emoji} {change.planet.name}",
                        description,
                        inline=False,
                    )
                case "Effects":
                    removed_effects: list[GalacticWarEffect] = [
                        effect
                        for effect in change.before
                        if effect.id not in [e.id for e in change.after]
                    ]
                    new_effects: list[GalacticWarEffect] = [
                        effect
                        for effect in change.after
                        if effect.id not in [e.id for e in change.before]
                    ]
                    for effect in removed_effects:
                        description_fmtd = (
                            f"\n-# {effect.planet_effect['description']}"
                            if effect.planet_effect["description"] != ""
                            else ""
                        )
                        self.add_field(
                            f"{faction_emoji} {change.planet.name} Removed effect",
                            f"**{effect.id}** - {effect.planet_effect['name']}{description_fmtd}",
                            inline=False,
                        )
                    for effect in new_effects:
                        description_fmtd = (
                            f"\n-# {effect.planet_effect['description']}"
                            if effect.planet_effect["description"] != ""
                            else ""
                        )
                        self.add_field(
                            f"{faction_emoji} {change.planet.name} New effect",
                            f"**{effect.id}** - {effect.planet_effect['name']}{description_fmtd}",
                            inline=False,
                        )
                case "Galactic Impact Mod":
                    self.add_field(
                        "Big jump in the Galactic Impact Modifier :warning:",
                        f"Before: {change.before}\nAfter: {change.after}\n-# Change: {change.before - change.after:+}",
                        inline=False,
                    )
                case "Region Regen":
                    self.add_field(
                        f"{faction_emoji} {change.planet.name} - Region: {change.after.name}",
                        f"Region Regeneration: **{change.before.regen_per_hour:.2f}**%/hr {Emojis.Stratagems.right} **{change.after.regen_per_hour:.2f}**%/hr",
                        inline=False,
                    )
                case "Planet Owner":
                    self.add_field(
                        f"{faction_emoji} {change.planet.name}",
                        f"Planet Owner: **{change.before.full_name}** {Emojis.Stratagems.right} **{change.after.full_name}**",
                        inline=False,
                    )
