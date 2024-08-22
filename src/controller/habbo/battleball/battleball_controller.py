import httpx, random, asyncio
from loguru import logger
from src.helper.singleton import Singleton
from concurrent.futures import ThreadPoolExecutor

@Singleton
class BattleballController:
    BASE_URL = "https://origins.habbo.es/api/public/"

    def __init__(self, proxy_file='src/assets/proxies.txt', max_concurrent_requests=100, max_threads=100):
        self.proxies = self.load_proxies(proxy_file)
        self.max_concurrent_requests = max_concurrent_requests
        self.executor = ThreadPoolExecutor(max_workers=max_threads)

    def load_proxies(self, proxy_file):
        with open(proxy_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    def get_random_proxy(self):
        return random.choice(self.proxies) if self.proxies else None

    async def request_with_retry(self, url, params=None, max_retries=10):
        for attempt in range(max_retries):
            proxy = self.get_random_proxy()
            try:
                async with httpx.AsyncClient(proxies=proxy) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                #logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries})")
                pass
        raise Exception(f"Failed to complete request after {max_retries} attempts.")

    async def get_bouncer_player_id(self, username):
        url = f"{self.BASE_URL}users?name={username}"
        data = await self.request_with_retry(url)
        return data['bouncerPlayerId']

    async def get_match_ids(self, bouncer_player_id, start_time=None, end_time=None):
        match_ids = []
        offset = 0
        limit = 100  # Smaller limit to ensure proper pagination

        while True:
            url = f"{self.BASE_URL}matches/v1/{bouncer_player_id}/ids"
            params = {"offset": offset, "limit": limit}
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time

            new_match_ids = await self.request_with_retry(url, params=params)

            if not new_match_ids:
                break

            match_ids.extend(new_match_ids)
            offset += limit  # Increase the offset to get the next batch

            # If we receive fewer matches than the limit, we're done
            if len(new_match_ids) < limit:
                break

        #logger.info(f"Total {len(match_ids)} match IDs retrieved for player {bouncer_player_id}")
        return match_ids

    async def get_match_data(self, match_id):
        """Fetches data for a single match."""
        url = f"{self.BASE_URL}matches/v1/{match_id}"
        return await self.request_with_retry(url)

    def fetch_match_data_threaded(self, match_id):
        """Function to be executed in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.get_match_data(match_id))

    async def fetch_all_match_data(self, match_ids):
        results = []

        # Use multithreading to fetch match data concurrently
        with ThreadPoolExecutor(max_workers=self.max_concurrent_requests) as executor:
            loop = asyncio.get_event_loop()
            futures = [loop.run_in_executor(executor, self.fetch_match_data_threaded, match_id) for match_id in match_ids]

            for future in asyncio.as_completed(futures):
                try:
                    result = await future
                    results.append(result)
                except Exception as e:
                    #logger.error(f"Error fetching match data: {e}")
                    pass

        return results
