from asyncio import sleep
from data.lists import supported_languages, faction_colours
from datetime import datetime, time, timedelta
from disnake import AppCmdInter, File, NotFound, Forbidden, PartialMessage
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from PIL import Image
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from utils.checks import wait_for_startup
from utils.db import GuildRecord, GuildsDB
from utils.functions import dashboard_maps


class MapCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.map_poster.start()

    def cog_unload(self):
        self.map_poster.stop()

    async def update_message(self, message: PartialMessage, embed_dict):
        guild: GuildRecord = GuildsDB.get_info(message.guild.id)
        if not guild:
            self.bot.map_messages.remove(message)
            return self.bot.logger.error(
                f"{self.qualified_name} | update_message | {guild = } | {message.guild.id = }"
            )
        try:
            await message.edit(embed=embed_dict[guild.language])
        except (NotFound, Forbidden) as e:
            self.bot.map_messages.remove(message)
            GuildsDB.update_map(message.guild.id, 0, 0)
            return self.bot.logger.error(
                f"{self.qualified_name} | update_message | {e} | removed from self.bot.map_messages | {message.channel.id = }"
            )
        except Exception as e:
            return self.bot.logger.error(
                f"{self.qualified_name} | update_message | {e} | {message.channel.id = }"
            )

    @tasks.loop(time=[time(hour=hour, minute=5, second=0) for hour in range(24)])
    async def map_poster(self, force: bool = False):
        if (
            self.bot.map_messages == []
            or not self.bot.data.loaded
            or not self.bot.c_n_m_loaded
        ):
            return
        update_start = datetime.now()
        try:
            await self.bot.waste_bin_channel.purge(
                before=update_start - timedelta(hours=2)
            )
        except:
            pass
        dashboard_maps_dict = {
            lang: await dashboard_maps(
                self.bot.data,
                self.bot.waste_bin_channel,
                self.bot.json_dict["planets"],
                lang,
            )
            for lang in GuildsDB.get_used_languages()
        }
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
            await sleep(1.1)
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
        description="Get an up-to-date map of the galaxy", dm_permission=False
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
        ephemeral = public != "Yes"
        await inter.response.defer(ephemeral=ephemeral)
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{faction = }> <{public = }>"
        )
        guild: GuildRecord = GuildsDB.get_info(inter.guild_id)
        if not guild:
            guild = GuildsDB.insert_new_guild(inter.guild.id)
        planets_coords = {}
        available_planets = [
            campaign.planet.name for campaign in self.bot.data.campaigns
        ]
        for planet in self.bot.data.planets.values():
            if faction and planet.current_owner != faction:
                continue
            for waypoint in planet.waypoints:
                planets_coords[waypoint] = (
                    (self.bot.data.planets[waypoint].position["x"] * 2000) + 2000,
                    (
                        (
                            self.bot.data.planets[waypoint].position["y"]
                            - (self.bot.data.planets[waypoint].position["y"] * 2)
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
                f"There are no planets under {faction} control. Let's keep it that way!",
                ephemeral=ephemeral,
            )
        with Image.open("resources/map.webp") as background:
            background_draw = Draw(background)
            for index, coords in planets_coords.items():
                for waypoint in self.bot.data.planets[index].waypoints:
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
            if self.bot.data.assignment:
                for task in self.bot.data.assignment.tasks:
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
                                fill=faction_colours["MO"],
                            )
                        except:
                            pass
            if self.bot.data.dss:
                if self.bot.data.dss.planet.index in planets_coords:
                    background_draw.ellipse(
                        [
                            (
                                planets_coords[self.bot.data.dss.planet.index][0] - 42,
                                planets_coords[self.bot.data.dss.planet.index][1] - 42,
                            ),
                            (
                                planets_coords[self.bot.data.dss.planet.index][0] + 42,
                                planets_coords[self.bot.data.dss.planet.index][1] + 42,
                            ),
                        ],
                        faction_colours["DSS"],
                    )
                    dss_icon = Image.open("resources/DSS.png")
                    dss_icon = dss_icon.convert("RGBA")
                    dss_coords = (
                        int(planets_coords[self.bot.data.dss.planet.index][0]) - 22,
                        int(planets_coords[self.bot.data.dss.planet.index][1]) - 180,
                    )
                    dss_icon = background.paste(dss_icon, dss_coords, dss_icon)
            for index, coords in planets_coords.items():
                if index == 64:
                    background_draw.ellipse(
                        [
                            (coords[0] - 35, coords[1] - 35),
                            (coords[0] + 35, coords[1] + 35),
                        ],
                        fill=(95, 61, 181),
                    )
                else:
                    background_draw.ellipse(
                        [
                            (coords[0] - 35, coords[1] - 35),
                            (coords[0] + 35, coords[1] + 35),
                        ],
                        fill=(
                            faction_colours[self.bot.data.planets[index].current_owner]
                            if self.bot.data.planets[index].name in available_planets
                            else faction_colours[
                                self.bot.data.planets[index].current_owner.lower()
                            ]
                        ),
                    )
                if faction and self.bot.data.planets[index].name in available_planets:
                    font = truetype("gww-font.ttf", 50)
                    border_colour = (
                        "black"
                        if not self.bot.data.planets[index].dss
                        else "deepskyblue"
                    )
                    background_draw.multiline_text(
                        xy=coords,
                        text=self.bot.json_dict["planets"][str(index)]["names"][
                            supported_languages[guild.language]
                        ].replace(" ", "\n"),
                        anchor="md",
                        font=font,
                        stroke_width=3,
                        stroke_fill=border_colour,
                        align="center",
                        spacing=-15,
                    )
            if faction and planets_coords != {}:
                min_x = min(planets_coords.values(), key=lambda x: x[0])[0] - 150
                max_x = max(planets_coords.values(), key=lambda x: x[0])[0] + 150
                min_y = min(planets_coords.values(), key=lambda x: x[1])[1] - 150
                max_y = max(planets_coords.values(), key=lambda x: x[1])[1] + 150
                background = background.crop(box=(min_x, min_y, max_x, max_y))
            background.save("resources/map_2.webp")
        await inter.send(
            file=File("resources/map_2.webp"),
            ephemeral=ephemeral,
        )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(MapCog(bot))
