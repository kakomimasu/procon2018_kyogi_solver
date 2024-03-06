import dataclasses, field
from enum import Enum
from typing import List


@dataclasses.dataclass
class KakomimasuField():
    width: int
    height: int
    points: List[int] = field(default_factory=list)
    tiles: List[KakomimasuTile] = field(default_factory=list)

@dataclasses.dataclass
class KakomimasuTile():
   type: KakomimasuTileType
   player: int

class KakomimasuTileType(Enum):
    AREA = 0
    WALL = 1

@dataclasses.dataclass
class KakomimasuGame():
    id: str
    status: KakomimasuGameStatus
    turn: int
    totalTurn: int
    nPlayer: int
    nAgent: int
    field: KakomimasuField
    players: List[KakomimasuPlayer] = field(default_factory=list)
    log: List[List[KakomimasuGamePlayer]] = field(default_factory=list)
    name: str
    startedAtUnixTime: int
    reservedUsers: List[str] = field(default_factory=list)
    type: KakomimasuGameType
    operationSec: int
    transitionSec: int

class KakomimasuGameStatus(Enum):
    FREE = 'free'
    READY = 'ready'
    GAMING = 'gaming'
    ENDED = 'ended'

class KakomimasuGameType(Enum):
    NORMAL = 'normal'
    SELF = 'self'
    PERSONAL = 'personal'

@dataclasses.dataclass
class KakomimasuPlayer():
    id: str
    agents: List[KakomimasuPlayerAgent] = field(default_factory=list)
    point: KakomimasuPoint
    type: KakomimasuPlayerType

@dataclasses.dataclass
class KakomimasuPlayerAgent():
    x: int
    y: int

class KakomimasuPlayerType(Enum):
    ACCOUNT = 'account'
    GUEST = 'guest'

@dataclasses.dataclass
class KakomimasuPoint():
    areaPoint: int
    wallPoint: int

@dataclasses.dataclass
class KakomimasuGamePlayer():
    point: KakomimasuPoint
    actions: List[KakomimasuAction] = field(default_factory=list)

@dataclasses.dataclass
class KakomimasuAction():
    agentId: int
    type: KakomimasuActionType
    x: int
    y: int
    res: KakomimasuActionResult

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
