import httpx, discord
from loguru import logger
from discord.ext import commands
from src.helper.config import Config
from src.controller.discord.schema.embed_schema import EmbedSchema
from src.controller.discord.embed_controller import EmbedController

class RadioController:
    _instance = None

    @classmethod
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RadioController, cls).__new__(cls)
        return cls._instance

    def __init__(self, bot: commands.Bot):
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

    async def get_now_playing(self, station_id: str) -> str:
        url = f"{self.config.azuracast_api_url}/nowplaying/{station_id}"
        try:
            response = await self.client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            now_playing = data.get("now_playing", {}).get("song", {}).get("title", "None or Error")
            current_streamer = data.get("live", {}).get("streamer_name", "AutoDJ or Error")

            if current_streamer == "":
                current_streamer = "AutoDJ or Error"

            return now_playing, current_streamer
        except Exception as e:
            logger.error(f"Failed to get now playing: {e}")
            return "None or Error"

    async def get_listeners(self, station_id: str) -> int:
        url = f"{self.config.azuracast_api_url}/station/{station_id}/listeners"
        try:
            response = await self.client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                return len(data)
            else:
                logger.error("Unexpected response format")
                return 0
        except Exception as e:
            logger.error(f"Failed to get listeners: {e}")
            return 0

    async def get_song_history(self, station_id: str) -> str:
        url = f"{self.config.azuracast_api_url}/station/{station_id}/history"
        try:
            response = await self.client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                song_titles = "\n".join([f"{song.get('song', {}).get('title', 'Unknown')}" for song in data[:5] if 'song' in song])
                return song_titles if song_titles else "None or Error"
            else:
                logger.error("Unexpected response format")
                return "None or Error"
        except Exception as e:
            logger.error(f"Failed to get song history: {e}")
            return "None or Error"

    async def get_song_queue(self, station_id: str) -> str:
        url = f"{self.config.azuracast_api_url}/station/{station_id}/queue"
        try:
            response = await self.client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                song_titles = "\n".join([f"{song.get('song', {}).get('title', 'Unknown')}" for song in data[:5] if 'song' in song])
                return song_titles if song_titles else None
            else:
                logger.error("Unexpected response format")
                return None
        except Exception as e:
            logger.error(f"Failed to get song queue: {e}")
            return None

    async def update_panel_config_values(self, panel_channel_id: int, panel_message_id: int) -> bool:
        try:
            self.config.change_value("panel_channel_id", panel_channel_id)
            self.config.change_value("panel_message_id", panel_message_id)
            return True
        except Exception as e:
            logger.error(f"Failed to update panel config values: {e}")
            return False

    async def create_or_update_embed(self) -> None:
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
