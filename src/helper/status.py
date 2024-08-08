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
        self.radio_controller = RadioController(bot)

        self.sentences = [
            self.get_user_count_status,
            self.get_now_playing_status,
            self.get_listeners_status,
        ]

        self.status_generator = cycle(self.sentences)

    async def get_user_count_status(self) -> str:
        """
        Generates a status message indicating the total number of users.

        Returns:
            str: A status message with the total user count.
        """
        user_count = sum(guild.member_count for guild in self.bot.guilds)
        return f"I can see {user_count} users in the discord!"

    async def get_now_playing_status(self) -> str:
        """
        Generates a status message indicating the currently playing song.

        Returns:
            str: A status message with the current song.
        """
        now_playing, current_dj = await self.radio_controller.get_now_playing(self.config.azuracast_station_name)
        return f"Now playing: {now_playing} | DJ: {current_dj}"

    async def get_listeners_status(self) -> str:
        """
        Generates a status message indicating the total number of listeners.

        Returns:
            str: A status message with the total listener count.
        """
        listeners = await self.radio_controller.get_listeners(self.config.azuracast_station_name)
        return f"Currently {listeners} listeners."

    async def get_status_message(self) -> str:
        """
        Retrieves the next status message.

        Returns:
            str: The next status message.
        """
        next_status_func = next(self.status_generator)
        return await next_status_func()
