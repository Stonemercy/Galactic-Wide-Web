from disnake import Colour, Embed, Guild
from utils.mixins import EmbedReprMixin


# DOESNT NEED LOCALIZATION (YET)
class CommunityServersEmbed(Embed, EmbedReprMixin):
    def __init__(self, guilds: list[Guild], new_index: int):
        super().__init__(
            title="Community Servers",
            colour=Colour.blue(),
            description=f"The GWW is in **{len(guilds)}** community servers",
        )
        for index, guild in enumerate(
            guilds[new_index - 16 : new_index], start=max(1, new_index - 15)
        ):
            if self.character_count() < 6000 and len(self.fields) < 24:
                self.add_field(
                    name=f"{index}. {guild.name}",
                    value=(
                        f"Members: **{guild.member_count}**"
                        f"\nInvite: [Link](<https://discord.com/invite/{guild.vanity_url_code}>)"
                        f"\nLocale: **{guild.preferred_locale}**"
                        f"\nCreated: <t:{int(guild.created_at.timestamp())}:R>"
                    ),
                )
                if index % 2 == 0:
                    self.add_field("", "", inline=False)
            else:
                break
        try:
            self.set_image([g for g in guilds if g.banner][0].banner.url)
        except:
            pass
        self.set_footer(text=f"{max(0, new_index)}/{len(guilds)}")

    def character_count(self):
        total_characters = 0
        if self.title:
            total_characters += len(self.title.strip())
        if self.description:
            total_characters += len(self.description.strip())
        if self.footer:
            total_characters += len(self._footer.get("text", "").strip())
        if self.author:
            total_characters += len(self._author.get("name", "").strip())
        if self.fields:
            for field in self.fields:
                total_characters += len(field.name.strip())
                total_characters += len(field.value.strip())
        return total_characters
