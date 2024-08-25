import time
from src.helper.config import Config
from src.helper.singleton import Singleton

@Singleton
class UpdateTimer:
    def __init__(self):
        self.last_run_time = 0
        self.config = Config()
        self.update_interval = self.config.battleball_api_update_interval_seconds

    def get_next_update_time(self) -> float:
        """
        Calculate the time remaining until the next update of the queue_top_users loop.

        Returns:
            float: The number of seconds until the next update.
        """
        current_time = time.time()
        time_since_last_run = current_time - self.last_run_time
        
        time_until_next_update = max(0, self.update_interval - time_since_last_run)
        return time_until_next_update

    def update_last_run_time(self):
        """
        Update the last run time to the current time.
        """
        self.last_run_time = time.time()