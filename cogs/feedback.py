from disnake import (
    AppCmdInter,
    Member,
    MessageInteraction,
    ModalInteraction,
    ButtonStyle,
)
from disnake.ext import commands
from disnake.ui import Button
from main import GalacticWideWebBot
from utils.checks import wait_for_startup
from utils.db import FeedbackDB, FeedbackRecord
from utils.embeds import FeedbackEmbed
from utils.modals import FeedbackModal


class FeedbackCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
        self.bot = bot
        self.feedback_users = {}

    @wait_for_startup()
    @commands.slash_command(description="Provide feedback for the bot")
    async def feedback(
        self,
        inter: AppCmdInter,
    ):
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name}"
        )
        user_in_db: FeedbackRecord = FeedbackDB.get_user(inter.user.id)
        if not user_in_db:
            user_in_db = FeedbackDB.new_user(inter.user.id)
        if user_in_db.banned:
            return await inter.send(
                f"You have been banned from providing feedback\nReason:\n# {user_in_db.reason}",
                ephemeral=True,
                components=Button(
                    label="Support Server",
                    style=ButtonStyle.link,
                    url="https://discord.gg/Z8Ae5H5DjZ",
                ),
            )
        modal = FeedbackModal()
        return await inter.response.send_modal(modal)

    @wait_for_startup()
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

    @wait_for_startup()
    @commands.Cog.listener("on_button_click")
    async def ban_listener(self, inter: MessageInteraction):
        button_id = inter.component.custom_id
        if button_id == "feedback_ban":
            user_to_ban = inter.message.embeds[0].author
            if user_to_ban.name in self.feedback_users:
                member: Member = self.feedback_users[user_to_ban.name]
                FeedbackDB.ban_user(member.id)
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
                FeedbackDB.good_user(member.id)
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
