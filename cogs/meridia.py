from datetime import datetime, time, timedelta
from disnake import AppCmdInter, File, InteractionContextTypes, ApplicationInstallTypes
from disnake.ext import commands, tasks
from cogs.admin.data_management import APIChanges
from main import GalacticWideWebBot
from math import sqrt
from numpy import array, hypot
from utils.checks import wait_for_startup
from utils.db import GWWGuild, Meridia
from utils.embeds.command_embeds import MeridiaCommandEmbed
from utils.embeds.loop_embeds import APIChangesLoopEmbed
import matplotlib.pyplot as plt
import PIL.Image as Image


class MeridiaCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.check_position.start()

    def cog_unload(self):
        self.check_position.stop()

    @tasks.loop(
        time=[
            time(hour=i, minute=j, second=0)
            for i in range(24)
            for j in range(10, 60, 15)
        ]
    )
    async def check_position(self):
        if not self.bot.data.meridia_position:
            return
        new_coords = self.bot.data.meridia_position
        last_location: Meridia.Locations.Location = Meridia().locations[-1]
        old_coords = (last_location.x, last_location.y)
        if new_coords != old_coords:
            Meridia.new_location(datetime.now().isoformat(), *new_coords)
            changes = [
                APIChanges(
                    self.bot.data.planets[64], "Location", old_coords, new_coords
                )
            ]
            await self.bot.api_changes_channel.send(embed=APIChangesLoopEmbed(changes))

    @check_position.before_loop
    async def before_check_position(self):
        await self.bot.wait_until_ready()

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
    @commands.slash_command(
        description="Get up-to-date information on Meridia",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
    )
    async def meridia(
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
        map_img = Image.open(f"resources/{guild.language}.webp")
        meridia_info = Meridia()
        coordinates = [(coord.x, coord.y) for coord in meridia_info.locations]
        coordinates_fixed = [
            ((x + 1) / 2 * 2000, (y + 1) / 2 * 2000) for x, y in coordinates
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
                ax.plot(px, py, "o", color="red", markersize=20, label="In Path")

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
        current_location: Meridia.Locations.Location = meridia_info.locations[-1]
        location_an_hour_ago: Meridia.Locations.Location = meridia_info.locations[-4]
        time_difference = (
            current_location.timestamp - location_an_hour_ago.timestamp
        ).total_seconds()
        delta_x = current_location.x - location_an_hour_ago.x
        delta_y = current_location.y - location_an_hour_ago.y
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
            "Estimated Direction of Meridia", color="white", fontsize=16, pad=20
        )
        plt.savefig(
            "resources/meridia_map.webp",
            dpi=300,
            bbox_inches="tight",
            facecolor="black",
        )
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
    bot.add_cog(MeridiaCog(bot))
