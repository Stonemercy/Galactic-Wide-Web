from datetime import datetime, time, timedelta
from disnake import (
    AppCmdInter,
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
        maps = Maps(
            data=self.bot.data,
            waste_bin_channel=self.bot.waste_bin_channel,
            planet_names_json=self.bot.json_dict["planets"],
            languages_json_list=[
                self.bot.json_dict["languages"][lang]
                for lang in list({guild.language for guild in GWWGuild.get_all()})
            ],
        )
        await maps.localize()
        await self.bot.interface_handler.edit_maps(maps.embeds)
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
        await inter.send(
            f"Map generating. Should be done <t:{int((datetime.now() + timedelta(seconds=10)).timestamp())}:R>",
            ephemeral=public != "Yes",
        )
        map = Maps(
            data=self.bot.data,
            waste_bin_channel=self.bot.waste_bin_channel,
            planet_names_json=self.bot.json_dict["planets"],
            languages_json_list=[self.bot.json_dict["languages"][guild.language]],
        )
        await map.localize()
        await inter.edit_original_response(content="", embeds=map.embeds.values())


def setup(bot: GalacticWideWebBot):
    bot.add_cog(MapCog(bot))
