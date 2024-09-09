from data.lists import language_dict
from disnake import AppCmdInter, File, Permissions, TextChannel
from disnake.ext import commands
from json import load
from main import GalacticWideWebBot
from utils.api import API, Data
from utils.checks import wait_for_startup
from utils.db import GuildRecord, GuildsDB
from utils.embeds import Dashboard, SetupEmbed
from utils.functions import dashboard_maps


class SetupCog(commands.Cog):
    def __init__(self, bot: GalacticWideWebBot):
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
            use_external_emojis=True,
        )
        self.map_perms_needed = Permissions(
            view_channel=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
        )

    @wait_for_startup()
    @commands.slash_command(
        description="Change the GWW settings for your server. Use this without options to see your set settings.",
        default_member_permissions=Permissions(manage_guild=True),
        dm_permission=False,
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
        await inter.response.defer(ephemeral=True)
        self.bot.logger.info(
            f"{self.qualified_name} | /{inter.application_command.name} <{dashboard_channel = }> <{announcement_channel = }> <{patch_notes = }> <{map_channel = }> <{language = }>"
        )
        embed = SetupEmbed()
        guild_in_db: GuildRecord = GuildsDB.get_info(inter.guild_id)
        if not guild_in_db:
            guild_in_db = GuildsDB.insert_new_guild(inter.guild_id)
        guild_language = load(
            open(f"data/languages/{guild_in_db.language}.json", encoding="UTF-8")
        )
        inv_lang_dict = {v: k for k, v in language_dict.items()}
        if not any(
            [
                dashboard_channel,
                announcement_channel,
                patch_notes,
                map_channel,
                language,
            ]
        ):
            try:
                dashboard_channel = inter.guild.get_channel(
                    guild_in_db.dashboard_channel_id
                ) or await inter.guild.fetch_channel(guild_in_db.dashboard_channel_id)
            except:
                dashboard_channel = guild_language["setup.not_set"]
            try:
                dashboard_message = dashboard_channel.get_partial_message(
                    guild_in_db.dashboard_message_id
                ).jump_url
            except:
                dashboard_message = guild_language["setup.not_set"]
            if isinstance(dashboard_channel, TextChannel):
                dashboard_channel = dashboard_channel.mention
            embed.add_field(
                guild_language["setup.dashboard"],
                (
                    f"{guild_language['setup.dashboard_channel']}: {dashboard_channel}\n"
                    f"{guild_language['setup.dashboard_message']}: {dashboard_message}"
                ),
                inline=False,
            )
            try:
                announcement_channel = (
                    inter.guild.get_channel(guild_in_db.announcement_channel_id).mention
                    or await inter.guild.fetch_channel(
                        guild_in_db.announcement_channel_id
                    ).mention
                )
            except:
                announcement_channel = guild_language["setup.not_set"]
            finally:
                embed.add_field(
                    guild_language["setup.announcements"],
                    f"{guild_language['setup.announcement_channel']}: {announcement_channel}",
                    inline=False,
                )
            try:
                map_channel = inter.guild.get_channel(
                    guild_in_db.map_channel_id
                ) or await inter.guild.fetch_channel(guild_in_db.map_channel_id)
            except:
                map_channel = guild_language["setup.not_set"]
            try:
                map_message = map_channel.get_partial_message(
                    guild_in_db.map_message_id
                ).jump_url
            except:
                map_message = guild_language["setup.not_set"]
            if isinstance(map_channel, TextChannel):
                map_channel = map_channel.mention
            embed.add_field(
                guild_language["setup.map"],
                (
                    f"{guild_language['setup.map_channel']}: {map_channel}\n"
                    f"{guild_language['setup.map_message']}: {map_message}"
                ),
                inline=False,
            ).add_field(
                guild_language["setup.language"], inv_lang_dict[guild_in_db.language]
            ).add_field(
                guild_language["setup.patch_notes_name"],
                {True: ":white_check_mark:", False: ":x:"}[guild_in_db.patch_notes],
            ).add_field(
                "", guild_language["setup.message"], inline=False
            ).title = guild_language[
                "setup.current_settings"
            ]
            return await inter.send(embed=embed, ephemeral=True)

        if language:
            current_lang = guild_in_db.language
            if current_lang == language:
                embed.add_field(
                    guild_language["setup.language"],
                    (
                        f"**{inv_lang_dict[current_lang]}** ➡️ **{inv_lang_dict[language]}**\n"
                        f"*{guild_language['setup.language_same']}*"
                    ),
                    inline=False,
                )
            else:
                GuildsDB.update_language(inter.guild_id, language)
                guild_language = load(
                    open(f"data/languages/{language}.json", encoding="UTF-8")
                )
                embed.add_field(
                    guild_language["setup.language"],
                    (
                        f"**{inv_lang_dict[current_lang]}** ➡️ **{inv_lang_dict[language]}**"
                    ),
                    inline=False,
                )
                guild_in_db = GuildsDB.get_info(inter.guild_id)

        if dashboard_channel:
            if dashboard_channel.id == guild_in_db.dashboard_channel_id:
                GuildsDB.update_dashboard(inter.guild_id, 0, 0)
                embed.add_field(
                    guild_language["setup.dashboard_channel"],
                    (
                        f"**{guild_in_db.dashboard_channel_id}** ➡️ **None**\n"
                        f"*{guild_language['setup.unset_dashboard']}*"
                    ),
                    inline=False,
                )
                guild_in_db = GuildsDB.get_info(inter.guild_id)
            else:
                dashboard_perms_have = dashboard_channel.permissions_for(
                    inter.guild.me
                ).is_superset(self.dashboard_perms_needed)
                if not dashboard_perms_have:
                    embed.add_field(
                        guild_language["setup.dashboard"],
                        guild_language["setup.missing_perm"],
                        inline=False,
                    )
                else:
                    api = API()
                    await api.pull_from_api(
                        get_campaigns=True,
                        get_assignments=True,
                        get_planet_events=True,
                        get_planets=True,
                    )
                    if api.error:
                        await self.bot.moderator_channel.send(
                            f"<@164862382185644032>{api.error[0]}\n{api.error[1]}\n:warning:"
                        )
                        return await inter.send(
                            "There was an issue connecting to the datacentre. Please try again.",
                            ephemeral=True,
                        )
                    data = Data(data_from_api=api)
                    liberation_changes = self.bot.get_cog(
                        "DashboardCog"
                    ).liberation_changes
                    dashboard = Dashboard(
                        data, guild_in_db.language, liberation_changes
                    )
                    try:
                        message = await dashboard_channel.send(
                            embeds=dashboard.embeds, file=File("resources/banner.png")
                        )
                    except Exception as e:
                        self.bot.logger.error(f"SetupCog, dashboard setup, {e}")
                        return await inter.send(
                            "An error has occured, I have contacted Super Earth High Command.",
                            ephemeral=True,
                        )
                    GuildsDB.update_dashboard(
                        inter.guild_id, dashboard_channel.id, message.id
                    )
                    self.bot.dashboard_messages.append(message)
                    embed.add_field(
                        guild_language["setup.dashboard"],
                        (
                            f"{guild_language['setup.dashboard_channel']}: {dashboard_channel.mention}\n"
                            f"{guild_language['setup.dashboard_message']}: {message.jump_url}\n"
                        ),
                    )
                    guild_in_db = GuildsDB.get_info(inter.guild_id)

        patch_notes_disabled = False
        if announcement_channel:
            patch_notes_text = ""
            if announcement_channel.id == guild_in_db.announcement_channel_id:
                if guild_in_db.patch_notes == True:
                    GuildsDB.update_patch_notes(inter.guild.id, False)
                    self.bot.patch_channels = [
                        channel
                        for channel in self.bot.patch_channels
                        if channel.guild != inter.guild
                    ]
                    patch_notes_text = f"Patch Notes:\n- Enabled ➡️ Disabled\n"
                    patch_notes_disabled = True
                GuildsDB.update_announcement_channel(inter.guild_id, 0)
                embed.add_field(
                    guild_language["setup.announcements"],
                    (
                        f"Announcement Channel:\n- {announcement_channel.jump_url} ➡️ None\n"
                        f"{patch_notes_text}"
                        f"*{guild_language['setup.unset_announce']}*"
                    ),
                    inline=False,
                )
                guild_in_db = GuildsDB.get_info(inter.guild_id)
            else:
                annnnouncement_perms_have = announcement_channel.permissions_for(
                    inter.guild.me
                ).is_superset(self.annnnouncement_perms_needed)
                if not annnnouncement_perms_have:
                    embed.add_field(
                        guild_language["setup.announcements"],
                        guild_language["setup.missing_perm"],
                        inline=False,
                    )
                    patch_notes_disabled = True
                else:
                    GuildsDB.update_announcement_channel(
                        inter.guild_id, announcement_channel.id
                    )
                    embed.add_field(
                        guild_language["setup.announcements"],
                        (
                            f"{guild_language['setup.announcement_channel']}: {announcement_channel.mention}\n"
                            f"*{guild_language['setup.announce_warn']}*"
                        ),
                        inline=False,
                    )
                    guild_in_db = GuildsDB.get_info(inter.guild_id)
                    self.bot.announcement_channels = [
                        channel
                        for channel in self.bot.announcement_channels
                        if channel.guild != inter.guild
                    ]
                    self.bot.announcement_channels.append(announcement_channel)

        if map_channel:
            if map_channel.id == guild_in_db.map_channel_id:
                GuildsDB.update_map(inter.guild_id, 0, 0)
                embed.add_field(
                    guild_language["setup.map"],
                    f"*{guild_language['setup.unset_map']}*",
                    inline=False,
                )
                guild_in_db = GuildsDB.get_info(inter.guild_id)
            else:
                map_perms_have = map_channel.permissions_for(
                    inter.guild.me
                ).is_superset(self.map_perms_needed)
                if not map_perms_have:
                    embed.add_field(
                        guild_language["setup.map"],
                        f"*{guild_language['setup.missing_perm']}*",
                        inline=False,
                    )
                else:
                    api = API()
                    await api.pull_from_api(
                        get_campaigns=True, get_planets=True, get_assignment=True
                    )
                    if api.error:
                        await self.bot.moderator_channel.send(
                            f"<@164862382185644032>{api.error[0]}\n{api.error[1]}\n:warning:"
                        )
                        return await inter.send(
                            "There was an issue connecting to the datacentre. Please try again.",
                            ephemeral=True,
                        )
                    else:
                        data = Data(data_from_api=api)
                        map_embeds = await dashboard_maps(
                            data, self.bot.waste_bin_channel
                        )
                        map_embed = map_embeds[guild_in_db.language]
                        message = await map_channel.send(
                            embed=map_embed,
                        )
                        GuildsDB.update_map(inter.guild_id, map_channel.id, message.id)
                        embed.add_field(
                            guild_language["setup.map"],
                            (
                                f"{guild_language['setup.map_channel']}: {map_channel.mention}\n"
                                f"{guild_language['setup.map_message']}: {message.jump_url}\n"
                            ),
                            inline=False,
                        )
                        guild_in_db = GuildsDB.get_info(inter.guild_id)
                        self.bot.map_messages.append(message)

        if patch_notes and not patch_notes_disabled:
            want_patch_notes = patch_notes == "Yes"
            if guild_in_db.patch_notes == want_patch_notes:
                embed.add_field(
                    "Patch Notes",
                    (
                        f"**{guild_in_db.patch_notes}** ➡️ **{want_patch_notes}**\n"
                        f"*{guild_language['setup.patch_notes_same']}*"
                    ),
                    inline=False,
                )
            elif guild_in_db.patch_notes != want_patch_notes:
                if want_patch_notes == True:
                    if (
                        guild_in_db.announcement_channel_id == 0
                        and not announcement_channel
                    ):
                        embed.add_field(
                            "Patch Notes",
                            guild_language["setup.need_announce"],
                            inline=False,
                        )
                    else:
                        try:
                            channel = (
                                inter.guild.get_channel(
                                    guild_in_db.announcement_channel_id
                                )
                                or await inter.guild.fetch_channel(
                                    guild_in_db.announcement_channel_id
                                )
                                if not announcement_channel
                                else announcement_channel
                            )
                            self.bot.patch_channels = [
                                channel
                                for channel in self.bot.patch_channels
                                if channel.guild != inter.guild
                            ]
                            self.bot.patch_channels.append(channel)
                            GuildsDB.update_patch_notes(
                                inter.guild_id, want_patch_notes
                            )
                            embed.add_field(
                                "Patch Notes",
                                (
                                    f"**{guild_in_db.patch_notes}** ➡️ **{want_patch_notes}**\n"
                                    f"*{guild_language['setup.patch_notes_enabled']}*"
                                ),
                                inline=False,
                            )
                        except:
                            embed.add_field(
                                "Patch Notes",
                                f"*{guild_language['setup.cant_get_announce_channel']}*",
                                inline=False,
                            )
                else:
                    self.bot.patch_channels = [
                        channel
                        for channel in self.bot.patch_channels
                        if channel.guild != inter.guild
                    ]
                    GuildsDB.update_patch_notes(inter.guild_id, want_patch_notes)
                    embed.add_field(
                        "Patch Notes",
                        f"*{guild_language['setup.patch_notes_disabled']}*",
                        inline=False,
                    )

        await inter.send(embed=embed, ephemeral=True)


def setup(bot: GalacticWideWebBot):
    bot.add_cog(SetupCog(bot))
