import httpx
from loguru import logger
from src.helper.config import Config

class RadioController:
    _instance = None

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
        self.headers = {"X-API-Key": self.config.azuracast_api_key}

    async def get_now_playing(self) -> str:
        url = f"{self.config.azuracast_api_url}/nowplaying"
        try:
            response = await self.client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                now_playing = data[0].get("now_playing", {}).get("song", {}).get("title", "Unknown")
                return now_playing
            else:
                logger.error("Unexpected response format or empty data list")
                return "Unknown"
        except Exception as e:
            logger.error(f"Failed to get now playing: {e}")
            return "Unknown"

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=None)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client.aclose()
