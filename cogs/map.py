from datetime import datetime, time, timedelta
from disnake import (
    AppCmdInter,
    Colour,
    Embed,
    File,
    InteractionContextTypes,
    ApplicationInstallTypes,
)
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import GWWGuild
from utils.maps import Maps


class MapCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.map_poster.start()

    def cog_unload(self):
        self.map_poster.stop()

    @tasks.loop(time=[time(hour=hour, minute=5, second=0) for hour in range(24)])
    async def map_poster(self):
        maps_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or maps_start < self.bot.ready_time
            or not self.bot.data.loaded
        ):
            return
        try:
            await self.bot.waste_bin_channel.purge(
                before=maps_start - timedelta(hours=2)
            )
        except:
            pass
        map_embeds = {
            code: Embed(colour=Colour.dark_embed())
            for code in self.bot.json_dict["languages"].keys()
        }
        fifteen_minutes_ago = datetime.now() - timedelta(minutes=15)
        requirements_met = not all(
            [
                code in self.bot.maps.latest_maps.keys()
                and self.bot.maps.latest_maps[code].updated_at > fifteen_minutes_ago
                for code in self.bot.json_dict["languages"].keys()
            ]
        )
        if requirements_met:
            await self.bot.maps.update_base_map(
                planets=self.bot.data.planets,
                assignment=self.bot.data.assignment,
                campaigns=self.bot.data.campaigns,
                dss=self.bot.data.dss,
            )
        for language_code, embed in map_embeds.items():
            latest_map = self.bot.maps.latest_maps.get(language_code, None)
            if not latest_map:
                language_json = self.bot.json_dict["languages"][language_code]
                self.bot.maps.localize_map(
                    language_code_short=language_json["code"],
                    language_code_long=language_json["code_long"],
                    planets=self.bot.data.planets,
                    active_planets=[
                        campaign.planet.index for campaign in self.bot.data.campaigns
                    ],
                    dss=self.bot.data.dss,
                    planet_names_json=self.bot.json_dict["planets"],
                )
                message = await self.bot.waste_bin_channel.send(
                    file=File(
                        fp=self.bot.maps.FileLocations.localized_map_path(
                            language_json["code"]
                        )
                    )
                )
                self.bot.maps.latest_maps[language_json["code"]] = Maps.LatestMap(
                    datetime.now(), message.attachments[0].url
                )
                latest_map = self.bot.maps.latest_maps[language_json["code"]]
            embed.set_image(url=latest_map.map_link)
            embed.add_field("", f"-# Updated <t:{int(datetime.now().timestamp())}:R>")
        await self.bot.interface_handler.edit_maps(map_dict=map_embeds)
        self.bot.logger.info(
            f"Updated {len(self.bot.interface_handler.maps)} maps in {(datetime.now()-maps_start).total_seconds():.2f} seconds"
        )

    @map_poster.before_loop
    async def before_map_poster(self):
        await self.bot.wait_until_ready()

    @wait_for_startup()
    @commands.slash_command(
        description="Get an up-to-date map of the galaxy",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Get an up-to-date map of the galaxy. This is generated upon use of the command so it may take a couple of seconds.",
            "example_usage": "**`/map faction:Automaton public:Yes`** would return a map of the galaxy zoomed in on Automaton planets with names over active planets. It can also be seen by others in discord.",
        },
    )
    async def map(
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
            if not guild:
                self.bot.logger.error(
                    msg=f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuild.new(inter.guild_id)
        else:
            guild = GWWGuild.default()
        latest_map = self.bot.maps.latest_maps.get(guild.language, None)
        fifteen_minutes_ago = datetime.now() - timedelta(minutes=15)
        if not latest_map or (
            latest_map and latest_map.updated_at < fifteen_minutes_ago
        ):
            await self.bot.maps.update_base_map(
                planets=self.bot.data.planets,
                assignment=self.bot.data.assignment,
                campaigns=self.bot.data.campaigns,
                dss=self.bot.data.dss,
            )
            language_json = self.bot.json_dict["languages"][guild.language]
            self.bot.maps.localize_map(
                language_code_short=language_json["code"],
                language_code_long=language_json["code_long"],
                planets=self.bot.data.planets,
                active_planets=[
                    campaign.planet.index for campaign in self.bot.data.campaigns
                ],
                dss=self.bot.data.dss,
                planet_names_json=self.bot.json_dict["planets"],
            )
            message = await self.bot.waste_bin_channel.send(
                file=File(
                    fp=self.bot.maps.FileLocations.localized_map_path(
                        language_json["code"]
                    )
                )
            )
            self.bot.maps.latest_maps[language_json["code"]] = Maps.LatestMap(
                datetime.now(), message.attachments[0].url
            )
            latest_map = self.bot.maps.latest_maps[language_json["code"]]
        embed = Embed(colour=Colour.dark_embed())
        embed.set_image(url=latest_map.map_link)
        await inter.edit_original_response(content="", embed=embed)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(MapCog(bot))
