import httpx
import random
from typing import List
from src.helper.singleton import Singleton
from src.controller.habbo.battleball.api_client.models import User, Match

@Singleton
class HabboApiClient:
    BASE_URL = "https://origins.habbo.es/api/public"
    TIMEOUT = 10.0
    MAX_ATTEMPTS = 10  # Maximum number of retry attempts

    def __init__(self):
        # Load proxies from the file at initialization
        self.proxies = self.load_proxies()

    def load_proxies(self) -> List[str]:
        # Read the proxies from the file
        with open("src/assets/proxies.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]

    def get_random_proxy(self) -> str:
        # Select a random proxy
        return random.choice(self.proxies)

    async def fetch_user_data(self, username: str) -> User:
        username = username.lower()  # Convert username to lowercase
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
                    continue  # Retry the request
                else:
                    raise  # Re-raise the exception after max attempts

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
                        response = await client.get(f"{self.BASE_URL}/matches/v1/{bouncerPlayerId}/ids", params={"offset": offset, "limit": limit})
                        response.raise_for_status()
                        data = response.json()
                        if not data:
                            break
                        match_ids.extend(data)
                        offset += limit
                return match_ids
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt < self.MAX_ATTEMPTS - 1:
                    continue  # Retry the request
                else:
                    raise  # Re-raise the exception after max attempts

    async def fetch_match_data_batch(self, match_ids: List[str]) -> List[Match]:
        matches = []
        for match_id in match_ids:
            for attempt in range(self.MAX_ATTEMPTS):
                try:
                    proxy = self.get_random_proxy()
                    async with httpx.AsyncClient(proxies=proxy, timeout=self.TIMEOUT) as client:
                        response = await client.get(f"{self.BASE_URL}/matches/v1/{match_id}")
                        response.raise_for_status()
                        data = response.json()
                        matches.append(Match(**data))
                        break  # Exit retry loop on success
                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    if attempt < self.MAX_ATTEMPTS - 1:
                        continue  # Retry the request
                    else:
                        raise  # Re-raise the exception after max attempts
        return matches