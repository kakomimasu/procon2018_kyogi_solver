import socket
import game
import solver
import json
from game import *
from fastapi import FastAPI, Form, Request
import numpy as np
import time

app = FastAPI()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    print("Time took to process the request and return response is {} sec".format(time.time() - start_time))
    return response

# field = game.field()

@app.post("/oninit")
async def oninit(
    board_points: str = Form(),
    total_turn: int = Form(),
    agent_count: int = Form()
):
    pass
    # print("board points", board_points)
    # print("total turn", total_turn)
    # print("agent count", agent_count)
    # field.clear()

@app.post("/onturn")
async def onturn(
    field_str: str = Form(),
    player_number: int = Form(),
    agents: str = Form(),
    turn: int = Form()
):
    # print("field", field)
    # print("player number", player_number)
    # print("agents", agents)
    # print("turn", turn)

    fieldObj = json.loads(field_str)
    agentObj = json.loads(agents)
    print(field_str)
    field2 = field()

    # ボードの高さと幅
    field2.width = len(fieldObj[0])
    field2.height = len(fieldObj)

    # 自分のエージェントの位置
    field2.own_a1 = {
        "x": 0,
        "y": 0
    }
    field2.own_a1["x"] = int(agentObj[0]["x"])
    field2.own_a1["y"] = int(agentObj[0]["y"])
    field2.own_a2 = {
        "x": 0,
        "y": 0
    }
    field2.own_a2["x"] = int(agentObj[1]["x"])
    field2.own_a2["y"] = int(agentObj[1]["y"])

    # 相手のエージェントの位置
    agent_no = 0
    field2.opponent_a1 = {
        "x": 0,
        "y": 0
    }
    field2.opponent_a2 = {
        "x": 0,
        "y": 0
    }
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

    field2.print_field()
    buf = solver.solve2(field2)
    return buf

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)