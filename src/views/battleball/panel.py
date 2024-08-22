import discord
from src.helper.config import Config
from src.controller.discord.schema.embed_schema import EmbedSchema
from src.controller.discord.embed_controller import EmbedController
from src.controller.habbo.battleball.score_manager import ScoreManager

class BattleballPanelView(discord.ui.View):
    """
    Represents the panel view for the Discord bot.
    This view is used to display the panel for Battleball.
    """

    def __init__(self):
        self.config = Config()
        self.battleball_score_manager = ScoreManager()
        super().__init__(timeout=None)

    async def not_implemented(self, interaction: discord.Interaction):
        return await interaction.response.send_message("Sorry! This option is **not** yet implemented.", ephemeral=True)

    @discord.ui.button(label='📲 Mobile Version', style=discord.ButtonStyle.green, custom_id='battleball_panel:mobile_version')
    async def create_room_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        leaderboard_mobile_string = await self.battleball_score_manager.get_leaderboard(mobile_version=True)
        fields = [
            {
                "name": "📃 Ranking",
                "value": f"```{leaderboard_mobile_string}```",
                "inline": True
            }
        ]

        embed_schema = EmbedSchema(
            title="BattleBall Leaderboard",
            description="It's probably not updated in real-time, but it should give you a good idea of who's on top!",
            author_url=self.config.app_url,
            fields=fields,
            color=0xF4D701
        )

        embed = await EmbedController().build_embed(embed_schema)
        await interaction.response.send_message(content=None, embed=embed, ephemeral=True)