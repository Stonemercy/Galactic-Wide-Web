from datetime import datetime
from disnake import Colour, Embed
from utils.data import DarkEnergy
from utils.mixins import EmbedReprMixin
from utils.trackers import BaseTrackerEntry


class MeridiaEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        language_json: dict,
        planet_names_json: dict,
        dark_energy_resource: DarkEnergy | None,
        total_de_available: int,
        active_invasions: int,
        dark_energy_changes: BaseTrackerEntry | None,
        time_to_reach_planets: dict[str:float],
    ):
        super().__init__(
            title="Meridia",
            colour=Colour.from_rgb(106, 76, 180),
            description="-# This is the path Meridia has taken\n-# ||the gaps were caused by AH||",
        )
        completion_timestamp = ""
        if dark_energy_changes:
            rate = f"{dark_energy_changes.change_rate_per_hour:+.2%}/hr"
            now_seconds = int(datetime.now().timestamp())
            if dark_energy_changes.change_rate_per_hour > 0:
                complete_seconds = (
                    now_seconds + dark_energy_changes.seconds_until_complete
                )
                completion_timestamp = language_json["MeridiaEmbed"]["reaches"].format(
                    number=100, timestamp=complete_seconds
                )
            elif dark_energy_changes.change_rate_per_hour < 0:
                complete_seconds = (
                    now_seconds + dark_energy_changes.seconds_until_complete
                )
                completion_timestamp = language_json["MeridiaEmbed"]["reaches"].format(
                    number=0, timestamp=complete_seconds
                )
        active_invasions_fmt = ""
        total_to_be_harvested = ""
        if dark_energy_resource:
            self.add_field(
                "",
                f"{dark_energy_resource.health_bar}\n**`{dark_energy_resource.perc:^25.3%}`**\n**`{rate:^25}`**",
                inline=False,
            )
            warning = ""
            if (
                (total_de_available / dark_energy_resource.max_value)
                + dark_energy_resource.perc
            ) > 1:
                warning = ":warning:"
            active_invasions_fmt = language_json["MeridiaEmbed"][
                "active_invasions"
            ].format(number=active_invasions)
            total_to_be_harvested = language_json["MeridiaEmbed"][
                "total_to_be_harvested"
            ].format(
                warning=warning,
                number=f"{(total_de_available / dark_energy_resource.max_value):.2%}",
                total_available=f"{(total_de_available / dark_energy_resource.max_value)+dark_energy_resource.perc:.2%}",
            )
        self.add_field(
            "",
            (
                f"{completion_timestamp}\n"
                f"{active_invasions_fmt}\n"
                f"{total_to_be_harvested}"
            ),
        )
        self.set_thumbnail(
            url="https://cdn.discordapp.com/emojis/1331357764039086212.webp?size=96"
        )
        if time_to_reach_planets:
            self.add_field(
                language_json["MeridiaEmbed"]["planets_in_path"],
                "\n".join(
                    [
                        f"{planet_names_json[str(planet)]['names'][language_json['code_long']]} <t:{int(seconds)}:R>"
                        for planet, seconds in time_to_reach_planets.items()
                    ]
                ),
                inline=False,
            )
