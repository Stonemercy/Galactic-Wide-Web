from utils.api_wrapper.clients import BaseAPIClient


class ItemsClient(BaseAPIClient):
    def __init__(self, logger, base_url: str):
        super().__init__(
            base_url=base_url,
            logger=logger,
        )

    async def get_items(self) -> list[dict]:
        return await self.get()
