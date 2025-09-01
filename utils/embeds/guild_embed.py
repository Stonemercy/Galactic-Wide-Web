from datetime import datetime
from disnake import Colour, Embed, Guild
from utils.dataclasses import Languages
from utils.dbv2 import GWWGuild
from utils.mixins import EmbedReprMixin


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


class GuildEmbed(Embed, EmbedReprMixin):
    def __init__(
        self,
        guild: Guild,
        db_guild: GWWGuild,
        joined: bool = False,
        removed: bool = False,
    ):
        super().__init__(
            title=f"Guild",
            description=f"**{guild.name}**",
            colour=Colour.dark_theme(),
        )
        if joined:
            self.title += " Joined"
            self.colour = Colour.brand_green()
        elif removed:
            self.title += " Left"
            self.colour = Colour.brand_red()
        if guild.icon:
            self.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            self.set_image(url=guild.banner.url)
        self.add_field(name="Guild ID", value=f"-# {guild.id}")
        self.add_field(name="👑 Owner", value=f"<@{guild.owner_id}>")
        if guild.vanity_url_code:
            self.add_field(
                name="Vanity URL code",
                value=f"<https://discord.com/invite/{guild.vanity_url_code}>",
                inline=False,
            )
        else:
            self.add_field(name="", value="", inline=False)
        self.add_field(name="👥 Members", value=f"**{guild.member_count}**")
        self.add_field(
            name="Channels",
            value=f"Text: **{len(guild.text_channels)}**\nVoice: **{len(guild.voice_channels)}**",
        )
        now = datetime.now()
        if guild.created_at.day == now.day and guild.created_at.month == now.month:
            created_on_title = "🎉 Created On"
        else:
            created_on_title = "Created On"
        self.add_field(
            name=created_on_title,
            value=f"<t:{int(guild.created_at.timestamp())}:F>\n<t:{int(guild.created_at.timestamp())}:R>",
            inline=False,
        )
        self.add_field(
            name="Verification Level",
            value=f"{str(guild.verification_level).capitalize()}\n-# {VERIFICATION_DICT.get(guild.verification_level.value, 'Unknown')}",
        )
        self.add_field(
            name="🌐 Locale",
            value=f"{FLAG_DICT.get(Languages.get_from_locale(guild.preferred_locale).short_code, '')} {guild.preferred_locale}",
        )
        if guild.features:
            features_text = ""
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
        self.add_field(name="Features", value=features_text or "None", inline=False)

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
        self.add_field(
            name="Bot Features Enabled", value=db_features_text, inline=False
        )
