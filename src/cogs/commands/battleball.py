import discord
from loguru import logger
from discord.ext import commands
from discord import app_commands
from src.views.battleball.panel import BattleballPanelView
from src.controller.habbo.battleball.score_manager import ScoreManager

class BattleLeaderboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.battleball_score_manager = ScoreManager(bot)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="battleball", description="Command to send the battleball leaderboard.")
    async def battle_leaderboard_command(self, interaction: discord.Interaction, battleball_channel_id: discord.TextChannel = None):
        if battleball_channel_id is None:
            battleball_channel_id = interaction.channel

        await interaction.response.defer(thinking=True)
        self.bot.loop.create_task(self.process_battle_leaderboard_task(interaction, battleball_channel_id))

    async def process_battle_leaderboard_task(self, interaction: discord.Interaction, battleball_channel_id: discord.TextChannel):
        try:
            battleball_message = await battleball_channel_id.send("Loading BattleBall leaderboard...", view=BattleballPanelView())

            if not await self.battleball_score_manager.update_battleball_config_values(battleball_channel_id.id, battleball_message.id):
                await battleball_channel_id.send("Failed to update battleball config values.", ephemeral=True)
                return

            await self.battleball_score_manager.create_or_update_embed()
        except Exception as e:
            logger.error(f"An error occurred while trying to get the leaderboard: {e}")
            await interaction.followup.send("An error occurred while trying to get the leaderboard.", ephemeral=True)

    @battle_leaderboard_command.error
    async def battle_leaderboard_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("You don't have the necessary permissions to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(BattleLeaderboard(bot))
    logger.info("Battle-Leaderboard command loaded!")
