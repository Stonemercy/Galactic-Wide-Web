from datetime import datetime, timedelta
from os import getenv
from aiohttp import ClientSession
from disnake import (
    AppCmdInter,
    File,
    InteractionContextTypes,
    ApplicationInstallTypes,
    Permissions,
)
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from math import sqrt
from numpy import array, hypot
from utils.checks import wait_for_startup
from utils.db import GWWGuild, Meridia
from utils.embeds.command_embeds import MeridiaCommandEmbed
import matplotlib.pyplot as plt
import PIL.Image as Image

AUTH_KEY = getenv("NEURAL_TOKEN")
NEURAL_URL = getenv("NEURAL_URL")
SUPPORT_SERVER_ID = [int(getenv("SUPPORT_SERVER"))]


class OrganisedData(list):
    def __init__(self, json: dict):
        for prediction in json["predictions"]:
            self.append(
                {
                    "timestamp": datetime.fromisoformat(prediction["timestamp"]),
                    "coords": (prediction["predicted_x"], prediction["predicted_y"]),
                }
            )


class MeridiaPredictionCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.train_model.start()

    def cog_unload(self):
        self.train_model.stop()

    @tasks.loop(minutes=1)
    async def train_model(self):
        if not self.bot.data.loaded:
            return
        dark_energy_remaining = 0
        for planet in self.bot.data.planet_events:
            if not planet.event.potential_buildup:
                continue
            if self.bot.data.liberation_changes != {}:
                liberation_change = self.bot.data.liberation_changes.get(
                    planet.index, None
                )
                if (
                    liberation_change
                    and len(liberation_change["liberation_changes"]) > 0
                    and sum(liberation_change["liberation_changes"]) != 0
                ):
                    start_seconds = int(planet.event.start_time_datetime.timestamp())
                    now_seconds = int(datetime.now().timestamp())
                    seconds_until_complete = int(
                        (
                            (100 - liberation_change["liberation"])
                            / sum(liberation_change["liberation_changes"])
                        )
                        * 3600
                    )
                    winning = (
                        datetime.fromtimestamp(now_seconds + seconds_until_complete)
                        < planet.event.end_time_datetime
                    )
                    if winning:
                        end_seconds = int(planet.event.end_time_datetime.timestamp())
                        total_duration = end_seconds - start_seconds
                        percentage = now_seconds / total_duration
                        dark_energy_remaining += round(
                            (
                                (planet.event.remaining_dark_energy * percentage)
                                / 1_000_000
                            )
                            * 100,
                            2,
                        )
                    else:
                        dark_energy_remaining += round(
                            (planet.event.remaining_dark_energy / 1_000_000) * 100, 2
                        )
                else:
                    return

        current_planet = self.bot.data.planets[64]
        self.bot.data_points.append(
            {
                "timestamp": datetime.now().isoformat(),
                "x": current_planet.position["x"],
                "y": current_planet.position["y"],
                "global_resource": round(
                    self.bot.data.global_resources.dark_energy.perc * 100, 2
                ),
                "dark_energy_potential_buildup": dark_energy_remaining,
                "active_invasions": len(
                    [
                        planet.index
                        for planet in self.bot.data.planet_events
                        if planet.event.potential_buildup
                    ]
                ),
            }
        )
        if len(self.bot.data_points) >= 30:
            async with ClientSession(
                headers={
                    "X-API-Token": AUTH_KEY,
                    "Content-Type": "application/json",
                }
            ) as session:
                async with session.post(
                    f"{NEURAL_URL}/training-data", json=self.bot.data_points
                ) as result:
                    self.bot.logger.info(
                        f"NERUAL DATA - {result.status} - {await result.text()}"
                    )
                    self.bot.data_points.clear()

    def point_line_distance(self, px, py, x1, y1, x2, y2):
        """Calculate the perpendicular distance from (px, py) to the line (x1, y1) -> (x2, y2)."""
        line_mag = hypot(x2 - x1, y2 - y1)
        if line_mag == 0:
            return hypot(px - x1, py - y1)
        u = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_mag**2
        closest_x = x1 + u * (x2 - x1)
        closest_y = y1 + u * (y2 - y1)
        closest_x = max(min(closest_x, max(x1, x2)), min(x1, x2))
        closest_y = max(min(closest_y, max(y1, y2)), min(y1, y2))
        return hypot(px - closest_x, py - closest_y)

    @wait_for_startup()
    @commands.is_owner()
    @commands.slash_command(
        guild_ids=SUPPORT_SERVER_ID,
        description="Get a prediction on where Meridia is going WIP",
        default_member_permissions=Permissions(administrator=True),
    )
    async def predict_meridia(
        self,
        inter: AppCmdInter,
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        await inter.response.defer(ephemeral=public != "Yes")
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{public = }>"
        )
        if inter.guild:
            guild = GWWGuild.get_by_id(inter.guild_id)
        else:
            guild = GWWGuild.default()
        async with ClientSession() as session:
            async with session.get(
                url=f"{NEURAL_URL}/predict?hours_ahead=72&interval_minutes=1440&num_predictions=20"
            ) as result:
                if result.status == 200:
                    data = await result.json()
                    prediction_info: list = OrganisedData(data)
                else:
                    self.bot.logger.info(f"NERUAL DATA - {result.status} - {data}")
        map_img = Image.open(f"resources/{guild.language}.webp")
        coordinates = [data_point["coords"] for data_point in prediction_info]
        coordinates_fixed = [
            ((coords[0] + 1) / 2 * 2000, (coords[1] + 1) / 2 * 2000)
            for coords in coordinates
        ]
        x, y = zip(*coordinates_fixed)
        padding = 200
        x_min, x_max = min(x) - padding, max(x) + padding
        y_min, y_max = min(y) - padding, max(y) + padding
        fig, ax = plt.subplots()
        fig.patch.set_facecolor("black")
        ax.set_facecolor("black")
        ax.imshow(map_img, extent=[0, 2000, 0, 2000])
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.plot(x, y, "o", color=(0.5, 0, 0.5), label="Coordinates")
        dataponts_to_use = 2
        while dataponts_to_use < 5:
            if len(x) > dataponts_to_use + 1:
                dataponts_to_use += 1
            else:
                break
        dp_to_use = -dataponts_to_use
        if len(x) > 1:
            ax.arrow(
                x[dp_to_use],
                y[dp_to_use],
                x[-1] - x[dp_to_use],
                y[-1] - y[dp_to_use],
                head_width=15,
                head_length=25,
                fc=(0.5, 0, 0.5),
                ec=(1, 0, 0.75),
            )
        num_recent_points = min(3, len(x) - 1)
        if num_recent_points > 1:
            recent_x, recent_y = array(x[-num_recent_points:]), array(
                y[-num_recent_points:]
            )
            dx = recent_x[-1] - recent_x[0]
            dy = recent_y[-1] - recent_y[0]
            magnitude = hypot(dx, dy)
            if magnitude > 0:
                dx /= magnitude
                dy /= magnitude
            step_size = 200
            future_x = x[-1] + dx * step_size
            future_y = y[-1] + dy * step_size

            # Check for close planets
            threshold = 25
            points_in_path = {
                index: coords
                for index, coords in self.bot.data.plot_coordinates.items()
                if self.point_line_distance(
                    coords[0], coords[1], x[-1], y[-1], future_x, future_y
                )
                < threshold
                and index != 64
            }
            planets_in_path = [self.bot.data.planets[index] for index in points_in_path]
            for px, py in points_in_path.values():
                ax.plot(px, py, "o", color="red", markersize=12, label="In Path")

            ax.plot(
                [x[-1], future_x],
                [y[-1], future_y],
                linestyle="dashed",
                color=(1, 0, 0.75),
                linewidth=2,
                dashes=(5, 5),
            )
            arrow_length = 25
            head_x = future_x - dx * arrow_length
            head_y = future_y - dy * arrow_length
            ax.arrow(
                head_x,
                head_y,
                dx * arrow_length,
                dy * arrow_length,
                head_width=10,
                head_length=25,
                fc=(1, 0, 0.75),
                ec=(1, 0, 0.75),
            )
            ax.plot(
                future_x,
                future_y,
                "o",
                color=(1, 0, 0.75),
                markersize=1,
                label="Future Position",
            )
        current_location: Meridia.Locations.Location = Meridia().locations[-1]
        location_in_one_day = prediction_info[-1]["coords"]
        time_difference = (
            current_location.timestamp - prediction_info[-1]["timestamp"]
        ).total_seconds()
        delta_x = current_location.x - location_in_one_day[0]
        delta_y = current_location.y - location_in_one_day[0]
        distance_moved = sqrt(delta_x**2 + delta_y**2)
        speed = distance_moved / time_difference  # in units per second

        time_to_reach_planets = {}
        for planet in planets_in_path:
            delta_x_to_planet = planet.position["x"] - current_location.x
            delta_y_to_planet = planet.position["y"] - current_location.y
            distance_to_planet = sqrt(delta_x_to_planet**2 + delta_y_to_planet**2)
            time_to_reach_planets[planet.index] = int(
                (
                    datetime.now() + timedelta(seconds=distance_to_planet / speed)
                ).timestamp()
            )

        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.set_frame_on(False)
        ax.set_title(
            "Predicted Direction of Meridia", color="white", fontsize=16, pad=20
        )
        plt.savefig(
            "resources/meridia_map.webp",
            dpi=300,
            bbox_inches="tight",
            facecolor="black",
        )
        plt.close(fig)
        embed = MeridiaCommandEmbed(
            self.bot.json_dict["languages"][guild.language],
            self.bot.json_dict["planets"],
            self.bot.data.global_resources.dark_energy,
            sum(
                [
                    planet.event.remaining_dark_energy
                    for planet in self.bot.data.planet_events
                ]
            ),
            len(
                [
                    planet
                    for planet in self.bot.data.planet_events
                    if planet.event.potential_buildup != 0
                ]
            ),
            self.bot.data.dark_energy_changes,
            time_to_reach_planets,
        )
        embed.set_image(file=File("resources/meridia_map.webp"))
        await inter.send(
            ephemeral=public != "Yes",
            embed=embed,
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(MeridiaPredictionCog(bot))
