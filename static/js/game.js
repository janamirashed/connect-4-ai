// game.js — connect 4 frontend controller

const ROWS = 6;
const COLS = 7;
const TOTAL_SLOTS = ROWS * COLS;

const EMPTY = 0;
const HUMAN = 1;
const AI = 2;

let grid = Array.from({ length: ROWS }, () => Array(COLS).fill(EMPTY));
let columnHeights = Array(COLS).fill(0);
let movesCount = 0;
let lastMove = { row: -1, col: -1 };
let moveHistory = [];
let isGameOver = false;
let isAiThinking = false;

// dom elements
const boardEl = document.getElementById("board");
const hoverTrackEl = document.getElementById("hover-track");
const statHumanScore = document.getElementById("stat-human-score");
const statAiScore = document.getElementById("stat-ai-score");
const turnMarker = document.getElementById("turn-marker");
const turnLabel = document.getElementById("turn-label");
const turnSub = document.getElementById("turn-sub");
const historyList = document.getElementById("history-list");

// metrics & inputs
const depthInputEl = document.getElementById("depth-input");
const statNodes = document.getElementById("stat-nodes");
const statTime = document.getElementById("stat-time");
const statMove = document.getElementById("stat-move");
const statValue = document.getElementById("stat-value");

// buttons & tree
const btnRestart = document.getElementById("btn-restart");
const treeContainer = document.getElementById("tree-container");
const btnToggleTree = document.getElementById("btn-toggle-tree");

// initialize hover track and board grid
function initBoard() {
  hoverTrackEl.innerHTML = "";
  boardEl.innerHTML = "";

  // 7 hover drop zones
  for (let c = 0; c < COLS; c++) {
    const zone = document.createElement("div");
    zone.className = "hover-col-zone";
    zone.dataset.col = c;

    const marker = document.createElement("div");
    marker.className = "drop-marker";
    marker.innerHTML = `
      <svg width="34" height="32" viewBox="0 0 38 36" fill="none">
        <path d="M19 32L5 12C3 9 5 5 9 5H29C33 5 35 9 33 12L19 32Z" fill="#FD6687" stroke="#000" stroke-width="3"/>
      </svg>
    `;
    zone.appendChild(marker);

    zone.addEventListener("click", () => handleColumnClick(c));
    hoverTrackEl.appendChild(zone);
  }

  // 42 circular slots
  for (let r = ROWS - 1; r >= 0; r--) {
    for (let c = 0; c < COLS; c++) {
      const cell = document.createElement("div");
      cell.className = "cell";
      cell.dataset.row = r;
      cell.dataset.col = c;
      cell.addEventListener("click", () => handleColumnClick(c));
      boardEl.appendChild(cell);
    }
  }
}

// render board pieces
function renderBoard(animatedRow = -1, animatedCol = -1) {
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const cell = boardEl.querySelector(`[data-row="${r}"][data-col="${c}"]`);
      if (!cell) continue;

      cell.className = "cell";
      const val = grid[r][c];

      if (val === HUMAN) {
        cell.classList.add("human");
      } else if (val === AI) {
        cell.classList.add("ai");
      }

      if (r === lastMove.row && c === lastMove.col) {
        cell.classList.add("last-move");
      }

      if (r === animatedRow && c === animatedCol) {
        cell.classList.add("drop-anim");
      }
    }
  }
}

// record move in history list
function recordHistory(player, row, col) {
  lastMove = { row, col };
  moveHistory.push({ player, row, col });

  if (historyList) {
    if (moveHistory.length === 1) historyList.innerHTML = "";
    const item = document.createElement("div");
    item.className = "history-item";

    const dot = document.createElement("span");
    dot.className = `history-dot ${player === HUMAN ? "red" : "yellow"}`;
    item.appendChild(dot);

    const txt = document.createElement("span");
    txt.textContent = `${player === HUMAN ? "P1" : "CPU"} -> Col ${col + 1} (Row ${row + 1})`;
    item.appendChild(txt);

    historyList.prepend(item);
  }
}

// handle column click by human player
async function handleColumnClick(col) {
  if (isGameOver || isAiThinking) return;
  if (columnHeights[col] >= ROWS) return; // column full

  // 1. drop human piece
  const row = columnHeights[col];
  grid[row][col] = HUMAN;
  columnHeights[col]++;
  movesCount++;

  recordHistory(HUMAN, row, col);
  renderBoard(row, col);
  updateScores();

  // send human move to backend
  try {
    await fetch("/api/human-move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ col })
    });
  } catch (err) {}

  if (movesCount >= TOTAL_SLOTS) {
    endGame();
    return;
  }

  // 2. switch turn to ai
  triggerAiMove();
}

// trigger ai move
async function triggerAiMove() {
  isAiThinking = true;
  updateTurnMarker(AI);

  const depthK = parseInt(depthInputEl.value) || 4;
  const startTime = performance.now();

  try {
    const res = await fetch("/api/ai-move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ k: depthK })
    });
    const data = await res.json();

    if (data && data.success) {
      const col = data.col;
      const row = columnHeights[col];
      grid[row][col] = AI;
      columnHeights[col]++;
      movesCount++;

      recordHistory(AI, row, col);
      renderBoard(row, col);
      updateScores();

      statNodes.textContent = data.nodes_expanded ? data.nodes_expanded.toLocaleString() : "—";
      statTime.textContent = data.time_taken ? `${data.time_taken.toFixed(3)}s` : `${((performance.now() - startTime) / 1000).toFixed(3)}s`;
      statMove.textContent = `Col ${col}`;
      statValue.textContent = data.minimax_value !== undefined ? data.minimax_value : "—";

      if (data.tree) renderTree(data.tree);
    } else {
      fallbackMove();
    }
  } catch (e) {
    fallbackMove();
  } finally {
    isAiThinking = false;
    if (movesCount >= TOTAL_SLOTS) {
      endGame();
    } else {
      updateTurnMarker(HUMAN);
    }
  }
}

// client-side fallback move while backend minimax is skeleton
function fallbackMove() {
  const validCols = [];
  for (let c = 0; c < COLS; c++) {
    if (columnHeights[c] < ROWS) validCols.push(c);
  }
  if (validCols.length === 0) return;

  const center = Math.floor(COLS / 2);
  validCols.sort((a, b) => Math.abs(a - center) - Math.abs(b - center));
  const col = validCols[0];

  const row = columnHeights[col];
  grid[row][col] = AI;
  columnHeights[col]++;
  movesCount++;

  recordHistory(AI, row, col);
  renderBoard(row, col);
  updateScores();
  statMove.textContent = `Col ${col}`;
}

// count 4-in-a-row sequences
function countFours(player) {
  let count = 0;
  // horizontal
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS - 3; c++) {
      if (grid[r][c] === player && grid[r][c+1] === player && grid[r][c+2] === player && grid[r][c+3] === player) count++;
    }
  }
  // vertical
  for (let r = 0; r < ROWS - 3; r++) {
    for (let c = 0; c < COLS; c++) {
      if (grid[r][c] === player && grid[r+1][c] === player && grid[r+2][c] === player && grid[r+3][c] === player) count++;
    }
  }
  // diagonal /
  for (let r = 0; r < ROWS - 3; r++) {
    for (let c = 0; c < COLS - 3; c++) {
      if (grid[r][c] === player && grid[r+1][c+1] === player && grid[r+2][c+2] === player && grid[r+3][c+3] === player) count++;
    }
  }
  // diagonal \
  for (let r = 3; r < ROWS; r++) {
    for (let c = 0; c < COLS - 3; c++) {
      if (grid[r][c] === player && grid[r-1][c+1] === player && grid[r-2][c+2] === player && grid[r-3][c+3] === player) count++;
    }
  }
  return count;
}

// update scores on player cards
function updateScores() {
  const hScore = countFours(HUMAN);
  const aScore = countFours(AI);
  statHumanScore.textContent = hScore;
  statAiScore.textContent = aScore;
}

// update turn marker banner
function updateTurnMarker(player) {
  const remaining = TOTAL_SLOTS - movesCount;

  if (player === HUMAN) {
    turnMarker.className = "turn-marker turn-human";
    turnLabel.textContent = "PLAYER 1'S TURN";
    turnSub.textContent = `${remaining} LEFT`;
  } else {
    turnMarker.className = "turn-marker turn-ai";
    turnLabel.textContent = "CPU'S TURN";
    turnSub.textContent = "THINKING...";
  }
}

// end game when all 42 slots are filled
function endGame() {
  isGameOver = true;
  const hScore = countFours(HUMAN);
  const aScore = countFours(AI);

  turnMarker.className = "turn-marker";
  if (hScore > aScore) {
    turnMarker.classList.add("turn-human");
    turnLabel.textContent = "YOU WIN!";
    turnSub.textContent = `${hScore} - ${aScore}`;
  } else if (aScore > hScore) {
    turnMarker.classList.add("turn-ai");
    turnLabel.textContent = "CPU WINS!";
    turnSub.textContent = `${aScore} - ${hScore}`;
  } else {
    turnMarker.style.backgroundColor = "#e2e8f0";
    turnLabel.textContent = "IT'S A TIE!";
    turnSub.textContent = `${hScore} - ${aScore}`;
  }
}

// reset game
async function resetGame() {
  grid = Array.from({ length: ROWS }, () => Array(COLS).fill(EMPTY));
  columnHeights = Array(COLS).fill(0);
  movesCount = 0;
  lastMove = { row: -1, col: -1 };
  moveHistory = [];
  isGameOver = false;
  isAiThinking = false;

  renderBoard();
  updateScores();
  updateTurnMarker(HUMAN);

  statNodes.textContent = "—";
  statTime.textContent = "—";
  statMove.textContent = "—";
  statValue.textContent = "—";
  treeContainer.innerHTML = '<span class="muted">No tree loaded yet. Drop a piece to trigger AI search!</span>';
  if (historyList) {
    historyList.innerHTML = '<span class="muted">No moves yet. Click any column to begin!</span>';
  }

  const depthK = parseInt(depthInputEl.value) || 4;
  try {
    await fetch("/api/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rows: ROWS, cols: COLS, k: depthK })
    });
  } catch (e) {}
}

// render minimax search tree in tree box
function renderTree(node) {
  if (!node) return;
  treeContainer.innerHTML = "";

  function createNode(n) {
    const item = document.createElement("div");
    item.className = "tree-node-item";

    const card = document.createElement("div");
    card.className = "tree-node-card";

    const badge = document.createElement("span");
    badge.className = `tree-badge ${n.pruned ? "pruned" : n.player_type.toLowerCase()}`;
    badge.textContent = n.pruned ? "PRUNED" : n.player_type;
    card.appendChild(badge);

    if (n.move_col !== null && n.move_col !== undefined) {
      const colSpan = document.createElement("span");
      colSpan.textContent = `C${n.move_col}`;
      card.appendChild(colSpan);
    }

    if (n.minimax_value !== null && n.minimax_value !== undefined) {
      const valSpan = document.createElement("span");
      valSpan.textContent = `v:${n.minimax_value}`;
      card.appendChild(valSpan);
    }

    item.appendChild(card);

    if (n.children && n.children.length > 0) {
      const childrenDiv = document.createElement("div");
      childrenDiv.className = "tree-children";
      card.addEventListener("click", () => childrenDiv.classList.toggle("collapsed"));
      n.children.forEach(c => childrenDiv.appendChild(createNode(c)));
      item.appendChild(childrenDiv);
    }
    return item;
  }

  treeContainer.appendChild(createNode(node));
}

btnRestart.addEventListener("click", resetGame);

btnToggleTree.addEventListener("click", () => {
  const children = treeContainer.querySelectorAll(".tree-children");
  const isAnyOpen = Array.from(children).some(c => !c.classList.contains("collapsed"));
  children.forEach(c => {
    if (isAnyOpen) c.classList.add("collapsed");
    else c.classList.remove("collapsed");
  });
  btnToggleTree.textContent = isAnyOpen ? "EXPAND ALL" : "COLLAPSE ALL";
});

// initial setup
initBoard();
resetGame();
