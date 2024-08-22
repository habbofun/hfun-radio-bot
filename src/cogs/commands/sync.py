import discord
from loguru import logger
from discord.ext import commands
from src.helper.config import Config

class SyncCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sync(self, ctx: commands.Context, guild: discord.Guild = None):
        await self.bot.command_queue.put((ctx, self.process_sync_command(ctx, guild)))

    async def process_sync_command(self, ctx: commands.Context, guild: discord.Guild = None):
        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            logger.warning("Tried to delete a message that was not found.")
        except discord.errors.Forbidden:
            logger.warning("Bot does not have permission to delete the message.")
        except Exception as e:
            logger.warning(f"Unexpected error while trying to delete the message: {e}")

        try:
            if guild is None:
                await self.bot.tree.sync()
                success_message = "✅ Successfully synced slash commands globally!"
            else:
                await self.bot.tree.sync(guild=guild)
                success_message = f"✅ Successfully synced slash commands in {guild.name}!"
            msg = await ctx.send(success_message)
            
            logger.info("Slash commands were synced by an admin.")

            # Delete the success message after a delay
            await msg.delete(delay=5)

        except discord.errors.Forbidden:
            error_message = "❌ Failed to sync slash commands: Bot does not have permission to send messages."
            logger.critical(error_message)
        except discord.errors.HTTPException as e:
            error_message = f"❌ Failed to sync slash commands: {e}"
            logger.critical(error_message)
        except Exception as e:
            error_message = f"❌ Failed to sync slash commands: {e}"
            logger.critical(error_message)

async def setup(bot: commands.Bot):
    await bot.add_cog(SyncCommand(bot))
    logger.info("Sync command loaded!")