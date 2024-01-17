import socket
import game
import solver
import json
import kakomimasu_py
from fastapi import FastAPI

print(kakomimasu_py.Game)

app = FastAPI()

# field = game.field()

@app.get("/oninit")
async def oninit(board_points: str, total_turn: int, agent_count: int):
    print("board points", board_points)
    print("total turn", total_turn)
    print("agent count", agent_count)
    # field.clear()

@app.get("/onturn")
async def onturn(field: str, player_number: int, agents: str, turn: int):
    print("field", field)
    print("player number", player_number)
    print("agents", agents)
    print("turn", turn)

    # hand = solver.solve(field)
    hand = "a"
    return { "data": hand }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
