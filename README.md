<div align="center">

# Connect-4 AI

*An interactive Connect-4 game powered by Minimax with Alpha-Beta pruning — featuring real-time SVG search tree visualization, step-by-step playback, console tree tracing, and performance benchmarking served by Flask.*

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

</div>

---

## Overview

Connect-4 AI is an adversarial search game where a human plays against an AI agent powered by depth-limited Minimax with Alpha-Beta pruning. Move ordering utilizes a center-out heuristic to maximize pruning efficiency. The frontend visualizes the decision-making process with an interactive SVG game tree, live alpha-beta bound tracking, and step-by-step playback animation. Additionally, each move generates a full text-based tree trace on the terminal console and supports benchmark evaluations across multiple search depths.

---

## Features

- **Adversarial Minimax Search:** Depth-bounded search with Alpha-Beta pruning across configurable depths (K = 1 to 6)
- **Multi-Factor Evaluation Heuristic:** Considers connected-4 counts, open 3-in-a-row threats, 2/1-piece potential, and center column control
- **Center-Out Move Ordering:** Prioritizes high-potential center columns (`[3, 2, 4, 1, 5, 0, 6]`) to produce early alpha-beta cutoffs
- **Interactive SVG Tree Visualizer:** Renders circular nodes, action badges, prune indicators, and distinct level-wise MAX/MIN margin markers
- **Dynamic Step-by-Step Playback:** Recursively walks the real Minimax search tree with timeline slider, play/pause controls, speed selection, and live narrative ticker
- **Console Tree Tracing:** Prints an indented search tree with node bounds and detailed heuristic breakdowns on every AI turn
- **Performance Benchmarking:** `benchmark.py` evaluates nodes expanded and computation time across different K values
- **Heuristic Self-Play Engine:** `selfplay.py` runs automated tournaments between competing heuristic weight configurations

---

## Architecture

| Component | Technology | Role |
|-----------|------------|------|
| **Board Logic** | Python (`game/board.py`) | 6×7 grid, connected-4 counting, column heights, move validity, and backtracking (`undo_move`) |
| **Search Engine** | Python (`game/minimax.py`) | Depth-limited Minimax with Alpha-Beta pruning and pruning branch markers |
| **Heuristics** | Python (`game/heuristic.py`) | Configurable multi-term evaluation function with component breakdown |
| **Tree Tracer** | Python (`game/tree.py`) | In-memory tree structure, dictionary serializer, and hierarchical console printer |
| **API Server** | Flask (`app.py`) | REST endpoints (`/api/reset`, `/api/human-move`, `/api/ai-move`) delivering game state & search tree JSON |
| **Web GUI** | Vanilla JS + CSS | Interactive game board, dynamic SVG tree renderer, playback controller, and metrics panel |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3, Flask |
| Algorithms | Minimax, Alpha-Beta Pruning, Heuristic Evaluation |
| Frontend | HTML5, Vanilla JavaScript, CSS3, Inline SVG |

---

## Running Locally

**Prerequisites:** Python 3.10+

```bash
# create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# run the web application
python app.py
```

App available at `http://127.0.0.1:5000`

### Running Benchmarks & Experiments

```bash
# run depth benchmark (k=1 to 6)
python benchmark.py

# run heuristic self-play tournaments
python selfplay.py
```

---

## Implementation Notes

<details>
<summary><b>Copying in Python: assignment vs. shallow vs. deep copy (<code>Board.clone()</code>)</b></summary>

Used so that minimax can try moves on a copy without touching the real board.

| | What happens | Independent? |
|---|---|---|
| **Assignment** `b = a` | No copy. One list, two names. | No: changing one changes the other |
| **Shallow copy** `a[:]` | New outer list. Items inside are shared. | Yes if the items are immutable (ints); no if they are lists |
| **Deep copy** `copy.deepcopy(a)` | New outer list and new copies of everything inside, at every level. | Yes, always |

**Rule of thumb:** copy every level that holds mutable objects. Ints can be shared safely, lists cannot.

**How it applies to `Board`:**

- `heights` is a flat list of ints, so `self.heights[:]` (shallow copy) is enough.
- `grid` is a list of lists, so a shallow copy would still share the rows. `clone()` uses `[row[:] for row in self.grid]`, a manual two-level copy. For a grid of ints it gives the same result as `deepcopy` and is much faster.
- `_col_order` is shared between clones on purpose. It is a list that is never modified after the board is created (it could be made a tuple to enforce this).
- `Board.__new__(Board)` creates an empty `Board` without running `__init__`, so `clone()` must assign every attribute by hand. If a new attribute is added to `__init__`, add it to `clone()` too.

```python
from game.board import Board  
def clone(self) -> "Board":
    """Return an independent copy of the board (mutable state is copied)."""
    b = Board.__new__(Board)                 # empty shell, __init__ is skipped
    b.rows, b.cols = self.rows, self.cols    # ints: immutable, safe to copy directly
    b.grid = [row[:] for row in self.grid]   # copy each row: independent (list of lists)
    b.heights = self.heights[:]              # shallow copy is enough: flat list of ints
    b._col_order = self._col_order           # never modified after creation, so shared
    return b
```

</details>

<details>
<summary><b>Why central columns are stronger (move ordering and the center bonus)</b></summary>

**Claim:** in Connect 4, a disc in a central column helps you build more potential fours, and blocks more of the opponent's, than a disc near the edge.

**Counting argument.** A four can only form inside a 4-cell window. A 7x6 board has 69 windows, and each cell belongs to a different number of them (rows drawn top to bottom):

```
 3  4  5  7  5  4  3
 4  6  8 10  8  6  4
 5  8 11 13 11  8  5
 5  8 11 13 11  8  5
 4  6  8 10  8  6  4
 3  4  5  7  5  4  3
```

- A center-column cell belongs to 7 to 13 windows; an edge-column cell belongs to only 3 to 5.
- Summed over the whole column, the center column is in 60 windows, versus 24 for an edge column.

**Where the difference comes from:**

- **Horizontal:** a center cell is in 4 horizontal windows, an edge cell in only 1.
- **Vertical:** no difference; every column offers the same vertical windows.
- **Diagonal:** the biggest effect. A center disc can sit in the middle of diagonals in both directions; an edge disc can only be the end of one, and edge diagonals often lack room for four cells.

**Where it is used in the code:**

- `Board._col_order` sorts columns center-out (e.g. `[3, 2, 4, 1, 5, 0, 6]` for 7 columns), and `get_valid_locations()` returns columns in that order. Minimax tries strong moves first, so alpha and beta tighten sooner and more branches are pruned. The returned value is the same as with left-to-right order; only the number of nodes visited changes.
- The heuristic can add a small bonus per computer disc in the center column (and subtract for human discs).

**Caveats:**

- It is a tendency, not a rule. A move that completes a four, blocks one, or sets up a double threat beats a central move that does nothing. That is why center-first is used only for ordering: the other moves are still searched unless pruned.
- It matters most in the early and middle game; late in the game, the specific cells that complete fours matter more.

</details>

---

## Authors

Jana Rashed · Esraa AbdElHay
