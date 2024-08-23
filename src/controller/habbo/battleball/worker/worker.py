import time, discord, asyncio
from loguru import logger
from tabulate import tabulate
from discord.ext import commands
from src.helper.config import Config
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
        self.running = False

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

    async def process_user(self, queue_item):
        start_time = time.time()

        username = queue_item["username"].lower()
        discord_id = queue_item["discord_id"]

        await self.db_service.add_user(username)
        user_id = await self.db_service.get_user_id(username)

        if not user_id:
            logger.error(f"User ID not found for username '{username}'")
            return

        bouncer_player_id = await self.api_client.fetch_user_bouncer_id(username)
        match_ids = await self.api_client.fetch_match_ids(bouncer_player_id)
        checked_match_ids = await self.db_service.get_checked_matches(user_id)

        new_match_ids = [match_id for match_id in match_ids if match_id not in checked_match_ids]

        logger.info(f"Processing {len(new_match_ids)} new matches for {username}")

        for i in range(0, len(new_match_ids), 3):
            batch = new_match_ids[i:i+3]
            matches = await self.api_client.fetch_match_data_batch(batch)

            for match_data in matches:
                match_id = match_data.metadata.matchId
                participant = next((p for p in match_data.info.participants if p.gamePlayerId == bouncer_player_id), None)

                if participant:
                    score = participant.gameScore
                    is_ranked = match_data.info.ranked
                    logger.info(f"Processing match '{match_id}' for user '{username}' with score '{score}' and ranked status '{is_ranked}'")
                else:
                    is_ranked = False

                # Ensure negative scores are subtracted from the total score
                match = Match(
                    match_id=match_id,
                    user_id=user_id,
                    game_score=score,
                    ranked=is_ranked
                )

                logger.debug(f"Attempting to add match '{match_id}' to the database for user ID '{user_id}'.")
                await self.db_service.add_match(match)
                await self.db_service.update_user_score_and_matches(user_id, score, is_ranked)

        try:
            user_that_queued = self.bot.get_user(discord_id)
            if user_that_queued:
                await user_that_queued.send(f"Job for user `{username}` has been completed.")
        except discord.HTTPException as e:
            logger.error(f"Failed to send DM to user '{username}': {e}")

        logger.info(f"Processed {len(new_match_ids)} matches for {username} in {time.time() - start_time:.2f} seconds")

    async def create_or_update_embed(self) -> None:
        leaderboard_string = await self.get_leaderboard()

        # Ensure the leaderboard string is within Discord's 1024-character limit.
        if len(leaderboard_string) > 1024:
            leaderboard_string = leaderboard_string[:1020] + "..."  # Truncate and add ellipsis

        embed = discord.Embed(
            title="BattleBall Leaderboard",
            description="It's probably not updated in real-time, but it should give you a good idea of who's on top!",
            color=0xF4D701
        )

        embed.add_field(
            name="📃 Ranking",
            value=f"```{leaderboard_string}```",
            inline=True
        )

        battleball_channel = self.bot.get_channel(self.config.battleball_channel_id)

        if not battleball_channel:
            logger.critical("Battleball channel not found")
            return

        try:
            battleball_message = await battleball_channel.fetch_message(self.config.battleball_message_id)
            await battleball_message.edit(content=None, embed=embed)
        except discord.NotFound:
            battleball_message = await battleball_channel.send(content=None, embed=embed)
            self.config.change_value("battleball_message_id", battleball_message.id)
        except discord.HTTPException as e:
            logger.error(f"Failed to create or update embed: {e}")

    async def get_leaderboard(self, mobile_version: bool = False) -> str:
        leaderboard = await self.db_service.get_leaderboard()

        if mobile_version:
            formatted_leaderboard = [
                (idx + 1, username, score)
                for idx, (username, score, _, _) in enumerate(leaderboard)
            ]
            return tabulate(
                formatted_leaderboard,
                headers=["Position", "Username", "Score"],
                tablefmt="pretty"
            )

        formatted_leaderboard = [
            (idx + 1, username, score, ranked_matches, non_ranked_matches)
            for idx, (username, score, ranked_matches, non_ranked_matches) in enumerate(leaderboard)
        ]

        return tabulate(
            formatted_leaderboard,
            headers=["Position", "Username", "Score", "Ranked Matches", "Non-Ranked Matches"],
            tablefmt="pretty"
        )
