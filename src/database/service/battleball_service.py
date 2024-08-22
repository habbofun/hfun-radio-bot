import time, aiosqlite
from src.helper.singleton import Singleton

@Singleton
class BattleballDatabaseService:
    """
    A class that provides database operations for the Battleball game.

    Attributes:
        db_path (str): The path to the SQLite database file.

    Methods:
        initialize: Initializes the database by creating necessary tables if they don't exist.
        get_user: Retrieves a user from the database based on the username.
        insert_user: Inserts a new user into the database.
        update_user_matches: Updates the number of ranked and non-ranked matches for a user.
        mark_match_as_processed_for_user: Marks a match as processed for a specific user.
        is_match_processed_for_user: Checks if a match has been processed for a specific user.
        update_score: Updates the total score for a user.
        get_user_score: Retrieves the total score of a user.
        get_user_cache: Retrieves cached data for a user.
        get_leaderboard: Retrieves the leaderboard of users based on their total scores.

    """

    def __init__(self, db_path='src/database/storage/battleball.db'):
        """
        Initializes a new instance of the BattleballDatabaseService class.

        Args:
            db_path (str): The path to the SQLite database file. Defaults to 'src/database/storage/battleball.db'.
        """
        self.db_path = db_path

    async def initialize(self):
        """
        Initializes the database by creating necessary tables if they don't exist.
        """
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
                    match_id TEXT PRIMARY KEY
                );
                CREATE TABLE IF NOT EXISTS scores (
                    user_id INTEGER NOT NULL,
                    total_score INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(user_id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
                CREATE TABLE IF NOT EXISTS user_match (
                    user_id INTEGER NOT NULL,
                    match_id TEXT NOT NULL,
                    processed BOOLEAN NOT NULL DEFAULT 0,
                    UNIQUE(user_id, match_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (match_id) REFERENCES matches(match_id)
                );
            ''')
            await db.commit()

    async def get_user(self, username):
        """
        Retrieves a user from the database based on the username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            dict: A dictionary representing the user's data, or None if the user doesn't exist.
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT * FROM users WHERE username = ?', (username,))
            return await cursor.fetchone()

    async def insert_user(self, username, bouncer_player_id):
        """
        Inserts a new user into the database.

        Args:
            username (str): The username of the user to insert.
            bouncer_player_id (str): The bouncer player ID of the user to insert.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO users (username, bouncer_player_id, last_updated, ranked_matches, non_ranked_matches)
                VALUES (?, ?, ?, 0, 0)
            ''', (username, bouncer_player_id, int(time.time())))
            await db.commit()

    async def update_user_matches(self, username, ranked_increment, non_ranked_increment):
        """
        Updates the number of ranked and non-ranked matches for a user.

        Args:
            username (str): The username of the user to update.
            ranked_increment (int): The amount to increment the ranked matches by.
            non_ranked_increment (int): The amount to increment the non-ranked matches by.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE users 
                SET ranked_matches = ranked_matches + ?, 
                    non_ranked_matches = non_ranked_matches + ?, 
                    last_updated = ? 
                WHERE username = ?
            ''', (ranked_increment, non_ranked_increment, int(time.time()), username))
            await db.commit()

    async def mark_match_as_processed_for_user(self, user_id, match_id):
        """
        Marks a match as processed for a specific user.

        Args:
            user_id (int): The ID of the user.
            match_id (str): The ID of the match to mark as processed.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO user_match (user_id, match_id, processed)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, match_id) DO UPDATE SET processed=1
            ''', (user_id, match_id))
            await db.commit()

    async def is_match_processed_for_user(self, user_id, match_id):
        """
        Checks if a match has been processed for a specific user.

        Args:
            user_id (int): The ID of the user.
            match_id (str): The ID of the match to check.

        Returns:
            bool: True if the match has been processed for the user, False otherwise.
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT processed FROM user_match 
                WHERE user_id = ? AND match_id = ?
            ''', (user_id, match_id))
            result = await cursor.fetchone()
            return result is not None and result[0] == 1

    async def update_score(self, username, score):
        """
        Updates the total score for a user.

        Args:
            username (str): The username of the user to update.
            score (int): The score to add to the user's total score.
        """
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
        """
        Retrieves the total score of a user.

        Args:
            username (str): The username of the user to retrieve the score for.

        Returns:
            int: The total score of the user, or 0 if the user doesn't exist.
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT s.total_score 
                FROM scores s
                JOIN users u ON s.user_id = u.id
                WHERE u.username = ?
            ''', (username,))
            result = await cursor.fetchone()
            return result[0] if result else 0

    async def get_user_cache(self, username):
        """
        Retrieves cached data for a user.

        Args:
            username (str): The username of the user.

        Returns:
            dict: A dictionary containing the user's cached score and last update time.
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT total_score, last_updated 
                FROM scores
                JOIN users ON scores.user_id = users.id
                WHERE users.username = ?
            ''', (username,))
            result = await cursor.fetchone()
            return {"total_score": result[0], "last_updated": result[1]} if result else None

    async def get_leaderboard(self, limit=10):
        """
        Retrieves the leaderboard of users based on their total scores.

        Args:
            limit (int): The maximum number of users to retrieve. Defaults to 10.

        Returns:
            list: A list of tuples representing the leaderboard entries. Each tuple contains the username, total score,
                number of ranked matches, and number of non-ranked matches.
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT u.username, s.total_score, u.ranked_matches, u.non_ranked_matches 
                FROM scores s
                JOIN users u ON s.user_id = u.id
                ORDER BY s.total_score DESC
                LIMIT ?
            ''', (limit,))
            return await cursor.fetchall()
