"""
This module contains the BattleFulminate cog for the Discord bot.

The BattleFulminate cog provides functionality to delete a BattleBall profile's data.
"""

import discord
from loguru import logger
from discord.ext import commands
from discord import app_commands

from src.database.service.battleball_service import BattleballDatabaseService
from src.controller.habbo.battleball.worker.worker import BattleballWorker


class BattleFulminate(commands.Cog):
    """
    A Discord bot cog for deleting BattleBall profile data.

    Attributes:
        bot (commands.Bot): The bot instance.
        db_service (BattleballDatabaseService): The database service for BattleBall.
        battleball_worker (BattleballWorker): The worker for managing BattleBall updates.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initializes the BattleFulminate cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.db_service = BattleballDatabaseService()
        self.battleball_worker = BattleballWorker(bot)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(
        name="fulminate",
        description="Command to delete a BattleBall profile's data."
    )
    async def battle_fulminate_command(self, interaction: discord.Interaction, username: str):
        """
        Command to delete a BattleBall profile's data.

        Args:
            interaction (discord.Interaction): The interaction object.
            username (str): The username of the BattleBall profile to delete.
        """
        await self.db_service.fulminate_user(username)

        await interaction.response.send_message(
            f"The user `{username}` and all associated data have been permanently deleted.",
            ephemeral=True
        )
        logger.info(
            f"User '{interaction.user.name}' triggered fulmination for '{username}'")


async def setup(bot: commands.Bot):
    """
    Sets up the BattleFulminate cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(BattleFulminate(bot))
    logger.info("BattleFulminate cog loaded")
