import discord
from loguru import logger
from discord.ext import commands
from discord import app_commands
from src.controller.discord.schema.embed_schema import EmbedSchema
from src.controller.discord.embed_controller import EmbedController

class BattleUpdate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="battle_update", description="Command to try to update a battleball profile data.")
    async def battle_update_command(self, interaction: discord.Interaction):
        await self.bot.command_queue.put((interaction, self.process_battle_update_command(interaction)))

    async def process_battle_update_command(self, interaction: discord.Interaction):
        try:

            embed_schema = EmbedSchema(
                title="",
                description=f"",
                color=0xb34760
            )

            embed = await EmbedController().build_embed(embed_schema)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.critical(f"Failed to respond to battle_update command: {e}")
            if not interaction.response.is_done():
                try:
                    await interaction.followup.send("There was an error trying to execute that command!", ephemeral=True)
                except Exception as followup_error:
                    logger.critical(f"Failed to send follow-up message: {followup_error}")

    @battle_update_command.error
    async def battle_update_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("You don't have the necessary permissions to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(BattleUpdate(bot))
    logger.info("Battle-Update command loaded!")
