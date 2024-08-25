"""
This module contains the BattleLeaderboard cog for the Discord bot.

The BattleLeaderboard cog provides commands and functionality related to the BattleBall leaderboard.
"""

import discord
from loguru import logger
from discord.ext import commands
from discord import app_commands

from src.helper.config import Config
from src.views.battleball.panel import BattleballPanelView
from src.controller.discord.schema.embed_schema import EmbedSchema
from src.controller.discord.embed_controller import EmbedController
from src.controller.habbo.battleball.worker.worker import BattleballWorker


class BattleLeaderboard(commands.Cog):
    """
    A class representing the BattleLeaderboard cog.

    This cog provides commands and functionality related to the BattleBall leaderboard.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initializes the BattleLeaderboard cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.config = Config()
        self.battleball_worker = BattleballWorker(bot)

    @app_commands.command(name="leaderboard", description="Show the Battleball leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        leaderboard = await self.battleball_worker.db_service.get_leaderboard()
        
        embed = discord.Embed(title="Battleball Leaderboard", color=0x00ff00)
        for idx, (username, total_score, ranked_matches) in enumerate(leaderboard[:10], start=1):
            embed.add_field(
                name=f"{idx}. {username}",
                value=f"Score: {total_score} | Ranked Matches: {ranked_matches}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(
        name="battleball",
        description="Command to send the battleball leaderboard."
    )
    async def battle_leaderboard_command(
        self,
        interaction: discord.Interaction,
        battleball_channel_id: discord.TextChannel = None
    ):
        """
        Command to send the battleball leaderboard.

        Args:
            interaction (discord.Interaction): The interaction object.
            battleball_channel_id (discord.TextChannel, optional): The text channel to send the leaderboard to.
        """
        if battleball_channel_id is None:
            battleball_channel_id = interaction.channel

        await interaction.response.defer(thinking=True)
        self.bot.loop.create_task(
            self.process_battle_leaderboard_task(
                interaction, battleball_channel_id)
        )

    async def process_battle_leaderboard_task(
        self, interaction: discord.Interaction, battleball_channel_id: discord.TextChannel
    ):
        """
        Processes the battleball leaderboard task.

        Args:
            interaction (discord.Interaction): The interaction object.
            battleball_channel_id (discord.TextChannel): The text channel to send the leaderboard to.
        """
        try:
            embed_schema = EmbedSchema(
                title="BattleBall Leaderboard",
                description="It's probably not updated in real-time, but it should give you a good idea of who's on top!",
                author_url=self.config.app_url,
                color=0xF4D701
            )

            embed = await EmbedController().build_embed(embed_schema)
            battleball_message = await battleball_channel_id.send(
                embed=embed,
                view=BattleballPanelView(self.bot)
            )

            await self.config.change_value("battleball_message_id", battleball_message.id)
            await self.config.change_value("battleball_channel_id", battleball_channel_id.id)

            await self.battleball_worker.create_or_update_embed()
        except Exception as e:
            logger.error(
                f"An error occurred while trying to get the leaderboard: {e}")
            await interaction.followup.send(
                "An error occurred while trying to get the leaderboard.",
                ephemeral=True
            )

    @battle_leaderboard_command.error
    async def battle_leaderboard_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """
        Handles errors that occur during the execution of the battle_leaderboard_command.

        Args:
            interaction (discord.Interaction): The interaction object.
            error (app_commands.AppCommandError): The error that occurred.
        """
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You don't have the necessary permissions to use this command.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"An error occurred: {error}",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    """
    Sets up the BattleLeaderboard cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(BattleLeaderboard(bot))
    logger.info("Battle-Leaderboard command loaded!")