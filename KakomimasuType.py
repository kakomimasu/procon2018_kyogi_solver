from dataclasses import dataclass
from enum import Enum
from typing import List

class KakomimasuActionType(Enum):
    PUT = 1
    NONE = 2
    MOVE = 3
    REMOVE = 4

class KakomimasuActionResult(Enum):
  SUCCESS = 0
  CONFLICT = 1
  REVERT = 2
  ERR_ONLY_ONE_TURN = 3
  ERR_ILLEGAL_AGENT = 4
  ERR_ILLEGAL_ACTION = 5

@dataclass
class KakomimasuAction():
    agentId: int
    type: KakomimasuActionType
    x: int
    y: int
    res: KakomimasuActionResult

@dataclass
class KakomimasuPoint():
    areaPoint: int
    wallPoint: int

@dataclass
class KakomimasuGamePlayer():
    point: KakomimasuPoint
    actions: List[KakomimasuAction]

class KakomimasuPlayerType(Enum):
    ACCOUNT = 'account'
    GUEST = 'guest'

@dataclass
class KakomimasuPlayerAgent():
    x: int
    y: int

@dataclass
class KakomimasuPlayer():
    id: str
    agents: List[KakomimasuPlayerAgent]
    point: KakomimasuPoint
    type: KakomimasuPlayerType

class KakomimasuGameType(Enum):
    NORMAL = 'normal'
    SELF = 'self'
    PERSONAL = 'personal'

class KakomimasuGameStatus(Enum):
    FREE = 'free'
    READY = 'ready'
    GAMING = 'gaming'
    ENDED = 'ended'

class KakomimasuTileType(Enum):
    AREA = 0
    WALL = 1

@dataclass
class KakomimasuTile():
   type: KakomimasuTileType
   player: int

@dataclass
class KakomimasuField():
    width: int
    height: int
    points: List[int]
    tiles: List[KakomimasuTile]

@dataclass
class KakomimasuGame():
    id: str
    status: KakomimasuGameStatus
    turn: int
    totalTurn: int
    nPlayer: int
    nAgent: int
    field: KakomimasuField
    players: List[KakomimasuPlayer]
    log: List[List[KakomimasuGamePlayer]]
    name: str
    startedAtUnixTime: int
    reservedUsers: List[str]
    type: KakomimasuGameType
    operationSec: int
    transitionSec: int
