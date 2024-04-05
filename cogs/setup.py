from disnake import AppCmdInter, File, Message, Permissions, TextChannel
from disnake.ext import commands
from helpers.db import Guilds
from helpers.embeds import Dashboard
from data.lists import language_dict, language_change_dict
from helpers.functions import get_info


class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Setup cog has finished loading")

    @commands.slash_command(description="Change the GWW settings for your server")
    async def setup(
        self,
        inter: AppCmdInter,
        dashboard_channel: TextChannel = commands.Param(
            default=None, description="The channel you want the dashboard to be sent to"
        ),
        announcement_channel: TextChannel = commands.Param(
            default=None,
            description="The channel you want War Announcements and Major Orders sent to",
        ),
        language: str = commands.Param(
            choices=list(language_dict.keys()),
            default=None,
            description="The language you want some of the dashboard in. Default = English",
        ),
    ):
        if not inter.author.guild_permissions.manage_guild:
            return await inter.send(
                "You need `Manager Server` permissions to use this command"
            )
        await inter.response.defer(ephemeral=True)
        guild_in_db = Guilds.get_info(inter.guild_id)
        if not guild_in_db:
            Guilds.insert_new_guild(inter.guild_id)
            guild_in_db = Guilds.get_info(inter.guild_id)

        if (
            dashboard_channel == None
            and announcement_channel == None
            and language == None
        ):
            return await inter.send(
                "You need to choose something to setup, you can't setup nothing",
                ephemeral=True,
            )

        if language != None:
            Guilds.update_language(inter.guild_id, language_dict[language])
            await inter.send(
                language_change_dict[language],
                ephemeral=True,
            )

        if dashboard_channel != None:
            dashboard_perms_needed = Permissions(
                send_messages=True,
                view_channel=True,
                attach_files=True,
                embed_links=True,
            )
            dashboard_perms_have = dashboard_channel.permissions_for(
                inter.guild.me
            ).is_superset(dashboard_perms_needed)
            if not dashboard_perms_have:
                return await inter.send(
                    (
                        f"I am missing one of the following permissions for {dashboard_channel.mention}:\n"
                        f"`View Channel\nSend MEssages\nEmbed Links\nAttach Files`"
                    ),
                    ephemeral=True,
                )
            if language == None:
                reverse_dict = {v: k for k, v in language_dict.items()}
                language = reverse_dict[guild_in_db[4]]
            info = await get_info()
            dashboard = Dashboard(language, info)
            await dashboard.get_data()
            dashboard.set_data()
            try:
                message = await dashboard_channel.send(
                    embeds=dashboard.embeds, file=File("resources/banner.png")
                )
            except Exception as e:
                print("setup", e)
                return await inter.send(
                    "An error has occured, I have contacted Super Earth High Command.",
                    ephemeral=True,
                )
            Guilds.update_dashboard(inter.guild_id, dashboard_channel.id, message.id)
            dashboard_info = Guilds.get_info(inter.guild.id)
            if not dashboard_info:
                return await inter.send(
                    "It appears the data used to setup the dashboard was lost in cyberspace.\nSuper Earth High Command has been notified.",
                    ephemeral=True,
                )
            await inter.send(
                (
                    f"Dashboard Channel: {dashboard_channel.mention}\n"
                    f"Message link: {message.jump_url}\n"
                    "# GLORY TO SUPER EARTH"
                ),
                ephemeral=True,
            )
            if not dashboard_channel.permissions_for(inter.guild.me).external_emojis:
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
                        print("Setup - Dashboard", e)
                    messages.remove(i)
            messages.append(message)
        if announcement_channel != None:
            annnnouncement_perms_needed = Permissions(
                view_channel=True, send_messages=True, embed_links=True
            )
            annnnouncement_perms_have = announcement_channel.permissions_for(
                inter.guild.me
            ).is_superset(annnnouncement_perms_needed)
            if not annnnouncement_perms_have:
                return await inter.send(
                    (
                        f"I am missing one of the following permissions for {announcement_channel.mention}:\n"
                        f"`View Channel\nSend MEssages\nEmbed Links`"
                    ),
                    ephemeral=True,
                )
            Guilds.update_announcement_channel(inter.guild_id, announcement_channel.id)
            await inter.send(
                f"Your announcements channel has been updated to {announcement_channel.mention}.",
                ephemeral=True,
            )
            channels: list[TextChannel] = self.bot.get_cog(
                "MOAnnouncementsCog"
            ).channels
            for i in channels:
                if i.guild == inter.guild:
                    channels.remove(i)
            channels.append(announcement_channel)


def setup(bot: commands.Bot):
    bot.add_cog(SetupCog(bot))
