from datetime import datetime
from disnake import Colour, Embed
from disnake.ext.tasks import Loop
from inspect import getmembers
from utils.bot import GalacticWideWebBot
from utils.mixins import EmbedReprMixin


class BotInfoEmbeds(list[Embed]):
    def __init__(self, bot: GalacticWideWebBot):
        self.append(self.HeaderEmbed(bot=bot))
        self.extend(self.CogEmbeds(bot=bot))
        self.append(self.InterfaceHandlerEmbed(bot=bot))

    class HeaderEmbed(Embed, EmbedReprMixin):
        def __init__(self, bot: GalacticWideWebBot):
            super().__init__(
                title="Galactic Wide Web bot info", colour=Colour.dark_theme()
            )
            uptime_seconds = (datetime.now() - bot.startup_time).total_seconds()
            hours = uptime_seconds // 3600
            minutes = (uptime_seconds % 3600) // 60
            remaining_seconds = uptime_seconds % 60

            self.add_field(
                "Uptime",
                f"{hours:.0f} hours, {minutes:.0f} minutes and {remaining_seconds:.0f} seconds",
                inline=False,
            )

    class CogEmbeds(list[Embed]):
        def __init__(self, bot: GalacticWideWebBot):

            cog_ids = []
            embed_count = 1
            embed = Embed(title=f"Cogs {embed_count}", colour=Colour.dark_theme())
            for cog_name, cog in bot.cogs.items():
                cog_info_text = f"-# id=**{id(cog)}**"
                for name, member in getmembers(cog):
                    if isinstance(member, Loop):
                        if member.next_iteration:
                            timestamp = (
                                f" - <t:{int(member.next_iteration.timestamp())}:R>"
                            )
                        elif member.count:
                            timestamp = " - COMPLETED"
                        else:
                            timestamp = " - ERROR :warning:"
                        cog_info_text += f"\n-#  - {name} {timestamp}"
                cog_ids.append(id(cog))
                embed.add_field(cog_name, cog_info_text, inline=False)
                if len(embed.fields) > 5:
                    self.append(embed)
                    embed_count += 1
                    embed = Embed(
                        title=f"Cogs {embed_count}", colour=Colour.dark_theme()
                    )
            duplicate_ids = [
                cog_id
                for cog_id in cog_ids
                if len([cid for cid in cog_ids if cid == cog_id]) > 1
            ]
            if duplicate_ids:
                self.append(Embed(title="Duplicate ID's", description=duplicate_ids))

    class InterfaceHandlerEmbed(Embed, EmbedReprMixin):
        def __init__(self, bot: GalacticWideWebBot):
            super().__init__(
                title="Interface handler lengths", colour=Colour.dark_theme()
            )
            for type, list in bot.interface_handler.lists.items():
                list_length = len(list)
                set_length = len(set(list))
                warning = "" if list_length == set_length else ":warning:"
                self.add_field(
                    type, f"Length: {list_length}\nSet Length: {set_length} {warning}"
                )
