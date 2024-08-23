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
    MAX_ATTEMPTS = 5  # Reduce the number of retry attempts to avoid long delays

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
                if attempt < self.MAX_ATTEMPTS - 1:
                    continue
                else:
                    raise e

    async def fetch_user_bouncer_id(self, username: str) -> str:
        user_data = await self.fetch_user_data(username)
        return user_data.bouncerPlayerId

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
                if attempt < self.MAX_ATTEMPTS - 1:
                    continue
                else:
                    raise e

    async def fetch_match_data_batch(self, match_ids: List[str]) -> List[Match]:
        matches = []
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            tasks = []
            for match_id in match_ids:
                tasks.append(self.fetch_match_data(client, match_id))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Match):
                    matches.append(result)
        return matches

    async def fetch_match_data(self, client: httpx.AsyncClient, match_id: str) -> Match:
        for attempt in range(self.MAX_ATTEMPTS):
            try:
                proxy = self.get_random_proxy()
                response = await client.get(f"{self.BASE_URL}/matches/v1/{match_id}", proxies=proxy)
                response.raise_for_status()
                data = response.json()
                return Match(**data)
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt < self.MAX_ATTEMPTS - 1:
                    logger.warning(f"Retry {attempt + 1}/{self.MAX_ATTEMPTS} for match ID '{match_id}'")
                    continue
                else:
                    logger.error(f"Failed to fetch match data for ID '{match_id}': {e}")
                    raise e
