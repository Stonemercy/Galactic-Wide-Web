from datetime import datetime
from json import load
from disnake import AppCmdInter, File, PartialMessage, NotFound, Forbidden
from disnake.ext import commands, tasks
from helpers.db import Guilds
from helpers.embeds import Map
from helpers.functions import pull_from_api
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
        self.cache_messages.start()

    def cog_unload(self):
        self.map_poster.stop()
        self.cache_messages.stop()

    async def map_message_list_gen(self, i):
        try:
            channel = self.bot.get_channel(int(i[6])) or await self.bot.fetch_channel(
                int(i[6])
            )
            try:
                message = channel.get_partial_message(int(i[7]))
                self.messages.append(message)
            except Exception as e:
                guild = self.bot.get_guild(int(i[0]))
                logger.error("MapCog map_message_list_gen message", guild.id, e)
        except Exception as e:
            return logger.error("MapCog map_message_list_gen channel", i[6], e)

    async def update_message(self, i: PartialMessage, embed_dict):
        guild = Guilds.get_info(i.guild.id)
        if guild == None:
            self.messages.remove(i)
            return logger.error("MapCog update_message - Guild not in DB")
        try:
            await i.edit(embed=embed_dict[guild[5]], attachments=None)
        except NotFound:
            self.messages.remove(i)
            return logger.error(("MapCog Map not found, removing", i.channel.name))
        except Forbidden:
            self.messages.remove(i)
            return logger.error(("MapCog Map forbidden, removing", i.channel.name))
        except Exception as e:
            return logger.error(("MapCog Map update_message", e, i.channel.name))

    @tasks.loop(count=1)
    async def cache_messages(self):
        guilds = Guilds.get_all_guilds()
        if not guilds:
            return
        self.messages = []
        for i in guilds:
            if i[6] == 0:
                continue
            self.bot.loop.create_task(self.map_message_list_gen(i))

    @tasks.loop(minutes=1)
    async def map_poster(self):
        now = datetime.now()
        if now.minute % 15 != 0 or self.messages == []:
            return
        channel = self.bot.get_channel(1242843098363596883)
        await channel.purge(limit=2)
        data = await pull_from_api(
            get_campaigns=True,
            get_planets=True,
        )
        if data["campaigns"] in (None, []) or data["planets"] in (None, []):
            return
        self.planet_names_loc = load(
            open(f"data/json/planets/planets.json", encoding="UTF-8")
        )
        languages = Guilds.get_used_languages()
        planets_coords = {}
        available_planets = [planet["planet"]["name"] for planet in data["campaigns"]]
        for i in data["planets"]:
            planets_coords[i["index"]] = (
                (i["position"]["x"] * 2000) + 2000,
                ((i["position"]["y"] - (i["position"]["y"] * 2)) * 2000) + 2000,
            )
        map_dict = {}
        for lang in languages:
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
                for index, coords in planets_coords.items():
                    if data["planets"][index]["name"] in available_planets:

                        font = truetype("impact.ttf", 75)
                        background_draw.text(
                            xy=coords,
                            text=self.planet_names_loc[str(index)]["names"][
                                supported_languages[lang]
                            ],
                            anchor="lb",
                            font=font,
                            stroke_width=3,
                            stroke_fill="black",
                            align="center",
                        )
                background.save(f"resources/map_{lang}.webp")
            message_for_url = await channel.send(
                file=File(f"resources/map_{lang}.webp"),
            )
            map_embed = Map(message_for_url.attachments[0].url)
            map_dict[lang] = map_embed
        chunked_messages = [
            self.messages[i : i + 20] for i in range(0, len(self.messages), 20)
        ]
        update_start = datetime.now()
        logger.info("Map update started")
        for chunk in chunked_messages:
            for message in chunk:
                self.bot.loop.create_task(self.update_message(message, map_dict))
            await sleep(2)
        logger.info(
            f"Map updates finished in {(datetime.now() - update_start).total_seconds()} seconds"
        )

    @map_poster.before_loop
    async def before_dashboard(self):
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
            description="MAP FACTION DESCRIPTION",
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="MAP PUBLIC DESCRIPTION",
        ),
    ):
        logger.info("map command used")
        public = {"Yes": False, "No": True}[public]
        await inter.response.defer(ephemeral=public)
        data = await pull_from_api(get_planets=True, get_campaigns=True)
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
                    font = truetype("impact.ttf", 35)
                    background_draw.text(
                        xy=coords,
                        text=data["planets"][index]["name"],
                        anchor="mm",
                        font=font,
                        stroke_width=3,
                        stroke_fill="black",
                        align="center",
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
