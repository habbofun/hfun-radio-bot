from discord.ext import commands, tasks
from loguru import logger

from src.database.service.battleball_service import BattleballDatabaseService
from src.controller.habbo.battleball.worker.worker import BattleballWorker

class BattleballUpdateLoop(commands.Cog):
    """
    A class representing a loop that queues the top 45 users in the battleball database for updates.

    This class is a cog that contains a task loop that runs every hour to add the top 45 users
    on the leaderboard to the update queue.

    Attributes:
        bot (commands.Bot): The instance of the bot.
        database_service (BattleballDatabaseService): The database service for battleball.
        battleball_worker (BattleballWorker): The worker for managing BattleBall updates.

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
        self.queue_top_users.start()

    @tasks.loop(hours=1)
    async def queue_top_users(self) -> None:
        """
        A task loop that queues the top 45 users in the battleball database for updates.

        This method is called every hour to add the top 45 users on the leaderboard
        to the update queue.

        Returns:
            None
        """
        leaderboard = await self.database_service.get_leaderboard()

        # Only process if there are users to queue
        if leaderboard:
            # Get the top 45 users
            top_users = leaderboard[:45]
            for user in top_users:
                username = user[0]
                discord_id = 0  # Replace with actual Discord ID if available

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
