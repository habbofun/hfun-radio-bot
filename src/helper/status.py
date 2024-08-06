from itertools import cycle
from discord.ext import commands
from src.helper.config import Config
from src.controller.radio.radio_controller import RadioController

class BotStatus:
    """
    Represents the status of the Discord bot.

    Attributes:
        bot (commands.Bot): The instance of the Discord bot.
        config (Config): The configuration object.
        sentences (list): A list of functions that generate status sentences.
        status_generator (itertools.cycle): An iterator that cycles through the status sentences.
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.config = Config()
        self.radio_controller = RadioController()

        self.sentences = [
            #self.get_user_count_status,
            self.get_now_playing_status
        ]

        self.status_generator = cycle(self.sentences)

    async def get_user_count_status(self) -> str:
        """
        Generates a status message indicating the total number of users.

        Returns:
            str: A status message with the total user count.
        """
        user_count = sum(guild.member_count for guild in self.bot.guilds)
        return f"I can see {user_count} users."

    async def get_now_playing_status(self) -> str:
        """
        Generates a status message indicating the currently playing song.

        Returns:
            str: A status message with the current song.
        """
        now_playing = await self.radio_controller.get_now_playing()
        return f"Now playing: {now_playing}"

    async def get_status_message(self) -> str:
        """
        Retrieves the next status message.

        Returns:
            str: The next status message.
        """
        next_status_func = next(self.status_generator)
        return await next_status_func()
