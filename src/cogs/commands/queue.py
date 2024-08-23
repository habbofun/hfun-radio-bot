import discord
from discord.ext import commands
from discord import app_commands
from src.controller.habbo.battleball.worker.worker import BattleballWorker
from src.database.service.battleball_service import BattleballDatabaseService

class BattleQueue(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_service = BattleballDatabaseService()
        self.battleball_worker = BattleballWorker(bot)  # Initialize the worker

    @app_commands.command(name="queue", description="Displays the current queue for BattleBall profile updates.")
    async def battle_queue_command(self, interaction: discord.Interaction):
        queue_list = await self.db_service.get_queue()

        if queue_list:
            queue_display = []
            for idx, entry in enumerate(queue_list):
                position = idx + 1
                username = entry['username']
                discord_id = entry['discord_id']

                if username == self.worker.current_user:
                    remaining_matches = await self.worker.get_remaining_matches()
                    queue_display.append(f"**{position}**. {username} (Added by: <@{discord_id}> - {remaining_matches} left)")
                else:
                    queue_display.append(f"**{position}**. {username} (Added by: <@{discord_id}>)")

            queue_message = "\n".join(queue_display)
            await interaction.response.send_message(f"**Current Queue:**\n{queue_message}", ephemeral=True)
        else:
            await interaction.response.send_message("The queue is currently empty.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(BattleQueue(bot))
