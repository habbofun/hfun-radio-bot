import discord
from loguru import logger
from discord.ext import commands
from discord import app_commands
from src.helper.config import Config
from httpx import HTTPStatusError, RequestError
from src.controller.habbo.habbo_controller import HabboController

class KekoCmd(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config()
        self.habbo_controller = HabboController()

    @app_commands.command(name="keko", description="Send the information about a Habbo Origins user.")
    async def habbo_keko_info(self, interaction: discord.Interaction, username: str, hidden: bool = False):
        await self.bot.command_queue.put((interaction, self.process_keko_info(interaction, username, hidden)))

    async def process_keko_info(self, interaction: discord.Interaction, username: str, hidden: bool):
        if not username:
            await interaction.response.send_message("You need to provide a username.", ephemeral=True)
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
                    await interaction.followup.send("There was an error trying to execute that command!", ephemeral=True)
                except Exception as followup_error:
                    logger.critical(f"Failed to send follow-up message: {followup_error}")

    async def create_habbo_image_and_handle_errors(self, username: str):
        try:
            return await self.habbo_controller.create_habbo_image(username)
        except HTTPStatusError as e:
            logger.error(f"HTTP error occurred while fetching user info for `{username}`: {e}")
        except RequestError as e:
            logger.error(f"Request error occurred while fetching user info for `{username}`: {e}")
        except IOError as e:
            logger.error(f"IO error occurred while creating image for `{username}`: {e}")
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
        return None

    @habbo_keko_info.error
    async def habbo_keko_info_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("You don't have the necessary permissions to use this command.", ephemeral=True)
        else:
            logger.error(f"An error occurred in the `/keko` command: {error}")
            if not interaction.response.is_done():
                await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(KekoCmd(bot))
    logger.info("Keko command loaded!")
