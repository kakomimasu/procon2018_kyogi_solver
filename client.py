import requests, json, time, game, solver
from game import *
import numpy as np
import random

match = requests.post(
    "https://api.kakomimasu.com/v1/matches/ai/players",
    data=json.dumps({
        "aiName": "a1",
        "boardName": "A-1",
        "guestName": "MLくん",
        "nAgent": 2
    }),
    headers={"Content-Type": "application/json"}
).json()

print(match)

pno = match["index"]
game_id = match['gameId']
pic = match["pic"]

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
    
    # print(game_info)

    field1 = game_info["field"]

    w = field1["width"]
    h = field1["height"]
    p = field1["points"]
    fieldObj = []
    tiles = field1["tiles"]
    for i in range(h):
        row = []
        for j in range(w):
            idx = i * w + j
            point = p[idx]
            type = tiles[idx]["type"]
            pid = tiles[idx]["player"]
            row.append({
                "type": type,
                "pid": pid,
                "point": point,
                "x": j,
                "y": i,
                "agentPid": -1
            })
        fieldObj.append(row)

    pntall = []
    for i in range(h):
        for j in range(w):
            pntall.append({
                "x": j,
                "y": i,
                "point": fieldObj[i][j]["point"]
            })
    
    pntall = sorted(pntall, key=lambda p: -p["point"])

    field2 = game.field()
    field2.width = len(fieldObj[0])
    field2.height = len(fieldObj)

    players = game_info["players"]
    agents = players[pno]["agents"]

    # 自分のエージェントの位置
    field2.own_a1 = { "x": 0, "y": 0 }
    field2.own_a1["x"] = agents[0]["x"]
    field2.own_a1["y"] = agents[0]["y"]

    field2.own_a2 = { "x": 0, "y": 0 }
    field2.own_a2["x"] = agents[1]["x"]
    field2.own_a2["y"] = agents[1]["y"]

    # 相手のエージェントの位置
    agent_no = 0
    field2.opponent_a1 = { "x": 0, "y": 0 }
    field2.opponent_a2 = { "x": 0, "y": 0 }

    for y in range(field2.height):
        for x in range(field2.width):
            cell = fieldObj[x][y]
            if cell["agentPid"] == 1:
                if agent_no == 0:
                    field2.opponent_a1["x"] = x
                    field2.opponent_a1["y"] = y
                    agent_no += 1
                elif agent_no == 1:
                    field2.opponent_a2["x"] = x
                    field2.opponent_a2["y"] = y

    # タイルの得点
    field2.value = np.zeros([field2.width, field2.height], dtype=int)
    for y in range(field2.height):
        for x in range(field2.width):
            cell = fieldObj[x][y]
            field2.value[x][y] = cell["point"]

    # 自分の持ってるセル
    field2.own_state = np.zeros([field2.width, field2.height], dtype=int)
    for y in range(field2.height):
        for x in range(field2.width):
            cell = fieldObj[x][y]
            if cell["pid"] == 0:
                field2.own_state[x][y] = EXISTENCE
            else:
                field2.own_state[x][y] = EMPTY

    # 相手の持っているセル
    field2.opponent_state = np.zeros([field2.width, field2.height], dtype=int)
    for y in range(field2.height):
        for x in range(field2.width):
            cell = fieldObj[x][y]
            if cell["pid"] == 1:
                field2.opponent_state[x][y] = EXISTENCE
            else:
                field2.opponent_state[x][y] = EMPTY

    # field2.print_field()

    hands = solver.solve2(field2)
    print("手", hands)

    actions = []
    offset = random.randint(0, len(agents) - 1)
    for i in range(len(agents)):
        agent = agents[i]
        if agent["x"] == -1:
            p = pntall[i + offset]
            actions.append({
                "agentId": i,
                "type": "PUT",
                "x": p["x"],
                "y": p["y"]
            })
        else:
            if hands[i] is not None:
                actions.append({
                    "agentId": i,
                    "type": "MOVE",
                    "x": hands[i]["x"],
                    "y": hands[i]["y"]
                })

    next_turn_unix_time = game_info["startedAtUnixTime"] + game_info["operationSec"] + game_info["transitionSec"] * game_info["turn"]
    wait_time = next_turn_unix_time - time.time()
    if wait_time > 0:
        time.sleep(wait_time)
        
    headers = {
        "Authorization": pic,
        "Content-Type": "application/json"
    }
    actionsBody = {
        "actions": actions
    }
    print("★actions", actions)
    result = requests.patch(f"https://api.kakomimasu.com/v1/matches/{game_id}/actions",headers=headers, json=actionsBody)
