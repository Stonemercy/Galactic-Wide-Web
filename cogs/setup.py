from disnake import AppCmdInter, File, Permissions, TextChannel
from disnake.ext import commands
from helpers.db import Guilds
from helpers.embeds import Dashboard
from helpers.functions import pull_from_api


class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("Setup cog has finished loading")

    @commands.slash_command(
        description="Change the GWW settings for your server. Use this without arguments to see your set settings."
    )
    async def setup(
        self,
        inter: AppCmdInter,
        dashboard_channel: TextChannel = commands.Param(
            default=None,
            description="The channel you want the dashboard to be sent to. Set this to your current set channel to unset it.",
        ),
        announcement_channel: TextChannel = commands.Param(
            default=None,
            description="The channel you want announcements sent to. Set this to your current set channel to unset it.",
        ),
        patch_notes: str = commands.Param(
            default=None,
            description="Toggle if you want patch notes sent to the announcements channel, default = No",
            choices=["Yes", "No"],
        ),
    ):
        await inter.response.defer(ephemeral=True)
        if not inter.author.guild_permissions.manage_guild:
            return await inter.send(
                "You need `Manager Server` permissions to use this command"
            )
        guild_in_db = Guilds.get_info(inter.guild_id)
        if not guild_in_db:
            Guilds.insert_new_guild(inter.guild_id)
            guild_in_db = Guilds.get_info(inter.guild_id)
        if not dashboard_channel and not announcement_channel and not patch_notes:
            try:
                dashboard_channel = inter.guild.get_channel(
                    guild_in_db[1]
                ) or await inter.guild.fetch_channel(guild_in_db[1])
                dashboard_channel
            except:
                dashboard_channel = "Not set"
            try:
                dashboard_message = dashboard_channel.get_partial_message(
                    guild_in_db[2]
                ).jump_url
            except:
                dashboard_message = "Not Set"
            try:
                announcement_channel = (
                    inter.guild.get_channel(guild_in_db[3]).mention
                    or await inter.guild.fetch_channel(guild_in_db[3]).mention
                )
            except:
                announcement_channel = "Not set"
            if isinstance(dashboard_channel, TextChannel):
                dashboard_channel = dashboard_channel.mention
            return await inter.send(
                (
                    "Here are your current settings:\n"
                    f"Dashboard channel: {dashboard_channel}\n"
                    f"Dashboard message: {dashboard_message}\n"
                    f"Announcement channel: {announcement_channel}\n"
                    f"Patch notes enabled: {'Yes' if guild_in_db[4] == True else 'No'}\n\n"
                    "If you're seeing `Not set` where a channel/message should be, check the permissions for the bot!"
                ),
                ephemeral=True,
            )

        if dashboard_channel != None:
            if dashboard_channel.id == guild_in_db[1]:
                Guilds.update_dashboard(inter.guild_id, 0, 0)
                await inter.send(
                    "I have unset your Dashboard. You are free to delete any old Dashboards in this server.",
                    ephemeral=True,
                )
            else:
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
                    await inter.send(
                        (
                            f"I am missing one of the following permissions for {dashboard_channel.mention}:\n"
                            f"`View Channel\nSend MEssages\nEmbed Links\nAttach Files`"
                        ),
                        ephemeral=True,
                    )
                data = await pull_from_api(
                    get_campaigns=True,
                    get_assignments=True,
                    get_planet_events=True,
                    get_planets=True,
                    get_war_state=True,
                )
                dashboard = Dashboard(data)
                try:
                    message = await dashboard_channel.send(
                        embeds=dashboard.embeds, file=File("resources/banner.png")
                    )
                except Exception as e:
                    print("setup", e)
                    await inter.send(
                        "An error has occured, I have contacted Super Earth High Command.",
                        ephemeral=True,
                    )
                Guilds.update_dashboard(
                    inter.guild_id, dashboard_channel.id, message.id
                )
                await inter.send(
                    (
                        f"Dashboard Channel: {dashboard_channel.mention}\n"
                        f"Message link: {message.jump_url}\n"
                        "# GLORY TO SUPER EARTH"
                    ),
                    ephemeral=True,
                )
                if not dashboard_channel.permissions_for(
                    inter.guild.me
                ).external_emojis:
                    await inter.send(
                        "I'm missing the `External Emojis` permission\nWhile not required, it makes the dashboard look better",
                        ephemeral=True,
                    )
                messages: list = self.bot.get_cog("DashboardCog").messages
                for i in messages:
                    if i.guild == inter.guild:
                        try:
                            await i.delete()
                        except Exception as e:
                            print("Setup - Dashboard", e)
                        messages.remove(i)
                messages.append(message)

        if announcement_channel != None:
            if announcement_channel.id == guild_in_db[3]:
                Guilds.update_announcement_channel(inter.guild_id, 0)
                Guilds.update_patch_notes(inter.guild_id, False)
                await inter.send(
                    "I have unset your Announcements channel and set your patch notes have been disabled.",
                    ephemeral=True,
                )
            else:
                annnnouncement_perms_needed = Permissions(
                    view_channel=True, send_messages=True, embed_links=True
                )
                annnnouncement_perms_have = announcement_channel.permissions_for(
                    inter.guild.me
                ).is_superset(annnnouncement_perms_needed)
                if not annnnouncement_perms_have:
                    await inter.send(
                        (
                            f"I am missing one of the following permissions for {announcement_channel.mention}:\n"
                            f"`View Channel\nSend MEssages\nEmbed Links`"
                        ),
                        ephemeral=True,
                    )
                Guilds.update_announcement_channel(
                    inter.guild_id, announcement_channel.id
                )
                await inter.send(
                    (
                        f"Your announcements channel has been updated to {announcement_channel.mention}.\n"
                        "While no announcements show up straight away, they will when events happen"
                    ),
                    ephemeral=True,
                )
                channels: list = self.bot.get_cog("AnnouncementsCog").channels
                for i in channels:
                    if i.guild == inter.guild:
                        channels.remove(i)
                channels.append(announcement_channel)

        if patch_notes != None:
            patch_notes_enabled = guild_in_db[4]
            want_patch_notes = {"Yes": True, "No": False}[patch_notes]
            if guild_in_db[3] == 0 and dashboard_channel == None:
                return await inter.send(
                    "You need to setup the announcement channel before enabling patch notes.",
                    ephemeral=True,
                )
            if guild_in_db[4] == want_patch_notes:
                return await inter.send(
                    f"Your patch_notes setting was already set to **{patch_notes}**, nothing has changed.",
                    ephemeral=True,
                )
            if patch_notes_enabled != want_patch_notes:
                Guilds.update_patch_notes(inter.guild_id, want_patch_notes)
                patch_channels: list = self.bot.get_cog(
                    "AnnouncementsCog"
                ).patch_channels
                if want_patch_notes == True:
                    channel_id = (
                        announcement_channel.id
                        if announcement_channel != None
                        else guild_in_db[3]
                    )
                    try:
                        channel = inter.guild.get_channel(
                            channel_id
                        ) or await inter.guild.fetch_channel(channel_id)
                    except:
                        return await inter.send(
                            "I had trouble getting your announcement channel, please make sure I have appropriate permissions.",
                            ephemeral=True,
                        )
                    for i in patch_channels:
                        if i.guild.id == inter.guild_id:
                            patch_channels.remove(i)
                    patch_channels.append(channel)
                    return await inter.send(
                        (
                            f"Patch notes will now show up in {channel.mention}\n"
                            "While no patch notes show up straight away, they will when patches are released"
                        ),
                        ephemeral=True,
                    )
                else:
                    try:
                        channel = inter.guild.get_channel(
                            guild_in_db[3]
                        ) or await inter.guild.fetch_channel(guild_in_db[3])
                    except:
                        return await inter.send(
                            "I had trouble getting your announcement channel, please make sure I have appropriate permissions.",
                            ephemeral=True,
                        )
                    for i in patch_channels:
                        if i.guild.id == inter.guild.id:
                            patch_channels.remove(i)
                    return await inter.send(
                        (f"Patch notes will no longer show up in {channel.mention}\n"),
                        ephemeral=True,
                    )


def setup(bot: commands.Bot):
    bot.add_cog(SetupCog(bot))
