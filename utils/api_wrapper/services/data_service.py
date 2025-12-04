from datetime import datetime, timedelta
from utils.dataclasses import Languages
from utils.dbv2 import GWWGuilds
from utils.logger import GWWLogger
from utils.mixins import ReprMixin
from ..clients import (
    AuthedClient,
    HelldiversClient,
    SteamNewsClient,
    SteamPlayerCountClient,
)
from ..services.tracking_service import TrackingService
from ..utils.constants import EndpointBase
from ..formatters import FormattedData, FormattedDataContext


class DataService(ReprMixin):
    __slots__ = ("war_id", "dss_id")

    def __init__(self, json_dict: dict, logger: GWWLogger) -> None:
        """The object to retrieve and organise all 3rd-party data used by the bot"""
        self.json_dict = json_dict
        self.logger = logger
        self.loaded = False
        self.fetching = False
        self.previous_data = None
        self.formatted_data: FormattedData = None
        self.tracking_service = TrackingService()

        self.war_id = 801
        self.dss_id = 0
        self.steam_player_count = 0
        self._raw_war_status: dict[str, dict] = {}
        self._raw_news_feed: dict[str, list[dict]] = {}
        self._raw_assignments: dict[str, list[dict]] = {}
        self._raw_dss: dict = {}
        self._raw_dss_votes: dict = {}
        self._raw_war_stats: dict = {}
        self._raw_war_info: dict = {}
        self._raw_war_effects: list = []
        self._raw_personal_order: dict = {}
        self._raw_steam_news: list = []

    async def pull_from_api(self) -> None:
        """Pulls the data from each endpoint"""
        self.logger.info("STARTING API PULLS")
        self.fetching = True
        async with HelldiversClient(
            logger=self.logger,
            base_url=EndpointBase.HELLDIVERS.value,
        ) as client:
            war_id = await client.get_war_id()
            if war_id:
                self.war_id = war_id["id"]

            unique_languages = GWWGuilds.unique_languages()
            in_use_languages = [
                l
                for l in Languages.all
                if l.short_code in unique_languages or True  # ALL FOR DEBUGGING
            ]
            for lang in in_use_languages:
                # war status
                raw_war_status = await client.get_war_status(
                    war_id=self.war_id,
                    lang=lang.long_code,
                )
                if raw_war_status:
                    self._raw_war_status[lang.short_code] = raw_war_status

                    if self.dss_id == 0:
                        self.dss_id: int = raw_war_status["spaceStations"][0]["id32"]

                # news_feed
                time_for_dispatches = int(
                    (
                        self._raw_war_status.get("en", {}).get(
                            "time",
                            (
                                datetime.now()
                                - datetime(
                                    year=2024, month=2, day=14, hour=15, minute=11
                                )
                            ).total_seconds(),
                        )
                    )
                    - timedelta(weeks=1).total_seconds()
                )
                news_feed = await client.get_news_feed(
                    war_id=self.war_id,
                    time_for_dispatches=time_for_dispatches,
                    lang=lang.long_code,
                )
                if news_feed:
                    self._raw_news_feed[lang.short_code] = news_feed

                # assignments
                assignments = await client.get_assignments(
                    war_id=self.war_id, lang=lang.long_code
                )
                if assignments:
                    self._raw_assignments[lang.short_code] = assignments

            # dss
            if self.dss_id != 0:
                dss = await client.get_dss_info(
                    war_id=self.war_id, station_id=self.dss_id
                )
                if dss:
                    self._raw_dss = dss

            # war stats
            war_stats = await client.get_war_stats(war_id=self.war_id)
            if war_stats:
                self._raw_war_stats = war_stats

            # war info
            war_info = await client.get_war_info(war_id=self.war_id)
            if war_info:
                self._raw_war_info = war_info

            # war effects
            war_effects = await client.get_war_effects()
            if war_effects:
                self._raw_war_effects = war_effects

        async with SteamPlayerCountClient(
            logger=self.logger, base_url=EndpointBase.STEAM_PLAYER_COUNT.value
        ) as client:
            # steam player count
            steam_count = await client.get_steam_count()
            if steam_count:
                self.steam_player_count = steam_count["response"]["player_count"]

        async with SteamNewsClient(
            logger=self.logger, base_url=EndpointBase.STEAM_NEWS.value
        ) as client:
            # steam news
            steam_news = await client.get_steam_news()
            if steam_news:
                self._raw_steam_news: list[dict] = [
                    pn
                    for pn in steam_news["appnews"]["newsitems"]
                    if pn["feedlabel"] == "Community Announcements"
                ]

        async with AuthedClient(logger=self.logger) as client:
            # dss votes
            dss_votes = await client.get_dss_votes()
            if dss_votes:
                self._raw_dss_votes = dss_votes

            # personal order
            personal_order = await client.get_personal_order()
            if personal_order:
                self._raw_personal_order = personal_order

        self.fetching = False
        self.logger.info("PULLS COMPLETE!")

    def format_data(self) -> None:
        if self.formatted_data != None:
            self.previous_data = self.formatted_data.copy()
        formatted_data_context = FormattedDataContext(
            war_id=self.war_id,
            dss_id=self.dss_id,
            steam_player_count=self.steam_player_count,
            war_status=self._raw_war_status,
            news_feed=self._raw_news_feed,
            assignments=self._raw_assignments,
            dss=self._raw_dss,
            dss_votes=self._raw_dss_votes,
            war_stats=self._raw_war_stats,
            war_info=self._raw_war_info,
            war_effects=self._raw_war_effects,
            personal_order=self._raw_personal_order,
            steam_news=self._raw_steam_news,
            json_dict=self.json_dict,
        )
        self.formatted_data = FormattedData(context=formatted_data_context)
        self.update_tracker_rates()
        if not self.loaded:
            self.loaded = True

    def update_tracker_rates(self):
        # liberation rates
        for campaign in self.formatted_data.campaigns:
            self.tracking_service.liberation_changes.add_entry(
                key=campaign.planet.index, value=campaign.progress
            )
            campaign.planet.tracker = (
                self.tracking_service.liberation_changes.get_entry(
                    campaign.planet.index
                )
            )

        # region rates
        planets_with_regions = [
            p for p in self.formatted_data.planets.values() if p.regions
        ]
        for planet in planets_with_regions:
            for region in planet.regions.values():
                if region.is_available:
                    self.tracking_service.region_changes.add_entry(
                        key=region.settings_hash, value=region.perc
                    )
                    region.tracker = self.tracking_service.region_changes.get_entry(
                        key=region.settings_hash
                    )
        # major order rates
        if self.formatted_data.assignments["en"]:
            for assignment in self.formatted_data.assignments["en"]:
                for task_index, task in enumerate(assignment.tasks, start=1):
                    if task.type in [11, 12, 13, 14, 15]:
                        continue
                    self.tracking_service.major_order_changes.add_entry(
                        key=(assignment.id, task_index), value=task.progress_perc
                    )
            for assignments in self.formatted_data.assignments.values():
                for assignment in assignments:
                    for task_index, task in enumerate(assignment.tasks, start=1):
                        task.tracker = (
                            self.tracking_service.major_order_changes.get_entry(
                                key=(assignment.id, task_index)
                            )
                        )
        # ta rates
        if self.formatted_data.dss:
            for ta in self.formatted_data.dss.tactical_actions:
                for cost in ta.cost:
                    self.tracking_service.tactical_action_changes.add_entry(
                        key=(ta.id, cost.item), value=cost.progress
                    )
                    ta.cost_changes[cost.item] = (
                        self.tracking_service.tactical_action_changes.get_entry(
                            key=(ta.id, cost.item)
                        )
                    )
