import time
import aiosqlite
from src.helper.singleton import Singleton

@Singleton
class BattleballDatabaseService:
    def __init__(self, db_path='src/database/storage/battleball.db'):
        self.db_path = db_path

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    bouncer_player_id TEXT UNIQUE NOT NULL,
                    last_updated INTEGER NOT NULL,
                    ranked_matches INTEGER NOT NULL DEFAULT 0,
                    non_ranked_matches INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS matches (
                    match_id TEXT PRIMARY KEY,
                    processed BOOLEAN NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS scores (
                    user_id INTEGER NOT NULL,
                    total_score INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(user_id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
            ''')
            await db.commit()

    async def get_user(self, username):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT * FROM users WHERE username = ?', (username,))
            return await cursor.fetchone()

    async def insert_user(self, username, bouncer_player_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO users (username, bouncer_player_id, last_updated, ranked_matches, non_ranked_matches)
                VALUES (?, ?, ?, 0, 0)
            ''', (username, bouncer_player_id, int(time.time())))
            await db.commit()

    async def update_user_matches(self, username, ranked_increment, non_ranked_increment):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE users 
                SET ranked_matches = ranked_matches + ?, 
                    non_ranked_matches = non_ranked_matches + ?, 
                    last_updated = ? 
                WHERE username = ?
            ''', (ranked_increment, non_ranked_increment, int(time.time()), username))
            await db.commit()

    async def mark_match_as_processed(self, match_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO matches (match_id, processed) VALUES (?, 1)
                ON CONFLICT(match_id) DO UPDATE SET processed=1
            ''', (match_id,))
            await db.commit()

    async def is_match_processed(self, match_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT processed FROM matches WHERE match_id = ?', (match_id,))
            result = await cursor.fetchone()
            return result is not None and result[0] == 1

    async def update_score(self, username, score):
        async with aiosqlite.connect(self.db_path) as db:
            user = await self.get_user(username)
            if user:
                user_id = user[0]
                await db.execute('''
                    INSERT INTO scores (user_id, total_score) 
                    VALUES (?, ?) 
                    ON CONFLICT(user_id) DO UPDATE SET total_score=total_score + ?
                ''', (user_id, score, score))
                await db.commit()

    async def get_user_score(self, username):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT s.total_score 
                FROM scores s
                JOIN users u ON s.user_id = u.id
                WHERE u.username = ?
            ''', (username,))
            result = await cursor.fetchone()
            return result[0] if result else 0

    async def get_leaderboard(self, limit=10):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT u.username, s.total_score, u.ranked_matches, u.non_ranked_matches 
                FROM scores s
                JOIN users u ON s.user_id = u.id
                ORDER BY s.total_score DESC
                LIMIT ?
            ''', (limit,))
            return await cursor.fetchall()
