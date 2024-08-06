import discord
from loguru import logger
from discord.ext import commands
from discord import app_commands
from src.controller.radio.radio_controller import RadioController
from src.controller.discord.schema.embed_schema import EmbedSchema
from src.controller.discord.embed_controller import EmbedController

class NowPlaying(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.radio_controller = RadioController()

    @app_commands.command(name="now_playing", description="Get the currently playing song.")
    async def now_playing_command(self, interaction: discord.Interaction):
        try:
            now_playing = await self.radio_controller.get_now_playing()
            if now_playing is None:
                now_playing = "No song is currently playing or failed to get the song name."

            embed_schema = EmbedSchema(
                title="🎵 Now playing",
                fields=[
                    {
                        "name": "",
                        "value": f"```{now_playing}```",
                    }
                ],
                color=0xb34760
            )

            embed = await EmbedController().build_embed(embed_schema)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.critical(f"Failed to respond to ping command: {e}")
            await interaction.response.send_message("There was an error trying to execute that command!", ephemeral=True)

    @now_playing_command.error
    async def now_playing_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(f"You don't have the necessary permissions to use this command.",ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(NowPlaying(bot))
    logger.info("Now Playing command loaded!")