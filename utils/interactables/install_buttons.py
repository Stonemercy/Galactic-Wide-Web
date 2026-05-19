from disnake import ButtonStyle
from disnake.ui import Button
from utils.emojis import Emojis


class GuildInstallButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.link,
            label="Add the bot to a server",
            url="https://discord.com/oauth2/authorize?client_id=1212535586972369008&scope=bot+applications.commands&integration_type=0",
            emoji=Emojis.Icons.discord,
        )


class UserInstallButton(Button):
    def __init__(self):
        super().__init__(
            style=ButtonStyle.link,
            label="Add the bot to your account",
            url="https://discord.com/oauth2/authorize?client_id=1212535586972369008&scope=applications.commands&integration_type=1",
            emoji=Emojis.Icons.hdc,
        )
