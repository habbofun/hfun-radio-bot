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
        self.battleball_worker = BattleballWorker(bot)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="fulminate", description="Command to delete a BattleBall profile's data.")
    async def battle_fulminate_command(self, interaction: discord.Interaction, username: str):
        await self.db_service.fulminate_user(username)

        await interaction.response.send_message(
            f"The user `{username}` and all associated data have been permanently deleted.",
            ephemeral=True
        )
        logger.info(f"User '{interaction.user.name}' triggered fulmination for '{username}'")

async def setup(bot: commands.Bot):
    await bot.add_cog(BattleRemove(bot))
    logger.info("BattleRemove cog loaded")
