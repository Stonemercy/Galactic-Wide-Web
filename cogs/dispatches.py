from datetime import datetime
from disnake import (
    AppCmdInter,
    ApplicationInstallTypes,
    InteractionContextTypes,
    InteractionTimedOut,
    MessageInteraction,
    NotFound,
)
from disnake.ext import commands, tasks
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.dbv2 import GWWGuild, GWWGuilds, WarInfo
from utils.embeds import DispatchEmbed
from utils.interactables import DispatchStringSelect


class DispatchesCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        if not self.dispatch_check.is_running():
            self.dispatch_check.start()
            self.bot.loops.append(self.dispatch_check)

    def cog_unload(self):
        if self.dispatch_check.is_running():
            self.dispatch_check.stop()
            if self.dispatch_check in self.bot.loops:
                self.bot.loops.remove(self.dispatch_check)

    @tasks.loop(minutes=1)
    async def dispatch_check(self):
        dispatch_start = datetime.now()
        if (
            not self.bot.interface_handler.loaded
            or dispatch_start < self.bot.ready_time
            or not self.bot.data.loaded
            or self.bot.interface_handler.busy
        ):
            return
        current_war_info = WarInfo()
        if not current_war_info.dispatch_id:
            await self.bot.moderator_channel.send(
                "# No dispatch ID found in the database. Please check the war info table."
            )
            return
        for dispatch in self.bot.data.dispatches[-10:]:
            if current_war_info.dispatch_id < dispatch.id:
                if len(dispatch.full_message) < 5 or "#planet" in dispatch.full_message:
                    current_war_info.dispatch_id = dispatch.id
                    current_war_info.save_changes()
                    continue
                unique_langs = GWWGuilds().unique_languages
                embeds = {
                    lang: [
                        DispatchEmbed(self.bot.json_dict["languages"][lang], dispatch)
                    ]
                    for lang in unique_langs
                }
                await self.bot.interface_handler.send_feature(
                    "war_announcements", embeds
                )
                current_war_info.dispatch_id = dispatch.id
                current_war_info.save_changes()
                self.bot.logger.info(
                    f"Sent dispatch out to {len(self.bot.interface_handler.war_announcements)} channels in {(datetime.now() - dispatch_start).total_seconds():.2f}s"
                )
                return

    @dispatch_check.before_loop
    async def before_dispatch_check(self):
        await self.bot.wait_until_ready()

    @wait_for_startup()
    @commands.slash_command(
        description="Get the 25 most recent dispatches",
        install_types=ApplicationInstallTypes.all(),
        contexts=InteractionContextTypes.all(),
        extras={
            "long_description": "Returns the 25 latest dispatches with a dropdown to select other ones via id-title.",
            "example_usage": "**`/dispatches public:Yes`** returns an embed with the most recent patch notes, it also has a dropdown for the most recent 10 patch notes you can choose from. Other people can see this too.",
        },
    )
    async def dispatches(
        self,
        inter: AppCmdInter,
        specific: int = commands.Param(
            default=None, description="Get a specific dispatch by ID"
        ),
        public: str = commands.Param(
            choices=["Yes", "No"],
            default="No",
            description="Do you want other people to see the response to this command?",
        ),
    ):
        try:
            await inter.response.defer(ephemeral=public != "Yes")
        except (NotFound, InteractionTimedOut):
            await inter.channel.send(
                "There was an error with that command, please try again.",
                delete_after=5,
            )
            return
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{specific = }> <{public = }>"
        )
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    msg=f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild_id, "en", [])
        else:
            guild = GWWGuild.default()
        dispatch = None
        if specific:
            specific_dispatch_list = [
                d for d in self.bot.data.dispatches if d.id == specific
            ]
            if specific_dispatch_list != []:
                dispatch = specific_dispatch_list[0]
        else:
            dispatch = self.bot.data.dispatches[-1]
        if not dispatch:
            await inter.send("I couldn't find that dispatch, sorry.", ephemeral=True)
            return
        await inter.send(
            embed=DispatchEmbed(
                language_json=self.bot.json_dict["languages"][guild.language],
                dispatch=dispatch,
                with_time=True,
            ),
            components=[DispatchStringSelect(self.bot.data.dispatches)],
            ephemeral=public != "Yes",
        )

    @commands.Cog.listener("on_dropdown")
    async def dispatches_listener(self, inter: MessageInteraction):
        if inter.component.custom_id != "dispatch":
            return
        dispatch = [
            d
            for d in self.bot.data.dispatches
            if d.id == int(inter.values[0].split("-")[0])
        ][0]
        if inter.guild:
            guild = GWWGuilds.get_specific_guild(id=inter.guild_id)
            if not guild:
                self.bot.logger.error(
                    msg=f"Guild {inter.guild_id} - {inter.guild.name} - had the bot installed but wasn't found in the DB"
                )
                guild = GWWGuilds.add(inter.guild_id, "en", [])
        else:
            guild = GWWGuild.default()
        embed = DispatchEmbed(
            language_json=self.bot.json_dict["languages"][guild.language],
            dispatch=dispatch,
            with_time=True,
        )
        await inter.response.edit_message(embed=embed)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(DispatchesCog(bot))
