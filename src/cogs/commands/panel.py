"""
This module contains the InfoPanel cog for the Discord bot.

The InfoPanel cog provides a command to manage the information panel about the radio station.
"""

import discord
from discord.ext import commands
from discord import app_commands
from loguru import logger

from src.helper.config import Config
from src.controller.radio.radio_controller import RadioController


class InfoPanel(commands.Cog):
    """
    A Discord bot cog for managing the information panel about the radio station.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initializes the InfoPanel cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.config = Config()
        self.radio_controller = RadioController(bot)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(
        name="panel",
        description="Send the information panel about our radio station."
    )
    async def info_panel(
        self,
        interaction: discord.Interaction,
        panel_channel_id: discord.TextChannel = None
    ):
        """
        Command to send the information panel about the radio station.

        Args:
            interaction (discord.Interaction): The interaction object.
            panel_channel_id (discord.TextChannel, optional): The channel to send the panel to. Defaults to None.
        """
        if panel_channel_id is None:
            panel_channel_id = interaction.channel

        await interaction.response.defer(thinking=True)
        self.bot.loop.create_task(
            self.process_info_panel(interaction, panel_channel_id)
        )

    async def process_info_panel(
        self,
        interaction: discord.Interaction,
        panel_channel_id: discord.TextChannel
    ):
        """
        Processes the information panel command.

        Args:
            interaction (discord.Interaction): The interaction object.
            panel_channel_id (discord.TextChannel): The channel to send the panel to.
        """
        try:
            panel_message = await panel_channel_id.send("Loading information panel...")

            if not await self.radio_controller.update_panel_config_values(
                panel_channel_id.id, panel_message.id
            ):
                await interaction.followup.send(
                    "Failed to update panel config values.",
                    ephemeral=True
                )
                return

            await self.radio_controller.create_or_update_embed()

            await interaction.followup.send(
                "Information panel updated.",
                ephemeral=True
            )
        except Exception as e:
            # Catch any unexpected exceptions during command processing
            logger.critical(f"Failed to respond to panel command: {e}")
            await interaction.followup.send(
                "An error occurred while trying to update the information panel.",
                ephemeral=True
            )

    @info_panel.error
    async def info_panel_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        """
        Handles errors that occur during the execution of the info_panel command.

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
    Sets up the InfoPanel cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(InfoPanel(bot))
    logger.info("Info Panel command loaded!")
