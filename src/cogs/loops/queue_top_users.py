from discord.ext import commands, tasks
from loguru import logger
import time

from src.database.service.battleball_service import BattleballDatabaseService
from src.controller.habbo.battleball.worker.worker import BattleballWorker
from src.utils.time_utils import UpdateTimer
from src.helper.config import Config

class BattleballUpdateLoop(commands.Cog):
    """
    A class representing a loop that queues the top 45 users in the battleball database for updates.

    This class is a cog that contains a task loop that runs every hour to add the top 45 users
    on the leaderboard to the update queue.

    Attributes:
        bot (commands.Bot): The instance of the bot.
        database_service (BattleballDatabaseService): The database service for battleball.
        battleball_worker (BattleballWorker): The worker for managing BattleBall updates.
        update_timer (UpdateTimer): The singleton instance of the UpdateTimer class.

    Methods:
        queue_top_users: The task loop that queues the top 45 users in the battleball database for updates.
        before_queue_top_users: A method that runs before the task loop starts.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Initializes the BattleballUpdateLoop cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.database_service = BattleballDatabaseService()
        self.battleball_worker = BattleballWorker(bot)
        self.update_timer = UpdateTimer()
        self.queue_top_users.start()

    @tasks.loop(seconds=Config().battleball_api_update_interval_seconds)
    async def queue_top_users(self) -> None:
        """
        A task loop that queues the top 45 users in the battleball database for updates.

        This method is called every X minutes to add the top 45 users on the leaderboard
        to the update queue.

        Returns:
            None
        """
        self.update_timer.update_last_run_time()  # Update the last_run_time here
        leaderboard = await self.database_service.get_leaderboard()

        # Only process if there are users to queue
        if leaderboard:
            # Get the top 45 users
            top_users = leaderboard[:45]
            for user in top_users:
                username = user[0]
                discord_id = 1270453978861142097

                await self.database_service.add_to_queue(username, discord_id)

            # Start the worker if it's not running
            if not self.battleball_worker.running:
                await self.battleball_worker.start()

    @queue_top_users.before_loop
    async def before_queue_top_users(self) -> None:
        """
        A method that runs before the task loop starts.

        This method is called before the `queue_top_users` task loop starts.
        It waits until the bot is ready before starting the loop.

        Returns:
            None
        """
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    """
    Sets up the BattleballUpdateLoop cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(BattleballUpdateLoop(bot))
    logger.info("BattleballUpdateLoop cog loaded!")