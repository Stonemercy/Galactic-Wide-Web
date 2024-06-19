from logging import getLogger
from disnake import AppCmdInter, ModalInteraction
from disnake.ext import commands, tasks
from helpers.embeds import FeedbackEmbed
from helpers.modals import FeedbackModal

logger = getLogger("disnake")


class FeedbackCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.get_feedback_channel.start()

    def cog_unload(self):
        self.get_feedback_channel.stop()

    @tasks.loop(count=1)
    async def get_feedback_channel(self):
        self.channel = self.bot.get_channel(
            1253032256339968153
        ) or await self.bot.fetch_channel(1253032256339968153)

    @get_feedback_channel.before_loop
    async def before_feedback_channel(self):
        await self.bot.wait_until_ready()

    @commands.slash_command(description="Provide feedback for the bot")
    async def feedback(
        self,
        inter: AppCmdInter,
    ):
        logger.info(f"FeedbackCog, feedback command used")
        modal = FeedbackModal()
        return await inter.response.send_modal(modal)

    @commands.Cog.listener()
    async def on_modal_submit(self, inter: ModalInteraction):
        if inter.custom_id != "feedback":
            return
        embed = FeedbackEmbed(inter)
        await self.channel.send(embed=embed)
        await inter.send("Your feedback has been recieved, thank you.", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(FeedbackCog(bot))
