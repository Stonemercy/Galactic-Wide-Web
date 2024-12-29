from asyncio import sleep
from datetime import datetime, time, timedelta
from disnake import (
    AppCmdInter,
    PartialMessage,
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

    async def update_message(self, message: PartialMessage, embed_dict):
        guild = GWWGuild.get_by_id(message.guild.id)
        if not guild and message in self.bot.map_messages:
            self.bot.map_messages.remove(message)
            return self.bot.logger.error(
                f"{self.qualified_name} | update_message | {guild = } | {message.guild.id = }"
            )
        try:
            await message.edit(embed=embed_dict[guild.language])
        except Exception as e:
            if message in self.bot.map_messages:
                self.bot.map_messages.remove(message)
            return self.bot.logger.error(
                f"{self.qualified_name} | update_message | {e} | removed from self.bot.map_messages | {message.channel.id = }"
            )

    @tasks.loop(time=[time(hour=hour, minute=5, second=0) for hour in range(24)])
    async def map_poster(self):
        update_start = datetime.now()
        if (
            not self.bot.map_messages
            or update_start < self.bot.ready_time
            or not self.bot.data.loaded
            or not self.bot.c_n_m_loaded
        ):
            return
        try:
            await self.bot.waste_bin_channel.purge(
                before=update_start - timedelta(hours=2)
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
        maps_updated = 0
        for chunk in [
            self.bot.map_messages[i : i + 50]
            for i in range(0, len(self.bot.map_messages), 50)
        ]:
            for message in chunk:
                self.bot.loop.create_task(
                    self.update_message(
                        message,
                        maps.embeds,
                    )
                )
                maps_updated += 1
            await sleep(1.5)
        self.bot.logger.info(
            f"Updated {maps_updated} maps in {(datetime.now() - update_start).total_seconds():.2f} seconds"
        )
        return maps_updated

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
