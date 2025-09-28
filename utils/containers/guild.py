from disnake import Colour, MediaGalleryItem, ui, Guild
from utils.dataclasses import Languages
from utils.dbv2 import GWWGuild
from utils.interactables.ADMIN.leave_guild_button import LeaveGuildButton
from utils.interactables.ADMIN.reset_guild_button import ResetGuildButton
from utils.mixins import ReprMixin


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
class GuildContainer(ui.Container, ReprMixin):
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
        title_component = ui.Section(
            ui.TextDisplay(f"# Guild"), accessory=ui.Thumbnail(guild.icon.url)
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
        components.extend([title_component, ui.Separator()])

        text_display = ui.TextDisplay("")
        text_display.content += f"👥 Members: **{guild.member_count}**"
        text_display.content += f"\n:hash: Text channels: **{len(guild.text_channels)}**\n:speaking_head: Voice channels: **{len(guild.voice_channels)}**"
        text_display.content += f"\nCreated On <t:{int(guild.created_at.timestamp())}:F>\n(<t:{int(guild.created_at.timestamp())}:R>)"
        components.extend([text_display, ui.Separator()])

        text_display = ui.TextDisplay("")
        text_display.content += f"## Verification Level\n**{str(guild.verification_level).capitalize()}**\n-# {VERIFICATION_DICT.get(guild.verification_level.value, 'Unknown')}"
        text_display.content += f"\n🌐 Locale\n{FLAG_DICT.get(Languages.get_from_locale(guild.preferred_locale).short_code, '')} {guild.preferred_locale}"
        components.extend([text_display, ui.Separator()])

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
                [ui.TextDisplay(f"## Features:\n{features_text}"), ui.Separator()]
            )

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
                ui.TextDisplay(f"## Bot Features Enabled\n{db_features_text}"),
                ui.Separator(),
            ]
        )
        components.extend(
            [
                ui.TextDisplay(f"###  Shard ID #{guild.shard_id}"),
                ui.Separator(),
            ]
        )

        if guild.banner:
            components.append(ui.MediaGallery(MediaGalleryItem(guild.banner.url)))

        if joined or fetching:
            components.append(ui.ActionRow(*[LeaveGuildButton(), ResetGuildButton()]))

        super().__init__(*components, accent_colour=colour)
