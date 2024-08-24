"""
This module contains the StatusLoop cog for the Discord bot.

The StatusLoop cog provides functionality to periodically change the bot's status
based on a custom status message.
"""

import discord
from loguru import logger
from discord.ext import commands, tasks

from src.helper.status import BotStatus as Status


class StatusLoop(commands.Cog):
    """
    A class representing a loop for changing the bot's status.

    This class is a cog that can be added to a Discord bot to periodically change the bot's status
    based on the status message obtained from the `Status` class.

    Attributes:
        bot (commands.Bot): The Discord bot instance.
        status (Status): An instance of the `Status` class for obtaining the status message.
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Initializes the StatusLoop cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.status = Status(self.bot)
        self.change_status.start()

    @tasks.loop(seconds=30)
    async def change_status(self):
        """
        A task that changes the bot's status.

        This task is executed every 30 seconds and updates the bot's presence with a custom activity
        using the status message obtained from the `Status` class.
        """
        status_message = await self.status.get_status_message()
        await self.bot.change_presence(
            status=discord.Status.do_not_disturb,
            activity=discord.CustomActivity(name=status_message)
        )

    @change_status.before_loop
    async def before_change_status(self) -> None:
        """
        A coroutine that waits until the bot is ready before starting the change_status task.
        """
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    """
    Sets up the StatusLoop cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(StatusLoop(bot))
    logger.info("Status loop loaded!")
