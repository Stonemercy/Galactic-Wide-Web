from datetime import datetime, timedelta
from utils.dataclasses import CalculatedEndTime


def get_end_time(source_planet, gambit_planets: dict[int] = {}) -> CalculatedEndTime:
    results = CalculatedEndTime()

    if not source_planet.tracker or source_planet.tracker.change_rate_per_hour <= 0:
        return results

    if source_planet.event:
        # Regular defence win
        if source_planet.tracker.complete_time < source_planet.event.end_time_datetime:
            results.source_planet = source_planet
            results.end_time = source_planet.tracker.complete_time

        # Gambit win
        if source_planet.index in gambit_planets:
            gambit_planet = gambit_planets[source_planet.index]
            way_planet_end_time_info = get_end_time(gambit_planet)
            if way_planet_end_time_info.end_time:
                if (
                    not results.end_time
                    and way_planet_end_time_info.end_time
                    < source_planet.event.end_time_datetime
                ) or (
                    results.end_time
                    and way_planet_end_time_info.end_time < results.end_time
                ):
                    results.clear()
                    results.gambit_planet = gambit_planet
                    results.end_time = way_planet_end_time_info.end_time

        non_lib_regions = sorted(
            [
                r
                for r in source_planet.regions.values()
                if r.owner.full_name != "Humans"
            ],
            key=lambda x: x.availability_factor,
        )
        if non_lib_regions:
            regions = []
            region_rates = [
                r.tracker.change_rate_per_hour * r.max_health
                for r in non_lib_regions
                if r.tracker and r.tracker.change_rate_per_hour > 0
            ]
            average_hp_per_hour = (
                sum(region_rates) / len(region_rates) if region_rates else 0
            )
            current_perc = source_planet.event.progress
            hours_from_now = 0
            if average_hp_per_hour > 0:
                for index, region in enumerate(non_lib_regions):
                    est_rate_pct = (
                        (average_hp_per_hour / region.max_health)
                        if not (
                            region.tracker and region.tracker.change_rate_per_hour > 0
                        )
                        else region.tracker.change_rate_per_hour
                    )
                    est_lib_time = (
                        ((1 - region.perc) / est_rate_pct)
                        if region.is_available
                        else (1 / est_rate_pct)
                    )
                    planet_health_at_region_lib = current_perc + (
                        source_planet.tracker.change_rate_per_hour * est_lib_time
                    )
                    if planet_health_at_region_lib > 1:
                        # if planet is liberated before region
                        time_until_lib = (
                            1 - current_perc
                        ) / source_planet.tracker.change_rate_per_hour
                        hours_from_now += time_until_lib
                        current_perc = 1
                        break
                    elif planet_health_at_region_lib + region.planet_damage_perc > 1:
                        # if region lib would cap planet
                        current_perc = (
                            planet_health_at_region_lib + region.planet_damage_perc
                        )
                        hours_from_now += est_lib_time
                        regions.append(region)
                        break
                    else:
                        # if region is liberated before planet
                        current_perc = (
                            planet_health_at_region_lib + region.planet_damage_perc
                        )
                        hours_from_now += est_lib_time
                        regions.append(region)
                        if region != non_lib_regions[-1]:
                            next_region = non_lib_regions[index + 1]
                            next_avail = next_region.availability_factor
                            event_duration = (
                                source_planet.event.end_time_datetime
                                - source_planet.event.start_time_datetime
                            ).total_seconds()
                            elapsed_time = (
                                (datetime.now() + timedelta(hours=hours_from_now))
                                - source_planet.event.start_time_datetime
                            ).total_seconds()
                            target_duration = event_duration * next_avail
                            time_until_in_sec = target_duration - elapsed_time
                            clamped_hours_until = max(0, time_until_in_sec / 3600)
                            hours_from_now += clamped_hours_until
                            current_perc += (
                                clamped_hours_until
                            ) * source_planet.tracker.change_rate_per_hour

                if current_perc < 1:
                    hours_from_now += (
                        1 - current_perc
                    ) / source_planet.tracker.change_rate_per_hour
                end_time = datetime.now() + timedelta(hours=hours_from_now)
                if results.end_time and end_time < results.end_time:
                    results.clear()
                    results.end_time = end_time
                    results.regions = regions
                elif not results.end_time:
                    results.end_time = end_time
                    results.regions = regions

            else:
                results.source_planet = source_planet
                results.end_time = source_planet.tracker.complete_time
    else:
        non_lib_regions = sorted(
            [
                r
                for r in source_planet.regions.values()
                if r.owner.full_name != "Humans"
            ],
            key=lambda x: x.availability_factor,
        )
        if non_lib_regions:
            regions = []
            region_rates = [
                r.tracker.change_rate_per_hour * r.max_health
                for r in non_lib_regions
                if r.tracker and r.tracker.change_rate_per_hour > 0
            ]
            average_hp_per_hour = (
                sum(region_rates) / len(region_rates) if region_rates else 0
            )
            current_perc = 1 - source_planet.health_perc
            hours_from_now = 0
            if average_hp_per_hour > 0:
                for index, region in enumerate(non_lib_regions):
                    est_rate_pct = (
                        average_hp_per_hour / region.max_health
                        if not (
                            region.tracker and region.tracker.change_rate_per_hour > 0
                        )
                        else region.tracker.change_rate_per_hour
                    )
                    est_lib_time = (
                        ((1 - region.perc) / est_rate_pct)
                        if region.is_available
                        else (1 / est_rate_pct)
                    )
                    planet_health_at_region_lib = current_perc + (
                        source_planet.tracker.change_rate_per_hour * est_lib_time
                    )
                    if planet_health_at_region_lib > 1:
                        # if planet is liberated before region
                        time_until_lib = (
                            1 - current_perc
                        ) / source_planet.tracker.change_rate_per_hour
                        hours_from_now += time_until_lib
                        current_perc = 1
                        break
                    elif planet_health_at_region_lib + region.planet_damage_perc > 1:
                        # if region lib would cap planet
                        current_perc = (
                            planet_health_at_region_lib + region.planet_damage_perc
                        )
                        hours_from_now += est_lib_time
                        regions.append(region)
                        break
                    else:
                        # if region is liberated before planet
                        current_perc = (
                            planet_health_at_region_lib + region.planet_damage_perc
                        )
                        hours_from_now += est_lib_time
                        regions.append(region)

                if current_perc < 1:
                    hours_from_now += (
                        1 - current_perc
                    ) / source_planet.tracker.change_rate_per_hour
                end_time = datetime.now() + timedelta(hours=hours_from_now)
                results.regions = regions
                results.end_time = end_time
        else:
            if source_planet.tracker.change_rate_per_hour > 0:
                results.source_planet = source_planet
                results.end_time = source_planet.tracker.complete_time

    return results
