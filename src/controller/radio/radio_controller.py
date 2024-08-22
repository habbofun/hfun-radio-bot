import httpx, discord
from typing import Tuple, Optional
from loguru import logger
from discord.ext import commands
from src.helper.config import Config
from src.helper.singleton import Singleton
from src.controller.discord.schema.embed_schema import EmbedSchema
from src.controller.discord.embed_controller import EmbedController

@Singleton
class RadioController:
    """
    Controller class for managing radio-related functionality.
    """

    ERROR_MESSAGE = "None or Error"
    AUTODJ_OR_ERROR = "AutoDJ or Error"
    UNEXPECTED_RESPONSE_FORMAT = "Unexpected response format"

    def __init__(self, bot: commands.Bot):
        """
        Initializes the RadioController instance.

        Args:
            bot (commands.Bot): The Discord bot instance.
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.bot = bot
        self.config = Config()
        self.client = httpx.AsyncClient(timeout=None)
        self.headers = {
            "X-API-Key": self.config.azuracast_api_key,
            "Accept": "application/json"
        }

        self._initialized = True

    async def get_now_playing(self, station_id: str) ->  Tuple[str, str]:
        """
        Retrieves the currently playing song and the current streamer for a given station.

        Args:
            station_id (str): The ID of the radio station.

        Returns:
            Tuple[str, str]: A tuple containing the currently playing song and the current streamer.
        """
        url = f"{self.config.azuracast_api_url}/nowplaying/{station_id}"
        try:
            response = await self.client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            now_playing = data.get("now_playing", {}).get("song", {}).get("title", self.ERROR_MESSAGE)
            current_streamer = data.get("live", {}).get("streamer_name", self.AUTODJ_OR_ERROR)

            if current_streamer == "":
                current_streamer = self.AUTODJ_OR_ERROR

            return now_playing, current_streamer
        except Exception as e:
            logger.error(f"Failed to get now playing: {e}")
            return self.ERROR_MESSAGE, self.AUTODJ_OR_ERROR

    async def get_listeners(self, station_id: str) -> int:
        """
        Retrieves the number of listeners for a given station.

        Args:
            station_id (str): The ID of the radio station.

        Returns:
            int: The number of listeners.
        """
        url = f"{self.config.azuracast_api_url}/station/{station_id}/listeners"
        try:
            response = await self.client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                return len(data)
            else:
                logger.error(self.UNEXPECTED_RESPONSE_FORMAT)
                return 0
        except Exception as e:
            logger.error(f"Failed to get listeners: {e}")
            return 0

    async def get_song_history(self, station_id: str) -> str:
        """
        Retrieves the song history for a given station.

        Args:
            station_id (str): The ID of the radio station.

        Returns:
            str: The song history.
        """
        url = f"{self.config.azuracast_api_url}/station/{station_id}/history"
        try:
            response = await self.client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                song_titles = "\n".join([f"{song.get('song', {}).get('title', 'Unknown')}" for song in data[:5] if 'song' in song])
                return song_titles if song_titles else self.ERROR_MESSAGE
            else:
                logger.error(self.UNEXPECTED_RESPONSE_FORMAT)
                return self.ERROR_MESSAGE
        except Exception as e:
            logger.error(f"Failed to get song history: {e}")
            return self.ERROR_MESSAGE

    async def get_song_queue(self, station_id: str) -> Optional[list[str]]:
        """
        Retrieves the song queue for a given station.

        Args:
            station_id (str): The ID of the radio station.

        Returns:
            Optional[list[str]]: The song queue, or None if there is no song queue.
        """
        url = f"{self.config.azuracast_api_url}/station/{station_id}/queue"
        try:
            response = await self.client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                song_titles = "\n".join([f"{song.get('song', {}).get('title', 'Unknown')}" for song in data[:5] if 'song' in song])
                return song_titles if song_titles else None
            else:
                logger.error(self.UNEXPECTED_RESPONSE_FORMAT)
                return None
        except Exception as e:
            logger.error(f"Failed to get song queue: {e}")
            return None

    async def update_panel_config_values(self, panel_channel_id: int, panel_message_id: int) -> bool:
        """
        Updates the panel configuration values.

        Args:
            panel_channel_id (int): The ID of the panel channel.
            panel_message_id (int): The ID of the panel message.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            self.config.change_value("panel_channel_id", panel_channel_id)
            self.config.change_value("panel_message_id", panel_message_id)
            return True
        except Exception as e:
            logger.error(f"Failed to update panel config values: {e}")
            return False

    async def create_or_update_embed(self) -> None:
        """
        Creates or updates the embed message with the radio station information.
        """
        now_playing, current_streamer = await self.get_now_playing(self.config.azuracast_station_name)
        current_listeners = await self.get_listeners(self.config.azuracast_station_name)
        song_history = await self.get_song_history(self.config.azuracast_station_name)
        song_queue = await self.get_song_queue(self.config.azuracast_station_name)

        fields = [
            {
                "name": "👤 Current Listeners",
                "value": f"```{current_listeners}```",
                "inline": True
            },
            {
                "name": "🎵 Now playing",
                "value": f"```{now_playing}```",
                "inline": True
            },
            {
                "name": "🎙️ Current DJ",
                "value": f"```{current_streamer}```",
                "inline": False
            },
            {
                "name": "📜 Song History",
                "value": f"```{song_history}```",
                "inline": True
            }
        ]

        if song_queue:
            fields.append({
                "name": "🎶 Song Queue",
                "value": f"```{song_queue}```",
                "inline": True
            })

        radio_station_hyperlink = f"[here]({self.config.app_url})"
        embed_schema = EmbedSchema(
            title="📻 Station Information",
            description=f"Click {radio_station_hyperlink} to go the station website.",
            author_url=self.config.azuracast_station_url,
            fields=fields,
            color=0xF4D701
        )

        embed = await EmbedController().build_embed(embed_schema)
        panel_channel = self.bot.get_channel(self.config.panel_channel_id)

        if not panel_channel:
            logger.critical("Panel channel not found")
            return

        try:
            message = await panel_channel.fetch_message(self.config.panel_message_id)
            await message.edit(embed=embed)
        except discord.NotFound:
            message = await panel_channel.send(embed=embed)
            self.config.change_value("panel_message_id", message.id)
        except discord.HTTPException as e:
            logger.error(f"Failed to create or update embed: {e}")

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=None)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client.aclose()
