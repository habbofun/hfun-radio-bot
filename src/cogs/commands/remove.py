import discord
from loguru import logger
from discord.ext import commands
from discord import app_commands
from src.database.service.battleball_service import BattleballDatabaseService
from src.controller.habbo.battleball.worker.worker import BattleballWorker

class BattleRemove(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_service = BattleballDatabaseService()
        self.worker = BattleballWorker(bot)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="fulminate", description="Command to delete a BattleBall profile's data.")
    async def battle_fulminate_command(self, interaction: discord.Interaction, username: str):
        await self.db_service.fulminate_user(username)
        
        await interaction.response.send_message(
            f"The user `{username}` and all associated data have been permanently deleted.",
            ephemeral=True
        )
        logger.info(f"User '{interaction.user.name}' triggered fulmination for '{username}'")

    @app_commands.command(name="leaderboard", description="Display the BattleBall leaderboard.")
    async def leaderboard_command(self, interaction: discord.Interaction, mobile_version: bool = False):
        leaderboard = await self.worker.get_leaderboard(mobile_version)
        await interaction.response.send_message(leaderboard, ephemeral=True)

    async def cog_unload(self):
        await self.worker.stop()

async def setup(bot: commands.Bot):
    await bot.add_cog(BattleRemove(bot))
    logger.info("BattleRemove cog loaded")
