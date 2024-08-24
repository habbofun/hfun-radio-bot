import discord
import yaml
from loguru import logger
from yaml import SafeLoader
from src.helper.singleton import Singleton


@Singleton
class Config:
    """
    A class that represents the configuration settings for the bot.

    Attributes:
        CONFIG_FILE_PATH (str): The path to the configuration file.
        settings (dict): The dictionary containing the loaded configuration settings.
        rainbow_line_gif (str): The URL of the rainbow line GIF.
        app_logo (str): The URL of the app logo.
        app_url (str): The URL of the app.
        app_name (str): The name of the app.
        app_name_branded (str): The branded name of the app.
        app_version (str): The version of the app.
        log_file (str): The path to the log file.
        bot_prefix (str): The prefix for bot commands.
        bot_token (str): The token for the bot.
        panel_channel_id (int): The ID of the panel channel.
        panel_message_id (int): The ID of the panel message.
        battleball_channel_id (int): The ID of the battleball channel.
        battleball_message_id (int): The ID of the battleball message.
        logs_channel (int): The ID of the logs channel.
        dev_guild_id (discord.Object): The ID of the development guild.
        azuracast_station_url (str): The URL of the AzuraCast station.
        azuracast_station_name (str): The name of the AzuraCast station.
        azuracast_api_url (str): The URL of the AzuraCast API.
        azuracast_api_key (str): The API key for the AzuraCast API.
    """

    CONFIG_FILE_PATH = "config.yaml"

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.load_config()
        self._initialized = True

    def load_config(self):
        """
        Loads the configuration settings from the config file.
        """
        with open(self.CONFIG_FILE_PATH, "r") as file:
            self.settings = yaml.load(file, Loader=SafeLoader)

        self.arriba_icon: str = "<:arriba:1269762468671131658>"
        self.abajo_icon: str = "<:abajo:1269762527374610512>"

        self.rainbow_line_gif: str = "https://i.imgur.com/mnydyND.gif"
        self.app_logo: str = self.settings.get("app_logo", "")
        self.app_url: str = self.settings.get("app_url", "")
        self.app_name: str = self.settings.get("app_name", "")
        self.app_name_branded: str = f"{self.app_name} • {self.app_url}"
        self.app_version: str = self.settings.get("app_version", "")
        self.log_file = "hfun.log"

        self.bot_prefix: str = self.settings.get("bot_prefix", "!")
        self.bot_token: str = self.settings.get("bot_token", "")

        self.panel_channel_id: int = int(
            self.settings.get("panel_channel_id", 0))
        self.panel_message_id: int = int(
            self.settings.get("panel_message_id", 0))

        self.battleball_channel_id: int = int(
            self.settings.get("battleball_channel_id", 0))
        self.battleball_message_id: int = int(
            self.settings.get("battleball_message_id", 0))

        self.logs_channel: int = int(self.settings.get("logs_channel", 0))
        self.dev_guild_id: discord.Object = discord.Object(
            int(self.settings.get("dev_guild_id", 0)))

        self.azuracast_station_url: str = self.settings.get(
            "azuracast_station_url", "")
        self.azuracast_station_name: str = self.settings.get(
            "azuracast_station_name", "")

        self.azuracast_api_url: str = self.settings.get(
            "azuracast_api_url", "")
        self.azuracast_api_key: str = self.settings.get(
            "azuracast_api_key", "")

    async def change_value(self, key, value):
        """
        Changes the value of a configuration setting and saves it to the config file.

        Args:
            key (str): The key of the configuration setting to change.
            value: The new value for the configuration setting.

        Returns:
            bool: True if the value was successfully changed and saved, False otherwise.
        """
        try:
            with open(self.CONFIG_FILE_PATH, "r") as file:
                config = yaml.load(file, Loader=SafeLoader)
            config[key] = value
            with open(self.CONFIG_FILE_PATH, "w") as file:
                yaml.dump(config, file)
            logger.info(
                f"Changed value in {self.CONFIG_FILE_PATH}: {key} -> {value}, the file was rewritten.")
            self.load_config()
            return True
        except Exception as e:
            logger.critical(
                f"Failed to change value in {self.CONFIG_FILE_PATH}: {e}")
            return False
