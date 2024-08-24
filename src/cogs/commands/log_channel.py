"""
This module contains the LogChannelCommand cog for the Discord bot.

The LogChannelCommand cog provides a command for setting the bot log channel.
"""

import discord
from discord.ext import commands
from discord import app_commands
from loguru import logger

from src.helper.config import Config
from src.controller.discord.schema.embed_schema import EmbedSchema
from src.controller.discord.embed_controller import EmbedController


class LogChannelCommand(commands.Cog):
    """
    A command cog for setting the bot log channel.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initializes the LogChannelCommand cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.config = Config()

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(
        name="log_channel",
        description="Set the bot log channel."
    )
    async def log_channel(
        self,
        interaction: discord.Interaction,
        log_channel: discord.TextChannel = None,
        hidden: bool = False
    ) -> None:
        """
        Command to set the bot log channel.

        Args:
            interaction (discord.Interaction): The interaction object.
            log_channel (discord.TextChannel, optional): The log channel to set. Defaults to None.
            hidden (bool, optional): Whether the response should be ephemeral. Defaults to False.
        """
        await self.bot.command_queue.put(
            (interaction, self.process_log_channel(
                interaction, log_channel, hidden))
        )

    async def process_log_channel(
        self,
        interaction: discord.Interaction,
        log_channel: discord.TextChannel,
        hidden: bool
    ):
        """
        Processes the log channel command.

        Args:
            interaction (discord.Interaction): The interaction object.
            log_channel (discord.TextChannel): The log channel to set.
            hidden (bool): Whether the response should be ephemeral.

        Returns:
            None
        """
        try:
            if log_channel is None:
                log_channel = interaction.channel

            try:
                self.config.change_value("logs_channel", log_channel.id)
            except Exception as e:
                # Handle specific exceptions related to configuration changes
                logger.critical(f"Failed to change value in config.yaml: {e}")
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "There was an error trying to write the config file!",
                        ephemeral=hidden
                    )
                return

            embed_schema = EmbedSchema(
                title="Log channel update",
                description="Successfully set the log channel to the channel below.",
                fields=[
                    {
                        "name": "New logs channel",
                        "value": f"- {log_channel.mention} (`{log_channel.id}`)"
                    }
                ],
                color=0x00ff00
            )

            embed = await EmbedController().build_embed(embed_schema)
            await interaction.response.send_message(embed=embed, ephemeral=hidden)
        except Exception as e:
            # Handle unexpected errors gracefully
            logger.critical(f"Failed to respond to info command: {e}")
            if not interaction.response.is_done():
                try:
                    await interaction.followup.send(
                        "There was an error trying to execute that command!",
                        ephemeral=hidden
                    )
                except Exception as followup_error:
                    logger.critical(
                        f"Failed to send follow-up message: {followup_error}")

    @log_channel.error
    async def log_channel_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        """
        Handles errors that occur during the execution of the log_channel command.

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
    Sets up the LogChannelCommand cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(LogChannelCommand(bot))
    logger.info("Log channel command loaded!")
