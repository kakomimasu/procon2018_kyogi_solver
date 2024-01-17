type Pnt = {
  x: number;
  y: number;
  point: number;
};

function sortByPoint(p: Pnt[]) {
  p.sort((a, b) => b.point - a.point);
}

// 8方向、上から時計回り
const DIR = [
  [0, -1],
  [1, -1],
  [1, 0],
  [1, 1],
  [0, 1],
  [-1, 1],
  [-1, 0],
  [-1, -1],
];

function rnd(n: number) {
  return Math.floor(Math.random() * n); // MT is better
}

export { DIR, rnd, sortByPoint };
export type { Pnt };
