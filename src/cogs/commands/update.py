import discord
from discord.ext import commands
from discord import app_commands
from src.database.service.battleball_service import BattleballDatabaseService
from src.controller.habbo.battleball.worker.worker import BattleballWorker
from loguru import logger

class BattleUpdate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_service = BattleballDatabaseService()
        self.worker = BattleballWorker(bot)

    @app_commands.command(name="update", description="Command to update a battleball profile's data.")
    async def battle_update_command(self, interaction: discord.Interaction, username: str):
        added_by = interaction.user.id
        added_by_name = interaction.user.name
        position = await self.db_service.add_to_queue(username, added_by)

        if position == 1:
            await interaction.response.send_message(
                f"The job for `{username}` is now being processed.\nYou'll receive a notification once it's done.",
                ephemeral=True
            )
            await self.log_queue_addition(username, added_by_name, position)
            if not self.worker.running:
                await self.worker.start()
        else:
            await self.log_queue_addition(username, added_by_name, position)
            await interaction.response.send_message(
                f"The user `{username}` is already at the queue at position `{position}`.",
                ephemeral=True
            )

    async def log_queue_addition(self, username: str, added_by_name: str, position: int):
        logger.info(f"User '{added_by_name}' added '{username}' to the queue at position '{position}'")

    @app_commands.command(name="leaderboard", description="Display the BattleBall leaderboard.")
    async def leaderboard_command(self, interaction: discord.Interaction, mobile_version: bool = False):
        leaderboard = await self.worker.get_leaderboard(mobile_version)
        await interaction.response.send_message(leaderboard, ephemeral=True)

    async def cog_unload(self):
        await self.worker.stop()

async def setup(bot: commands.Bot):
    await bot.add_cog(BattleUpdate(bot))
    logger.info("BattleUpdate cog loaded")