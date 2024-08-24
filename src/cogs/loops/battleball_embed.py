"""
This module contains the UpdateBattleballPanelLoop cog for the Discord bot.

The UpdateBattleballPanelLoop cog provides functionality to update the battleball panel
every 30 seconds.
"""

from loguru import logger
from discord.ext import commands, tasks

from src.helper.config import Config
from src.controller.habbo.battleball.worker.worker import BattleballWorker


class UpdateBattleballPanelLoop(commands.Cog):
    """
    A class representing a loop that updates the battleball panel.

    This class is a cog that contains a task loop that runs every 30 seconds to update the battleball panel.
    It uses a `BattleballWorker` instance to create or update the embed for the battleball panel.

    Attributes:
        bot (commands.Bot): The instance of the bot.
        config (Config): The configuration object.
        battleball_worker (BattleballWorker): The worker object for battleball operations.

    Methods:
        update_battleball_panel: The task loop that updates the battleball panel.
        before_update_battleball_panel: A method that runs before the task loop starts.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Initializes the UpdateBattleballPanelLoop cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.config = Config()
        self.battleball_worker = BattleballWorker(bot)
        self.update_battleball_panel.start()

    @tasks.loop(seconds=30)
    async def update_battleball_panel(self) -> None:
        """
        A task loop that updates the battleball panel.

        This method is called every 30 seconds to create or update the embed for the battleball panel.
        It uses the `battleball_worker` to perform the necessary operations.

        Returns:
            None
        """
        await self.battleball_worker.create_or_update_embed()

    @update_battleball_panel.before_loop
    async def before_update_battleball_panel(self) -> None:
        """
        A method that runs before the task loop starts.

        This method is called before the `update_battleball_panel` task loop starts.
        It waits until the bot is ready before starting the loop.

        Returns:
            None
        """
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    """
    Sets up the UpdateBattleballPanelLoop cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(UpdateBattleballPanelLoop(bot))
    logger.info("UpdateBattleballPanelLoop loop loaded!")
