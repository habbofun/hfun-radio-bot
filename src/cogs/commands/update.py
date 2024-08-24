"""
This module contains the BattleUpdate cog for the Discord bot.

The BattleUpdate cog provides functionality to update a BattleBall profile's data.
"""

import discord
from discord.ext import commands
from discord import app_commands
from loguru import logger

from src.database.service.battleball_service import BattleballDatabaseService
from src.controller.habbo.battleball.worker.worker import BattleballWorker


class BattleUpdate(commands.Cog):
    """
    A Discord bot cog for updating BattleBall profile data.

    Attributes:
        bot (commands.Bot): The bot instance.
        db_service (BattleballDatabaseService): The database service for BattleBall.
        battleball_worker (BattleballWorker): The worker for managing BattleBall updates.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initializes the BattleUpdate cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.db_service = BattleballDatabaseService()
        self.battleball_worker = BattleballWorker(bot)

    @app_commands.command(
        name="update",
        description="Command to update a battleball profile's data."
    )
    async def battle_update_command(
        self,
        interaction: discord.Interaction,
        username: str
    ):
        """
        Command to update a BattleBall profile's data.

        Args:
            interaction (discord.Interaction): The interaction object.
            username (str): The username of the BattleBall profile to update.
        """
        added_by = interaction.user.id
        added_by_name = interaction.user.name
        position = await self.db_service.add_to_queue(username, added_by)

        if position == 1:
            await interaction.response.send_message(
                f"The job for `{username}` is now being processed.\n"
                "You'll receive a notification once it's done.",
                ephemeral=True
            )
            await self.log_queue_addition(username, added_by_name, position)
            if not self.battleball_worker.running:
                await self.battleball_worker.start()
        else:
            await self.log_queue_addition(username, added_by_name, position)
            await interaction.response.send_message(
                f"The user `{username}` is already at the queue at position `{position}`.",
                ephemeral=True
            )

    async def log_queue_addition(self, username: str, added_by_name: str, position: int):
        """
        Logs the addition of a user to the BattleBall update queue.

        Args:
            username (str): The username of the BattleBall profile.
            added_by_name (str): The name of the user who added the profile.
            position (int): The position in the queue.
        """
        logger.info(
            f"User '{added_by_name}' added '{username}' to the queue at position '{position}'"
        )


async def setup(bot: commands.Bot):
    """
    Sets up the BattleUpdate cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(BattleUpdate(bot))
    logger.info("BattleUpdate cog loaded")
