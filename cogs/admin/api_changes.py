from datetime import time
from disnake.ext.commands import Cog
from disnake.ext.tasks import loop
from disnake.ui import Container, Separator, TextDisplay
from utils.api_wrapper.models import GalacticWarEffect
from utils.bot import GalacticWideWebBot
from utils.dataclasses import PlanetFeatures, Subfactions
from utils.embeds import PersonalOrderCommandEmbed
from utils.emojis import Emojis


def gwe_api_change_format(gwe: GalacticWarEffect) -> str:
    content = f"**{gwe.id}** - {gwe.effect_description['simplified_name']}"

    if gwe.name is not None:
        content += f"\n-# Name: {gwe.name}"
    if gwe.short_description is not None:
        content += f"\n-# Short Description: {gwe.short_description}"
    if gwe.long_description is not None:
        content += f"\n-# Longer Description: {gwe.long_description}"
    if gwe.fluff_description is not None:
        content += f"\n-# Fluff Description: {gwe.fluff_description}"
    if gwe.resource is not None:
        content += f"\n-# Resource: {gwe.resource}"

    if (feature := PlanetFeatures.all.get(gwe.id)) is not None:
        content += f"\n-# **{feature.name}** {feature.emoji}"

    if gwe.found_enemy is not None:
        if (
            subfaction := next(
                (
                    sf
                    for sf in Subfactions._all
                    if sf.resource_hash == gwe.resource_hash
                    or sf.token_effect_id == gwe.id
                ),
                None,
            )
        ) is not None:
            content += f"\n-# Enemy: **{subfaction.eng_name}** {subfaction.emoji}"
        else:
            content += f"\n-# Enemy: **{gwe.found_enemy}**"

    if gwe.found_stratagem is not None and gwe.found_stratagem not in content:
        content += f"\n-# Stratagem: **{gwe.found_stratagem}**"

    if gwe.stratagem_category is not None:
        content += f"\n-# Stratagem Category: **{gwe.stratagem_category}**"

    if gwe.found_booster is not None and gwe.found_booster not in content:
        content += f"\n-# Booster: **{gwe.found_booster}**"

    if gwe.count is not None:
        count = "Count" if gwe.effect_type != 32 else "Uses per mission"
        amount = f"{gwe.count}"
        if gwe.count == 0:
            amount = "Infinite"
        content += f"\n-# {count}: **{amount}**"
    if gwe.percent is not None:
        percent = gwe.percent
        match gwe.effect_type:
            case 1 | 72:
                percent -= 100
        content += f"\n-# Percent: **{percent:+,}%**"

    return content


class APIChangesCog(Cog):
    def __init__(self, bot: GalacticWideWebBot) -> None:
        self.bot = bot

    def cog_load(self) -> None:
        if not self.api_changes.is_running():
            self.api_changes.start()
            self.bot.loops.append(self.api_changes)

    def cog_unload(self) -> None:
        if self.api_changes.is_running():
            self.api_changes.cancel()
        if self.api_changes in self.bot.loops:
            self.bot.loops.remove(self.api_changes)

    @loop(
        time=[time(hour=j, minute=i, second=15) for j in range(24) for i in range(60)]
    )
    async def api_changes(self) -> None:
        if not self.bot.ready:
            self.bot.logger.warning("api_changes loop returning - the bot isn't ready")
            return
        if self.bot.data.previous_data is None:
            self.bot.logger.warning(
                "api_changes loop returning - previous data is missing"
            )
            return
        change_components: list[TextDisplay] = []
        current_data = self.bot.data.formatted_data
        previous_data = self.bot.data.previous_data

        # Global Resources
        # New resources
        if (
            new_global_resources := [
                i
                for i in current_data.global_resources
                if i not in previous_data.global_resources
            ]
        ) != []:
            text_display = TextDisplay(
                f"## NEW GLOBAL RESOURCE(S) {Emojis.Decoration.alert_icon}"
            )
            for gr in new_global_resources:
                text_display.content += f"\n```json\n{gr}\n```"
            change_components.append(text_display)

        # Removed resources
        if (
            removed_global_resources := [
                i
                for i in previous_data.global_resources
                if i not in current_data.global_resources
            ]
        ) != []:
            text_display = TextDisplay(
                f"### GLOBAL RESOURCE(S) REMOVED {Emojis.Decoration.alert_icon}"
            )
            for gr in removed_global_resources:
                text_display.content += f"\n```json\n{gr}\n```"
            change_components.append(text_display)

        # Changes to resources
        for gr in [
            i
            for i in current_data.global_resources
            if i in previous_data.global_resources
        ]:
            previous_resource = next(
                (pgr for pgr in previous_data.global_resources if pgr == gr)
            )

            # Galactic resource max value changes
            if gr.max_value != previous_resource.max_value:
                change_components.append(
                    TextDisplay(
                        (
                            f"### {gr.name} MAX AMOUNT CHANGED {Emojis.Decoration.alert_icon}"
                            f"\n-# **{previous_resource.max_value:,}** {Emojis.Stratagems.right} **{gr.max_value:,}**"
                            f"\n-# **{gr.max_value - previous_resource.max_value:+,}**"
                        )
                    )
                )
                change_components.append(text_display)

        # Global Resources END

        # Galactic War Effects
        # New effects
        new_effects = current_data.war_effects.keys() - previous_data.war_effects.keys()
        removed_effects = (
            previous_data.war_effects.keys() - current_data.war_effects.keys()
        )
        common_effects = (
            current_data.war_effects.keys() & previous_data.war_effects.keys()
        )

        if len(new_effects) != 0:
            text_display = TextDisplay(
                f"### NEW GALACTIC EFFECTS ✅ {Emojis.Decoration.alert_icon}"
            )
            for gwe_id in new_effects:
                gwe = current_data.war_effects[gwe_id]
                text_display.content += f"\n\n{gwe_api_change_format(gwe)}"

            change_components.append(text_display)

        # Removed effects
        if len(removed_effects) != 0:
            text_display = TextDisplay(
                f"### REMOVED GALACTIC EFFECTS ❌ {Emojis.Decoration.alert_icon}"
            )
            for gwe_id in removed_effects:
                gwe = current_data.war_effects[gwe_id]
                text_display.content += f"\n\n{gwe_api_change_format(gwe)}"
            change_components.append(text_display)

        # Changes to effects
        for effect_id in common_effects:
            effect = current_data.war_effects[effect_id]
            previous_effect = previous_data.war_effects[effect_id]
            previous_text = gwe_api_change_format(previous_effect)
            current_text = gwe_api_change_format(effect)
            if previous_text != current_text:
                change_components.append(
                    TextDisplay(
                        (
                            f"### EFFECT CHANGED {Emojis.Decoration.alert_icon}"
                            f"\n{previous_text}"
                            f"\n{Emojis.Stratagems.down}"
                            f"\n{current_text}"
                        )
                    )
                )

        # Galactic War Effects END

        # Endpoint Items
        new_items = (
            current_data.organised_items.keys() - previous_data.organised_items.keys()
        )
        removed_items = (
            previous_data.organised_items.keys() - current_data.organised_items.keys()
        )
        common_items = (
            current_data.organised_items.keys() & previous_data.organised_items.keys()
        )

        # New items
        for item_id in new_items:
            item = current_data.organised_items[item_id]
            change_components.append(
                TextDisplay(
                    f"### NEW ITEM ✅ {Emojis.Decoration.alert_icon}"
                    f"\nName: **{item.name or f'Unknown Item {item.mix_id}'}**"
                    f"\n-# Type: **{item.category.name.replace('_', ' ')}**"
                    f"\n-# Required level: **{item.required_level or 'Any'}**"
                )
            )

        # Removed items
        for item_id in removed_items:
            item = previous_data.organised_items[item_id]
            change_components.append(
                TextDisplay(
                    f"### REMOVED ITEM ❌ {Emojis.Decoration.alert_icon}"
                    f"\nName: **{item.name or f'Unknown Item {item.mix_id}'}**"
                    f"\n-# Type: **{item.category.name.replace('_', ' ')}**"
                    f"\n-# Required level: **{item.required_level or 'Any'}**"
                )
            )

        # Changes to items
        for item_id in common_items:
            item = current_data.organised_items[item_id]
            previous_item = previous_data.organised_items[item_id]

            # Item price changes
            if item.buy_price != previous_item.buy_price:
                previous_currencies = (
                    "\n".join(
                        [
                            f"-# **{i[0].name or i[0].mix_id}** x **{i[1]:,}**"
                            for i in previous_item.buy_items
                        ]
                    )
                    or "-# **N/A**"
                )
                new_currencies = (
                    "\n".join(
                        [
                            f"-# **{i[0].name or i[0].mix_id}** x **{i[1]:,}**"
                            for i in item.buy_items
                        ]
                    )
                    or "-# **N/A**"
                )
                change_components.append(
                    TextDisplay(
                        (
                            f"### {item.category.name.replace('_', ' ')} {item.name or item.mix_id} PRICE CHANGED {Emojis.Decoration.alert_icon}"
                            f"\n{previous_currencies}"
                            f"\n{Emojis.Stratagems.down}"
                            f"\n{new_currencies}"
                        )
                    )
                )

            # Item required level changes
            if item.required_level != previous_item.required_level:
                change_components.append(
                    TextDisplay(
                        (
                            f"### {item.category.name.replace('_', ' ')} {item.name or item.mix_id} REQUIRED LEVEL CHANGED {Emojis.Decoration.alert_icon}"
                            f"\n-# Level **{previous_item.required_level}**"
                            f"\n{Emojis.Stratagems.down}"
                            f"\n-# Level **{item.required_level}**"
                        )
                    )
                )

        # Endpoint Items END

        # Assignments
        for assignment in current_data.assignments.get("en", []):
            previous_assignment = next(
                (
                    a
                    for a in previous_data.assignments.get("en", [])
                    if a.id == assignment.id
                ),
                None,
            )
            if previous_assignment is None:
                continue

            # Assignment rewards changes
            if assignment.rewards != previous_assignment.rewards:
                prev_rewards = "\n".join([f"{i}" for i in previous_assignment.rewards])
                curr_rewards = "\n".join([f"{i}" for i in assignment.rewards])
                change_components.append(
                    TextDisplay(
                        (
                            f"### CHANGE TO '{assignment.title}' REWARD(S) {Emojis.Decoration.alert_icon}"
                            f"\n-# **{prev_rewards}**"
                            f"\n{Emojis.Stratagems.down}"
                            f"\n-# **{curr_rewards}**"
                        )
                    )
                )

            # Task changes
            for index, (prev_task, curr_task) in enumerate(
                zip(previous_assignment.tasks, assignment.tasks), start=1
            ):
                # Task target amount changes
                if prev_task.target != curr_task.target:
                    change_components.append(
                        TextDisplay(
                            (
                                f"### CHANGE TO TARGET OF TASK #{index} FOR '{assignment.title}' {Emojis.Decoration.alert_icon}"
                                f"\n-# **{prev_task.target:,}** {Emojis.Stratagems.right} **{curr_task.target:,}**"
                                f"\n-# {(curr_task.target - prev_task.target):+,}"
                            )
                        )
                    )

        # Assignments END

        # Personal Assignments
        # PO change
        if (
            self.bot.data.previous_data.personal_order
            and self.bot.data.formatted_data.personal_order
        ):
            if (
                self.bot.data.previous_data.personal_order.id
                != self.bot.data.formatted_data.personal_order.id
            ):
                old_po_text = (
                    PersonalOrderCommandEmbed(
                        self.bot.data.previous_data.personal_order,
                        self.bot.json_dict,
                    )
                    .fields[0]
                    .name
                )
                new_po_text = (
                    PersonalOrderCommandEmbed(
                        self.bot.data.formatted_data.personal_order,
                        self.bot.json_dict,
                    )
                    .fields[0]
                    .name
                )
                change_components.append(
                    TextDisplay(
                        (
                            f"### PERSONAL ORDER CHANGED"
                            f"\n-# {old_po_text}"
                            f"\n{Emojis.Stratagems.down}"
                            f"\n-# {new_po_text}"
                        )
                    )
                )

        # Personal Assignments END

        # Planets
        new_planets = current_data.planets.keys() - previous_data.planets.keys()
        removed_planets = previous_data.planets.keys() - current_data.planets.keys()
        common_planets = current_data.planets.keys() & previous_data.planets.keys()

        # New planets
        for planet_index in new_planets:
            planet = current_data.planets[planet_index]
            change_components.append(
                TextDisplay(
                    (
                        f"### NEW PLANET '{planet.name}' {Emojis.Decoration.alert_icon} {planet.exclamations}"
                    )
                )
            )

        # Removed planets
        for planet_index in removed_planets:
            planet = previous_data.planets[planet_index]
            change_components.append(
                TextDisplay(
                    (
                        f"### REMOVED PLANET '{planet.name}' {Emojis.Decoration.alert_icon} {planet.exclamations}"
                    )
                )
            )

        # Planet changes
        for planet_id in common_planets:
            planet = current_data.planets[planet_id]
            previous_planet = previous_data.planets[planet_id]
            planet_change_text = f"## CHANGES ON {planet.name} {planet.faction.emoji}{planet.exclamations}"
            planet_changes_present = False

            # Planet movement
            if planet.position != previous_planet.position:
                planet_change_text += (
                    "\n### Planet has __**moved**__"
                    f"\n-# **{previous_planet.position['x']}, {previous_planet.position['y']}**"
                    f"\n{Emojis.Stratagems.down}"
                    f"\n-# **{planet.position['x']}, {planet.position['y']}**"
                    f"\n-# ({(planet.position['x'] - (previous_planet.position['x'])):+.8f}, {(planet.position['y'] - (previous_planet.position['y'])):+.8f})"
                )
                planet_changes_present = True

            # Planet waypoint changes
            if planet.waypoints != previous_planet.waypoints:
                planet_change_text += "\n### Waypoint Changes"
                for waypoint in previous_planet.waypoints:
                    way_planet = current_data.planets.get(waypoint)
                    way_planet_name = (
                        way_planet.name
                        if way_planet is not None
                        else f"Unknown Planet #{waypoint}"
                    )
                    if waypoint in planet.waypoints:
                        planet_change_text += f"\n{way_planet_name}"
                    else:
                        planet_change_text += f"\n-# ~~{way_planet_name}~~"

                for waypoint in planet.waypoints:
                    way_planet = current_data.planets.get(waypoint)
                    way_planet_name = (
                        way_planet.name
                        if way_planet is not None
                        else f"Unknown Planet #{waypoint}"
                    )
                    if waypoint not in previous_planet.waypoints:
                        planet_change_text += f"\n-# **++{way_planet_name}**"
                planet_changes_present = True

            # Planet max health changes
            if planet.max_health != previous_planet.max_health:
                planet_change_text += (
                    "\n### **Max health** has changed:"
                    f"\n-# **{previous_planet.max_health:,}** {Emojis.Stratagems.right} **{planet.max_health:,}**"
                    f"\n-# ({(planet.max_health - previous_planet.max_health):+,})"
                )
                planet_changes_present = True

            # Planet faction changes
            if planet.faction != previous_planet.faction:
                planet_change_text += (
                    "\n### **Owner** has changed:"
                    f"\n{previous_planet.faction.emoji} {Emojis.Stratagems.right} {planet.faction.emoji}"
                )
                planet_changes_present = True

            # Planet regen changes
            if planet.regen_perc_per_hour != previous_planet.regen_perc_per_hour:
                planet_change_text += (
                    "\n### **Regen** has changed:"
                    f"\n-# **{previous_planet.regen_perc_per_hour:+.2%}**/hr {Emojis.Stratagems.right} **{planet.regen_perc_per_hour:+.2%}**/hr"
                    f"\n-# ({planet.regen_perc_per_hour - previous_planet.regen_perc_per_hour:+.2%})"
                )
                planet_changes_present = True

            # Planet DSS presence changes
            if planet.dss_in_orbit and not previous_planet.dss_in_orbit:
                planet_change_text += "\n### DSS is **now in orbit** ✅"
                planet_changes_present = True
            elif previous_planet.dss_in_orbit and not planet.dss_in_orbit:
                planet_change_text += "\n### DSS is **no longer in orbit** ❌"
                planet_changes_present = True

            # Planet effects
            new_effects = planet.effect_ids - previous_planet.effect_ids
            removed_effects = previous_planet.effect_ids - planet.effect_ids

            # New planet effects
            if new_effects != set():
                planet_change_text += "\n### Effect(s) __added__ ✅"
                for effect_id in new_effects:
                    new_effect = current_data.war_effects[effect_id]
                    planet_change_text += f"\n{gwe_api_change_format(new_effect)}\n"
                planet_changes_present = True

            # Removed planet effects
            if removed_effects != set():
                planet_change_text += "\n### Effect(s) __removed__ ❌"
                for effect_id in removed_effects:
                    previous_effect = previous_data.war_effects[effect_id]
                    planet_change_text += (
                        f"\n{gwe_api_change_format(previous_effect)}\n"
                    )
                planet_changes_present = True

            # Planet sector changes
            if planet.sector != previous_planet.sector:
                planet_change_text += (
                    f"\n### __**Sector has changed**__:"
                    f"\n-# **{previous_planet.sector}** {Emojis.Stratagems.right} **{planet.sector}**"
                )
                planet_changes_present = True

            # Planet region presence changes
            if planet.regions != previous_planet.regions:
                planet_change_text += "\n### Region Changes"
                for index, region in previous_planet.regions.items():
                    curr_region = planet.regions.get(index)
                    curr_region_name = (
                        curr_region.name
                        if curr_region is not None
                        else f"Unknown Region #{index}"
                    )
                    if index in planet.regions:
                        planet_change_text += f"\n{curr_region_name}"
                    else:
                        planet_change_text += f"\n-# ~~{curr_region_name}~~"

                for index, region in planet.regions.items():
                    curr_region = planet.regions.get(index)
                    curr_region_name = (
                        curr_region.name
                        if curr_region is not None
                        else f"Unknown Region #{index}"
                    )
                    if index not in previous_planet.regions:
                        planet_change_text += f"\n**++{curr_region_name}**"
                planet_changes_present = True

            # Planet name changes
            if planet.name != previous_planet.name:
                planet_change_text += (
                    f"\n### __**Name has changed**__:"
                    f"\n-# **{previous_planet.name}** {Emojis.Stratagems.right} **{planet.name}**"
                )
                planet_changes_present = True

            # Planet alt name changes
            if planet.alt_name != previous_planet.alt_name:
                planet_change_text += (
                    f"\n### __**Alternative name has changed**__:"
                    f"\n-# **{previous_planet.alt_name}** {Emojis.Stratagems.right} **{planet.alt_name}**"
                )
                planet_changes_present = True

            # Planet alt biome changes
            if planet.alt_biome != previous_planet.alt_biome:
                planet_change_text += (
                    f"\n### __**Alternative biome has changed**__:"
                    f"\n-# **{previous_planet.alt_biome}** {Emojis.Stratagems.right} **{planet.alt_biome}**"
                )
                planet_changes_present = True

            # Region changes
            for id, region in planet.regions.items():
                previous_region = previous_planet.regions.get(id)
                if previous_region is None:
                    continue
                region_changes_text = (
                    f"\n## REGION {region.name} {region.emoji} {region.owner.emoji}"
                )
                region_changes_present = False

                # Region owner changes
                if region.owner != previous_region.owner:
                    region_changes_text += (
                        f"\n### **Owner has changed**:"
                        f"\n{previous_region.owner.emoji} {Emojis.Stratagems.right} {region.owner.emoji}"
                    )
                    region_changes_present = True

                # Region type changes
                if region.type != previous_region.type:
                    prev_type = (
                        f"Class {previous_region.size} Megafactory"
                        if previous_region.is_factory
                        else previous_region.type.name.replace("_", " ")
                    )
                    curr_type = (
                        f"Class {region.size} Megafactory"
                        if region.is_factory
                        else region.type.name.replace("_", " ")
                    )
                    region_changes_text += (
                        f"\n### __**Type has changed**__:"
                        f"\n{previous_region.emoji} **{prev_type}**"
                        f"\n{Emojis.Stratagems.down}"
                        f"\n{region.emoji} **{curr_type}**"
                    )
                    region_changes_present = True

                # Region regen changes
                if region.regen_perc_per_hour != previous_region.regen_perc_per_hour:
                    region_changes_text += (
                        f"\n### **Regen has changed**:"
                        f"\n**{previous_region.regen_perc_per_hour:.2%}** {Emojis.Stratagems.right} **{region.regen_perc_per_hour:.2%}**"
                        f"\n-# ({region.regen_perc_per_hour - previous_region.regen_perc_per_hour:+.2%})"
                    )
                    region_changes_present = True

                # Region availability changes
                if region.is_available != previous_region.is_available:
                    region_changes_text += "\n### Availability change"
                    if region.is_available:
                        region_changes_text += "\nIs **now available** ✅"
                    else:
                        region_changes_text += "\nIs **no longer available** ❌"
                    region_changes_present = True

                # Region damage multiplier changes
                if region.damage_multiplier != previous_region.damage_multiplier:
                    region_changes_text += (
                        f"\n### Damage multiplier has changed:"
                        f"\n**{previous_region.damage_multiplier:.2}x** {Emojis.Stratagems.right} **{region.damage_multiplier}x**"
                        f"\n-# ({region.damage_multiplier - previous_region.damage_multiplier:+.2}x)"
                    )
                    region_changes_present = True

                if region_changes_present:
                    planet_changes_present = True
                    planet_change_text += region_changes_text

            if planet_changes_present:
                change_components.extend([TextDisplay(planet_change_text), Separator()])

        # Control Center
        eng_curr_cc = current_data.control_centre.get("en")
        eng_prev_cc = previous_data.control_centre.get("en")
        if None not in (eng_curr_cc, eng_prev_cc):
            for episode in eng_curr_cc.episodes:
                previous_episode = next(
                    (pep for pep in eng_prev_cc.episodes if pep.id == episode.id), None
                )

                # New campaigns
                if previous_episode is None:
                    change_components.append(
                        TextDisplay(
                            (
                                f"### NEW CAMPAIGN '{episode.title}' {episode.faction.emoji}{Emojis.Decoration.alert_icon}"
                                f"\n-# {episode.description}"
                            )
                        )
                    )
                    continue

                # Campaign faction changes
                if episode.faction != previous_episode.faction:
                    change_components.append(
                        TextDisplay(
                            (
                                f"### CAMPAIGN '{episode.title}' FACTION CHANGE {episode.faction.emoji}{Emojis.Decoration.alert_icon}"
                                f"\n{previous_episode.faction.emoji} {Emojis.Stratagems.right} {episode.faction.emoji}"
                            )
                        )
                    )

                # Campaign status changes
                if episode.status != previous_episode.status:
                    change_components.append(
                        TextDisplay(
                            (
                                f"### CAMPAIGN '{episode.title}' STATUS CHANGE {episode.faction.emoji}"
                                f"\n**{previous_episode.status.name.replace('_', ' ')}** {Emojis.Stratagems.right} **{episode.status.name.replace('_', ' ')}**"
                            )
                        )
                    )

                # Removed phases
                if (
                    removed_phases := [
                        p for p in previous_episode.phases if p not in episode.phases
                    ]
                ) != []:
                    removed_phases_text = "\n".join(
                        [
                            (
                                f"**{p.outro_title or p.intro_title}**"
                                f"\n-# Reward(s): `{p.rewards}`"
                            )
                            for p in removed_phases
                        ]
                    )
                    change_components.append(
                        TextDisplay(
                            (
                                f"### PHASES REMOVED FROM CAMPAIGN '{episode.title}' {episode.faction.emoji}{Emojis.Decoration.alert_icon}"
                                f"\n{removed_phases_text}"
                            )
                        )
                    )

                # Campaign Phase presence changes
                # New phases
                if (
                    new_phases := [
                        p for p in episode.phases if p not in previous_episode.phases
                    ]
                ) != []:
                    new_phases_text = "\n".join(
                        [
                            (f"**{p.intro_title}**" f"\n-# Reward(s): `{p.rewards}`")
                            for p in new_phases
                        ]
                    )
                    change_components.append(
                        TextDisplay(
                            (
                                f"### CAMPAIGN '{episode.title}' HAS NEW PHASE(S) {episode.faction.emoji}{Emojis.Decoration.alert_icon}"
                                f"\n{new_phases_text}"
                            )
                        )
                    )

                # Phase changes
                for phase in [
                    p for p in episode.phases if p in previous_episode.phases
                ]:
                    previous_phase = next(
                        (pp for pp in previous_episode.phases if pp.id == phase.id),
                        None,
                    )

                    # Phase status changes
                    if phase.status != previous_phase.status:
                        change_components.append(
                            TextDisplay(
                                (
                                    f"### PHASE '{phase.intro_title}' STATUS CHANGE"
                                    f"\n**{previous_phase.status.name.replace('_', ' ')}** {Emojis.Stratagems.right} **{phase.status.name.replace('_', ' ')}**"
                                )
                            )
                        )

                    # Phase entries changes
                    if phase.entries != previous_phase.entries:
                        change_components.append(
                            TextDisplay(
                                (
                                    f"### PHASE '{phase.intro_title}' ENTRIES CHANGE {Emojis.Decoration.alert_icon}"
                                    f"\n**{previous_phase.entries}**"
                                    f"\n{Emojis.Stratagems.down}"
                                    f"\n**{phase.entries}**"
                                )
                            )
                        )

                    # Phase rewards changes
                    if phase.rewards != previous_phase.rewards:
                        change_components.append(
                            TextDisplay(
                                (
                                    f"### PHASE '{phase.intro_title}' REWARDS CHANGE {Emojis.Decoration.alert_icon}"
                                    f"\n**{previous_phase.rewards}**"
                                    f"\n{Emojis.Stratagems.down}"
                                    f"\n**{phase.rewards}**"
                                )
                            )
                        )

                # Campaign Reward changes
                if episode.rewards != previous_episode.rewards:
                    change_components.append(
                        TextDisplay(
                            (
                                f"### CAMPAIGN '{phase.intro_title}' REWARDS CHANGE {Emojis.Decoration.alert_icon}"
                                f"\n**{previous_episode.rewards}**"
                                f"\n{Emojis.Stratagems.down}"
                                f"\n**{episode.rewards}**"
                            )
                        )
                    )

        # warbonds
        for id, warbond in current_data.warbonds.items():
            if id not in previous_data.warbonds:
                change_components.append(
                    TextDisplay(
                        f"### NEW WARBOND {Emojis.Decoration.alert_icon}"
                        f"\n-# ID: **{warbond.id}**"
                        f"\n-# Pages: **{len(warbond.pages)}**"
                        f"\n-# Total cost: **{warbond.total_cost:,} Medals**"
                        f"\n-# Cost per page: {' / '.join([str(sum([i.cost for i in p.items])) for p in warbond.pages])}"
                    )
                )

        if change_components != []:
            chunked_changes = [
                change_components[i : i + 5]
                for i in range(0, len(change_components), 5)
            ]
            for chunk in chunked_changes:
                container = Container(*chunk)
                msg = await self.bot.channels.api_changes_channel.send(
                    components=container
                )
                await msg.publish()
            self.bot.logger.info(
                f"api_changes loop - sent out api changes for {len(change_components)} total change(s)"
            )

    @api_changes.before_loop
    async def before_api_changes(self):
        await self.bot.wait_until_ready()

    @api_changes.error
    async def api_changes_error(self, error: Exception) -> None:
        error_handler = self.bot.get_cog("ErrorHandlerCog")
        if error_handler:
            await error_handler.log_error(None, error, "api_changes loop")


def setup(bot: GalacticWideWebBot):
    bot.add_cog(APIChangesCog(bot))
