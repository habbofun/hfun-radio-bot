import time
import uvicorn
import asyncio
from loguru import logger
from discord.ext import commands
from src.helper.config import Config
from fastapi import FastAPI, HTTPException
from src.helper.singleton import Singleton
from fastapi.middleware.cors import CORSMiddleware
from src.cogs.loops.queue_top_users import BattleballUpdateLoop
from src.database.service.battleball_service import BattleballDatabaseService


@Singleton
class BattleballAPI:
    """
    A class to encapsulate the FastAPI application for Battleball.
    """

    def __init__(self, bot: commands.Bot):
        """
        Initializes the BattleballAPI class, setting up the FastAPI app and database service.
        """
        self.app = FastAPI()
        self.config = Config()
        self.db_service = BattleballDatabaseService()
        self.battleball_update_loop = BattleballUpdateLoop(bot)

        # Enable CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Register API routes
        self.register_routes()

    def register_routes(self):
        """
        Registers all the API routes with the FastAPI app.
        """
        @self.app.get("/")
        async def root():
            """
            A simple root endpoint that returns a welcome message.

            Returns:
                dict: A dictionary containing a welcome message.
            """
            logger.info("Root endpoint accessed")
            return {"message": "Welcome to the Battleball API!"}

        @self.app.get("/leaderboard")
        async def get_leaderboard():
            """
            Fetches the leaderboard from the database and returns it as JSON.

            Returns:
                dict: A dictionary containing the leaderboard and next update time.
            """
            leaderboard = await self.db_service.get_leaderboard()
            if not leaderboard:
                logger.warning("Leaderboard not found")
                raise HTTPException(status_code=404, detail="Leaderboard not found")

            formatted_leaderboard = [
                {
                    "position": idx + 1,
                    "username": username,
                    "total_score": score,
                    "ranked_matches": ranked_matches
                }
                for idx, (username, score, ranked_matches) in enumerate(leaderboard)
            ]

            # Calculate time remaining until next queue_top_users execution
            next_run_time = 0
            if self.battleball_update_loop:
                last_run_time = self.battleball_update_loop.last_run_time
                interval = self.battleball_update_loop.queue_top_users.seconds  # This should be in seconds
                next_run_time = last_run_time + interval - time.time()

            logger.info("Leaderboard fetched successfully")
            return {
                "leaderboard": formatted_leaderboard,
                "next_update_in": max(0, round(next_run_time))
            }

    def run(self, host=Config().battleball_api_host, port=Config().battleball_api_port):
        """
        Starts the FastAPI server using Uvicorn with no logging output.

        Args:
            host (str): The host IP address to bind the server to.
            port (int): The port number to bind the server to.
        """
        # Configure Uvicorn to have no logging output
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="critical",  # Set the log level to critical to suppress most logging
            access_log=False,  # Disable the access log
        )

    async def start_server(self):
        """
        Starts the FastAPI server asynchronously, allowing it to run alongside other async tasks.
        """
        logger.info(f"Starting Battleball API at '{self.config.battleball_api_host}':'{self.config.battleball_api_port}'")
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self.run)