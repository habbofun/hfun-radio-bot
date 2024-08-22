import aiosqlite
from typing import Optional
from src.database.models.battleball import User, Match
from src.helper.singleton import Singleton

@Singleton
class BattleballDatabaseService:
    def __init__(self, db_path: str = 'src/database/storage/battleball.db'):
        self.db_path = db_path

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    discord_id INTEGER UNIQUE,
                    username TEXT,
                    total_score INTEGER DEFAULT 0,
                    ranked_matches INTEGER DEFAULT 0,
                    non_ranked_matches INTEGER DEFAULT 0
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    discord_id INTEGER,
                    position INTEGER
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_id TEXT,
                    user_id INTEGER,
                    game_score INTEGER,
                    ranked BOOLEAN,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            await db.commit()

    async def add_user(self, username: str, discord_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO users (discord_id, username)
                VALUES (?, ?)
            """, (discord_id, username))
            await db.commit()

    async def get_user_id(self, discord_id: int) -> Optional[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id FROM users WHERE discord_id = ?", (discord_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def update_user_score_and_matches(self, user_id: int, score: int, is_ranked: bool):
        async with aiosqlite.connect(self.db_path) as db:
            if is_ranked:
                await db.execute("""
                    UPDATE users
                    SET total_score = total_score + ?, ranked_matches = ranked_matches + 1
                    WHERE id = ?
                """, (score, user_id))
            else:
                await db.execute("""
                    UPDATE users
                    SET total_score = total_score + ?, non_ranked_matches = non_ranked_matches + 1
                    WHERE id = ?
                """, (score, user_id))
            await db.commit()

    async def add_match(self, match: Match):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO matches (match_id, user_id, game_score, ranked)
                VALUES (?, ?, ?, ?)
            """, (match.match_id, match.user_id, match.game_score, match.ranked))
            await db.commit()

    async def get_checked_matches(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT match_id FROM matches WHERE user_id = ? AND ranked = 1", (user_id,)) as cursor:
                return [row[0] for row in await cursor.fetchall()]

    async def add_to_queue(self, username: str, discord_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT MAX(position) FROM queue")
            max_position = await cursor.fetchone()
            position = (max_position[0] or 0) + 1

            await db.execute("""
                INSERT INTO queue (username, discord_id, position)
                VALUES (?, ?, ?)
            """, (username, discord_id, position))
            await db.commit()
            return position

    async def get_next_in_queue(self) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM queue ORDER BY position LIMIT 1") as cursor:
                row = await cursor.fetchone()
                if row:
                    return {"id": row[0], "username": row[1], "discord_id": row[2], "position": row[3]}
                return None

    async def remove_from_queue(self, queue_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM queue WHERE id = ?", (queue_id,))
            await db.commit()

    async def get_leaderboard(self):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT username, total_score, ranked_matches, non_ranked_matches
                FROM users
                ORDER BY total_score DESC
            """) as cursor:
                return await cursor.fetchall()
