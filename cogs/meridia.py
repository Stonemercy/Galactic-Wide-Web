from datetime import datetime, time
from disnake import AppCmdInter, File, InteractionContextTypes, ApplicationInstallTypes
from disnake.ext import commands, tasks
from cogs.admin.data_management import APIChanges
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GWWGuild, Meridia
from utils.embeds import APIChangesEmbed, MeridiaEmbed
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
            self.bot.logger.info(changes)
            await self.bot.api_changes_channel.send(embed=APIChangesEmbed(changes))

    @check_position.before_loop
    async def before_check_position(self):
        await self.bot.wait_until_ready()

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
        embed = MeridiaEmbed(
            Meridia(),
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
        )
        map_img = Image.open(f"resources/{guild.language}.webp")
        coordinates = [(coord.x, coord.y) for coord in Meridia().locations]
        coordinates_fixed = [
            ((x + 1) / 2 * 2000, (y + 1) / 2 * 2000) for x, y in coordinates
        ]
        x, y = zip(*coordinates_fixed)
        fig, ax = plt.subplots()
        fig.patch.set_facecolor("black")
        ax.set_facecolor("black")
        ax.imshow(map_img, extent=[0, 2000, 0, 2000])
        ax.plot(x, y, "o", color=(0.1098, 0.0863, 0.1882), label="Coordinates")
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
                head_width=50,
                head_length=250,
                fc=(0.4157, 0.2980, 0.7059),
                ec=(0.75, 0, 0),
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
        embed.set_image(file=File("resources/meridia_map.webp"))
        await inter.send(
            ephemeral=public != "Yes",
            embed=embed,
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(MeridiaCog(bot))
