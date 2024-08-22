import time
import aiosqlite
from loguru import logger
from tabulate import tabulate
from src.helper.singleton import Singleton
from src.database.service.battleball_service import BattleballDatabaseService
from src.controller.habbo.battleball.battleball_controller import BattleballController

@Singleton
class ScoreManager:
    def __init__(self):
        self.api_controller = BattleballController()
        self.db_service = BattleballDatabaseService()
        self.cache = {}  # In-memory cache for quick access
    
    async def initialize(self):
        await self.db_service.initialize()
    
    async def process_user_scores(self, username):
        start_time = time.time()  # Start timing the process

        if username in self.cache and (time.time() - self.cache[username]['last_updated']) < 3600:
            #logger.info(f"Returning cached score for {username}.")
            return self.cache[username]['total_score']

        user = await self.db_service.get_user(username)
        if user:
            bouncer_player_id = user[2]
        else:
            bouncer_player_id = await self.api_controller.get_bouncer_player_id(username)
            await self.db_service.insert_user(username, bouncer_player_id)

        match_ids = await self.api_controller.get_match_ids(bouncer_player_id)

        match_data_list = await self.api_controller.fetch_all_match_data(match_ids)

        await self._process_all_matches(match_data_list, username, bouncer_player_id)

        total_score = await self.db_service.get_user_score(username)

        self.cache[username] = {
            'total_score': total_score,
            'last_updated': time.time()
        }

        end_time = time.time()  # End timing the process
        elapsed_time = end_time - start_time
        #logger.info(f"Time taken to gather and process all info for {username}: {elapsed_time:.2f} seconds")

        return total_score

    async def _process_all_matches(self, match_data_list, username, bouncer_player_id):
        ranked_matches = 0
        non_ranked_matches = 0

        for match_data in match_data_list:
            match_id = match_data['metadata']['matchId']
            is_ranked = match_data['info']['ranked']

            if not await self.db_service.is_match_processed(match_id):
                if is_ranked:
                    ranked_matches += 1
                    await self._process_match(match_data, bouncer_player_id)
                else:
                    non_ranked_matches += 1

                await self.db_service.mark_match_as_processed(match_id)

        await self.db_service.update_user_matches(username, ranked_matches, non_ranked_matches)

    async def _process_match(self, match_data, bouncer_player_id):
        for participant in match_data['info']['participants']:
            if participant['gamePlayerId'] == bouncer_player_id:
                user_score = participant['gameScore']
                username = await self._get_username_by_bouncer_id(bouncer_player_id)
                await self.db_service.update_score(username, user_score)
                break

    async def _get_username_by_bouncer_id(self, bouncer_player_id):
        async with aiosqlite.connect(self.db_service.db_path) as db:
            cursor = await db.execute('SELECT username FROM users WHERE bouncer_player_id = ?', (bouncer_player_id,))
            result = await cursor.fetchone()
            return result[0] if result else None

    async def get_leaderboard(self):
        leaderboard = await self.db_service.get_leaderboard()
        formatted_leaderboard = [
            (idx + 1, username, score, ranked_matches, non_ranked_matches)
            for idx, (username, score, ranked_matches, non_ranked_matches) in enumerate(leaderboard)
        ]
        return tabulate(formatted_leaderboard, headers=["Position", "Username", "Score", "Ranked Matches", "Non-Ranked Matches"], tablefmt="pretty")
