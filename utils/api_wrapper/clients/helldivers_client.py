from ...api_wrapper.clients import BaseAPIClient


class HelldiversClient(BaseAPIClient):
    def __init__(self, logger, base_url: str):
        super().__init__(
            base_url=base_url,
            logger=logger,
            headers={
                "Accept-Language": "en-GB",
                "X-Super-Client": "Galactic Wide Web",
                "X-Super-Contact": "Stonemercy",
            },
        )

    async def get_news_feed(
        self, war_id: int, time_for_dispatches: int, lang: str = "en-GB"
    ) -> list[dict]:
        """Get the most recent news"""
        return await self.get(
            endpoint=f"NewsFeed/{war_id}?fromTimestamp={time_for_dispatches}",
            headers={"Accept-Language": lang},
        )

    async def get_war_status(self, war_id: int, lang: str = "en-GB") -> dict:
        """Get the current war status"""
        return await self.get(
            endpoint=f"WarSeason/{war_id}/Status",
            headers={"Accept-Language": lang},
        )

    async def get_assignments(self, war_id: int, lang: str = "en-GB") -> list[dict]:
        """Get current major orders"""
        return await self.get(
            endpoint=f"v2/Assignment/War/{war_id}",
            headers={"Accept-Language": lang},
        )

    async def get_dss_info(self, war_id: int, station_id: int) -> dict:
        """Get DSS tactical actions and status"""
        return await self.get(endpoint=f"SpaceStation/{war_id}/{station_id}")

    async def get_war_id(self) -> int:
        """Get the current war ID"""
        return await self.get(endpoint="WarSeason/current/WarID")

    async def get_war_info(self, war_id: int) -> dict:
        """Get the current war info"""
        return await self.get(endpoint=f"WarSeason/{war_id}/WarInfo")

    async def get_war_effects(self) -> list:
        """Get the current war effects"""
        return await self.get(endpoint=f"WarSeason/GalacticWarEffects")

    async def get_war_stats(self, war_id: int) -> dict:
        """Get the current war stats"""
        return await self.get(endpoint=f"Stats/War/{war_id}/Summary")
