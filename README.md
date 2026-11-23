# Connect 4 AI

## Quickstart

```bash
pip install -r requirements.txt
python3 app.py
```

Open `http://127.0.0.1:5000` in your browser.

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

