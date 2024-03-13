// だいたい点数の高い順にデタラメに置き、デタラメに動くアルゴリズム
import { ActionPost, KakomimasuClient } from "./KakomimasuClient.ts";
import { DIR, Pnt, rnd, sortByPoint } from "./client_util.ts";

export const client = new KakomimasuClient({ name: "MLくん", spec: "", aiName: "a1", aiBoard: "A-1", nAgent: 2 });
const pntall: Pnt[] = [];

client.oninit = async (boardPoints, agentCount, totalTurn) => {
  const formData = new FormData();
  formData.append("board_points", JSON.stringify(boardPoints));
  formData.append("agent_count", agentCount.toString());
  formData.append("total_turn", totalTurn.toString());
  await fetch("http://localhost:8000/oninit", {
    method: "POST",
    body: formData
  });

  const w = boardPoints[0].length;
  const h = boardPoints.length;

  // ポイントの高い順ソート
  for (let i = 0; i < h; i++) {
    for (let j = 0; j < w; j++) {
      pntall.push({ x: j, y: i, point: boardPoints[i][j] });
    }
  }
  sortByPoint(pntall);
};

client.onturn = async (field, playerNumber, agents, turn) => {
  // Python側で思考
  const formData = new FormData();
  formData.append("field_str", JSON.stringify(field));
  formData.append("player_number", playerNumber.toString());
  formData.append("agents", JSON.stringify(agents));
  formData.append("turn", turn.toString());
  const resp = await fetch("http://localhost:8000/onturn", {
    method: "POST",
    body: formData
  });

  const hands = await resp.json();
  console.log("hands: ", hands);

  const actions: ActionPost[] = [];
  const offset = rnd(agents.length);
  for (let i = 0; i < agents.length; i++) {
    const agent = agents[i];
    if (agent.x === -1) {
      const p = pntall[i + offset];
      actions.push({
        agentId: i,
        type: "PUT",
        x: p.x,
        y: p.y,
      });
    } else {
      actions.push({
        agentId: i,
        type: "MOVE",
        x: hands[i].x,
        y: hands[i].y
      });
    }
  }
  console.log("actions", actions);
  return actions;
};

await client.match();
