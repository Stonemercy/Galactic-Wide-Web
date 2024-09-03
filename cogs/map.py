from asyncio import sleep
from data.lists import supported_languages
from datetime import datetime, time, timedelta
from disnake import AppCmdInter, File, NotFound, Forbidden, PartialMessage
from disnake.ext import commands, tasks
from json import load
from main import GalacticWideWebBot
from PIL import Image
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from utils.checks import wait_for_startup
from utils.db import Guilds
from utils.functions import dashboard_maps
from utils.api import API, Data


class MapCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.faction_colour = {
            "Automaton": (252, 76, 79),
            "automaton": (126, 38, 22),
            "Terminids": (253, 165, 58),
            "terminids": (126, 82, 29),
            "Illuminate": (103, 43, 166),
            "illuminate": (51, 21, 83),
            "Humans": (36, 205, 76),
            "humans": (18, 102, 38),
            "MO": (254, 226, 76),
        }
        self.planet_names_loc = load(
            open(f"data/json/planets/planets.json", encoding="UTF-8")
        )
        self.map_poster.start()

    def cog_unload(self):
        self.map_poster.stop()

    async def update_message(self, message: PartialMessage, embed_dict):
        guild = Guilds.get_info(message.guild.id)
        if not guild:
            self.bot.map_messages.remove(message)
            return self.bot.logger.error(
                f"MapCog, update_message, guild == None, {message.guild.id}"
            )
        try:
            await message.edit(embed=embed_dict[guild[5]])
        except (NotFound, Forbidden) as e:
            self.bot.map_messages.remove(message)
            Guilds.update_map(message.guild.id, 0, 0)
            return self.bot.logger.error(
                f"MapCog, update_message, {e}, removing, {message.channel.name}"
            )
        except Exception as e:
            return self.bot.logger.error(
                f"MapCog, update_message, {e}, {message.channel.name}"
            )

    times = [time(hour=hour, minute=5, second=0) for hour in range(24)]

    @wait_for_startup()
    @tasks.loop(time=times)
    async def map_poster(self, force: bool = False):
        if self.bot.map_messages == []:
            return
        update_start = datetime.now()
        try:
            await self.bot.waste_bin_channel.purge(
                before=update_start - timedelta(hours=2)
            )
        except:
            pass
        api = API()
        await api.pull_from_api(
            get_campaigns=True,
            get_planets=True,
            get_assignment=True,
            get_planet_events=True,
        )
        if api.error:
            return await self.bot.moderator_channel.send(
                f"<@{self.bot.owner_id}>\n{api.error[0]}\n{api.error[1]}\n:warning:"
            )
        data = Data(data_from_api=api)
        dashboard_maps_dict = await dashboard_maps(data, self.bot.waste_bin_channel)
        chunked_messages = [
            self.bot.map_messages[i : i + 50]
            for i in range(0, len(self.bot.map_messages), 50)
        ]
        maps_updated = 0
        for chunk in chunked_messages:
            for message in chunk:
                self.bot.loop.create_task(
                    self.update_message(message, dashboard_maps_dict)
                )
                maps_updated += 1
            await sleep(1.025)
        if not force:
            self.bot.logger.info(
                f"Updated {maps_updated} maps in {(datetime.now() - update_start).total_seconds():.2f} seconds"
            )
        self.bot.get_cog("StatsCog").maps_updated += maps_updated
        return maps_updated

    @map_poster.before_loop
    async def before_map_poster(self):
        await self.bot.wait_until_ready()

    @wait_for_startup()
    @commands.slash_command(
        description="Get an up-to-date map of the galaxy",
    )
    async def map(
        self,
        inter: AppCmdInter,
        faction=commands.Param(
            choices=["Humans", "Automaton", "Terminids", "Illuminate"],
            default=None,
            description="The faction to focus on",
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        public = public != "Yes"
        await inter.response.defer(ephemeral=public)
        self.bot.logger.info(
            f"MapCog, map faction:{faction} public:{public} command used"
        )
        guild = Guilds.get_info(inter.guild_id)
        if not guild:
            guild = Guilds.insert_new_guild(inter.guild.id)
        api = API()
        await api.pull_from_api(
            get_planets=True,
            get_campaigns=True,
            get_assignment=True,
            get_planet_events=True,
        )
        if api.error:
            await self.bot.moderator_channel.send(
                f"<@164862382185644032>\n{data.error[0]}\n{data.error[1]}\n:warning:"
            )
            return await inter.send(
                "There was an issue getting the data for the map.\nPlease try again later.",
                ephemeral=True,
            )
        data = Data(data_from_api=api)
        planets_coords = {}
        available_planets = [campaign.planet.name for campaign in data.campaigns]
        for planet in data.planets.values():
            if faction:
                if planet.current_owner != faction:
                    continue
                for waypoint in planet.waypoints:
                    planets_coords[waypoint] = (
                        (data.planets[waypoint].position["x"] * 2000) + 2000,
                        (
                            (
                                data.planets[waypoint].position["y"]
                                - (data.planets[waypoint].position["y"] * 2)
                            )
                            * 2000
                        )
                        + 2000,
                    )
            planets_coords[planet.index] = (
                (planet.position["x"] * 2000) + 2000,
                ((planet.position["y"] - (planet.position["y"] * 2)) * 2000) + 2000,
            )
        if planets_coords == {}:
            return await inter.send(
                f"There are no planets under {faction} control. Let's keep it that way!"
            )
        with Image.open("resources/map.webp") as background:
            background_draw = Draw(background)
            for index, coords in planets_coords.items():
                for waypoint in data.planets[index].waypoints:
                    try:
                        background_draw.line(
                            (
                                planets_coords[waypoint][0],
                                planets_coords[waypoint][1],
                                coords[0],
                                coords[1],
                            ),
                            width=5,
                        )
                    except:
                        continue
            if data.assignment:
                for task in data.assignment.tasks:
                    if task.type in (11, 13):
                        try:
                            background_draw.ellipse(
                                [
                                    (
                                        planets_coords[task.values[2]][0] - 50,
                                        planets_coords[task.values[2]][1] - 50,
                                    ),
                                    (
                                        planets_coords[task.values[2]][0] + 50,
                                        planets_coords[task.values[2]][1] + 50,
                                    ),
                                ],
                                fill=self.faction_colour["MO"],
                            )
                        except:
                            pass
            for index, coords in planets_coords.items():
                background_draw.ellipse(
                    [
                        (coords[0] - 35, coords[1] - 35),
                        (coords[0] + 35, coords[1] + 35),
                    ],
                    fill=(
                        self.faction_colour[data.planets[index].current_owner]
                        if data.planets[index].name in available_planets
                        else self.faction_colour[
                            data.planets[index].current_owner.lower()
                        ]
                    ),
                )
                if faction and data.planets[index].name in available_planets:
                    font = truetype("gww-font.ttf", 50)
                    background_draw.multiline_text(
                        xy=coords,
                        text=self.planet_names_loc[str(index)]["names"][
                            supported_languages[guild[5]]
                        ].replace(" ", "\n"),
                        anchor="md",
                        font=font,
                        stroke_width=3,
                        stroke_fill="black",
                        align="center",
                        spacing=-15,
                    )
            if faction and planets_coords != {}:
                min_x = min(planets_coords.values(), key=lambda x: x[0])[0]
                max_x = max(planets_coords.values(), key=lambda x: x[0])[0]
                min_y = min(planets_coords.values(), key=lambda x: x[1])[1]
                max_y = max(planets_coords.values(), key=lambda x: x[1])[1]
                background = background.crop(
                    (
                        min_x - 150,
                        min_y - 150,
                        max_x + 150,
                        max_y + 150,
                    )
                )
            background.save("resources/map_2.webp")
        await inter.send(
            file=File("resources/map_2.webp"),
            ephemeral=public,
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(MapCog(bot))
