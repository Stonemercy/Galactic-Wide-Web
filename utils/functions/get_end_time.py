from datetime import datetime, timedelta
from utils.dataclasses import CalculatedEndTime


def get_end_time(source_planet, gambit_planets: dict[int] = {}) -> CalculatedEndTime:
    results = CalculatedEndTime()

    if not source_planet.tracker or source_planet.tracker.change_rate_per_hour <= 0:
        return results

    if source_planet.event:
        if source_planet.tracker.complete_time < source_planet.event.end_time_datetime:
            results.source_planet = source_planet
            results.end_time = source_planet.tracker.complete_time

        if source_planet.index in gambit_planets and not results.end_time:
            gambit_planet = gambit_planets[source_planet.index]
            end_time_info = get_end_time(gambit_planet)
            if (
                end_time_info.end_time
                and end_time_info.end_time < source_planet.event.end_time_datetime
            ):
                results.gambit_planet = gambit_planet
                results.end_time = end_time_info.end_time

        non_lib_regions = sorted(
            [
                r
                for r in source_planet.regions.values()
                if r.owner.full_name != "Humans"
            ],
            key=lambda x: x.availability_factor,
        )
        if non_lib_regions and not results.end_time:
            results.regions = []
            region_rates = [
                r.tracker.change_rate_per_hour / r.size
                for r in non_lib_regions
                if r.tracker and r.tracker.change_rate_per_hour > 0
            ]
            average_region_rate = (
                (sum(region_rates) / len(region_rates)) if region_rates != [] else 0
            )
            current_perc = source_planet.event.progress
            hours_from_now = 0
            if average_region_rate != 0:
                for index, region in enumerate(non_lib_regions):
                    est_lib_time = (
                        ((1 - region.perc) / (average_region_rate * region.size))
                        if region.is_available
                        else (1 / (average_region_rate * region.size))
                    )
                    planet_health_at_region_lib = current_perc + (
                        source_planet.tracker.change_rate_per_hour * est_lib_time
                    )
                    if planet_health_at_region_lib < 1:
                        # if region is liberated before planet
                        current_perc = (
                            planet_health_at_region_lib + region.planet_damage_perc
                        )
                        hours_from_now += est_lib_time
                        results.regions.append(region)
                    else:
                        # if planet is liberated before region
                        if region != non_lib_regions[-1]:
                            next_region_availability = non_lib_regions[
                                index + 1
                            ].availability_factor
                            next_stage_hours = (
                                next_region_availability - current_perc
                            ) / source_planet.tracker.change_rate_per_hour
                        else:
                            next_stage_hours = (
                                1 - current_perc
                            ) / source_planet.tracker.change_rate_per_hour
                        hours_from_now += next_stage_hours
                        current_perc = 1
                        results.end_time = datetime.now() + timedelta(
                            hours=hours_from_now
                        )
                        if region == non_lib_regions[0]:
                            results.source_planet = source_planet

                results.end_time = datetime.now() + timedelta(hours=hours_from_now)
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
            results.regions = []
            region_rates = [
                r.tracker.change_rate_per_hour / r.size
                for r in non_lib_regions
                if r.tracker and r.tracker.change_rate_per_hour > 0
            ]
            average_region_rate = (
                (sum(region_rates) / len(region_rates)) if region_rates != [] else 0
            )
            current_perc = 1 - source_planet.health_perc
            hours_from_now = 0
            if average_region_rate != 0:
                for index, region in enumerate(non_lib_regions):
                    est_lib_time = (
                        ((1 - region.perc) / (average_region_rate * region.size))
                        if region.is_available
                        else (1 / (average_region_rate * region.size))
                    )
                    planet_health_at_region_lib = current_perc + (
                        source_planet.tracker.change_rate_per_hour * est_lib_time
                    )
                    if planet_health_at_region_lib < 1:
                        # if region is liberated before planet
                        current_perc = (
                            planet_health_at_region_lib + region.planet_damage_perc
                        )
                        hours_from_now += est_lib_time
                        results.regions.append(region)
                    else:
                        # if planet is liberated before region
                        if region != non_lib_regions[-1]:
                            next_region_availability = non_lib_regions[
                                index + 1
                            ].availability_factor
                            next_stage_hours = (
                                next_region_availability - current_perc
                            ) / source_planet.tracker.change_rate_per_hour
                        else:
                            next_stage_hours = (
                                1 - current_perc
                            ) / source_planet.tracker.change_rate_per_hour
                        hours_from_now += next_stage_hours
                        current_perc = 1
                        results.end_time = datetime.now() + timedelta(
                            hours=hours_from_now
                        )
                        if region == non_lib_regions[0]:
                            results.source_planet = source_planet

                results.end_time = datetime.now() + timedelta(hours=hours_from_now)
            else:
                results.source_planet = source_planet
                results.end_time = source_planet.tracker.complete_time
        else:
            if source_planet.tracker.change_rate_per_hour > 0:
                results.source_planet = source_planet
                results.end_time = source_planet.tracker.complete_time

    return results
