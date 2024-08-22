import os
from loguru import logger
from src.helper.config import Config
from src.helper.singleton import Singleton

defaultConfig = """
# [APP]
app_logo: # String, URL to the app logo
app_name: # String, Name of the app
app_url: # String, URL to the app
app_version: # String, Version of the app
log_file: # String, Path to the log file (Example: ai_bot.log)

# [BOT]
bot_prefix: # String, Prefix of the bot
bot_token: # String, Token of the bot
dev_guild_id: # Integer, ID of the developer guild
logs_channel: # Integer, ID of the logs channel

# [Channels]
panel_channel_id: # Integer, ID of the panel channel
panel_message_id: # Integer, ID of the panel message
battleball_channel_id: # Integer, ID of the battleball channel
battleball_message_id: # Integer, ID of the battleball message

# [Radio]
azuracast_station_url: # String, URL to the Azuracast station
azuracast_station_name: # String, Name of the Azuracast station
azuracast_api_url: # String, URL to the Azuracast API
azuracast_api_key: # String, API key of the Azuracast API
"""

@Singleton
class FileManager:
    """
    A class that manages files for the bot.
    """

    def __init__(self):
        """
        Initializes the FileManager class.
        """
        self.config = Config()

    def check_input(self):
        """
        Checks if the required files and directories exist.
        If not, creates them.
        """
        if not os.path.isfile("config.yaml"):
            logger.info("Config file not found, creating one...")
            open("config.yaml", "w+").write(defaultConfig)
            logger.info("Successfully created config.yml, please fill it out and try again.")
            exit()

        if not os.path.exists("src/database"):
            os.makedirs("src/database")