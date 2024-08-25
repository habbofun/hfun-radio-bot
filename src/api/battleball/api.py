import time
import uvicorn
import asyncio
from loguru import logger
from discord.ext import commands
from src.helper.config import Config
from fastapi import FastAPI, HTTPException, Query
from src.helper.singleton import Singleton
from fastapi.middleware.cors import CORSMiddleware
from src.utils.time_utils import UpdateTimer
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
        self.update_timer = UpdateTimer()

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
        async def get_leaderboard(
            page: int = Query(None, ge=1, description="Page number"),
            per_page: int = Query(None, ge=1, le=100, description="Items per page")
        ):
            """
            Fetches the leaderboard from the database and returns it as JSON.
            If page and per_page are not provided, returns the entire leaderboard.

            Args:
                page (int, optional): The page number
                per_page (int, optional): The number of items per page (max: 100)

            Returns:
                dict: A dictionary containing the leaderboard and metadata.
            """
            if page is None or per_page is None:
                # Return the entire leaderboard
                leaderboard = await self.db_service.get_leaderboard()
                total_users = len(leaderboard)
                formatted_leaderboard = [
                    {
                        "position": idx + 1,
                        "username": username,
                        "total_score": score,
                        "ranked_matches": ranked_matches
                    }
                    for idx, (username, score, ranked_matches) in enumerate(leaderboard)
                ]
            else:
                # Return paginated leaderboard
                offset = (page - 1) * per_page
                leaderboard = await self.db_service.get_leaderboard(limit=per_page, offset=offset)
                total_users = await self.db_service.get_total_users()
                formatted_leaderboard = [
                    {
                        "position": offset + idx + 1,
                        "username": username,
                        "total_score": score,
                        "ranked_matches": ranked_matches
                    }
                    for idx, (username, score, ranked_matches) in enumerate(leaderboard)
                ]

            if not leaderboard:
                logger.warning("Leaderboard not found")
                raise HTTPException(status_code=404, detail="Leaderboard not found")

            response = {
                "leaderboard": formatted_leaderboard,
                "metadata": {
                    "total_users": total_users,
                },
                "next_update_in": max(0, round(self.update_timer.get_next_update_time())),
                "update_interval_minutes": self.config.battleball_api_update_interval_minutes,
                "update_interval_seconds": self.config.battleball_api_update_interval_seconds
            }

            if page is not None and per_page is not None:
                total_pages = (total_users + per_page - 1) // per_page
                response["metadata"].update({
                    "page": page,
                    "per_page": per_page,
                    "total_pages": total_pages,
                })

            logger.debug("Leaderboard fetched successfully")
            return response

        @self.app.get("/queue")
        async def get_queue(
            page: int = Query(None, ge=1, description="Page number"),
            per_page: int = Query(None, ge=1, le=100, description="Items per page")
        ):
            """
            Fetches the queue from the database and returns it as JSON.
            If page and per_page are not provided, returns the entire queue.

            Args:
                page (int, optional): The page number
                per_page (int, optional): The number of items per page (max: 100)

            Returns:
                dict: A dictionary containing the queue and metadata.
            """
            if page is None or per_page is None:
                # Return the entire queue
                queue = await self.db_service.get_queue(include_discord_id=False)
                total_users = len(queue)
                formatted_queue = [
                    {
                        "position": item["position"],
                        "username": item["username"]
                    }
                    for item in queue
                ]
            else:
                # Return paginated queue
                offset = (page - 1) * per_page
                queue = await self.db_service.get_queue(limit=per_page, offset=offset, include_discord_id=False)
                total_users = await self.db_service.get_total_queue_users()
                formatted_queue = [
                    {
                        "position": item["position"],
                        "username": item["username"]
                    }
                    for item in queue
                ]

            if not queue:
                logger.warning("Queue is empty")
                raise HTTPException(status_code=404, detail="Queue is empty")

            response = {
                "queue": formatted_queue,
                "metadata": {
                    "total_users": total_users,
                },
            }

            if page is not None and per_page is not None:
                total_pages = (total_users + per_page - 1) // per_page
                response["metadata"].update({
                    "page": page,
                    "per_page": per_page,
                    "total_pages": total_pages,
                })

            logger.debug("Queue fetched successfully")
            return response

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