from loguru import logger
from src.helper.config import Config
from discord.ext import commands, tasks
from src.controller.habbo.battleball.score_manager import ScoreManager

class UpdateBattleballPanelLoop(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.config = Config()
        self.battleball_score_manager = ScoreManager(bot)
        self.update_battleball_panel.start()

    @tasks.loop(seconds=30)
    async def update_battleball_panel(self) -> None:
        await self.battleball_score_manager.create_or_update_embed()

    @update_battleball_panel.before_loop
    async def before_update_battleball_panel(self) -> None:
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UpdateBattleballPanelLoop(bot))
    logger.info("UpdateBattleballPanelLoop loop loaded!")
