from disnake import (
    AppCmdInter,
    Member,
    MessageInteraction,
    ModalInteraction,
    ButtonStyle,
)
from disnake.ext import commands
from disnake.ui import Button
from helpers.db import Feedback
from helpers.embeds import FeedbackEmbed
from helpers.modals import FeedbackModal
from main import GalacticWideWebBot


class FeedbackCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.feedback_users = {}

    @commands.slash_command(description="Provide feedback for the bot")
    async def feedback(
        self,
        inter: AppCmdInter,
    ):
        self.bot.logger.info(f"FeedbackCog, feedback command used")
        user_in_db = Feedback.get_user(inter.user.id)
        if not user_in_db:
            user_in_db = Feedback.new_user(inter.user.id)
        if user_in_db[1] == True:
            return await inter.send(
                f"You have been banned from providing feedback\nReason: {user_in_db[2]}",
                ephemeral=True,
                components=Button(
                    label="Support Server",
                    style=ButtonStyle.link,
                    url="https://discord.gg/Z8Ae5H5DjZ",
                ),
            )
        modal = FeedbackModal()
        return await inter.response.send_modal(modal)

    @commands.Cog.listener()
    async def on_modal_submit(self, inter: ModalInteraction):
        if inter.custom_id != "feedback":
            return
        embed = FeedbackEmbed(inter)
        self.feedback_users[inter.author.name] = inter.author
        await self.bot.feedback_channel.send(
            embed=embed,
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
        if button_id == "feedback_ban":
            user_to_ban = inter.message.embeds[0].author
            if user_to_ban.name in self.feedback_users:
                member: Member = self.feedback_users[user_to_ban.name]
                Feedback.ban_user(member.id)
                await inter.send(
                    f"{member.mention} banned", ephemeral=True, delete_after=10
                )
            else:
                return await inter.send(
                    "User not in `self.feedback_users`.\nLOOK INTO THIS", ephemeral=True
                )
        elif button_id == "feedback_good":
            good_user = inter.message.embeds[0].author
            if good_user.name in self.feedback_users:
                member: Member = self.feedback_users[good_user.name]
                Feedback.good_user(member.id)
                await inter.send(
                    f"{member.mention} labeled as a good user",
                    ephemeral=True,
                    delete_after=10,
                )
            else:
                return await inter.send(
                    "User not in `self.feedback_users`.\nLOOK INTO THIS", ephemeral=True
                )


def setup(bot: GalacticWideWebBot):
    bot.add_cog(FeedbackCog(bot))
