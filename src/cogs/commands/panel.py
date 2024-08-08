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
        await self.bot.command_queue.put((interaction, self.process_info_panel(interaction, panel_channel_id)))

    async def process_info_panel(self, interaction: discord.Interaction, panel_channel_id: discord.TextChannel):
        try:
            if panel_channel_id is None:
                panel_channel_id = interaction.channel

            if not await self.radio_controller.update_panel_config_values(panel_channel_id.id, self.config.panel_message_id):
                await interaction.response.send_message("Failed to update panel config values.", ephemeral=True)
                return

            await self.radio_controller.create_or_update_embed()
            await interaction.response.send_message("Information panel updated.", ephemeral=True)
        except Exception as e:
            logger.critical(f"Failed to respond to panel command: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("There was an error trying to execute that command!", ephemeral=True)

    @info_panel.error
    async def info_panel_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("You don't have the necessary permissions to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(InfoPanel(bot))
    logger.info("Info Panel command loaded!")
