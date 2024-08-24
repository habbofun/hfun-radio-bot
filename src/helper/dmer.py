from loguru import logger
from discord import Embed
from discord.ui import View
from discord.ext import commands
from src.helper.singleton import Singleton


@Singleton
class DiscordDmer:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_dm(self, user_id: int, message: str = None, embed: Embed = None, view: View = None):
        try:
            user = await self.bot.fetch_user(user_id)
            await user.send(content=message, embed=embed, view=view)
        except Exception as e:
            logger.error(f"Failed to send DM to user ID '{user_id}': {e}")
