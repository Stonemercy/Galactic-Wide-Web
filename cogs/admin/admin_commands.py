from asyncio import sleep
from datetime import datetime
from logging import getLogger
from os import getenv
from disnake import AppCmdInter
from disnake.ext import commands
from helpers.db import Feedback, Guilds
from helpers.embeds import AnnouncementEmbed, Dashboard
from helpers.functions import dashboard_maps, pull_from_api

logger = getLogger("disnake")
support_server = [int(getenv("SUPPORT_SERVER"))]


class AdminCommandsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
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
        }

    @commands.slash_command(
        guild_ids=support_server,
        description="You shouldn't be able to see this",
    )
    async def force_update_dashboard(self, inter: AppCmdInter):
        update_start = datetime.now()
        logger.critical(
            f"AdminCommandsCog, {inter.application_command.name} command used by {inter.author.id} - {inter.author.name}"
        )
        if inter.author.id != self.bot.owner_id:
            return await inter.send(
                "You can't use this", ephemeral=True, delete_after=3.0
            )
        await inter.response.defer(ephemeral=True)
        dashboards_updated = await self.bot.get_cog("DashboardCog").dashboard(
            force=True
        )
        text = f"Forced updates of {dashboards_updated} dashboards in {(datetime.now() - update_start).total_seconds():.2f} seconds"
        logger.info(text)
        await inter.send(text, ephemeral=True)

    @commands.slash_command(
        guild_ids=support_server,
        description="You shouldn't be able to see this",
    )
    async def force_update_maps(self, inter: AppCmdInter):
        update_start = datetime.now()
        logger.critical(
            f"AdminCommandsCog, {inter.application_command.name} command used by {inter.author.id} - {inter.author.name}"
        )
        if inter.author.id != self.bot.owner_id:
            return await inter.send(
                "You can't use this", ephemeral=True, delete_after=3.0
            )
        await inter.response.defer(ephemeral=True)
        maps_updated = await self.bot.get_cog("MapCog").map_poster(force=True)
        text = f"Forced updates of {maps_updated} maps in {(datetime.now() - update_start).total_seconds():.2f} seconds"
        logger.info(text)
        await inter.send(text, ephemeral=True)

    @commands.slash_command(
        guild_ids=support_server,
        description="You shouldn't be able to see this",
    )
    async def send_announcement(self, inter: AppCmdInter, test: bool = False):
        update_start = datetime.now()
        logger.critical(
            f"AdminCommandsCog, {inter.application_command.name} command used by {inter.author.id} - {inter.author.name}"
        )
        if inter.author.id != self.bot.owner_id:
            return await inter.send(
                "You can't use this", ephemeral=True, delete_after=3.0
            )
        await inter.response.defer(ephemeral=True)
        embeds = {}
        languages = Guilds.get_used_languages()
        for lang in languages:
            embeds[lang] = AnnouncementEmbed()
        if test == True:
            return await inter.send(embed=embeds["en"], ephemeral=True)
        channels = self.bot.get_cog("AnnouncementsCog").channels
        chunked_channels = [channels[i : i + 50] for i in range(0, len(channels), 50)]
        for chunk in chunked_channels:
            for channel in chunk:
                self.bot.loop.create_task(
                    self.bot.get_cog("AnnouncementsCog").send_embed(
                        channel, embeds, "Announcement"
                    )
                )
            await sleep(1.025)
        await inter.send(
            f"Attempted to send out an announcement to {len(channels)} channels in {(datetime.now() - update_start).total_seconds():.2f} seconds",
            ephemeral=True,
        )

    @commands.slash_command(
        guild_ids=support_server,
        description="You shouldn't be able to see this",
    )
    async def feedback_unban(self, inter: AppCmdInter, user_id):
        Feedback.unban_user(user_id)
        if inter.author.id != self.bot.owner_id:
            return await inter.send(
                "You can't use this", ephemeral=True, delete_after=3.0
            )
        await inter.send(f"Unbanned {user_id}", ephemeral=True)

    @commands.slash_command(
        guild_ids=support_server,
        description="You shouldn't be able to see this",
    )
    async def feedback_ban_reason(self, inter: AppCmdInter, user_id, reason):
        if inter.author.id != self.bot.owner_id:
            return await inter.send(
                "You can't use this", ephemeral=True, delete_after=3.0
            )
        user = Feedback.get_user(user_id)
        if user == None:
            return await inter.send("That user doesn't exist in the db", ephemeral=True)
        elif user[1] == False:
            return await inter.send("That user isn't banned", ephemeral=True)
        Feedback.set_reason(user_id, reason)
        await inter.send(f"Reason set for {user_id}:\n{reason}", ephemeral=True)

    @commands.slash_command(
        guild_ids=support_server,
        description="You shouldn't be able to see this",
    )
    async def not_good_feedback(self, inter: AppCmdInter, user_id):
        if inter.author.id != self.bot.owner_id:
            return await inter.send(
                "You can't use this", ephemeral=True, delete_after=3.0
            )
        user = Feedback.get_user(user_id)
        if user == None:
            return await inter.send("That user doesn't exist in the db", ephemeral=True)
        elif user[3] == False:
            return await inter.send("That user isn't a good user", ephemeral=True)
        Feedback.not_good_user(user_id)
        await inter.send(f"User **{user_id}** set as not-good feedback", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(AdminCommandsCog(bot))
