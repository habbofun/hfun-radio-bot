import time
import discord
import asyncio
from loguru import logger
from tabulate import tabulate
from discord.ext import commands
from src.helper.config import Config
from src.helper.dmer import DiscordDmer
from src.helper.singleton import Singleton
from src.controller.habbo.battleball.api_client.client import HabboApiClient
from src.database.service.battleball_service import BattleballDatabaseService, Match


@Singleton
class BattleballWorker:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config()
        self.db_service = BattleballDatabaseService()
        self.api_client = HabboApiClient()
        self.dmer = DiscordDmer(bot)
        self.running = False
        self.current_user = None
        self.remaining_matches = 0  # Track the number of remaining matches

    async def start(self):
        self.running = True
        while True:
            queue_item = await self.db_service.get_next_in_queue()
            if not queue_item:
                break

            await self.process_user(queue_item)
            await self.db_service.remove_from_queue(queue_item["id"])
            await asyncio.sleep(1)  # Throttle to avoid API rate limits

        self.running = False

    async def stop(self):
        self.running = False

    async def process_user(self, queue_item):
        start_time = time.time()

        username = queue_item["username"].lower()
        discord_id = queue_item["discord_id"]

        await self.db_service.add_user(username)
        user_id = await self.db_service.get_user_id(username)

        if not user_id:
            logger.error(f"User ID not found for username '{username}'")
            return

        self.current_user = username
        user_data = await self.api_client.fetch_user_data(username)

        if not user_data:
            self.dmer.send_dm(
                discord_id, f"{self.config.abajo_icon} Failed to process user '{username}'.")
            return

        checked_match_ids = await self.db_service.get_checked_matches(user_id)

        bouncer_player_id = user_data.bouncerPlayerId
        match_ids = await self.api_client.fetch_match_ids(bouncer_player_id)

        new_match_ids = [
            match_id for match_id in match_ids if match_id not in checked_match_ids]
        # Set the initial count of remaining matches
        self.remaining_matches = len(new_match_ids)

        logger.info(
            f"Processing '{self.remaining_matches}' new matches for '{username}'")

        for i in range(0, len(new_match_ids), 3):
            batch = new_match_ids[i:i+3]
            matches = await self.api_client.fetch_match_data_batch(batch)

            for match_data in matches:
                match_id = match_data.metadata.matchId
                participant = next(
                    (p for p in match_data.info.participants if p.gamePlayerId == bouncer_player_id), None)

                if participant:
                    score = participant.gameScore
                    is_ranked = match_data.info.ranked
                    remaining_matches = await self.get_remaining_matches()
                    logger.info(
                        f"Processing match '{match_id}' ({remaining_matches}) for user '{username}' with score '{score}'")
                else:
                    score = 0
                    is_ranked = False

                match = Match(
                    match_id=match_id,
                    user_id=user_id,
                    game_score=score,
                    ranked=is_ranked
                )

                await self.db_service.add_match(match)
                await self.db_service.update_user_score_and_matches(user_id, score, is_ranked)

                # Decrement the remaining matches count
                self.remaining_matches -= 1

        try:
            self.dmer.send_dm(
                discord_id, f"{self.config.arriba_icon} Job for user `{username}` has been completed.")
        except discord.HTTPException as e:
            logger.error(f"Failed to send DM to user '{username}': {e}")

        logger.info(
            f"Processed '{len(new_match_ids)}' matches for '{username}' in '{time.time() - start_time:.2f}' seconds")
        self.current_user = None
        self.remaining_matches = 0  # Reset after processing

    async def get_remaining_matches(self) -> int:
        """
        Returns the number of remaining matches for the current user being processed.
        """
        if self.current_user:
            return self.remaining_matches
        else:
            logger.info("No user is currently being processed.")
            return 0

    async def create_or_update_embed(self) -> None:
        leaderboard_string = await self.get_leaderboard()

        # Ensure the leaderboard string is within Discord's 4096-character limit for the description.
        if len(leaderboard_string) > 4096:
            # Truncate and add ellipsis
            leaderboard_string = leaderboard_string[:4092] + "..."

        embed = discord.Embed(
            title="BattleBall Leaderboard",
            description=f"```{leaderboard_string}```",
            color=0xF4D701,
            timestamp=discord.utils.utcnow()  # Set the current time as the timestamp
        )

        embed.set_footer(
            text="It's probably not updated in real-time, but it should give you a good idea of who's on top!"
        )

        battleball_channel = self.bot.get_channel(
            self.config.battleball_channel_id)

        if not battleball_channel:
            logger.critical("Battleball channel not found")
            return

        try:
            battleball_message = await battleball_channel.fetch_message(self.config.battleball_message_id)
            await battleball_message.edit(content=None, embed=embed)
        except discord.NotFound:
            battleball_message = await battleball_channel.send(content=None, embed=embed)
            self.config.change_value(
                "battleball_message_id", battleball_message.id)
        except discord.HTTPException as e:
            logger.error(f"Failed to create or update embed: {e}")

    async def get_leaderboard(self, mobile_version: bool = False, limit: int = 40, offset: int = 0) -> str:
        leaderboard = await self.db_service.get_leaderboard(limit, offset)

        if mobile_version:
            formatted_leaderboard = [
                f"**{idx + 1}**. {username} - {score}"
                for idx, (username, score, _) in enumerate(leaderboard)
            ]
            formatted_text = "\n".join(formatted_leaderboard)

            logger.debug(f"Formatted text length: {len(formatted_text)}")
            return formatted_text

        formatted_leaderboard = [
            (idx + 1, username, score, ranked_matches)
            for idx, (username, score, ranked_matches) in enumerate(leaderboard)
        ]
        formatted_text =  tabulate(
            formatted_leaderboard,
            headers=["Position", "Username", "Score", "Ranked Matches"],
            tablefmt="pretty"
        )

        logger.debug(f"Formatted text length: {len(formatted_text)}")
        return formatted_text

    async def update_user_stats(self, user_id, username, matches):
        total_score = 0
        ranked_matches = 0

        for match in matches:
            if match.info.ranked:
                total_score += match.info.gameScore
                ranked_matches += 1

        await self.db_service.update_user_stats(user_id, username, total_score, ranked_matches)