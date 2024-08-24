"""
This module contains the UpdateInfoPanelLoop cog for the Discord bot.

The UpdateInfoPanelLoop cog provides functionality to update the information panel
periodically by calling the `create_or_update_embed` method of the `RadioController` class.
"""

from loguru import logger
from discord.ext import commands, tasks

from src.helper.config import Config
from src.controller.radio.radio_controller import RadioController


class UpdateInfoPanelLoop(commands.Cog):
    """
    A class representing a loop that updates the information panel.

    This class is a subclass of `commands.Cog` and is responsible for periodically updating
    the information panel by calling the `create_or_update_embed` method of the `RadioController` class.

    Attributes:
        bot (commands.Bot): The instance of the bot.
        config (Config): The configuration object.
        radio_controller (RadioController): The instance of the radio controller.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Initializes the UpdateInfoPanelLoop cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.config = Config()
        self.radio_controller = RadioController(bot)
        self.update_info_panel.start()

    @tasks.loop(seconds=30)
    async def update_info_panel(self) -> None:
        """
        A coroutine that updates the information panel.

        This coroutine is called periodically every 30 seconds by the `update_info_panel` task.
        It calls the `create_or_update_embed` method of the `RadioController` class to update
        the information panel.
        """
        await self.radio_controller.create_or_update_embed()

    @update_info_panel.before_loop
    async def before_update_info_panel(self) -> None:
        """
        A coroutine that runs before the `update_info_panel` task starts.

        This coroutine waits until the bot is ready before starting the `update_info_panel` task.
        """
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    """
    Sets up the UpdateInfoPanelLoop cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(UpdateInfoPanelLoop(bot))
    logger.info("UpdateInfoPanel loop loaded!")
