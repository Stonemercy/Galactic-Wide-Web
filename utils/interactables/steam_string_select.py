from disnake import SelectOption
from disnake.ui import StringSelect
from utils.data import Steam


class SteamStringSelect(StringSelect):
    def __init__(self, steam_posts: list[Steam]):
        super().__init__(
            placeholder="Choose Steam Post",
            min_values=1,
            max_values=1,
            options=[SelectOption(label=steam.title) for steam in steam_posts[:25]],
            custom_id="steam",
        )
