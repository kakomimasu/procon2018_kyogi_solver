import socket
import game
import solver
import json
from fastapi import FastAPI, Form

app = FastAPI()

# field = game.field()

@app.post("/oninit")
async def oninit(
    board_points: str = Form(),
    total_turn: int = Form(),
    agent_count: int = Form()
):
    print("board points", board_points)
    print("total turn", total_turn)
    print("agent count", agent_count)
    # field.clear()

@app.post("/onturn")
async def onturn(
    field: str = Form(),
    player_number: int = Form(),
    agents: str = Form(),
    turn: int = Form()
):
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