import discord
import yaml
from loguru import logger
from yaml import SafeLoader
from src.helper.singleton import Singleton

@Singleton
class Config:
    CONFIG_FILE_PATH = "config.yaml"

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.load_config()
        self._initialized = True

    def load_config(self):
        with open(self.CONFIG_FILE_PATH, "r") as file:
            self.settings = yaml.load(file, Loader=SafeLoader)

        self.rainbow_line_gif: str = "https://i.imgur.com/mnydyND.gif"
        self.app_logo: str = self.settings.get("app_logo", "")
        self.app_url: str = self.settings.get("app_url", "")
        self.app_name: str = self.settings.get("app_name", "")
        self.app_name_branded: str = f"{self.app_name} • {self.app_url}"
        self.app_version: str = self.settings.get("app_version", "")
        self.log_file = "hfun.log"

        self.bot_prefix: str = self.settings.get("bot_prefix", "!")
        self.bot_token: str = self.settings.get("bot_token", "")

        self.panel_channel_id: int = int(self.settings.get("panel_channel_id", 0))
        self.panel_message_id: int = int(self.settings.get("panel_message_id", 0))

        self.battleball_channel_id: int = int(self.settings.get("battleball_channel_id", 0))
        self.battleball_message_id: int = int(self.settings.get("battleball_message_id", 0))

        self.logs_channel: int = int(self.settings.get("logs_channel", 0))
        self.dev_guild_id: discord.Object = discord.Object(int(self.settings.get("dev_guild_id", 0)))

        self.azuracast_station_url: str = self.settings.get("azuracast_station_url", "")
        self.azuracast_station_name: str = self.settings.get("azuracast_station_name", "")

        self.azuracast_api_url: str = self.settings.get("azuracast_api_url", "")
        self.azuracast_api_key: str = self.settings.get("azuracast_api_key", "")

    def change_value(self, key, value):
        try:
            with open(self.CONFIG_FILE_PATH, "r") as file:
                config = yaml.load(file, Loader=SafeLoader)
            config[key] = value
            with open(self.CONFIG_FILE_PATH, "w") as file:
                yaml.dump(config, file)
            logger.info(f"Changed value in {self.CONFIG_FILE_PATH}: {key} -> {value}, the file was rewritten.")
            self.load_config()
            return True
        except Exception as e:
            logger.critical(f"Failed to change value in {self.CONFIG_FILE_PATH}: {e}")
            return False
