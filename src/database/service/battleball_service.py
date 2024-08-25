import aiosqlite
from loguru import logger
from typing import Optional
from src.helper.singleton import Singleton
from src.database.models.battleball import User, Match


@Singleton
class BattleballDatabaseService:
    def __init__(self, db_path: str = 'src/database/storage/battleball.db'):
        self.db_path = db_path

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    total_score INTEGER DEFAULT 0,
                    ranked_matches INTEGER DEFAULT 0
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    discord_id INTEGER,
                    position INTEGER,
                    UNIQUE(username)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT,
                    user_id INTEGER,
                    game_score INTEGER,
                    ranked BOOLEAN,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    UNIQUE(match_id, user_id)
                )
            """)
            await db.commit()
            logger.debug(
                "Database initialized with tables: users, queue, matches")

    async def add_user(self, username: str):
        username = username.lower()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id FROM users WHERE username = ?", (username,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    logger.debug(
                        f"User '{username}' already exists in the database with ID '{row[0]}'.")
                    return row[0]
                else:
                    await db.execute("""
                        INSERT INTO users (username)
                        VALUES (?)
                    """, (username,))
                    await db.commit()
                    logger.debug(f"User '{username}' added to the database.")

    async def get_user_id(self, username: str) -> Optional[int]:
        username = username.lower()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id FROM users WHERE username = ?", (username,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    logger.debug(
                        f"User ID '{row[0]}' found for username '{username}'.")
                else:
                    logger.warning(
                        f"No User ID found for username '{username}'.")
                return row[0] if row else None

    async def update_user_score_and_matches(self, user_id: int, score: int, is_ranked: bool):
        async with aiosqlite.connect(self.db_path) as db:
            if is_ranked:
                await db.execute("""
                    UPDATE users
                    SET total_score = total_score + ?, ranked_matches = ranked_matches + 1
                    WHERE id = ?
                """, (score, user_id))
            await db.commit()
        logger.debug(
            f"Updated user ID '{user_id}' with score '{score}' and ranked status '{is_ranked}'.")

    async def add_match(self, match: Match):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO matches (match_id, user_id, game_score, ranked)
                VALUES (?, ?, ?, ?)
            """, (match.match_id, match.user_id, match.game_score, match.ranked))
            await db.commit()
        logger.debug(
            f"Added match '{match.match_id}' for user ID '{match.user_id}' with score '{match.game_score}'.")

    async def get_checked_matches(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT match_id FROM matches WHERE user_id = ? AND ranked = 1", (user_id,)) as cursor:
                matches = [row[0] for row in await cursor.fetchall()]
        logger.debug(
            f"Retrieved {len(matches)} checked matches for user ID '{user_id}'.")
        return matches

    async def add_to_queue(self, username: str, discord_id: int) -> Optional[int]:
        username = username.lower()
        async with aiosqlite.connect(self.db_path) as db:
            # Check if the username is already in the queue and return the position
            async with db.execute("SELECT position FROM queue WHERE username = ?", (username,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    logger.debug(
                        f"User '{username}' is already in the queue at position '{row[0]}'")
                    return row[0]

            # Find the next available position
            async with db.execute("SELECT position FROM queue ORDER BY position") as cursor:
                existing_positions = set(row[0] for row in await cursor.fetchall())
            
            position = 1
            while position in existing_positions:
                position += 1

            await db.execute("""
                INSERT INTO queue (username, discord_id, position)
                VALUES (?, ?, ?)
            """, (username, discord_id, position))
            await db.commit()
            logger.debug(
                f"User '{username}' added to the queue at position '{position}'.")
            return position

    async def get_queue(self, limit: int = 0, offset: int = 0, include_discord_id: bool = True):
        async with aiosqlite.connect(self.db_path) as db:
            query = """
                SELECT username, discord_id, position
                FROM queue
                ORDER BY position
            """
            if limit > 0:
                query += f" LIMIT {limit}"
            if offset > 0:
                query += f" OFFSET {offset}"
            
            async with db.execute(query) as cursor:
                if include_discord_id:
                    queue = [{"username": row[0], "discord_id": row[1], "position": row[2]} for row in await cursor.fetchall()]
                else:
                    queue = [{"username": row[0], "position": row[2]} for row in await cursor.fetchall()]
        return queue

    async def get_next_in_queue(self, include_discord_id: bool = True) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM queue ORDER BY position LIMIT 1") as cursor:
                row = await cursor.fetchone()
                if row:
                    if include_discord_id:
                        logger.debug(
                            f"Next in queue: ID '{row[0]}', Username '{row[1]}', Discord ID '{row[2]}', Position '{row[3]}'")
                        return {"id": row[0], "username": row[1], "discord_id": row[2], "position": row[3]}
                    else:
                        logger.debug(
                            f"Next in queue: ID '{row[0]}', Username '{row[1]}', Position '{row[3]}'")
                        return {"id": row[0], "username": row[1], "position": row[3]}
                logger.debug("Queue is empty.")
                return None

    async def remove_from_queue(self, queue_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM queue WHERE id = ?", (queue_id,))
            await db.commit()
        logger.debug(f"Removed queue item with ID '{queue_id}'.")
        await self.reorder_queue()

    async def reorder_queue(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id FROM queue ORDER BY position") as cursor:
                queue_items = await cursor.fetchall()
            
            for new_position, (item_id,) in enumerate(queue_items, start=1):
                await db.execute("UPDATE queue SET position = ? WHERE id = ?", (new_position, item_id))
            
            await db.commit()
        logger.debug("Queue reordered successfully.")

    async def fulminate_user(self, username: str):
        # Delete the user and everything related to them in every table
        username = username.lower()
        async with aiosqlite.connect(self.db_path) as db:
            user_id = await self.get_user_id(username)
            if user_id:
                await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
                await db.execute("DELETE FROM queue WHERE username = ?", (username,))
                await db.execute("DELETE FROM matches WHERE user_id = ?", (user_id,))
                await db.commit()
                await self.reorder_queue()
                logger.debug(
                    f"Fulminated user '{username}' with ID '{user_id}'.")
            else:
                logger.warning(f"User '{username}' not found in the database.")

    async def get_queue(self, limit: int = 0, offset: int = 0, include_discord_id: bool = True):
        async with aiosqlite.connect(self.db_path) as db:
            query = """
                SELECT username, discord_id, position
                FROM queue
                ORDER BY position
            """
            if limit > 0:
                query += f" LIMIT {limit}"
            if offset > 0:
                query += f" OFFSET {offset}"
            
            async with db.execute(query) as cursor:
                if include_discord_id:
                    queue = [{"username": row[0], "discord_id": row[1], "position": row[2]} for row in await cursor.fetchall()]
                else:
                    queue = [{"username": row[0], "position": row[2]} for row in await cursor.fetchall()]
        return queue

    async def get_total_queue_users(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM queue") as cursor:
                (count,) = await cursor.fetchone()
                return count

    async def get_leaderboard(self, limit: int = 0, offset: int = 0):
        async with aiosqlite.connect(self.db_path) as db:
            query = """
                SELECT username, total_score, ranked_matches
                FROM users
                ORDER BY total_score DESC
            """
            if limit > 0:
                query += f" LIMIT {limit}"
            if offset > 0:
                query += f" OFFSET {offset}"
            
            cursor = await db.execute(query)
            return await cursor.fetchall()

    async def get_total_users(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                (count,) = await cursor.fetchone()
                return count