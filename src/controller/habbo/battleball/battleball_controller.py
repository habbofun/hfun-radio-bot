import httpx, random, asyncio
from loguru import logger
from src.helper.singleton import Singleton
from concurrent.futures import ThreadPoolExecutor

@Singleton
class BattleballController:
    """
    Controller class for handling Battleball game data retrieval.
    """

    BASE_URL = "https://origins.habbo.es/api/public/"

    def __init__(self, proxy_file='src/assets/proxies.txt', max_concurrent_requests=2, max_threads=5):
        """
        Initializes the BattleballController.

        Args:
            proxy_file (str): Path to the file containing proxy information.
            max_concurrent_requests (int): Maximum number of concurrent requests.
            max_threads (int): Maximum number of threads for fetching match data.
        """
        self.proxies = self.load_proxies(proxy_file)
        self.max_concurrent_requests = max_concurrent_requests
        self.executor = ThreadPoolExecutor(max_workers=max_threads)

    def load_proxies(self, proxy_file):
        """
        Loads the proxy information from a file.

        Args:
            proxy_file (str): Path to the file containing proxy information.

        Returns:
            list: List of proxy URLs.
        """
        with open(proxy_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    def get_random_proxy(self):
        """
        Returns a random proxy URL from the list of proxies.

        Returns:
            str: Random proxy URL.
        """
        return random.choice(self.proxies) if self.proxies else None

    async def request_with_retry(self, url, params=None, max_retries=10):
        """
        Sends an HTTP GET request to the specified URL with optional parameters and retries on failure.

        Args:
            url (str): The URL to send the request to.
            params (dict, optional): The parameters to include in the request. Defaults to None.
            max_retries (int, optional): The maximum number of retries. Defaults to 10.

        Returns:
            dict: The JSON response from the request.

        Raises:
            Exception: If the request fails after the maximum number of retries.
        """
        for attempt in range(max_retries):
            proxy = self.get_random_proxy()
            try:
                async with httpx.AsyncClient(proxies=proxy) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                pass
        raise Exception(f"Failed to complete request after {max_retries} attempts.")

    async def get_bouncer_player_id(self, username):
        """
        Retrieves the bouncer player ID for the specified username.

        Args:
            username (str): The username to retrieve the bouncer player ID for.

        Returns:
            str: The bouncer player ID.
        """
        url = f"{self.BASE_URL}users?name={username}"
        data = await self.request_with_retry(url)
        return data['bouncerPlayerId']

    async def get_match_ids(self, bouncer_player_id, start_time=None, end_time=None):
        """
        Retrieves the match IDs for the specified bouncer player ID within the specified time range.

        Args:
            bouncer_player_id (str): The bouncer player ID to retrieve the match IDs for.
            start_time (str, optional): The start time of the time range. Defaults to None.
            end_time (str, optional): The end time of the time range. Defaults to None.

        Returns:
            list: List of match IDs.
        """
        match_ids = []
        offset = 0
        limit = 100

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
            offset += limit

            if len(new_match_ids) < limit:
                break

        return match_ids

    async def get_match_data(self, match_id):
        """
        Retrieves the match data for the specified match ID.

        Args:
            match_id (str): The match ID to retrieve the data for.

        Returns:
            dict: The match data.
        """
        url = f"{self.BASE_URL}matches/v1/{match_id}"
        return await self.request_with_retry(url)

    def fetch_match_data_threaded(self, match_id):
        """
        Fetches the match data for the specified match ID in a separate thread.

        Args:
            match_id (str): The match ID to fetch the data for.

        Returns:
            dict: The match data.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.get_match_data(match_id))

    async def fetch_all_match_data(self, match_ids):
        """
        Fetches the match data for all the specified match IDs concurrently.

        Args:
            match_ids (list): List of match IDs to fetch the data for.

        Returns:
            list: List of match data.
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.max_concurrent_requests) as executor:
            loop = asyncio.get_event_loop()
            futures = [loop.run_in_executor(executor, self.fetch_match_data_threaded, match_id) for match_id in match_ids]

            for future in asyncio.as_completed(futures):
                try:
                    result = await future
                    results.append(result)
                except Exception as e:
                    pass

        return results
