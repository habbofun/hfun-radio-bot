from loguru import logger
from src.helper.config import Config
from discord.ext import commands, tasks
from src.controller.radio.radio_controller import RadioController

class UpdateInfoPanelLoop(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.config = Config()
        self.radio_controller = RadioController(bot)
        self.update_info_panel.start()

    @tasks.loop(seconds=30)
    async def update_info_panel(self) -> None:
        await self.radio_controller.create_or_update_embed()

    @update_info_panel.before_loop
    async def before_update_info_panel(self) -> None:
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UpdateInfoPanelLoop(bot))
    logger.info("UpdateInfoPanel loop loaded!")
