import traceback
from loguru import logger
from src.helper.singleton import Singleton
from src.database.service.battleball_service import BattleballDatabaseService


@Singleton
class DatabaseLoader:
    """
    Class responsible for loading the database and setting it up.
    """

    def __init__(self) -> None:
        self.battleball_db_service = BattleballDatabaseService()

    async def setup(self) -> None:
        """
        Initializes the database(s) by creating the necessary tables.
        """
        try:
            await self.battleball_db_service.initialize()
        except Exception as e:
            logger.critical(f"Error setting up database(s): {e}")
            traceback.print_exc()
