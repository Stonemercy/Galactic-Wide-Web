from ...api_wrapper.clients import BaseAPIClient
from ...dataclasses import Config


class AuthedClient(BaseAPIClient):
    def __init__(self, logger):
        super().__init__(
            base_url=Config.AUTHED_API_URL,
            logger=logger,
            headers=Config.AUTHED_API_HEADERS,
        )

    async def get_dss_votes(self) -> dict:
        return await self.get("/raw/election")

    async def get_personal_order(self) -> dict:
        return await self.get("/raw/assignment")

    async def get_player(self, user_id: str, platform: int) -> dict:
        return await self.get(f"/player/lookup?user={user_id}&platform={platform}")


class AltDSSVotesAuthedClient(BaseAPIClient):
    def __init__(self, logger):
        super().__init__(
            base_url=Config.ALT_AUTHED_API_DSS_ENDPOINT,
            logger=logger,
            headers=Config.ALT_AUTHED_API_HEADERS,
        )

    async def get_dss_votes(self, period_id: str) -> dict:
        return await self.get(f"/{period_id}")


class AltPOAuthedClient(BaseAPIClient):
    def __init__(self, logger):
        super().__init__(
            base_url=Config.ALT_PO_ENDPOINT,
            logger=logger,
            headers=Config.ALT_AUTHED_API_HEADERS,
        )

    async def get_personal_order(self) -> dict:
        return await self.get()
