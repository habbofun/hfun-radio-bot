import discord
from loguru import logger
from discord.ext import commands
from discord import app_commands
from src.controller.discord.schema.embed_schema import EmbedSchema
from src.controller.discord.embed_controller import EmbedController
from src.controller.habbo.battleball.score_manager import ScoreManager

class BattleLeaderboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.battleball_score_manager = ScoreManager()

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="battle_leaderboard", description="Command to get the BattleBall leaderboard.")
    async def battle_leaderboard_command(self, interaction: discord.Interaction, hidden: bool = False) -> None:
        self.bot.loop.create_task(self.process_battle_leaderboard_task(interaction, hidden))

    async def process_battle_leaderboard_task(self, interaction: discord.Interaction, hidden: bool):
        try:
            leaderboard_string = await self.battleball_score_manager.get_leaderboard()
            embed_schema = EmbedSchema(
                title="BattleBall Leaderboard",
                description="It's probably not updated in real-time, but it should give you a good idea of who's on top!",
                fields=[
                    {
                        "name": "Ranking",
                        "value": f"```{leaderboard_string}```",
                    }
                ],
                color=0x00ff00
            )

            embed = await EmbedController().build_embed(embed_schema)
            await interaction.response.send_message(embed=embed, ephemeral=hidden)
        except Exception as e:
            logger.error(f"An error occurred while trying to get the leaderboard: {e}")
            await interaction.response.send_message("An error occurred while trying to get the leaderboard.", ephemeral=True)

    @battle_leaderboard_command.error
    async def battle_leaderboard_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("You don't have the necessary permissions to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(BattleLeaderboard(bot))
    logger.info("Battle-Leaderboard command loaded!")
