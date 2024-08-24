from pydantic import BaseModel
from typing import List


class User(BaseModel):
    uniqueId: str
    name: str
    bouncerPlayerId: str


class MatchParticipant(BaseModel):
    gamePlayerId: str
    gameScore: int
    playerPlacement: int
    teamId: int
    teamPlacement: int
    timesStunned: int
    powerUpPickups: int
    powerUpActivations: int
    tilesCleaned: int
    tilesColoured: int
    tilesStolen: int
    tilesLocked: int
    tilesColouredForOpponents: int


class MatchMetadata(BaseModel):
    matchId: str
    participantPlayerIds: List[str]


class MatchInfo(BaseModel):
    gameCreation: int
    gameDuration: int
    gameEnd: int
    gameMode: str
    mapId: int
    ranked: bool
    participants: List[MatchParticipant]


class Match(BaseModel):
    metadata: MatchMetadata
    info: MatchInfo
