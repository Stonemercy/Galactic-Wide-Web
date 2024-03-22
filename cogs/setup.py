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
        dashboard = Dashboard()
        await dashboard.get_data()
        dashboard.set_data()
        if not channel.permissions_for(inter.guild.me).send_messages:
            return await inter.send(
                "I don't have the `Send Messages` permission for that channel",
                ephemeral=True,
            )
        elif not channel.permissions_for(inter.guild.me).embed_links:
            return await inter.send(
                "I don't have the `Embed Links` permission for that channel",
                ephemeral=True,
            )
        elif not channel.permissions_for(inter.guild.me).attach_files:
            return await inter.send(
                "I don't have the `Attach Files` permission for that channel",
                ephemeral=True,
            )
        try:
            message = await channel.send(
                embeds=dashboard.embeds, file=File("resources/banner.png")
            )
        except Exception as e:
            print(e)
            return await inter.send(
                "An error has occured, I have contacted my Administrator.",
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
        if not channel.permissions_for(inter.guild.me).external_emojis:
            await inter.send(
                "I'm missing the `External Emojis` permission\nWhile not required, it makes the dashboard look better",
                ephemeral=True,
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
