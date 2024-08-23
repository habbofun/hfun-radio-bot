import os
from loguru import logger
from pyfiglet import Figlet
from discord.ext import commands
from src.helper.config import Config
from pystyle import Colors, Colorate, Center
from src.views.battleball.panel import BattleballPanelView
from src.controller.habbo.battleball.worker.worker import BattleballWorker

class OnReady(commands.Cog):
    """
    A class representing the on_ready event handler for the bot.
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config()
        self.battleball_worker = BattleballWorker(self)

    @commands.Cog.listener()
    async def on_ready(self):
        """
        A coroutine that is called when the bot is ready to start receiving events.
        """

        os.system("cls||clear")

        logo = Figlet(font="big").renderText(self.config.app_name)
        centered_logo = Center.XCenter(Colorate.Vertical(Colors.white_to_blue, logo, 1))
        divider = Center.XCenter(Colorate.Vertical(Colors.white_to_blue, "────────────────────────────────────────────", 1))
        print(f"{centered_logo}\n{divider}\n\n")

        logger.debug("Setting persistent views...")
        self.bot.add_view(BattleballPanelView(self.bot))

        logger.debug("Loading workers...")
        if not self.battleball_worker.running:
            await self.battleball_worker.start()

        logger.info(f"Logged in as {self.bot.user.name}#{self.bot.user.discriminator}.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OnReady(bot))
    return logger.info("On ready event registered!")