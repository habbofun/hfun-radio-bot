import os, discord, asyncio
from loguru import logger
from traceback import format_exc
from discord.ext import commands
from src.helper.config import Config
from src.database.loader import DatabaseLoader
from src.manager.file_manager import FileManager

logger.add(Config().log_file, mode="w+")

class Bot(commands.Bot):
    """
    Represents a bot that extends the `commands.Bot` class.

    Attributes:
        file_manager (FileManager): The file manager instance.
        command_queue (asyncio.Queue): The queue for storing commands.

    Methods:
        __init__: Initializes the Bot instance.
        setup_hook: Sets up the bot by checking inputs, setting up databases, loading cogs, and starting the command worker.
        command_worker: Handles commands from the command queue.
        handle_not_found_error: Handles the "not found" error when responding to an interaction.
        handle_generic_error: Handles generic errors that occur while executing a command.
        send_followup_error_message: Sends a follow-up error message to the interaction.
        close: Closes the bot.
    """

    def __init__(self) -> None:
        self.file_manager = FileManager()
        self.command_queue = asyncio.Queue()
        super().__init__(command_prefix=Config().bot_prefix, help_command=None, intents=discord.Intents.all())

    async def setup_hook(self) -> None:
        """
        Sets up the bot by checking inputs, setting up databases, loading cogs, and starting the command worker.
        """
        try:
            os.system("cls||clear")
            logger.info("Starting bot...")

            logger.debug("Checking for file inputs...")
            self.file_manager.check_input()

            logger.debug("Setting up databases...")
            await DatabaseLoader().setup()

            logger.debug("Loading cogs...")
            for filename in os.listdir("./src/cogs/commands"):
                if filename.endswith(".py") and not filename.startswith("_"):
                    await self.load_extension(f"src.cogs.commands.{filename[:-3]}")

            logger.debug("Loading events...")
            for filename in os.listdir("./src/cogs/events"):
                if filename.endswith(".py") and not filename.startswith("_"):
                    await self.load_extension(f"src.cogs.events.{filename[:-3]}")

            logger.debug("Loading loops...")
            for filename in os.listdir("./src/cogs/loops"):
                if filename.endswith(".py") and not filename.startswith("_"):
                    await self.load_extension(f"src.cogs.loops.{filename[:-3]}")

            self.loop.create_task(self.command_worker())

            logger.info("Setup completed!")
        except Exception:
            logger.critical(f"Error setting up bot: {format_exc()}")
            exit()

    async def command_worker(self):
        """
        Handles commands from the command queue.
        """
        while True:
            interaction, coro = await self.command_queue.get()
            try:
                self.loop.create_task(coro)
            except Exception as e:
                await self.handle_generic_error(interaction, e)
            finally:
                self.command_queue.task_done()

    async def handle_not_found_error(self, interaction, error):
        """
        Handles the "not found" error when responding to an interaction.

        Args:
            interaction: The interaction object.
            error: The error that occurred.
        """
        logger.critical(f"Failed to respond to interaction: {error}")
        await self.send_followup_error_message(interaction, "An error occurred while executing your command. Please notify an Admin.")

    async def handle_generic_error(self, interaction, error):
        """
        Handles generic errors that occur while executing a command.

        Args:
            interaction: The interaction object.
            error: The error that occurred.
        """
        logger.critical(f"Unexpected error: {error}")
        await self.send_followup_error_message(interaction, "An error occurred while executing your command. Please notify an Admin.")

    async def send_followup_error_message(self, interaction, message):
        """
        Sends a follow-up error message to the interaction.

        Args:
            interaction: The interaction object.
            message: The error message to send.
        """
        if hasattr(interaction, 'followup') and not interaction.response.is_done():
            try:
                await interaction.followup.send(message, ephemeral=True)
            except Exception as followup_error:
                logger.critical(f"Failed to send follow-up message: {followup_error}")

    async def close(self) -> None:
        """
        Closes the bot.
        """
        await super().close()

if __name__ == "__main__":
    try:
        bot = Bot()
        bot.run(Config().bot_token)
    except KeyboardInterrupt:
        logger.critical("Goodbye!")
        exit()
    except Exception:
        logger.critical(f"Error running bot: {format_exc()}")
        exit()
