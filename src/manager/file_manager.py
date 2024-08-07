import os
from loguru import logger
from src.helper.config import Config

defaultConfig = """
# [APP]
app_logo: 
app_name: 
app_url: 
app_version: 
log_file: 

# [BOT]
bot_prefix: 
bot_token: 
dev_guild_id: 
logs_channel: 
panel_channel_id: 
panel_message_id: 

# [Radio]
azuracast_station_url: 
azuracast_station_name: 
azuracast_api_url: 
azuracast_api_key: 
"""

class FileManager:

    def __init__(self):
        self.config = Config()

    # Function to check if the input files are valid
    def check_input(self):

        # if there is no config file, create one.
        if not os.path.isfile("config.yaml"):
            logger.info("Config file not found, creating one...")
            open("config.yaml", "w+").write(defaultConfig)
            logger.info("Successfully created config.yml, please fill it out and try again.")
            exit()

        # If the folder "/src/database" doesn't exist, create it.
        if not os.path.exists("src/database"):
            os.makedirs("src/database")