// だいたい点数の高い順にデタラメに置き、デタラメに動くアルゴリズム
import { ActionPost, KakomimasuClient } from "./KakomimasuClient.ts";
import { DIR, Pnt, rnd, sortByPoint } from "./client_util.ts";

export const client = new KakomimasuClient({ name: "AI-1", spec: "", aiName: "a1" });
const pntall: Pnt[] = [];

client.oninit = async (boardPoints, agentCount, totalTurn) => {
  await fetch(`http://localhost:8000/oninit?board_points=${encodeURIComponent(JSON.stringify(boardPoints))}&total_turn=${totalTurn}&agent_count=${agentCount}`);
};

client.onturn = async (field, playerNumber, agents, turn) => {
  // Python側で思考
  const resp = await fetch(`http://localhost:8000/onturn?field=${encodeURIComponent(JSON.stringify(field))}&playerNumber=${playerNumber}&agents=${encodeURIComponent(JSON.stringify(agents))}&turn=${turn}`);
  const json = await resp.json();
  console.log("resp: ", json);

  // ランダムにずらしつつ置けるだけおく
  // 置いたものはランダムに8方向動かす
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
      const [dx, dy] = DIR[rnd(8)];
      actions.push({
        agentId: i,
        type: "MOVE",
        x: agent.x + dx,
        y: agent.y + dy,
      });
    }
  }
  return actions;
};

await client.match();

// Pythonとの通信テスト
// setInterval(async () => {
//   // Python側で思考
//   const formData = new FormData();
//   formData.append("data", "test!");
//   const resp = await fetch("http://localhost:8000/onturn?data=test!");
//   const json = await resp.json();
//   console.log("resp: ", json);
// }, 1000);
