from disnake import (
    AppCmdInter,
    MessageInteraction,
    ModalInteraction,
    ButtonStyle,
)
from disnake.ext import commands
from disnake.ui import Button
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import FeedbackUser
from utils.embeds import FeedbackEmbed
from utils.modals import FeedbackModal


class FeedbackCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot

    @wait_for_startup()
    @commands.slash_command(description="Provide feedback for the bot")
    async def feedback(
        self,
        inter: AppCmdInter,
    ):
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name}"
        )
        feedback_user = FeedbackUser.get_by_id(inter.user.id)
        if not feedback_user:
            feedback_user = FeedbackUser.new(inter.user.id)
        if feedback_user.banned:
            return await inter.send(
                f"You have been banned from providing feedback\nReason:\n# {feedback_user.reason}",
                ephemeral=True,
                components=Button(
                    label="Support Server",
                    style=ButtonStyle.link,
                    url="https://discord.gg/Z8Ae5H5DjZ",
                ),
            )
        return await inter.response.send_modal(FeedbackModal())

    @commands.Cog.listener()
    async def on_modal_submit(self, inter: ModalInteraction):
        if inter.custom_id != "feedback":
            return
        await self.bot.feedback_channel.send(
            embed=FeedbackEmbed(inter),
            components=[
                Button(label="BAN", style=ButtonStyle.danger, custom_id="feedback_ban"),
                Button(
                    label="GOOD FEEDBACK",
                    style=ButtonStyle.green,
                    custom_id="feedback_good",
                ),
            ],
        )
        await inter.send("Your feedback has been recieved, thank you.", ephemeral=True)

    @commands.Cog.listener("on_button_click")
    async def ban_listener(self, inter: MessageInteraction):
        button_id = inter.component.custom_id
        if "feedback" in button_id:
            feedback_user = FeedbackUser.get_by_id(inter.message.embeds[0].author.name)
        if button_id == "feedback_ban":
            feedback_user.banned = True
            feedback_user.save_changes()
            return await inter.send(f"<@{feedback_user.user_id}> banned")
        elif button_id == "feedback_good":
            feedback_user.good_feedback = True
            feedback_user.save_changes()
            return await inter.send(
                f"<@{feedback_user.user_id}> labeled as a good user",
            )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(FeedbackCog(bot))
