import dataclasses
from KakomimasuType import *

@dataclasses.dataclass
class KakomimasuClient():
    name: str
    spec: str
    bearerToken: str
    aiName
    aiBoard: str
    gameId: str
    pic: str
    pno: int
    gameInfo
    field: KakomimasuField
    log



#   private name?: string;
#   private spec?: string;
#   private bearerToken?: string;
#   private aiName?: JoinAiMatchReq["aiName"];
#   private aiBoard?: string;
#   private gameId?: string;
#   private pic?: string;
#   private pno?: number;
#   private gameInfo?: Game;
#   private field?: Field[][];
#   private log?: Game[];
