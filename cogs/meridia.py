from datetime import datetime, time, timedelta
from disnake import (
    AppCmdInter,
    File,
    InteractionContextTypes,
    ApplicationInstallTypes,
    NotFound,
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
from utils.embeds.loop_embeds import MeridiaLoopEmbed


class MeridiaCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.meridia_update.start()

    def cog_unload(self):
        self.meridia_update.stop()

    @tasks.loop(
        time=[time(hour=i, minute=j) for i in range(24) for j in range(10, 60, 15)]
    )
    async def meridia_update(self):
        if not self.bot.data.meridia_position:
            return
        now = datetime.now()
        newest_coords = self.bot.data.meridia_position
        meridia = Meridia()
        if newest_coords != meridia.locations[-1].as_tuple:
            meridia.new_location(datetime.now().isoformat(), *newest_coords)
        else:
            return
        if (
            now.hour % 4 == 0
            and now.minute == 10
            and meridia.locations[-1].timestamp > now - timedelta(hours=4)
        ):
            embed = MeridiaLoopEmbed(
                meridia=meridia, dark_energy=self.bot.data.global_resources.dark_energy
            )
            msg = await self.bot.api_changes_channel.send(embed=embed)
            await msg.publish()

    @meridia_update.before_loop
    async def before_check_position(self):
        await self.bot.wait_until_ready()

    @wait_for_startup()
    @commands.slash_command(
        description="Get up-to-date information on Meridia",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Get an view of the Meridian Singularity and it's direction of travel. This is generated upon use of the command so it may take a couple of seconds.",
            "example_usage": "**`/meridia public:Yes`** would return some brief information of the Meridian Singularity and it's estimated direction, including any planets in it's path. It can also be seen by others in discord.",
        },
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
        try:
            await inter.response.defer(ephemeral=public != "Yes")
        except NotFound:
            await inter.send(
                "There was an error with that command, please try again.",
                ephemeral=True,
            )
            return
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{public = }>"
        )
        if inter.guild:
            guild = GWWGuild.get_by_id(inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    msg=f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuild.new(inter.guild_id)
        else:
            guild = GWWGuild.default()
        map_img = Image.open(f"resources/maps/{guild.language}.webp")
        meridia_info = Meridia()
        coordinates_fixed = [
            ((x + 1) / 2 * 2000, (y + 1) / 2 * 2000)
            for x, y in [coord.as_tuple for coord in meridia_info.locations]
        ]
        x, y = zip(*coordinates_fixed)
        padding = meridia_info.locations[-1].x * 1000
        x_min, x_max = min(x) - padding, max(x) + padding
        y_min, y_max = min(y) - padding, max(y) + padding
        fig, ax = plt.subplots()
        fig.patch.set_facecolor("black")
        ax.set_facecolor("black")
        ax.imshow(map_img, extent=[0, 2000, 0, 2000])
        map_img.close()
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
            planets_to_check = [
                effect["index"]
                for effect in self.bot.data.planet_active_effects
                if effect["galacticEffectId"] == 1240
            ]
            points_in_path = {
                index: coords
                for index, coords in self.bot.data.plot_coordinates.items()
                if index != 64 and index in planets_to_check
            }
            planets_in_path = [self.bot.data.planets[index] for index in points_in_path]
            for px, py in points_in_path.values():
                ax.plot(px, py, "o", color="red", markersize=5)

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

        current_location: Meridia.Location = meridia_info.locations[-1]
        padding_distance = 0.006
        time_to_reach_planets = {}
        for planet in planets_in_path:
            if set([1241, 1252]) & planet.active_effects:
                continue
            delta_x_to_planet = planet.position["x"] - current_location.x
            delta_y_to_planet = planet.position["y"] - current_location.y
            distance_to_planet = sqrt(delta_x_to_planet**2 + delta_y_to_planet**2)
            adjusted_distance = max(distance_to_planet - 2 * padding_distance, 0)
            time_to_reach_planets[planet.index] = int(
                (
                    datetime.now()
                    + timedelta(seconds=adjusted_distance / meridia_info.speed)
                ).timestamp()
            )
        time_to_reach_planets = dict(
            sorted(time_to_reach_planets.copy().items(), key=lambda x: x[1])
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
    bot.add_cog(MeridiaCog(bot))
