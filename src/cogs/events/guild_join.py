"""
This module contains the GuildJoin cog for the Discord bot.

The GuildJoin cog provides functionality to handle the event when the bot joins a guild.
"""

import discord
from loguru import logger
from discord.ext import commands


class GuildJoin(commands.Cog):
    """
    A class representing a Discord bot event handler for when the bot joins a guild.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initializes the GuildJoin cog with a bot instance.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """
        An event handler that is triggered when the bot joins a guild.

        Args:
            guild (discord.Guild): The guild that the bot joined.
        """
        try:
            await self.bot.tree.sync()
        except discord.errors.HTTPException as e:
            logger.critical(f"❌ Failed to sync slash commands: {e}")
            return
        except Exception as e:
            # Catch any unexpected exceptions during command sync
            logger.critical(
                f"❌ An unexpected error occurred while syncing commands: {e}")
            return

        try:
            await guild.owner.send(
                f"Hello `{guild.owner.name}`, your guild `{guild.name}` has successfully "
                "synced commands with the bot!"
            )
        except discord.errors.Forbidden:
            logger.error(
                f"❌ Couldn't send a DM to the guild owner of {guild.name} "
                f"({guild.owner.id}) due to insufficient permissions."
            )
        except discord.errors.HTTPException as e:
            logger.error(
                f"❌ Failed to send a DM to the guild owner of {guild.name} "
                f"({guild.owner.id}): {e}"
            )
        except Exception as e:
            # Catch any unexpected exceptions during DM sending
            logger.error(
                f"❌ An unexpected error occurred while sending a DM to the guild owner "
                f"of {guild.name} ({guild.owner.id}): {e}"
            )

        logger.info(f"✅ Bot joined Guild: {guild.name}. ({guild.id})")


async def setup(bot: commands.Bot) -> None:
    """
    Sets up the GuildJoin cog for the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(GuildJoin(bot))
    logger.info("On guild join event registered!")
