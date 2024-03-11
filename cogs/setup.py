from disnake import AppCmdInter, File, Message, TextChannel
from disnake.ext import commands
from helpers.db import Guilds
from helpers.embeds import Dashboard


class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Setup cog has finished loading")

    @commands.slash_command(
        description="Choose which channel the dashboard will be in for your server (this can be changed later)"
    )
    async def setup(self, inter: AppCmdInter, channel: TextChannel):
        await inter.response.defer()
        dashboard = Dashboard()
        await dashboard.get_data()
        dashboard.set_data()
        try:
            message = await channel.send(
                embeds=dashboard.embeds, file=File("resources/banner.jpg")
            )
        except:
            return await inter.send(
                "I don't have permission to post in that channel, please check the permissions",
                ephemeral=True,
            )
        Guilds.set_info(inter.guild.id, channel.id, message.id)
        dashboard_info = Guilds.get_info(inter.guild.id)
        if not dashboard_info:
            await inter.send(
                "Something went wrong, please contact my owner",
                ephemeral=True,
                delete_after=10.0,
            )
        await inter.send(
            (
                f"Dashboard Channel: {channel.mention}\n"
                f"Message link: {message.jump_url}"
            ),
            ephemeral=True,
            delete_after=10.0,
        )
        messages: list[Message] = self.bot.get_cog("DashboardCog").messages
        for i in messages:
            if i.guild == inter.guild:
                try:
                    await i.delete()
                except Exception as e:
                    print("Setup", e)
                messages.remove(i)
        messages.append(message)
        print(
            f"Setup complete, {len(self.bot.get_cog('DashboardCog').messages)} messages cached"
        )


def setup(bot: commands.Bot):
    bot.add_cog(SetupCog(bot))
