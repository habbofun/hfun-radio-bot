"""
This module contains the Ping cog for the Discord bot.

The Ping cog provides functionality for testing the bot's latency.
"""

import discord
from loguru import logger
from discord.ext import commands
from discord import app_commands

from src.controller.discord.schema.embed_schema import EmbedSchema
from src.controller.discord.embed_controller import EmbedController


class Ping(commands.Cog):
    """
    A class representing the Ping command cog.

    This cog provides functionality for testing the bot's latency.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initializes the Ping cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(
        name="ping",
        description="Command to test the bot's latency."
    )
    async def ping_command(self, interaction: discord.Interaction):
        """
        Command to test the bot's latency.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        await self.bot.command_queue.put(
            (interaction, self.process_ping_command(interaction))
        )

    async def process_ping_command(self, interaction: discord.Interaction):
        """
        Processes the ping command to test bot latency.

        Args:
            interaction (discord.Interaction): The interaction object.
        """
        try:
            latency = round(self.bot.latency * 1000)

            embed_schema = EmbedSchema(
                title="🏓 Pong!",
                description=f"Latency is `{latency}ms`.",
                color=0xb34760
            )

            embed = await EmbedController().build_embed(embed_schema)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            # Catch any unexpected exceptions during command processing
            logger.critical(f"Failed to respond to ping command: {e}")
            if not interaction.response.is_done():
                try:
                    await interaction.followup.send(
                        "There was an error trying to execute that command!",
                        ephemeral=True
                    )
                except Exception as followup_error:
                    logger.critical(
                        f"Failed to send follow-up message: {followup_error}")

    @ping_command.error
    async def ping_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        """
        Handles errors that occur during the execution of the ping command.

        Args:
            interaction (discord.Interaction): The interaction object.
            error (app_commands.AppCommandError): The error that occurred.
        """
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You don't have the necessary permissions to use this command.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"An error occurred: {error}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """
    Sets up the Ping cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(Ping(bot))
    logger.info("Ping command loaded!")
