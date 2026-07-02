from utils.api_wrapper.clients import BaseAPIClient
from utils.dataclasses import Config


class ArsenalClient(BaseAPIClient):
    def __init__(self, logger):
        super().__init__(base_url=Config.ARSENAL_API_URL, logger=logger)

    async def get_community_target(self) -> list[dict]:
        return await self.get()
