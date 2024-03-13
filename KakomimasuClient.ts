import {
  type ActionMatchReq,
  type ApiRes,
  default as ApiClient,
  type Game,
  type JoinAiMatchReq,
  type JoinMatchReqBase,
  type JoinMatchRes,
  // } from "../client-js/deno/mod.ts";
} from "https://raw.githubusercontent.com/kakomimasu/client-js/v1.0.0-beta.13/deno/mod.ts";

function sleep(msec: number) {
  return new Promise<void>((resolve) => {
    setTimeout(() => resolve(), msec);
  });
}

function diffTime(unixTime: number) {
  console.log(new Date(), unixTime, new Date(unixTime * 1000));
  const dt = unixTime * 1000 - new Date().getTime();
  console.log("diffTime", dt);
  return dt;
}

type Field = {
  type: 0 | 1;
  pid: number | null;
  point: number;
  x: number;
  y: number;
  agentPid: number;
};

type AgentPos = {
  x: number;
  y: number;
};

class KakomimasuClient {
  private name?: string;
  private spec?: string;
  private bearerToken?: string;
  private aiName?: JoinAiMatchReq["aiName"];
  private aiBoard?: string;
  private gameId?: string;
  private pic?: string;
  private pno?: number;
  private gameInfo?: Game;
  private field?: Field[][];
  private log?: Game[];
  private nAgent?: number;

  apiClient: ApiClient;

  constructor(
    param:
      & {
        host?: string;
        aiName?: JoinAiMatchReq["aiName"];
        aiBoard?: string;
        gameId?: string;
        nAgent?: number;
      }
      & ({ name: string; spec?: string } | { bearerToken: string }),
  ) {
    if ("bearerToken" in param) {
      this.bearerToken = param.bearerToken;
    } else {
      this.name = param.name;
      this.spec = param.spec;
    }
    if (param.host === undefined) {
      this.apiClient = new ApiClient("https://api.kakomimasu.com");
    } else {
      let host = param.host;
      if (host.endsWith("/")) {
        host = host.substring(0, host.length - 1);
      }
      //setHost(`${host}/api`);
      this.apiClient = new ApiClient(host);
    }
    this.aiName = param.aiName;
    this.aiBoard = param.aiBoard;
    this.gameId = param.gameId;
    this.nAgent = 2;
  }

  async waitMatching() { // GameInfo
    const matchParam: JoinMatchReqBase = {
      spec: this.spec,
    };
    // Bearerがない場合はゲストで参加
    if (!this.bearerToken) {
      matchParam.guestName = this.name ?? "ゲスト";
    }
    let matchRes: ApiRes<JoinMatchRes>;
    if (this.aiName) {
      // matchParam.useAi = true;
      // matchParam.aiOption = {
      //   aiName: this.useAi,
      //   boardName: this.aiBoard,
      // };
      matchRes = await this.apiClient.joinAiMatch(
        { ...matchParam, aiName: this.aiName, boardName: this.aiBoard, nAgent: this.nAgent },
        `Bearer ${this.bearerToken}`,
      );
    } else if (this.gameId) {
      // matchParam.gameId = this.gameId;
      matchRes = await this.apiClient.joinGameIdMatch(
        this.gameId,
        matchParam,
        `Bearer ${this.bearerToken}`,
      );
    } else {
      //console.log(matchParam);
      matchRes = await this.apiClient.joinFreeMatch(
        matchParam,
        `Bearer ${this.bearerToken}`,
      );
    }
    //console.log(MatchRes);
    if (matchRes.success) {
      const matchGame = matchRes.data;
      this.pic = matchRes.data.pic;
      this.gameId = matchGame.gameId;
      this.pno = matchGame.index;
      console.log("playerid", matchGame, this.pno);
    } else {
      console.log(matchRes.data);
      throw Error("Match Error");
    }
    do {
      const gameRes = await this.apiClient.getMatch(this.gameId);
      if (gameRes.success) this.gameInfo = gameRes.data;
      else throw Error("Get Match Error");
      await sleep(100);
    } while (this.gameInfo.startedAtUnixTime === null);

    console.log(this.gameInfo);
    console.log(
      "ゲーム開始時間：",
      new Date(this.gameInfo.startedAtUnixTime * 1000).toLocaleString("ja-JP"),
    );
    return this.gameInfo;
  }

  getPlayerNumber() {
    return this.pno;
  }

  getAgentCount() {
    if (this.gameInfo?.players && this.pno !== undefined) {
      return this.gameInfo.players[this.pno].agents.length;
    }
  }

  getPoints() {
    if (!this.gameInfo?.field) {
      return undefined;
    }
    const w = this.gameInfo.field.width;
    const h = this.gameInfo.field.height;
    const p = this.gameInfo.field.points;
    const res = [];
    for (let i = 0; i < h; i++) {
      const row = [];
      for (let j = 0; j < w; j++) {
        row.push(p[i * w + j]);
      }
      res.push(row);
    }
    return res;
  }

  _makeField() {
    if (!this.gameInfo?.field) {
      return;
    }
    const w = this.gameInfo.field.width;
    const h = this.gameInfo.field.height;
    const p = this.gameInfo.field.points;
    const res = [];
    const tiles = this.gameInfo.field.tiles;
    if (!tiles) {
      return;
    }
    for (let i = 0; i < h; i++) {
      const row = [];
      for (let j = 0; j < w; j++) {
        const idx = i * w + j;
        const point = p[idx];
        const type = tiles[idx].type;
        const pid = tiles[idx].player;
        row.push({ type, pid, point, x: j, y: i, agentPid: -1 });
      }
      res.push(row);
    }
    this.field = res;
  }

  _updateField() {
    if (!this.gameInfo?.field || !this.field) {
      return;
    }
    const w = this.gameInfo.field.width;
    const h = this.gameInfo.field.height;
    const tiles = this.gameInfo.field.tiles;
    if (!tiles) {
      return;
    }

    const agentXYs: Record<string, number> = {};
    for (let i = 0; i < this.gameInfo.players.length; i++) {
      const player = this.gameInfo.players[i];
      for (const agent of player.agents) {
        if (agent.x != -1) {
          agentXYs[agent.x + "," + agent.y] = i;
        }
      }
    }

    for (let i = 0; i < h; i++) {
      for (let j = 0; j < w; j++) {
        const f = this.field[i][j];
        const idx = i * w + j;
        f.type = tiles[idx].type;
        f.pid = tiles[idx].player;
        const agentPid = agentXYs[j + "," + i];
        f.agentPid = (agentPid != undefined) ? agentPid : -1;
      }
    }
  }

  getField() { // after start
    return this.field;
  }

  async waitStart() { // GameInfo
    if (!this.gameInfo || !this.gameInfo.startedAtUnixTime || !this.gameId) {
      return;
    }
    await sleep(diffTime(this.gameInfo.startedAtUnixTime));
    const res = await this.apiClient.getMatch(this.gameId);
    if (res.success) this.gameInfo = res.data;
    else {
      console.error(res.data);
      throw Error("Get Match Error");
    }
    console.log(this.gameInfo);
    this.log = [this.gameInfo];
    console.log("totalTurn", this.gameInfo.totalTurn);
    this._makeField();
    return this.gameInfo;
  }

  async setActions(actions: ActionMatchReq["actions"]) { // void
    if (!this.gameId || !this.pic) {
      return;
    }
    const res = await this.apiClient.setAction(
      this.gameId,
      { actions },
      this.pic,
    );
    //console.log("setActions", res);
    if (res.success === false) {
      console.error(res.data);
      throw Error("Set Action Error");
    }
  }

  async waitNextTurn() { // GameInfo? (null if end)
    if (!this.log || !this.gameInfo || !this.gameId) {
      return;
    }
    if (this.gameInfo.startedAtUnixTime === null) return;
    const nextTurnUnixTime = this.gameInfo.startedAtUnixTime +
      (this.gameInfo.operationSec + this.gameInfo.transitionSec) *
        this.gameInfo.turn;
    console.log("nextTurnUnixTime", nextTurnUnixTime);
    await sleep(diffTime(nextTurnUnixTime));

    for (;;) {
      const res = await this.apiClient.getMatch(this.gameId);
      
      console.log("waitNextTurn")
      if (res.success) {
        console.log("waitNextTurn turn:",res.data.turn)
        this.gameInfo = res.data;
        break;
      }
      await sleep(100);
    }

    this.log.push(this.gameInfo);
    console.log("turn", this.gameInfo.turn);
    this._updateField();
    if (this.gameInfo.status === "gaming") return this.gameInfo;
    else return null;
  }

  public oninit: (
    boardPoints: number[][],
    agentCount: number,
    totalTurn: number,
  ) => void = async () => {};
  public onturn: (
    field: Field[][],
    playerNumber: number,
    agents: AgentPos[],
    turn: number,
  ) => ActionMatchReq["actions"] = async () => {
    return [];
  };

  async match() {
    console.log("match start");
    let info: Game | null | undefined = await this.waitMatching();
    const ac = this.getAgentCount();
    const points = this.getPoints();
    if (ac === undefined || points === undefined) {
      return;
    }
    await this.oninit(
      points,
      ac,
      info.totalTurn,
    );
    info = await this.waitStart();
    while (info) {
      const field = this.getField();
      const pn = this.getPlayerNumber();
      if (field && pn !== undefined) {
        const actions = await this.onturn(
          field,
          pn,
          info.players[pn].agents,
          info.turn,
        );
        this.setActions(actions);
      }
      info = await this.waitNextTurn();
    }
    console.log("match end");
  }
}

export { KakomimasuClient };
export type ActionPost = ActionMatchReq["actions"][number];
export type { Field };
