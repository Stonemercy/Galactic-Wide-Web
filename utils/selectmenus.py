import disnake
from main import GalacticWideWebBot


class SteamStringSelect(disnake.ui.StringSelect):
    def __init__(self, bot: GalacticWideWebBot):
        options = [disnake.SelectOption(label=steam.title) for steam in bot.data.steam]
        super().__init__(
            placeholder="Choose Patch Notes",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="steam",
        )
