import discord
from discord.ext import commands
from discord import app_commands
from src.controller.habbo.battleball.worker.worker import BattleballWorker
from src.database.service.battleball_service import BattleballDatabaseService

class BattleQueue(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_service = BattleballDatabaseService()

    @app_commands.command(name="queue", description="Displays the current queue for BattleBall profile updates.")
    async def battle_queue_command(self, interaction: discord.Interaction):
        queue_list = await self.db_service.get_queue()

        if queue_list:
            queue_display = "\n".join([f"{idx + 1}. {entry['username']} (Added by: <@{entry['discord_id']}>)"
                                       for idx, entry in enumerate(queue_list)])
            await interaction.response.send_message(f"**Current Queue:**\n{queue_display}", ephemeral=True)
        else:
            await interaction.response.send_message("The queue is currently empty.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(BattleQueue(bot))
