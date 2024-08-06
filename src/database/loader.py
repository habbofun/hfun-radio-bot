import traceback
from loguru import logger

class DatabaseLoader:
    """
    Class responsible for loading the database and setting it up.
    """

    def __init__(self) -> None:
        ...

    async def setup(self) -> None:
        """
        Sets up the database by creating the necessary table.
        """
        try:
            ...
        except Exception as e:
            logger.critical(f"Error setting up database(s): {e}")
            traceback.print_exc()