from disnake import (
    AppCmdInter,
    Member,
    MessageInteraction,
    ModalInteraction,
    ButtonStyle,
)
from disnake.ext import commands, tasks
from disnake.ui import Button
from helpers.db import Feedback
from helpers.embeds import FeedbackEmbed
from helpers.modals import FeedbackModal


class FeedbackCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.feedback_users = {}
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
        self.bot.logger.info(f"FeedbackCog, feedback command used")
        user_in_db = Feedback.get_user(inter.user.id)
        if user_in_db == None:
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
        await self.channel.send(
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


def setup(bot: commands.Bot):
    bot.add_cog(FeedbackCog(bot))
