"""
This module contains the BattleQueue cog for the Discord bot.

The BattleQueue cog provides functionality for displaying the current queue for
BattleBall profile updates.
"""

import discord
from discord.ext import commands
from discord import app_commands

from src.helper.config import Config
from src.controller.habbo.battleball.worker.worker import BattleballWorker
from src.database.service.battleball_service import BattleballDatabaseService


class BattleQueue(commands.Cog):
    """
    A Discord bot cog for managing the BattleBall profile update queue.

    Attributes:
        bot (commands.Bot): The bot instance.
        config (Config): The configuration object.
        db_service (BattleballDatabaseService): The database service for BattleBall.
        battleball_worker (BattleballWorker): The worker for managing BattleBall updates.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initializes the BattleQueue cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.config = Config()
        self.db_service = BattleballDatabaseService()
        self.battleball_worker = BattleballWorker(bot)  # Initialize the worker

    @app_commands.command(
        name="queue",
        description="Displays the current queue for BattleBall profile updates."
    )
    async def battle_queue_command(self, interaction: discord.Interaction):
        """
        Command to display the current queue for BattleBall profile updates.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        queue_list = await self.db_service.get_queue()

        if queue_list:
            queue_display = []
            for idx, entry in enumerate(queue_list):
                position = idx + 1
                username = entry['username']
                discord_id = entry['discord_id']

                if username == self.battleball_worker.current_user:
                    remaining_matches = await self.battleball_worker.get_remaining_matches()
                    queue_display.append(
                        f"{self.config.arriba_icon} **{position}**. {username} "
                        f"(Added by: <@{discord_id}> - {remaining_matches} left)"
                    )
                else:
                    queue_display.append(
                        f"{self.config.abajo_icon} **{position}**. {username} "
                        f"(Added by: <@{discord_id}>)"
                    )

            queue_message = "\n".join(queue_display)
            await interaction.response.send_message(
                f"**Current Queue:**\n{queue_message}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "The queue is currently empty.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """
    Sets up the BattleQueue cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(BattleQueue(bot))
