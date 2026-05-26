from dataclasses import dataclass
from utils.emojis import Emojis


@dataclass
class Community:
    emoji: str
    discord_link: str
    full_name: str
    long_description: str = ""


arsenal = Community(
    emoji=Emojis.CommunityIcons.arsenal,
    discord_link="https://discord.gg/rsnl",
    full_name="ARSENAL",
)
