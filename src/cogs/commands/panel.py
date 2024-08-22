import discord
from loguru import logger
from discord.ext import commands
from discord import app_commands
from src.helper.config import Config
from src.controller.radio.radio_controller import RadioController

class InfoPanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config()
        self.radio_controller = RadioController(bot)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="panel", description="Send the information panel about our radio station.")
    async def info_panel(self, interaction: discord.Interaction, panel_channel_id: discord.TextChannel = None):
        # Ensure panel_channel_id is set before processing
        if panel_channel_id is None:
            panel_channel_id = interaction.channel

        # Acknowledge the command and start the background task
        await interaction.response.defer(thinking=True)
        self.bot.loop.create_task(self.process_info_panel(interaction, panel_channel_id))

    async def process_info_panel(self, interaction: discord.Interaction, panel_channel_id: discord.TextChannel):
        try:
            # Send an initial loading message in the specified channel
            panel_message = await panel_channel_id.send("Loading information panel...")

            # Update the panel config with the new channel and message IDs
            if not await self.radio_controller.update_panel_config_values(panel_channel_id.id, panel_message.id):
                await interaction.followup.send("Failed to update panel config values.", ephemeral=True)
                return

            # Create or update the information panel embed
            await self.radio_controller.create_or_update_embed()

            # Send a confirmation message
            await interaction.followup.send("Information panel updated.", ephemeral=True)
        except Exception as e:
            logger.critical(f"Failed to respond to panel command: {e}")
            await interaction.followup.send("An error occurred while trying to update the information panel.", ephemeral=True)

    @info_panel.error
    async def info_panel_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("You don't have the necessary permissions to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(InfoPanel(bot))
    logger.info("Info Panel command loaded!")
