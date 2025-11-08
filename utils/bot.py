from data.lists import json_dict
from datetime import datetime, timedelta
from disnake import Intents, Message, Status, TextChannel
from disnake.ext import commands, tasks
from json import load
from os import listdir
from utils.data import Data
from utils.dataclasses import BotChannels, Config, GWWBotModes
from utils.interface_handler import InterfaceHandler
from utils.logger import GWWLogger
from utils.maps import Maps


class GalacticWideWebBot(commands.AutoShardedInteractionBot):
    def __init__(self) -> None:
        """The main Galactic Wide Web bot class"""
        super().__init__(intents=Intents.default(), status=Status.idle)
        self.MODE = GWWBotModes.LIVE
        self.config = Config
        self.logger = GWWLogger()
        self.startup_time = datetime.now()
        self.ready_time = self.startup_time + timedelta(seconds=45)
        self.interface_handler = InterfaceHandler(bot=self)
        self.channels = BotChannels()
        self.json_dict = json_dict.copy()
        self.load_json()
        self.data = Data(
            json_dict=self.json_dict,
            logger=self.logger,
            moderator_channel=self.channels.moderator_channel,
        )
        self.previous_data: Data | None = None
        self.bot_dashboard_channel: TextChannel | None = None
        self.bot_dashboard_message: Message | None = None
        self.maps = Maps()
        self.loops: list[tasks.Loop] = []
        self.load_extensions("cogs/admin")
        self.load_extensions("cogs")

    @property
    def time_until_ready(self) -> int:
        return int((self.ready_time - datetime.now()).total_seconds())

    async def on_ready(self) -> None:
        await self.channels.get_channels(self, self.config)
        self.logger.info(
            f"Loaded {len(self.cogs)}/{len([f for f in listdir('cogs') if f.endswith('.py')]) + len([f for f in listdir('cogs/admin') if f.endswith('.py')])} cogs successfully"
        )
        await self.get_owner()

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

    async def get_owner(self) -> None:
        max_retries = 10
        retries = 0
        while not self.owner and retries < max_retries:
            if self.owners:
                self.owner = list(self.owners)[0]
            elif self.owner_ids:
                owner_id = list(self.owner_ids)[0]
                self.owner = self.get_user(owner_id) or await self.fetch_user(owner_id)
            retries += 1

    def super_start(self) -> None:
        token_to_use = (
            self.config.BOT_TOKEN
            if self.MODE != GWWBotModes.DEBUG
            else self.config.BETA_BOT_TOKEN
        )
        self.run(token_to_use)
