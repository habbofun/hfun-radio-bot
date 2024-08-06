import httpx
from loguru import logger
from src.helper.config import Config

class RadioController:

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if self._instance is not None:
            raise ValueError("An instance of RadioController already exists.")
        
        self.config = Config()
        self.client = httpx.AsyncClient(timeout=None)
        self.headers = {
            "X-API-Key": self.config.azuracast_api_key
        }

    async def get_now_playing(self) -> str:
        url = f"{self.config.azuracast_api_url}/nowplaying"
        try:
            response = await self.client.get(url, headers=self.headers)
            data = response.json()
            return data["now_playing"]["song"]["title"]
        except Exception as e:
            logger.error(f"Failed to get now playing: {e}")
            return None