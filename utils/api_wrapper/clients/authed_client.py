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
        """Get the current war status"""
        return await self.get("/election")

    async def get_personal_order(self) -> dict:
        """Get the current personal orders"""
        return await self.get("/assignment")
