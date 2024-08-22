import discord
from loguru import logger
from discord.ext import commands
from discord import app_commands
from src.controller.habbo.battleball.score_manager import ScoreManager

class BattleUpdate(commands.Cog):
    """
    A class representing a Discord cog for updating battleball profiles.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.battleball_score_manager = ScoreManager(bot)

    @app_commands.command(name="update", description="Command to try to update a battleball profile data.")
    async def battle_update_command(self, interaction: discord.Interaction, username: str):
        await interaction.response.send_message(f"Starting update for {username}.\nYou will receive a DM when the process is complete.", ephemeral=True)
        self.bot.loop.create_task(self.process_battle_update_task(interaction, username))

    async def process_battle_update_task(self, interaction: discord.Interaction, username: str):
        try:
            await self.battleball_score_manager.process_user_scores(username)

            user = await self.bot.fetch_user(interaction.user.id)
            await user.send(f"Update complete for {username}.")
        except Exception as e:
            logger.critical(f"Failed to update battle profile for {username}: {e}")
            user = await self.bot.fetch_user(interaction.user.id)
            await user.send(f"There was an error trying to update the profile for {username}. Please try again later.")

    @battle_update_command.error
    async def battle_update_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("You don't have the necessary permissions to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(BattleUpdate(bot))
    logger.info("Battle-Update command loaded!")
