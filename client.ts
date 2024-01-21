// だいたい点数の高い順にデタラメに置き、デタラメに動くアルゴリズム
import { ActionPost, KakomimasuClient } from "./KakomimasuClient.ts";
import { DIR, Pnt, rnd, sortByPoint } from "./client_util.ts";

export const client = new KakomimasuClient({ name: "AI-1", spec: "", aiName: "a1" });
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
};

client.onturn = async (field, playerNumber, agents, turn) => {
  // Python側で思考
  const formData = new FormData();
  formData.append("field", JSON.stringify(field));
  formData.append("player_number", playerNumber.toString());
  formData.append("agents", JSON.stringify(agents));
  formData.append("turn", turn.toString());
  const resp = await fetch("http://localhost:8000/onturn", {
    method: "POST",
    body: formData
  });

  const json = await resp.json();
  console.log("resp: ", json);
  return [];
};

await client.match();
