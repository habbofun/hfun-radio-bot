import uvicorn, asyncio
from loguru import logger
from fastapi import FastAPI, HTTPException


from src.helper.singleton import Singleton
from src.database.service.battleball_service import BattleballDatabaseService

@Singleton
class BattleballAPI:
    """
    A class to encapsulate the FastAPI application for Battleball.

    This class handles the initialization and running of a FastAPI server to provide
    access to the Battleball database through a RESTful API.

    Attributes:
        app (FastAPI): The FastAPI application instance.
        db_service (BattleballDatabaseService): The database service for accessing Battleball data.
    """

    def __init__(self):
        """
        Initializes the BattleballAPI class, setting up the FastAPI app and database service.
        """
        self.app = FastAPI()
        self.db_service = BattleballDatabaseService()

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
            return {"message": "Welcome to the Battleball API!"}

        @self.app.get("/leaderboard")
        async def get_leaderboard():
            """
            Fetches the leaderboard from the database and returns it as JSON.

            Returns:
                list: A list of dictionaries representing the leaderboard.
            """
            leaderboard = await self.db_service.get_leaderboard()
            if not leaderboard:
                raise HTTPException(status_code=404, detail="Leaderboard not found")

            formatted_leaderboard = [
                {
                    "position": idx + 1,
                    "username": username,
                    "total_score": score,
                    "ranked_matches": ranked_matches,
                    "non_ranked_matches": non_ranked_matches
                }
                for idx, (username, score, ranked_matches, non_ranked_matches) in enumerate(leaderboard)
            ]

            return formatted_leaderboard

    def run(self, host="0.0.0.0", port=8000):
        """
        Starts the FastAPI server using Uvicorn.

        Args:
            host (str): The host IP address to bind the server to.
            port (int): The port number to bind the server to.
        """
        uvicorn.run(self.app, host=host, port=port)

    async def start_server(self):
        """
        Starts the FastAPI server asynchronously, allowing it to run alongside other async tasks.
        """
        logger.info("Starting Battleball API at '0.0.0.0':'8000'")
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, self.run)
