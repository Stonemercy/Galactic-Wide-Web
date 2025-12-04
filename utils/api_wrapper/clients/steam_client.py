from ...api_wrapper.clients import BaseAPIClient


class SteamPlayerCountClient(BaseAPIClient):
    def __init__(self, logger, base_url: str):
        super().__init__(
            base_url=base_url,
            logger=logger,
        )

    async def get_steam_count(self) -> dict:
        """Get the current steam player count"""
        return await self.get(
            endpoint="",
            params={"appid": 553850},
        )


class SteamNewsClient(BaseAPIClient):
    def __init__(self, logger, base_url: str):
        super().__init__(
            base_url=base_url,
            logger=logger,
        )

    async def get_steam_news(self) -> dict:
        """Get the recent steam news"""
        return await self.get(
            endpoint="",
        )
