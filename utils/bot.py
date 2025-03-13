from data.lists import json_dict
from datetime import datetime, timedelta
from disnake import Activity, ActivityType, Intents, TextChannel
from disnake.ext import commands
from json import load
from logging import INFO, FileHandler, Formatter, getLogger
from os import getenv, listdir
from utils.data import Data
from utils.interface_handler import InterfaceHandler

MODERATOR_CHANNEL_ID = int(getenv(key="MODERATION_CHANNEL"))
FEEDBACK_CHANNEL_ID = int(getenv(key="FEEDBACK_CHANNEL"))
WASTE_BIN_CHANNEL_ID = int(getenv(key="WASTE_BIN_CHANNEL"))
API_CHANGES_CHANNEL_ID = int(getenv(key="API_CHANGES_CHANNEL"))


class GalacticWideWebBot(commands.AutoShardedInteractionBot):
    def __init__(self) -> None:
        """The main Galactic Wide Web bot class"""
        super().__init__(
            intents=Intents.default(),
            activity=Activity(name="for dissidents", type=ActivityType.watching),
        )
        self.logger = getLogger()
        self.logger.setLevel(level=INFO)
        handler = FileHandler(filename="bot.log", encoding="utf-8", mode="w")
        handler.setFormatter(
            fmt=Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        )
        self.logger.addHandler(hdlr=handler)
        self.startup_time = datetime.now()
        self.ready_time = self.startup_time + timedelta(seconds=30)
        self.interface_handler = InterfaceHandler(bot=self)
        self.json_dict = json_dict.copy()
        self.load_json()
        self.data = Data()
        self.previous_data: Data | None = None
        self.command_usage: dict = {}
        self.moderator_channel: TextChannel | None = None
        self.feedback_channel: TextChannel | None = None
        self.waste_bin_channel: TextChannel | None = None
        self.api_changes_channel: TextChannel | None = None

    async def on_ready(self) -> None:
        await self.get_channels()
        self.logger.info(
            msg=f"Loaded {len(self.cogs)}/{len([f for f in listdir('cogs') if f.endswith('.py')]) + len([f for f in listdir('cogs/admin') if f.endswith('.py')])} cogs successfully"
        )
        self.owner = [owner for owner in self.owners][0]
        self.owner_id = self.owner.id

    def load_json(self) -> None:
        for key, values in self.json_dict.copy().items():
            if "path" not in values:
                for second_key, second_values in values.items():
                    if "path" in second_values:
                        with open(
                            file=second_values["path"], encoding="UTF-8"
                        ) as json_file:
                            self.json_dict[key][second_key] = load(fp=json_file)
                            continue
                continue
            else:
                with open(file=values["path"], encoding="UTF-8") as json_file:
                    self.json_dict[key] = load(json_file)

    async def get_channels(self) -> None:
        """Fetches the specific channels needed for the bots functions"""
        channel_dict = {
            "moderator_channel": MODERATOR_CHANNEL_ID,
            "feedback_channel": FEEDBACK_CHANNEL_ID,
            "waste_bin_channel": WASTE_BIN_CHANNEL_ID,
            "api_changes_channel": API_CHANGES_CHANNEL_ID,
        }
        for attr, channel_id in channel_dict.items():
            while not getattr(self, attr):
                setattr(
                    self,
                    attr,
                    self.get_channel(channel_id)
                    or await self.fetch_channel(channel_id),
                )
