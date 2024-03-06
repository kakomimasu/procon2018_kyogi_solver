import requests, json, time, game, solver
from game import *
import numpy as np

match = requests.post(
    "https://api.kakomimasu.com/v1/matches/ai/players",
    data=json.dumps({
        "aiName": "a1",
        "boardName": "A-1",
        "guestName": "MLくん"
    }),
    headers={"Content-Type": "application/json"}
).json()

print(match)

pno = match["index"]
game_id = match['gameId']

while True:
    game_info = requests.get(f"https://api.kakomimasu.com/v1/matches/{game_id}").json()
    if "startedAtUnixTime" in game_info: break
    time.sleep(0.1)

wait_time = game_info["startedAtUnixTime"] - time.time()
print("ゲーム開始待ち")
time.sleep(wait_time)
print("ゲーム開始！")

while True:
    while True:
        game_info = requests.get(f"https://api.kakomimasu.com/v1/matches/{game_id}").json()
        if "errorCode" not in game_info: break
        time.sleep(0.1)
    
    print(game_info)

    field1 = game_info["field"]

    field2 = game.field()
    field2.width = field1["width"]
    field2.height = field1["height"]

    players = game_info["players"]

    # 自分のエージェントの位置
    field2.own_a1 = { "x": 0, "y": 0 }
    field2.own_a1["x"] = players[pno]["agents"][0]["x"]
    field2.own_a1["y"] = players[pno]["agents"][0]["y"]

    field2.own_a2 = { "x": 0, "y": 0 }
    field2.own_a2["x"] = players[pno]["agents"][1]["x"]
    field2.own_a2["y"] = players[pno]["agents"][1]["y"]

    # 相手のエージェントの位置
    agent_no = 0
    field2.opponent_a1 = { "x": 0, "y": 0 }
    field2.opponent_a2 = { "x": 0, "y": 0 }

    # タイルの得点
    field2.value = np.zeros([field2.width, field2.height], dtype=int)

    # 自分の持ってるセル
    field2.own_state = np.zeros([field2.width, field2.height], dtype=int)

    # 相手の持っているセル
    field2.opponent_state = np.zeros([field2.width, field2.height], dtype=int)

    field2.print_field()

    buf = solver.solve2(field2)
    print("手", buf)

    next_turn_unix_time = game_info["startedAtUnixTime"] + game_info["operationSec"] + game_info["transitionSec"] * game_info["turn"]
    wait_time = next_turn_unix_time - time.time()
    if wait_time > 0:
        time.sleep(wait_time)
