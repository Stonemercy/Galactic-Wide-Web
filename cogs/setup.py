from json import load
from logging import getLogger
from disnake import AppCmdInter, File, Permissions, TextChannel
from disnake.ext import commands
from helpers.db import Guilds
from helpers.embeds import Dashboard, SetupEmbed
from helpers.functions import dashboard_maps, pull_from_api
from data.lists import language_dict

logger = getLogger("disnake")


class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.faction_colour = {
            "Automaton": (252, 76, 79),
            "automaton": (126, 38, 22),
            "Terminids": (253, 165, 58),
            "terminids": (126, 82, 29),
            "Illuminate": (116, 163, 180),
            "illuminate": (58, 81, 90),
            "Humans": (36, 205, 76),
            "humans": (18, 102, 38),
        }
        self.dashboard_perms_needed = Permissions(
            send_messages=True,
            view_channel=True,
            attach_files=True,
            embed_links=True,
            use_external_emojis=True,
        )
        self.annnnouncement_perms_needed = Permissions(
            view_channel=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            use_external_emojis=True,
        )
        self.map_perms_needed = Permissions(
            view_channel=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
        )

    @commands.slash_command(
        description="Change the GWW settings for your server. Use this without options to see your set settings."
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
        map_channel: TextChannel = commands.Param(
            default=None,
            description="The channel you want the map sent to. Set this to your current set channel to unset it.",
        ),
        language: str = commands.Param(
            default=None,
            description="The language you want the bot to respond in",
            choices=language_dict,
        ),
    ):
        logger.info(
            f"SetupCog, setup dashboard_channel:{dashboard_channel} announcement_channel:{announcement_channel} patch_notes:{patch_notes} map_channel:{map_channel} language:{language} command used"
        )
        if not inter.author.guild_permissions.manage_guild:
            return await inter.send(
                "You need `Manager Server` permissions to use this command"
            )
        await inter.response.defer(ephemeral=True)
        embed = SetupEmbed()
        guild_in_db = Guilds.get_info(inter.guild_id)
        if not guild_in_db:
            Guilds.insert_new_guild(inter.guild_id)
            guild_in_db = Guilds.get_info(inter.guild_id)
        guild_language = load(
            open(f"data/languages/{guild_in_db[5]}.json", encoding="UTF-8")
        )
        inv_lang_dict = {v: k for k, v in language_dict.items()}
        if (
            not dashboard_channel
            and not announcement_channel
            and not patch_notes
            and not map_channel
            and not language
        ):
            try:
                dashboard_channel = inter.guild.get_channel(
                    guild_in_db[1]
                ) or await inter.guild.fetch_channel(guild_in_db[1])
            except:
                dashboard_channel = guild_language["setup.not_set"]
            try:
                dashboard_message = dashboard_channel.get_partial_message(
                    guild_in_db[2]
                ).jump_url
            except:
                dashboard_message = guild_language["setup.not_set"]
            if isinstance(dashboard_channel, TextChannel):
                dashboard_channel = dashboard_channel.mention
            embed.add_field(
                "Dashboard",
                (
                    f"{guild_language['setup.dashboard_channel']}: {dashboard_channel}\n"
                    f"{guild_language['setup.dashboard_message']}: {dashboard_message}"
                ),
                inline=False,
            )
            try:
                announcement_channel = (
                    inter.guild.get_channel(guild_in_db[3]).mention
                    or await inter.guild.fetch_channel(guild_in_db[3]).mention
                )
            except:
                announcement_channel = guild_language["setup.not_set"]
            finally:
                embed.add_field(
                    "Announcements",
                    f"{guild_language['setup.announcement_channel']}: {announcement_channel}",
                    inline=False,
                )
            try:
                map_channel = inter.guild.get_channel(
                    guild_in_db[6]
                ) or await inter.guild.fetch_channel(guild_in_db[6])
            except:
                map_channel = guild_language["setup.not_set"]
            try:
                map_message = map_channel.get_partial_message(guild_in_db[7]).jump_url
            except:
                map_message = guild_language["setup.not_set"]
            if isinstance(map_channel, TextChannel):
                map_channel = map_channel.mention
            embed.add_field(
                "Map",
                (
                    f"{guild_language['setup.map_channel']}: {map_channel}\n"
                    f"{guild_language['setup.map_message']}: {map_message}"
                ),
                inline=False,
            )
            embed.add_field(
                guild_language["setup.language"],
                inv_lang_dict[guild_in_db[5]],
                inline=False,
            )
            embed.add_field("", guild_language["setup.message"], inline=False)
            embed.title = guild_language["setup.current_settings"]
            return await inter.send(embed=embed, ephemeral=True)

        if language != None:
            current_lang = guild_in_db[5]
            if current_lang == language:
                embed.add_field(
                    "Language",
                    (
                        f"**{inv_lang_dict[current_lang]}** ➡️ **{inv_lang_dict[language]}**\n"
                        f"*{guild_language['setup.language_same']}*"
                    ),
                    inline=False,
                )
            else:
                Guilds.update_language(inter.guild_id, language)
                guild_language = load(
                    open(f"data/languages/{language}.json", encoding="UTF-8")
                )
                embed.add_field(
                    "Language",
                    (f"{inv_lang_dict[current_lang]} ➡️ {inv_lang_dict[language]}"),
                    inline=False,
                )
                guild_in_db = Guilds.get_info(inter.guild_id)

        if dashboard_channel != None:
            if dashboard_channel.id == guild_in_db[1]:
                Guilds.update_dashboard(inter.guild_id, 0, 0)
                embed.add_field(
                    "Dashboard Channel",
                    (
                        f"**{guild_in_db[1]}** ➡️ **0**\n"
                        f"*{guild_language['setup.unset_dashboard']}*"
                    ),
                    inline=False,
                )
                guild_in_db = Guilds.get_info(inter.guild_id)
            else:
                dashboard_perms_have = dashboard_channel.permissions_for(
                    inter.guild.me
                ).is_superset(self.dashboard_perms_needed)
                if not dashboard_perms_have:
                    embed.add_field(
                        "Dashboard", guild_language["setup.missing_perm"], inline=False
                    )
                else:
                    data = await pull_from_api(
                        get_campaigns=True,
                        get_assignments=True,
                        get_planet_events=True,
                        get_planets=True,
                        get_war_state=True,
                    )
                    for data_key, data_value in data.items():
                        if data_value == None and data_key != "planet_events":
                            logger.error(
                                f"SetupCog, dashboard, {data_key} returned {data_value}"
                            )
                            return await inter.send(
                                "There was an issue connecting to the datacentre. Please try again.",
                                ephemeral=True,
                            )
                    dashboard = Dashboard(data, guild_in_db[5])
                    try:
                        message = await dashboard_channel.send(
                            embeds=dashboard.embeds, file=File("resources/banner.png")
                        )
                    except Exception as e:
                        logger.error(f"SetupCog, dashboard setup, {e}")
                        return await inter.send(
                            "An error has occured, I have contacted Super Earth High Command.",
                            ephemeral=True,
                        )
                    Guilds.update_dashboard(
                        inter.guild_id, dashboard_channel.id, message.id
                    )
                    embed.add_field(
                        "Dashboard",
                        (
                            f"{guild_language['setup.dashboard_channel']}: {dashboard_channel.mention}\n"
                            f"{guild_language['setup.dashboard_message']}: {message.jump_url}\n"
                        ),
                    )
                    guild_in_db = Guilds.get_info(inter.guild_id)
                    messages: list = self.bot.get_cog("DashboardCog").messages
                    for i in messages:
                        if i.guild == inter.guild:
                            try:
                                await i.delete()
                            except Exception as e:
                                logger.error(f"SetupCog, dashboard setup, {e}")
                            messages.remove(i)
                    messages.append(message)

        if announcement_channel != None:
            if announcement_channel.id == guild_in_db[3]:
                Guilds.update_announcement_channel(inter.guild_id, 0)
                Guilds.update_patch_notes(inter.guild_id, False)
                embed.add_field(
                    "Announcements",
                    (
                        f"{guild_in_db[3]} ➡️ 0\n"
                        f"{guild_in_db[4]} ➡️ False\n"
                        f"*{guild_language['setup.unset_announce']}*"
                    ),
                    inline=False,
                )
                guild_in_db = Guilds.get_info(inter.guild_id)
            else:
                annnnouncement_perms_have = announcement_channel.permissions_for(
                    inter.guild.me
                ).is_superset(self.annnnouncement_perms_needed)
                if not annnnouncement_perms_have:
                    embed.add_field(
                        "Announcements",
                        guild_language["setup.missing_perm"],
                        inline=False,
                    )
                else:
                    Guilds.update_announcement_channel(
                        inter.guild_id, announcement_channel.id
                    )
                    embed.add_field(
                        "Announcements",
                        (
                            f"{guild_language['setup.announcement_channel']}: {announcement_channel.mention}\n"
                            f"*{guild_language['setup.announce_warn']}*"
                        ),
                        inline=False,
                    )
                    guild_in_db = Guilds.get_info(inter.guild_id)
                    channels: list = self.bot.get_cog("AnnouncementsCog").channels
                    for i in channels:
                        if i.guild == inter.guild:
                            channels.remove(i)
                    channels.append(announcement_channel)

        if map_channel != None:
            if map_channel.id == guild_in_db[6]:
                Guilds.update_map(inter.guild_id, 0, 0)
                embed.add_field(
                    "Map", f"*{guild_language['setup.unset_map']}*", inline=False
                )
                guild_in_db = Guilds.get_info(inter.guild_id)
            else:
                map_perms_have = map_channel.permissions_for(
                    inter.guild.me
                ).is_superset(self.map_perms_needed)
                if not map_perms_have:
                    embed.add_field(
                        "Map", f"*{guild_language['setup.missing_perm']}*", inline=False
                    )
                else:
                    data = await pull_from_api(
                        get_campaigns=True, get_planets=True, get_assignments=True
                    )
                    for data_key, data_value in data.items():
                        if data_value == None and data_key != "planet_events":
                            logger.error(
                                f"SetupCog, map, {data_key} returned {data_value}"
                            )
                            return await inter.send(
                                "There was an issue connecting to the datacentre. Please try again.",
                                ephemeral=True,
                            )
                    else:
                        channel = self.bot.get_channel(1242843098363596883)
                        map_embeds = await dashboard_maps(data, channel)
                        map_embed = map_embeds[guild_in_db[5]]
                        message = await map_channel.send(
                            embed=map_embed,
                        )
                        Guilds.update_map(inter.guild_id, map_channel.id, message.id)
                        embed.add_field(
                            "Map",
                            (
                                f"{guild_language['setup.map_channel']}: {map_channel.mention}\n"
                                f"{guild_language['setup.map_message']}: {message.jump_url}\n"
                            ),
                            inline=False,
                        )
                        guild_in_db = Guilds.get_info(inter.guild_id)
                        messages: list = self.bot.get_cog("MapCog").messages
                        for i in messages:
                            if i.guild == inter.guild:
                                try:
                                    await i.delete()
                                except Exception as e:
                                    logger.error(f"SetupCog, map setup, {e}")
                                messages.remove(i)
                        messages.append(message)

        if patch_notes != None:
            want_patch_notes = patch_notes == "Yes"
            if guild_in_db[3] == 0 and dashboard_channel == None:
                embed.add_field(
                    "Patch Notes", guild_language["setup.need_announce"], inline=False
                )
            if guild_in_db[4] == want_patch_notes:
                embed.add_field(
                    "Patch Notes",
                    (
                        f"**{guild_in_db[4]}** ➡️ **{want_patch_notes}**\n"
                        f"*{guild_language['setup.patch_notes_same']}*"
                    ),
                    inline=False,
                )
            if guild_in_db[4] != want_patch_notes:
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
                        embed.add_field(
                            "Patch Notes",
                            f"*{guild_language['setup.cant_get_announce_channel']}*",
                            inline=False,
                        )
                    for i in patch_channels:
                        if i.guild.id == inter.guild_id:
                            patch_channels.remove(i)
                    patch_channels.append(channel)
                    embed.add_field(
                        "Patch Notes",
                        (
                            f"**{guild_in_db[4]}** ➡️ **{want_patch_notes}**\n"
                            f"*{guild_language['setup.patch_notes_enabled']}*"
                        ),
                        inline=False,
                    )
                else:
                    try:
                        channel = inter.guild.get_channel(
                            guild_in_db[3]
                        ) or await inter.guild.fetch_channel(guild_in_db[3])
                    except:
                        embed.add_field(
                            "Patch Notes",
                            f"*{guild_language['setup.cant_get_announce_channel']}*",
                            inline=False,
                        )
                    for i in patch_channels:
                        if i.guild.id == inter.guild.id:
                            patch_channels.remove(i)
                    embed.add_field(
                        "Patch Notes",
                        f"*{guild_language['setup.patch_notes_disabled']}*",
                        inline=False,
                    )

        await inter.send(embed=embed, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(SetupCog(bot))
