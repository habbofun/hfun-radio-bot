"""
This module contains the CleanupBattleballDatabaseLoop cog for the Discord bot.

The CleanupBattleballDatabaseLoop cog provides functionality to clean up the battleball
database by removing users who are out of the top 40 on the leaderboard every hour.
"""

from loguru import logger
from discord.ext import commands, tasks

from src.helper.config import Config
from src.database.service.battleball_service import BattleballDatabaseService


class CleanupBattleballDatabaseLoop(commands.Cog):
    """
    A class representing a loop that cleans up the battleball database.

    This class is a cog that contains a task loop that runs every hour to remove users
    who are out of the top 40 on the leaderboard from the database.

    Attributes:
        bot (commands.Bot): The instance of the bot.
        config (Config): The configuration object.
        database_service (BattleballDatabaseService): The database service for battleball.

    Methods:
        cleanup_database: The task loop that cleans up the battleball database.
        before_cleanup_database: A method that runs before the task loop starts.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Initializes the CleanupBattleballDatabaseLoop cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.config = Config()
        self.database_service = BattleballDatabaseService()
        self.cleanup_database.start()

    @tasks.loop(hours=1)
    async def cleanup_database(self) -> None:
        """
        A task loop that cleans up the battleball database.

        This method is called every hour to remove users who are out of the top 40
        on the leaderboard from the database.

        Returns:
            None
        """
        leaderboard = await self.database_service.get_leaderboard()
        if len(leaderboard) > 40:
            # Determine the minimum score of the top 40 users
            # Assuming the score is the second item in each tuple
            min_score_to_keep = leaderboard[39][1]
            for user in leaderboard[40:]:
                # Check if the user's score is below the 40th user's score
                if user[1] < min_score_to_keep:
                    # Remove the user by username
                    await self.database_service.fulminate_user(user[0])
                    logger.info(
                        f"Removed user '{user[0]}' from the database for being out of the top 40."
                    )

    @cleanup_database.before_loop
    async def before_cleanup_database(self) -> None:
        """
        A method that runs before the task loop starts.

        This method is called before the `cleanup_database` task loop starts.
        It waits until the bot is ready before starting the loop.

        Returns:
            None
        """
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    """
    Sets up the CleanupBattleballDatabaseLoop cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(CleanupBattleballDatabaseLoop(bot))
    logger.info("CleanupBattleballDatabaseLoop loop loaded!")
