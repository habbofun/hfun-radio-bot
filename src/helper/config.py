import discord
import yaml
from loguru import logger
from yaml import SafeLoader

class Config:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.load_config()
        self._initialized = True

    def load_config(self):
        with open("config.yaml", "r") as file:
            self.config = yaml.load(file, Loader=SafeLoader)

        self.rainbow_line_gif: str = "https://i.imgur.com/mnydyND.gif"
        self.app_logo: str = self.config.get("app_logo", "")
        self.app_url: str = self.config.get("app_url", "")
        self.app_name: str = self.config.get("app_name", "")
        self.app_name_branded: str = f"{self.app_name} • {self.app_url}"
        self.app_version: str = self.config.get("app_version", "")
        self.log_file = self.config.get("log_file", "")

        self.bot_prefix: str = self.config.get("bot_prefix", "!")
        self.bot_token: str = self.config.get("bot_token", "")
        self.panel_channel_id: int = int(self.config.get("panel_channel_id", 0))
        self.panel_message_id: int = int(self.config.get("panel_message_id", 0))
        self.logs_channel: int = int(self.config.get("logs_channel", 0))
        self.dev_guild_id: discord.Object = discord.Object(int(self.config.get("dev_guild_id", 0)))

        self.azuracast_station_url: str = self.config.get("azuracast_station_url", "")
        self.azuracast_station_name: str = self.config.get("azuracast_station_name", "")

        self.azuracast_api_url: str = self.config.get("azuracast_api_url", "")
        self.azuracast_api_key: str = self.config.get("azuracast_api_key", "")

    def change_value(self, key, value):
        try:
            with open("config.yaml", "r") as file:
                config = yaml.load(file, Loader=SafeLoader)
            config[key] = value
            with open("config.yaml", "w") as file:
                yaml.dump(config, file)
            logger.info(f"Changed value in config.yaml: {key} -> {value}, the file was rewritten.")
            self.load_config()
            return True
        except Exception as e:
            logger.critical(f"Failed to change value in config.yaml: {e}")
            return False
