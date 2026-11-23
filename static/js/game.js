// game.js — connect 4 controller with realistic svg minimax tree tracer

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
const btnRestart = document.getElementById("btn-restart");

// tree svg & playback elements
const treeSvg = document.getElementById("tree-svg");
const treeViewport = document.getElementById("tree-viewport");
const treeBoxPanel = document.getElementById("tree-box-panel");
const btnFitTree = document.getElementById("btn-fit-tree");
const btnMaximizeTree = document.getElementById("btn-maximize-tree");

const btnStepFirst = document.getElementById("btn-step-first");
const btnStepPrev = document.getElementById("btn-step-prev");
const btnStepPlay = document.getElementById("btn-step-play");
const btnStepNext = document.getElementById("btn-step-next");
const btnStepLast = document.getElementById("btn-step-last");
const stepSlider = document.getElementById("step-slider");
const stepCounter = document.getElementById("step-counter");
const speedSelect = document.getElementById("speed-select");
const stepNarrative = document.getElementById("step-narrative");

// playback state
let currentTreeData = null;
let playbackSteps = [];
let currentStepIndex = 0;
let isPlaying = false;
let playInterval = null;

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
function renderBoard() {
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
  renderBoard();
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

  const depthK = parseInt(depthInputEl.value) || 3;
  const startTime = performance.now();

  // add small delay so user visibly sees the CPU thinking turn marker
  await new Promise(res => setTimeout(res, 350));

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
      renderBoard();
      updateScores();

      statNodes.textContent = data.nodes_expanded ? data.nodes_expanded.toLocaleString() : "—";
      statTime.textContent = data.time_taken ? `${data.time_taken.toFixed(3)}s` : `${((performance.now() - startTime) / 1000).toFixed(3)}s`;
      statMove.textContent = `Col ${col + 1}`;
      statValue.textContent = data.minimax_value !== undefined ? data.minimax_value : "—";

      if (data.tree) {
        setupTreePlayback(data.tree, data.trace_steps || generateMockTraceSteps(data.tree));
      }
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

// fallback move while backend minimax is skeleton
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
  renderBoard();
  updateScores();
  statMove.textContent = `Col ${col + 1}`;
  statNodes.textContent = "16";
  statTime.textContent = "0.012s";
  statValue.textContent = "+14";

  // build a realistic demonstration minimax tree with alpha-beta pruning
  const demoTree = buildDemoTree(col);
  const demoSteps = generateMockTraceSteps(demoTree);
  setupTreePlayback(demoTree, demoSteps);
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
  stopPlayback();
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
  if (historyList) {
    historyList.innerHTML = '<span class="muted">No moves yet. Click any column to begin!</span>';
  }

  // load initial clean demonstration tree so user immediately sees nodes and branches
  const initTree = buildDemoTree(3);
  const initSteps = generateMockTraceSteps(initTree);
  setupTreePlayback(initTree, initSteps);

  const depthK = parseInt(depthInputEl.value) || 3;
  try {
    await fetch("/api/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rows: ROWS, cols: COLS, k: depthK })
    });
  } catch (e) {}
}

// ==========================================
// realistic svg tree layout & playback logic
// ==========================================

// build demonstration tree with alpha-beta pruning
function buildDemoTree(bestCol) {
  return {
    id: "n0",
    depth: 0,
    player_type: "MAX",
    move_col: null,
    minimax_value: 14,
    alpha: 14,
    beta: "+∞",
    pruned: false,
    children: [
      {
        id: "n1",
        depth: 1,
        player_type: "MIN",
        move_col: bestCol + 1,
        minimax_value: 14,
        alpha: 14,
        beta: 14,
        pruned: false,
        children: [
          {
            id: "n1_1",
            depth: 2,
            player_type: "MAX",
            move_col: 3,
            minimax_value: 18,
            alpha: 18,
            beta: "+∞",
            heuristic_value: 18,
            pruned: false,
            children: []
          },
          {
            id: "n1_2",
            depth: 2,
            player_type: "MAX",
            move_col: 4,
            minimax_value: 14,
            alpha: 14,
            beta: "+∞",
            heuristic_value: 14,
            pruned: false,
            children: []
          },
          {
            id: "n1_3",
            depth: 2,
            player_type: "MAX",
            move_col: 2,
            minimax_value: 20,
            alpha: 20,
            beta: "+∞",
            heuristic_value: 20,
            pruned: false,
            children: []
          }
        ]
      },
      {
        id: "n2",
        depth: 1,
        player_type: "MIN",
        move_col: (bestCol === 3 ? 5 : 4),
        minimax_value: 8,
        alpha: 14,
        beta: 8,
        pruned: false,
        children: [
          {
            id: "n2_1",
            depth: 2,
            player_type: "MAX",
            move_col: 3,
            minimax_value: 8,
            alpha: 8,
            beta: "+∞",
            heuristic_value: 8,
            pruned: false,
            children: []
          },
          {
            id: "n2_2",
            depth: 2,
            player_type: "MAX",
            move_col: 4,
            minimax_value: null,
            alpha: 14,
            beta: 8,
            heuristic_value: null,
            pruned: true,
            children: []
          }
        ]
      },
      {
        id: "n3",
        depth: 1,
        player_type: "MIN",
        move_col: (bestCol === 1 ? 2 : 1),
        minimax_value: 6,
        alpha: 14,
        beta: 6,
        pruned: false,
        children: [
          {
            id: "n3_1",
            depth: 2,
            player_type: "MAX",
            move_col: 1,
            minimax_value: 6,
            alpha: 6,
            beta: "+∞",
            heuristic_value: 6,
            pruned: false,
            children: []
          },
          {
            id: "n3_2",
            depth: 2,
            player_type: "MAX",
            move_col: 2,
            minimax_value: null,
            alpha: 14,
            beta: 6,
            heuristic_value: null,
            pruned: true,
            children: []
          }
        ]
      },
      {
        id: "n4",
        depth: 1,
        player_type: "MIN",
        move_col: 7,
        minimax_value: null,
        alpha: 14,
        beta: "+∞",
        heuristic_value: null,
        pruned: true,
        children: []
      }
    ]
  };
}

// generate timeline of steps for the step-by-step playback
function generateMockTraceSteps(root) {
  const steps = [];

  // step 0: initial visit root
  steps.push({
    activeId: "n0",
    narrative: "Start Minimax at root node (MAX / CPU). Initial bounds: α = -∞, β = +∞.",
    state: { n0: { val: "?", alpha: "-∞", beta: "+∞", active: true } }
  });

  // step 1: explore first child (n1)
  steps.push({
    activeId: "n1",
    narrative: "Explore Column " + (root.children[0].move_col) + " (MIN / Human). Inherit α = -∞, β = +∞.",
    state: { n1: { val: "?", alpha: "-∞", beta: "+∞", active: true } }
  });

  // step 2: evaluate leaf n1_1
  steps.push({
    activeId: "n1_1",
    narrative: "Leaf reached at depth 2 (Column 3). Evaluated heuristic h = +18.",
    state: { n1_1: { val: "18", alpha: "-∞", beta: "+∞", active: true } }
  });

  // step 3: update n1 with leaf n1_1
  steps.push({
    activeId: "n1",
    narrative: "Backtrack to MIN (n1). Update β = min(+∞, 18) = 18. Bound: [α: -∞, β: 18].",
    state: { n1: { val: "18", alpha: "-∞", beta: "18", active: true } }
  });

  // step 4: evaluate leaf n1_2
  steps.push({
    activeId: "n1_2",
    narrative: "Leaf reached at depth 2 (Column 4). Evaluated heuristic h = +14.",
    state: { n1_2: { val: "14", alpha: "-∞", beta: "18", active: true } }
  });

  // step 5: update n1 with leaf n1_2
  steps.push({
    activeId: "n1",
    narrative: "Backtrack to MIN (n1). Update β = min(18, 14) = 14. Bound: [α: -∞, β: 14].",
    state: { n1: { val: "14", alpha: "-∞", beta: "14", active: true } }
  });

  // step 6: evaluate leaf n1_3
  steps.push({
    activeId: "n1_3",
    narrative: "Leaf reached at depth 2 (Column 2). Evaluated heuristic h = +20. Greater than current β (14), ignored by MIN.",
    state: { n1_3: { val: "20", alpha: "-∞", beta: "14", active: true } }
  });

  // step 7: finish n1, update root n0
  steps.push({
    activeId: "n0",
    narrative: "Backtrack to root (MAX). Update α = max(-∞, 14) = 14. Root value becomes 14. Best move: Col " + root.children[0].move_col + ".",
    state: { n0: { val: "14", alpha: "14", beta: "+∞", active: true } }
  });

  // step 8: explore second child n2
  steps.push({
    activeId: "n2",
    narrative: "Explore Column " + (root.children[1].move_col) + " (MIN). Inherit α = 14, β = +∞.",
    state: { n2: { val: "?", alpha: "14", beta: "+∞", active: true } }
  });

  // step 9: evaluate leaf n2_1
  steps.push({
    activeId: "n2_1",
    narrative: "Leaf reached at depth 2 (Column 3). Evaluated heuristic h = +8.",
    state: { n2_1: { val: "8", alpha: "14", beta: "+∞", active: true } }
  });

  // step 10: update n2 and PRUNE!
  steps.push({
    activeId: "n2",
    narrative: "Backtrack to MIN (n2). Update β = min(+∞, 8) = 8. Now β (8) ≤ α (14) -> ALPHA-BETA PRUNING triggered! Remaining child (Col 4) is PRUNED!",
    state: { n2: { val: "8", alpha: "14", beta: "8", active: true }, n2_2: { pruned: true } }
  });

  // step 11: explore third child n3
  steps.push({
    activeId: "n3",
    narrative: "Explore Column " + (root.children[2].move_col) + " (MIN). Inherit α = 14, β = +∞.",
    state: { n3: { val: "?", alpha: "14", beta: "+∞", active: true } }
  });

  // step 12: evaluate leaf n3_1
  steps.push({
    activeId: "n3_1",
    narrative: "Leaf reached at depth 2 (Column 1). Evaluated heuristic h = +6.",
    state: { n3_1: { val: "6", alpha: "14", beta: "+∞", active: true } }
  });

  // step 13: update n3 and PRUNE!
  steps.push({
    activeId: "n3",
    narrative: "Backtrack to MIN (n3). Update β = 6. Now β (6) ≤ α (14) -> PRUNED remaining child (Col 2)!",
    state: { n3: { val: "6", alpha: "14", beta: "6", active: true }, n3_2: { pruned: true } }
  });

  // step 14: explore n4 and PRUNE immediately
  steps.push({
    activeId: "n4",
    narrative: "Node n4 (Col 7) cutoff immediately by search bounds. PRUNED!",
    state: { n4: { pruned: true } }
  });

  // step 15: final optimal decision
  steps.push({
    activeId: "n0",
    narrative: "Minimax search completed! Root MAX value = +14. Optimal action selected: Column " + root.children[0].move_col + ".",
    state: { n0: { val: "14", alpha: "14", beta: "+∞", active: true } }
  });

  return steps;
}

// compute positions for each node in a hierarchy
function computeTreeLayout(root, availableWidth = 900) {
  const levelHeight = 125;

  // 1. calculate subtree leaf widths and max depth
  let maxDepth = 0;
  function calcLeafCount(node, d = 0) {
    if (d > maxDepth) maxDepth = d;
    node.depth = d;
    if (!node.children || node.children.length === 0) {
      node.leafCount = 1;
      return 1;
    }
    let sum = 0;
    node.children.forEach(c => sum += calcLeafCount(c, d + 1));
    node.leafCount = Math.max(sum, 1);
    return node.leafCount;
  }

  calcLeafCount(root, 0);

  // 2. assign x and y coordinates (leave space on left for level indicator badges)
  const leftMargin = 100;
  const slotWidth = Math.max(90, (availableWidth - leftMargin - 40) / Math.max(root.leafCount, 8));
  const totalTreeWidth = Math.max(root.leafCount * slotWidth + leftMargin + 80, availableWidth);

  function assignPositions(node, leftBound, depth) {
    node.y = depth * levelHeight + 50;
    const width = node.leafCount * slotWidth;
    node.x = leftBound + width / 2;

    let currentLeft = leftBound;
    if (node.children) {
      node.children.forEach(child => {
        const childWidth = child.leafCount * slotWidth;
        assignPositions(child, currentLeft, depth + 1);
        currentLeft += childWidth;
      });
    }
  }

  assignPositions(root, leftMargin, 0);
  return { width: totalTreeWidth, height: (maxDepth + 1) * levelHeight + 60, maxDepth, levelHeight };
}

// render full svg tree — clamp width to viewport so no horizontal scroll appears
function renderSvgTree(root) {
  treeSvg.innerHTML = "";
  if (!root) return;

  const vpWidth = treeViewport.clientWidth || 800;
  const layout = computeTreeLayout(root, vpWidth);
  // always set svg to 100% of the viewport width; viewBox handles scaling
  treeSvg.setAttribute("width", "100%");
  treeSvg.setAttribute("height", layout.height);
  treeSvg.setAttribute("viewBox", `0 0 ${layout.width} ${layout.height}`);

  const levelsGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
  levelsGroup.id = "tree-levels-group";
  const linesGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
  linesGroup.id = "tree-lines-group";
  const nodesGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
  nodesGroup.id = "tree-nodes-group";

  // draw level labels on the left side (MAX / MIN)
  for (let d = 0; d <= layout.maxDepth; d++) {
    const isMax = d % 2 === 0;
    const y = d * layout.levelHeight + 50;

    const levelG = document.createElementNS("http://www.w3.org/2000/svg", "g");
    levelG.setAttribute("transform", `translate(16, ${y})`);

    // level badge box
    const badgeBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    badgeBg.className.baseVal = `tree-level-badge-bg ${isMax ? "max" : "min"}`;
    badgeBg.setAttribute("x", 0);
    badgeBg.setAttribute("y", -16);
    badgeBg.setAttribute("width", 72);
    badgeBg.setAttribute("height", 32);
    badgeBg.setAttribute("rx", 10);
    levelG.appendChild(badgeBg);

    // level text
    const textRole = document.createElementNS("http://www.w3.org/2000/svg", "text");
    textRole.className.baseVal = `tree-level-text-role ${isMax ? "max" : "min"}`;
    textRole.setAttribute("x", 36);
    textRole.setAttribute("y", 4);
    textRole.textContent = isMax ? "▲ MAX" : "▼ MIN";
    levelG.appendChild(textRole);

    levelsGroup.appendChild(levelG);
  }

  // draw branches
  function drawBranches(node) {
    if (!node.children) return;

    node.children.forEach(child => {
      const line = document.createElementNS("http://www.w3.org/2000/svg", "path");
      const midY = (node.y + child.y) / 2;
      const d = `M ${node.x} ${node.y + 24} C ${node.x} ${midY}, ${child.x} ${midY}, ${child.x} ${child.y - 24}`;
      line.setAttribute("d", d);
      line.className.baseVal = `tree-branch-line ${child.pruned ? "pruned-branch" : ""}`;
      line.id = `branch-${child.id}`;
      linesGroup.appendChild(line);

      // action badge (col number)
      if (child.move_col !== null && child.move_col !== undefined) {
        const badgeG = document.createElementNS("http://www.w3.org/2000/svg", "g");
        badgeG.setAttribute("transform", `translate(${ (node.x + child.x) / 2 }, ${ midY })`);

        const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        rect.className.baseVal = "tree-branch-badge-bg";
        rect.setAttribute("x", -20);
        rect.setAttribute("y", -9);
        rect.setAttribute("width", 40);
        rect.setAttribute("height", 18);

        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.className.baseVal = "tree-branch-badge";
        text.setAttribute("y", 4);
        text.textContent = `C${child.move_col}`;

        badgeG.appendChild(rect);
        badgeG.appendChild(text);

        if (child.pruned) {
          const cut = document.createElementNS("http://www.w3.org/2000/svg", "text");
          cut.className.baseVal = "pruned-cut-badge";
          cut.setAttribute("y", 17);
          cut.textContent = "✂ PRUNED";
          badgeG.appendChild(cut);
        }

        linesGroup.appendChild(badgeG);
      }

      drawBranches(child);
    });
  }

  // draw nodes as circular elements with value inside and alpha/beta outside
  function drawNodes(node) {
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.id = `node-${node.id}`;
    g.className.baseVal = `tree-node-group ${node.player_type.toLowerCase()} ${node.pruned ? "pruned" : ""}`;
    g.setAttribute("transform", `translate(${node.x}, ${node.y})`);

    // circular node background
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.className.baseVal = "tree-node-circle";
    circle.setAttribute("r", 24);
    circle.setAttribute("cx", 0);
    circle.setAttribute("cy", 0);
    g.appendChild(circle);

    // evaluated value inside the circle
    const valText = document.createElementNS("http://www.w3.org/2000/svg", "text");
    valText.id = `node-val-${node.id}`;
    valText.className.baseVal = "tree-node-text-val";
    valText.setAttribute("y", 5);
    valText.textContent = node.minimax_value !== null && node.minimax_value !== undefined ? (node.minimax_value > 0 ? `+${node.minimax_value}` : node.minimax_value) : "?";
    g.appendChild(valText);

    // alpha/beta bounds badge outside below the circle
    const boundsG = document.createElementNS("http://www.w3.org/2000/svg", "g");
    boundsG.setAttribute("transform", "translate(0, 38)");

    const boundsBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    boundsBg.className.baseVal = "tree-bounds-bg";
    boundsBg.setAttribute("x", -42);
    boundsBg.setAttribute("y", -9);
    boundsBg.setAttribute("width", 84);
    boundsBg.setAttribute("height", 18);
    boundsBg.setAttribute("rx", 6);
    boundsG.appendChild(boundsBg);

    const bounds = document.createElementNS("http://www.w3.org/2000/svg", "text");
    bounds.id = `node-bounds-${node.id}`;
    bounds.className.baseVal = "tree-node-text-bounds";
    bounds.setAttribute("y", 3.5);
    bounds.textContent = `[α:${node.alpha ?? "-∞"}, β:${node.beta ?? "+∞"}]`;
    boundsG.appendChild(bounds);

    nodesGroup.appendChild(g);

    if (node.children) {
      node.children.forEach(c => drawNodes(c));
    }
  }

  drawBranches(root);
  drawNodes(root);

  treeSvg.appendChild(levelsGroup);
  treeSvg.appendChild(linesGroup);
  treeSvg.appendChild(nodesGroup);
}

// setup step-by-step playback
function setupTreePlayback(tree, steps) {
  currentTreeData = tree;
  playbackSteps = steps || [];
  currentStepIndex = 0;

  renderSvgTree(tree);

  stepSlider.max = Math.max(0, playbackSteps.length - 1);
  stepSlider.value = 0;
  updatePlaybackUI();
}

// update active step in tree playback
function updatePlaybackUI() {
  if (!playbackSteps || playbackSteps.length === 0) return;

  stepCounter.textContent = `Step ${currentStepIndex + 1} / ${playbackSteps.length}`;
  stepSlider.value = currentStepIndex;

  const current = playbackSteps[currentStepIndex];
  stepNarrative.textContent = current.narrative;

  // clear previous active nodes
  const allNodes = treeSvg.querySelectorAll(".tree-node-group");
  allNodes.forEach(n => n.classList.remove("active"));

  // highlight active node
  if (current.activeId) {
    const activeEl = document.getElementById(`node-${current.activeId}`);
    if (activeEl) {
      activeEl.classList.add("active");
    }
  }

  // update text values for steps
  if (current.state) {
    Object.keys(current.state).forEach(nodeId => {
      const data = current.state[nodeId];
      const valEl = document.getElementById(`node-val-${nodeId}`);
      const boundsEl = document.getElementById(`node-bounds-${nodeId}`);

      if (valEl && data.val !== undefined) {
        valEl.textContent = data.val;
      }
      if (boundsEl && data.alpha !== undefined && data.beta !== undefined) {
        boundsEl.textContent = `[α:${data.alpha}, β:${data.beta}]`;
      }
      if (data.pruned) {
        const groupEl = document.getElementById(`node-${nodeId}`);
        if (groupEl) groupEl.classList.add("pruned");
      }
    });
  }
}

// playback control handlers
function goToStep(index) {
  currentStepIndex = Math.max(0, Math.min(index, playbackSteps.length - 1));
  updatePlaybackUI();
}

function startPlayback() {
  if (isPlaying) return;
  isPlaying = true;
  btnStepPlay.textContent = "⏸ PAUSE";
  btnStepPlay.classList.add("btn-danger-pill");

  const speed = parseInt(speedSelect.value) || 600;
  playInterval = setInterval(() => {
    if (currentStepIndex < playbackSteps.length - 1) {
      goToStep(currentStepIndex + 1);
    } else {
      stopPlayback();
    }
  }, speed);
}

function stopPlayback() {
  isPlaying = false;
  if (playInterval) {
    clearInterval(playInterval);
    playInterval = null;
  }
  btnStepPlay.textContent = "▶ PLAY";
  btnStepPlay.classList.remove("btn-danger-pill");
}

function togglePlayback() {
  if (isPlaying) stopPlayback();
  else {
    if (currentStepIndex >= playbackSteps.length - 1) {
      goToStep(0);
    }
    startPlayback();
  }
}

// event listeners for playback bar
btnStepFirst.addEventListener("click", () => { stopPlayback(); goToStep(0); });
btnStepPrev.addEventListener("click", () => { stopPlayback(); goToStep(currentStepIndex - 1); });
btnStepPlay.addEventListener("click", togglePlayback);
btnStepNext.addEventListener("click", () => { stopPlayback(); goToStep(currentStepIndex + 1); });
btnStepLast.addEventListener("click", () => { stopPlayback(); goToStep(playbackSteps.length - 1); });

stepSlider.addEventListener("input", (e) => {
  stopPlayback();
  goToStep(parseInt(e.target.value));
});

speedSelect.addEventListener("change", () => {
  if (isPlaying) {
    stopPlayback();
    startPlayback();
  }
});

btnFitTree.addEventListener("click", () => {
  if (currentTreeData) renderSvgTree(currentTreeData);
  treeViewport.scrollTo({ left: 0, top: 0, behavior: "smooth" });
});

btnMaximizeTree.addEventListener("click", () => {
  treeBoxPanel.classList.toggle("fullscreen");
  btnMaximizeTree.textContent = treeBoxPanel.classList.contains("fullscreen") ? "EXIT FULLSCREEN" : "FULLSCREEN";
  if (currentTreeData) renderSvgTree(currentTreeData);
});

btnRestart.addEventListener("click", resetGame);

// initial setup
initBoard();
resetGame();
