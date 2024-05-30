from datetime import datetime, timedelta
from json import load
from disnake import AppCmdInter, File, NotFound, Forbidden, PartialMessage
from disnake.ext import commands, tasks
from helpers.db import Guilds
from helpers.functions import dashboard_maps, pull_from_api
from PIL import Image
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from asyncio import sleep
from data.lists import supported_languages
from logging import getLogger

logger = getLogger("disnake")


class MapCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.messages = []
        self.faction_colour = {
            "Automaton": (252, 76, 79),
            "automaton": (126, 38, 22),
            "Terminids": (253, 165, 58),
            "terminids": (126, 82, 29),
            "Illuminate": (116, 163, 180),
            "illuminate": (58, 81, 90),
            "Humans": (36, 205, 76),
            "humans": (18, 102, 38),
        }
        self.map_poster.start()
        self.planet_names_loc = load(
            open(f"data/json/planets/planets.json", encoding="UTF-8")
        )

    def cog_unload(self):
        self.map_poster.stop()

    async def update_message(self, message: PartialMessage, embed_dict):
        guild = Guilds.get_info(message.guild.id)
        if guild == None:
            self.messages.remove(message)
            return logger.error(
                "MapCog, update_message, guild == None, {message.guild.id}"
            )
        try:
            await message.edit(embed=embed_dict[guild[5]])
        except NotFound:
            self.messages.remove(message)
            Guilds.update_map(message.guild.id, 0, 0)
            return logger.error(
                f"MapCog, update_message, NotFound, removing, {message.channel.name}"
            )
        except Forbidden:
            self.messages.remove(message)
            Guilds.update_map(message.guild.id, 0, 0)
            return logger.error(
                f"MapCog, update_message, Forbidden, removing, {message.channel.name}"
            )
        except Exception as e:
            return logger.error(f"MapCog, update_message, {e}, {message.channel.name}")

    @tasks.loop(minutes=1)
    async def map_poster(self):
        channel = self.bot.get_channel(1242843098363596883)
        now = datetime.now()
        if now.minute != 1 or self.messages == []:
            return
        try:
            await channel.purge(before=now - timedelta(hours=2))
        except:
            pass
        data = await pull_from_api(
            get_campaigns=True,
            get_planets=True,
        )
        for data_key, data_value in data.items():
            if data_value == None:
                logger.error(f"MapCog, map_poster, {data_key} returned {data_value}")
                return
        dashboard_maps_dict = await dashboard_maps(data, channel)
        chunked_messages = [
            self.messages[i : i + 50] for i in range(0, len(self.messages), 50)
        ]
        update_start = datetime.now()
        maps_updated = 0
        for chunk in chunked_messages:
            for message in chunk:
                self.bot.loop.create_task(
                    self.update_message(message, dashboard_maps_dict)
                )
                maps_updated += 1
            await sleep(1.025)
        logger.info(
            f"Updated {maps_updated} maps in {(datetime.now() - update_start).total_seconds():.2f} seconds"
        )

    @map_poster.before_loop
    async def before_map_poster(self):
        await self.bot.wait_until_ready()

    @commands.slash_command(
        description="Get an up-to-date map of the galaxy",
    )
    async def map(
        self,
        inter: AppCmdInter,
        faction=commands.Param(
            choices=["Humans", "Automaton", "Terminids"],
            default=None,
            description="The faction to focus on",
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        public = {"Yes": False, "No": True}[public]
        await inter.response.defer(ephemeral=public)
        logger.info("MapCog, map command used")
        guild = Guilds.get_info(inter.guild_id)
        data = await pull_from_api(get_planets=True, get_campaigns=True)
        for data_key, data_value in data.items():
            if data_value == None:
                logger.error(f"MapCog, map command, {data_key} returned {data_value}")
                return await inter.send(
                    "Something went wrong, please try again later", ephemeral=True
                )
        planets_coords = {}
        available_planets = [planet["planet"]["name"] for planet in data["campaigns"]]
        for i in data["planets"]:
            if faction != None:
                if i["currentOwner"] != faction:
                    continue
                for j in i["waypoints"]:
                    planets_coords[j] = (
                        (data["planets"][j]["position"]["x"] * 2000) + 2000,
                        (
                            (
                                data["planets"][j]["position"]["y"]
                                - (data["planets"][j]["position"]["y"] * 2)
                            )
                            * 2000
                        )
                        + 2000,
                    )
            planets_coords[i["index"]] = (
                (i["position"]["x"] * 2000) + 2000,
                ((i["position"]["y"] - (i["position"]["y"] * 2)) * 2000) + 2000,
            )
        with Image.open("resources/map.webp") as background:
            background_draw = Draw(background)
            for index, coords in planets_coords.items():
                for i in data["planets"][index]["waypoints"]:
                    try:
                        background_draw.line(
                            (
                                planets_coords[i][0],
                                planets_coords[i][1],
                                coords[0],
                                coords[1],
                            ),
                            width=5,
                        )
                    except:
                        continue
            for index, coords in planets_coords.items():
                background_draw.ellipse(
                    [
                        (coords[0] - 35, coords[1] - 35),
                        (coords[0] + 35, coords[1] + 35),
                    ],
                    fill=(
                        self.faction_colour[data["planets"][index]["currentOwner"]]
                        if data["planets"][index]["name"] in available_planets
                        else self.faction_colour[
                            data["planets"][index]["currentOwner"].lower()
                        ]
                    ),
                )
                if (
                    faction != None
                    and data["planets"][index]["name"] in available_planets
                ):
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
            if faction != None:
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


def setup(bot: commands.Bot):
    bot.add_cog(MapCog(bot))
