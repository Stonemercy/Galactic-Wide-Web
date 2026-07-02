from disnake import Colour, MediaGalleryItem, Guild
from disnake.ui import (
    ActionRow,
    Container,
    MediaGallery,
    Section,
    Separator,
    TextDisplay,
    Thumbnail,
)
from utils.dataclasses import Languages
from utils.dbv2 import GWWGuild
from utils.interactables.ADMIN import LeaveGuildButton, ResetGuildButton

VERIFICATION_DICT = {
    0: "No criteria set.",
    1: "Member must have a verified email on their Discord account.",
    2: "Member must have a verified email and be registered on Discord for more than five minutes.",
    3: "Member must have a verified email, be registered on Discord for more than five minutes, and be a member of the guild itself for more than ten minutes.",
    4: "Member must have a verified phone on their Discord account.",
}

FLAG_DICT = {
    "en": ":flag_gb:",
    "fr": ":flag_fr:",
    "de": ":flag_de:",
    "it": ":flag_it:",
    "pt-br": ":flag_br:",
    "ru": ":flag_ru:",
    "es": ":flag_es:",
}


# DOESNT NEED LOCALIZATION
class GuildContainer(Container):
    def __init__(
        self,
        guild: Guild,
        db_guild: GWWGuild,
        joined: bool = False,
        removed: bool = False,
        fetching: bool = False,
    ):
        components = []
        colour = Colour.dark_theme()
        title_component = Section(
            TextDisplay(f"# Guild"),
            accessory=Thumbnail(
                guild.icon.url
                if guild.icon
                else "https://cdn.discordapp.com/attachments/1212735927223590974/1422512588973015081/0xa92d559bf3ae174.png?ex=68dcf196&is=68dba016&hm=6d361df60c5c8b49467f549fa599f018039887cb355f329f1575ba701bcd7d60&"
            ),
        )

        if joined:
            title_component.children[0].content += " Joined"
            colour = Colour.brand_green()
        elif removed:
            title_component.children[0].content += " Left"
            colour = Colour.brand_red()
        title_component.children[0].content += f"\n# {guild.name}"

        title_component.children[0].content += f"\n-# Guild ID: {guild.id}"
        title_component.children[0].content += f"\n-# 👑 Owner <@{guild.owner_id}>"
        if guild.vanity_url_code:
            title_component.children[
                0
            ].content += f"\n-# Vanity URL code\n<https://discord.com/invite/{guild.vanity_url_code}>"
        if guild.description:
            title_component.children[0].content += f"\n-# {guild.description}"
        components.extend([title_component, Separator()])

        text_display = TextDisplay("")
        text_display.content += f"👥 Members: **{guild.member_count}**"
        text_display.content += f"\n:hash: Text channels: **{len(guild.text_channels)}**\n:speaking_head: Voice channels: **{len(guild.voice_channels)}**"
        text_display.content += f"\nCreated On <t:{int(guild.created_at.timestamp())}:F>\n(<t:{int(guild.created_at.timestamp())}:R>)"
        components.extend([text_display, Separator()])

        text_display = TextDisplay("")
        text_display.content += f"## Verification Level\n**{str(guild.verification_level).capitalize()}**\n-# {VERIFICATION_DICT.get(guild.verification_level.value, 'Unknown')}"
        text_display.content += f"\n🌐 Locale\n{FLAG_DICT.get(Languages.get_from_locale(guild.preferred_locale).short_code, '')} {guild.preferred_locale}"
        components.extend([text_display, Separator()])

        features_text = ""
        if guild.features:
            for feature in [
                f
                for f in guild.features
                if f
                in [
                    "COMMUNITY",
                    "CREATOR_MONETIZABLE",
                    "CREATOR_MONETIZABLE_PROVISIONAL",
                    "CREATOR_STORE_PAGE",
                    "DEVELOPER_SUPPORT_SERVER",
                    "DISCOVERABLE",
                    "ENABLED_DISCOVERABLE_BEFORE",
                    "FEATURABLE",
                    "GUILD_HOME_TEST",
                    "HAS_DIRECTORY_ENTRY",
                    "HUB",
                    "LINKED_TO_HUB",
                    "NEWS",
                    "PARTNERED",
                    "ROLE_SUBSCRIPTIONS_AVAILABLE_FOR_PURCHASE",
                    "ROLE_SUBSCRIPTIONS_ENABLED",
                    "VANITY_URL",
                    "VERIFIED",
                    "VIP_REGIONS",
                    "WELCOME_SCREEN_ENABLED",
                ]
            ]:
                features_text += f"-# - {feature.replace('_', ' ').capitalize()}\n"
        if features_text:
            components.extend(
                [TextDisplay(f"## Features:\n{features_text}"), Separator()]
            )
        if not joined:
            if db_guild.features != []:
                db_features_text = ""
                for feature in db_guild.features:
                    if feature.message_id != None:
                        feature_link = f"https://discord.com/channels/{feature.guild_id}/{feature.channel_id}/{feature.message_id}"
                    else:
                        feature_link = f"<#{feature.channel_id}>"
                    db_features_text += f"\n{feature.name} - {feature_link}"
            else:
                db_features_text = "-# None"
            components.extend(
                [
                    TextDisplay(f"## Bot Features Enabled\n{db_features_text}"),
                    Separator(),
                ]
            )
        components.extend(
            [TextDisplay(f"###  Shard ID #{guild.shard_id}"), Separator()]
        )

        if guild.banner:
            components.append(MediaGallery(MediaGalleryItem(guild.banner.url)))

        if joined or fetching:
            components.append(ActionRow(*[LeaveGuildButton(), ResetGuildButton()]))

        super().__init__(*components, accent_colour=colour)
