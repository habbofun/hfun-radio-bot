"""
This module contains the KekoCmd cog for the Discord bot.

The KekoCmd cog provides functionality to send information about a Habbo Origins user.
"""

import discord
from discord.ext import commands
from discord import app_commands
from loguru import logger
from httpx import HTTPStatusError, RequestError

from src.helper.config import Config
from src.controller.habbo.habbo_controller import HabboController


class KekoCmd(commands.Cog):
    """
    A class representing the Keko command cog.

    This cog provides functionality to send information about a Habbo Origins user.

    Attributes:
        bot (commands.Bot): The instance of the bot.
        config (Config): The configuration object.
        habbo_controller (HabboController): The controller for handling Habbo-related operations.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initializes the KekoCmd cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.config = Config()
        self.habbo_controller = HabboController()

    @app_commands.command(
        name="keko",
        description="Send the information about a Habbo Origins user."
    )
    async def habbo_keko_info(
        self,
        interaction: discord.Interaction,
        username: str,
        hidden: bool = False
    ):
        """
        Sends information about a Habbo Origins user.

        Args:
            interaction (discord.Interaction): The interaction object.
            username (str): The username of the Habbo user.
            hidden (bool, optional): Whether the response should be ephemeral. Defaults to False.
        """
        await self.bot.command_queue.put(
            (interaction, self.process_keko_info(interaction, username, hidden))
        )

    async def process_keko_info(
        self,
        interaction: discord.Interaction,
        username: str,
        hidden: bool
    ):
        """
        Processes the Habbo user information and sends it to the channel.

        Args:
            interaction (discord.Interaction): The interaction object.
            username (str): The username of the Habbo user.
            hidden (bool): Whether the response should be ephemeral.
        """
        if not username:
            await interaction.response.send_message(
                "You need to provide a username.",
                ephemeral=True
            )
            return

        try:
            output_file = await self.create_habbo_image_and_handle_errors(username)
            if output_file:
                await interaction.response.send_message(
                    f"Habbo Origins: ES user `{username}` information:",
                    file=discord.File(output_file),
                    ephemeral=hidden
                )
                await self.habbo_controller.delete_image(username)
            else:
                await interaction.response.send_message(
                    f"Failed to get user information for `{username}`.",
                    ephemeral=True
                )
        except Exception as e:
            logger.critical(f"Failed to respond to username command: {e}")
            if not interaction.response.is_done():
                try:
                    await interaction.followup.send(
                        "There was an error trying to execute that command!",
                        ephemeral=True
                    )
                except Exception as followup_error:
                    logger.critical(
                        f"Failed to send follow-up message: {followup_error}")

    async def create_habbo_image_and_handle_errors(self, username: str):
        """
        Creates a Habbo user image and handles any errors that occur during the process.

        Args:
            username (str): The username of the Habbo user.

        Returns:
            Optional[str]: The path to the created image file, or None if an error occurred.
        """
        try:
            return await self.habbo_controller.create_habbo_image(username)
        except HTTPStatusError as e:
            logger.error(
                f"HTTP error occurred while fetching user info for `{username}`: {e}")
        except RequestError as e:
            logger.error(
                f"Request error occurred while fetching user info for `{username}`: {e}")
        except IOError as e:
            logger.error(
                f"IO error occurred while creating image for `{username}`: {e}")
        except Exception as e:
            # This general exception catch is retained to handle unexpected errors
            logger.error(f"Unexpected error occurred: {e}")
        return None

    @habbo_keko_info.error
    async def habbo_keko_info_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        """
        Handles errors that occur during the execution of the habbo_keko_info command.

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
            logger.error(f"An error occurred in the `/keko` command: {error}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"An error occurred: {error}",
                    ephemeral=True
                )


async def setup(bot: commands.Bot):
    """
    Sets up the KekoCmd cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(KekoCmd(bot))
    logger.info("Keko command loaded!")
