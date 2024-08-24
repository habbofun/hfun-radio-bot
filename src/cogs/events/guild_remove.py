"""
This module contains the GuildRemove cog for the Discord bot.

The GuildRemove cog provides functionality to handle the event when the bot leaves a guild.
"""

import discord
from loguru import logger
from discord.ext import commands


class GuildRemove(commands.Cog):
    """
    A class representing a Discord bot event for when the bot leaves a guild.

    Attributes:
        bot (discord.ext.commands.Bot): The instance of the bot.

    Methods:
        on_guild_remove: A listener method that is triggered when the bot leaves a guild.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initializes the GuildRemove cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """
        A listener method that is triggered when the bot leaves a guild.

        Args:
            guild (discord.Guild): The guild that the bot left.
        """
        logger.info(f"The bot left the guild {guild.name} ({guild.id}).")


async def setup(bot: commands.Bot) -> None:
    """
    Sets up the GuildRemove cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(GuildRemove(bot))
    logger.info("On guild leave event registered!")
