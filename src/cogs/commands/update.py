import discord
from discord.ext import commands
from discord import app_commands
from src.database.service.battleball_service import BattleballDatabaseService
from src.controller.habbo.battleball.worker.worker import BattleballWorker

class BattleUpdate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_service = BattleballDatabaseService()
        self.worker = BattleballWorker(bot)

    @app_commands.command(name="update", description="Command to update a battleball profile's data.")
    async def battle_update_command(self, interaction: discord.Interaction, username: str):
        await self.db_service.initialize()

        added_by = interaction.user.id
        position = await self.db_service.add_to_queue(username, added_by)
        
        if position == 1:
            await interaction.response.send_message(
                f"{username} is now being processed. You'll receive a notification once it's done.",
                ephemeral=True
            )
            if not self.worker.running:
                await self.worker.start()
        else:
            await interaction.response.send_message(
                f"{username} was added to the queue at position {position}.",
                ephemeral=True
            )

    @app_commands.command(name="leaderboard", description="Display the BattleBall leaderboard.")
    async def leaderboard_command(self, interaction: discord.Interaction, mobile_version: bool = False):
        leaderboard = await self.worker.get_leaderboard(mobile_version)
        await interaction.response.send_message(leaderboard, ephemeral=True)

    async def cog_unload(self):
        await self.worker.stop()

async def setup(bot: commands.Bot):
    await bot.add_cog(BattleUpdate(bot))
