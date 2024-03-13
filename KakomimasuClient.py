from dataclasses import dataclass
from typing import List
from KakomimasuType import KakomimasuGame, KakomimasuField

@dataclass
class KakomimasuClient():
    name: str
    spec: str
    bearerToken: str
    aiName: str
    aiBoard: str
    gameId: str
    pic: str
    pno: int
    gameInfo: KakomimasuGame
    field: List[List[KakomimasuField]]
    log: List[KakomimasuGame]
