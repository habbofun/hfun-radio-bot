from pydantic import BaseModel

class User(BaseModel):
    discord_id: int
    username: str
    total_score: int = 0
    ranked_matches: int = 0
    non_ranked_matches: int = 0

class Match(BaseModel):
    match_id: str
    user_id: int
    game_score: int
    ranked: bool