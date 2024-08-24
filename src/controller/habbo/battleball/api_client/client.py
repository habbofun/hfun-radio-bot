import httpx
import random
import asyncio
from typing import List
from loguru import logger
from src.helper.singleton import Singleton
from src.controller.habbo.battleball.api_client.models import User, Match

@Singleton
class HabboApiClient:
    BASE_URL = "https://origins.habbo.es/api/public"
    TIMEOUT = 10.0
    MAX_ATTEMPTS = 5
    MAX_WORKERS = 5  # Maximum concurrent requests

    def __init__(self):
        self.proxies = self.load_proxies()

    def load_proxies(self) -> List[str]:
        with open("src/assets/proxies.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]

    def get_random_proxy(self) -> str:
        return random.choice(self.proxies)

    async def fetch_user_data(self, username: str) -> User:
        username = username.lower()
        for attempt in range(self.MAX_ATTEMPTS):
            try:
                proxy = self.get_random_proxy()
                async with httpx.AsyncClient(proxies=proxy, timeout=self.TIMEOUT) as client:
                    response = await client.get(f"{self.BASE_URL}/users?name={username}")
                    response.raise_for_status()
                    data = response.json()
                    return User(**data)
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.warning(f"Attempt {attempt + 1}/{self.MAX_ATTEMPTS} failed for user '{username}': {e}")
                if attempt < self.MAX_ATTEMPTS - 1:
                    await asyncio.sleep(1)  # Add a small delay before retrying
        logger.error(f"Failed to fetch user data for username '{username}' after {self.MAX_ATTEMPTS} attempts")
        return None

    async def fetch_match_ids(self, bouncerPlayerId: str, offset: int = 0, limit: int = 100) -> List[str]:
        match_ids = []
        for attempt in range(self.MAX_ATTEMPTS):
            try:
                proxy = self.get_random_proxy()
                async with httpx.AsyncClient(proxies=proxy, timeout=self.TIMEOUT) as client:
                    while True:
                        response = await client.get(
                            f"{self.BASE_URL}/matches/v1/{bouncerPlayerId}/ids",
                            params={"offset": offset, "limit": limit}
                        )
                        response.raise_for_status()
                        data = response.json()

                        if not data:
                            break

                        match_ids.extend(data)
                        offset += limit
                return match_ids
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.warning(f"Attempt {attempt + 1}/{self.MAX_ATTEMPTS} failed for bouncerPlayerId '{bouncerPlayerId}': {e}")
                if attempt < self.MAX_ATTEMPTS - 1:
                    await asyncio.sleep(1)  # Add a small delay before retrying
        logger.error(f"Failed to fetch match IDs for bouncerPlayerId '{bouncerPlayerId}' after {self.MAX_ATTEMPTS} attempts")
        return []

    async def fetch_match_data_batch(self, match_ids: List[str]) -> List[Match]:
        async def fetch_match_data(match_id: str) -> Match:
            for attempt in range(self.MAX_ATTEMPTS):
                try:
                    proxy = self.get_random_proxy()
                    async with httpx.AsyncClient(proxies=proxy, timeout=self.TIMEOUT) as client:
                        response = await client.get(f"{self.BASE_URL}/matches/v1/{match_id}")
                        response.raise_for_status()
                        data = response.json()
                        return Match(**data)
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    logger.warning(f"Attempt {attempt + 1}/{self.MAX_ATTEMPTS} failed for match ID '{match_id}': {e}")
                    if attempt < self.MAX_ATTEMPTS - 1:
                        await asyncio.sleep(1)  # Add a small delay before retrying
            logger.error(f"Failed to fetch match data for ID '{match_id}' after {self.MAX_ATTEMPTS} attempts")
            return None

        tasks = [fetch_match_data(match_id) for match_id in match_ids]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]