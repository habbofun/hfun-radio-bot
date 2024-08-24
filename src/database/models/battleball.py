from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str
    total_score: int
    ranked_matches: int
    non_ranked_matches: int


class Match(BaseModel):
    match_id: str
    user_id: int
    game_score: int
    ranked: bool
