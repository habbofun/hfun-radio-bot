"""
This module contains the OnReady cog for the Discord bot.

The OnReady cog provides functionality to handle the event when the bot is ready.
"""

import os
from loguru import logger
from pyfiglet import Figlet
from discord.ext import commands
from pystyle import Colors, Colorate, Center

from src.helper.config import Config
from src.views.battleball.panel import BattleballPanelView
from src.controller.habbo.battleball.worker.worker import BattleballWorker


class OnReady(commands.Cog):
    """
    A class representing the on_ready event handler for the bot.

    Attributes:
        bot (commands.Bot): The bot instance.
        config (Config): The configuration object.
        battleball_worker (BattleballWorker): The worker for managing BattleBall updates.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initializes the OnReady cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.config = Config()
        self.battleball_worker = BattleballWorker(self)

    @commands.Cog.listener()
    async def on_ready(self):
        """
        A coroutine that is called when the bot is ready to start receiving events.
        """
        os.system("cls||clear")

        logo = Figlet(font="big").renderText(self.config.app_name)
        centered_logo = Center.XCenter(
            Colorate.Vertical(Colors.white_to_blue, logo, 1))
        divider = Center.XCenter(
            Colorate.Vertical(Colors.white_to_blue,
                              "──────────────────────────────────────────", 1)
        )
        print(f"{centered_logo}\n{divider}\n\n")

        logger.debug("Setting persistent views...")
        self.bot.add_view(BattleballPanelView(self.bot))

        logger.debug("Loading workers...")
        if not self.battleball_worker.running:
            await self.battleball_worker.start()

        logger.info(
            f"Logged in as {self.bot.user.name}#{self.bot.user.discriminator}.")


async def setup(bot: commands.Bot) -> None:
    """
    Sets up the OnReady cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(OnReady(bot))
    logger.info("On ready event registered!")
