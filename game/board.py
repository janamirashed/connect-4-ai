from typing import List, Tuple

PLAYER_EMPTY = 0
PLAYER_HUMAN = 1
PLAYER_AI = 2

# what is a "window"? A "window" is simply a group of 4 connected slots where a win could happen
def get_windows(rows: int, cols: int) -> Tuple[Tuple[Tuple[int, int], ...], ...]:
    # all 4-cell lines (horizontal, vertical, both diagonals) on a rows x cols board
    # built once per Board
    windows = []
    for r in range(rows):
        for c in range(cols):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                end_r, end_c = r + 3 * dr, c + 3 * dc
                if 0 <= end_r < rows and 0 <= end_c < cols:
                    windows.append(tuple((r + i * dr, c + i * dc) for i in range(4)))
    return tuple(windows)


class Board:
    def __init__(self, rows: int = 6, cols: int = 7):
        self.rows = rows
        self.cols = cols
        # grid[0] is the TOP row, grid[rows-1] is the bottom (matches how it is drawn)
        self.grid = [[PLAYER_EMPTY] * cols for _ in range(rows)]
        # a list of 7 numbers like [0, 0, 0, 0, 0, 0, 0]. It tracks how many pieces are currently stacked in each column
        self.heights = [0] * cols
        self.windows = get_windows(self.rows, self.cols)
        mid = cols // 2
        # we sort the column indices by how close they are to the middle column (mid = 7 // 2 = 3)
        self._col_order = sorted(range(cols), key=lambda c: (abs(c - mid), c))

    # checks if a column exists (between 0 and 6) and isn't full (its height is less than 6)
    def is_valid_location(self, col: int) -> bool:
        return 0 <= col < self.cols and self.heights[col] < self.rows

    # returns a list of all columns that still have room for a piece, ordered from the center outward ([3, 2, 4, 1, 5, 0, 6])
    def get_valid_locations(self) -> List[int]:
        return [c for c in self._col_order if self.heights[c] < self.rows]

    def drop_piece(self, col: int, player: int) -> bool:
        # simulates gravity and falls into the lowest spot and increases the height by 1
        if not self.is_valid_location(col):
            return False
        self.grid[self.rows - 1 - self.heights[col]][col] = player
        self.heights[col] += 1
        return True

    def undo_move(self, col: int) -> bool:
        # instead of making a copy for board each time to test future scenarios AI can drop to test and undo
        if not (0 <= col < self.cols) or self.heights[col] == 0:
            return False
        self.heights[col] -= 1
        self.grid[self.rows - 1 - self.heights[col]][col] = PLAYER_EMPTY
        return True

    def landing_row(self, col: int) -> int:
        # row index of the top piece in `col` (call right after drop_piece to learn where the piece landed). returns -1 if the column is empty.
        if self.heights[col] == 0:
            return -1
        return self.rows - self.heights[col]

    # checks if every single column has reached 6 pieces (all 42 slots filled). This tells us if the game is over
    def is_full(self) -> bool:
        return all(h == self.rows for h in self.heights)


    def count_connected_fours(self, player: int) -> int:
        # count total connected-4 sequences for `player`
        # how scoring works: it loops through all 69 pre-calculated windows (self.windows)
        # if all 4 cells in a window belong to that player, it adds 1 to their score
        g = self.grid
        return sum(
            1
            for w in self.windows
            if all(g[r][c] == player for r, c in w)
        )

    def get_scores(self) -> Tuple[int, int]:
        # return (human_score, ai_score)
        return (
            self.count_connected_fours(PLAYER_HUMAN),
            self.count_connected_fours(PLAYER_AI),
        )

    def clone(self) -> "Board":
        # return an independent copy of the board
        # deepcopy is slow in python because it recursively inspects every object
        # targeted shallow copy is preferred: we copy each row [row[:] for row in self.grid]
        # and share read-only data (windows, _col_order), making it ~10x faster
        b = Board.__new__(Board)                # empty shell, __init__ is skipped
        b.rows, b.cols = self.rows, self.cols   # ints: immutable, safe to copy directly
        b.grid = [row[:] for row in self.grid]  # copy each row: independent (list of lists)
        b.heights = self.heights[:]             # shallow copy is enough: flat list of ints
        b._col_order = self._col_order          # never modified after creation, so shared
        b.windows = self.windows
        return b

    def to_dict(self) -> dict:
        # serialize board state for Flask JSON response
        human, ai = self.get_scores()
        return {
            "grid": [row[:] for row in self.grid],
            "rows": self.rows,
            "cols": self.cols,
            "heights": self.heights[:],
            "scores": {"human": human, "ai": ai},
            "is_full": self.is_full(),
        }


# notes and explanations:
#
# 1. window calculation (get_windows):
#    - a "window" is a group of 4 connected coordinates where a win is possible.
#    - for a standard 6x7 board, there are 4 directions checked:
#        * horizontal (0, 1): 24 windows
#        * vertical   (1, 0): 21 windows
#        * diagonal / (1, 1): 12 windows
#        * diagonal \ (1, -1): 12 windows
#        -> total = 69 possible windows across the entire board.
#    - why precompute once?
#      instead of repeatedly calculating coordinates in loops during minimax,
#      we compute all 69 coordinate tuples once at startup. checking the board
#      is then just looking up these pre-saved coordinates.
#
# 2. counting connected 4s (count_connected_fours):
#    - iterates over all 69 precomputed windows.
#    - for each window, checks: all(grid[r][c] == player for r, c in window).
#    - if all 4 cells match the player's number, add 1 point.
#    - overlapping sequences count properly: e.g., 5 pieces in a row will
#      contain two overlapping 4-windows, correctly giving 2 points according
#      to assignment rules.
#
# 3. center-out move ordering (_col_order & mid):
#    - column index mid = cols // 2 (7 // 2 = 3, the exact center column).
#    - we sort columns by distance from center: abs(c - mid):
#        * col 3 -> distance 0
#        * col 2, 4 -> distance 1
#        * col 1, 5 -> distance 2
#        * col 0, 6 -> distance 3
#        -> resulting exploration order: [3, 2, 4, 1, 5, 0, 6].
#    - strategic reason:
#      pieces placed in the center column belong to far more potential 4-windows
#      (horizontal, vertical, both diagonals) compared to edge columns (0 or 6).
#    - alpha-beta pruning speedup:
#      searching the most promising (center) moves first establishes high alpha /
#      low beta bounds immediately, enabling earlier and more frequent cutoffs
#      on the worse (edge) branches, saving massive amounts of search time.
#
# 4. copying: why deep copy is bad and targeted shallow copy is preferred:
#    - copy.deepcopy() is notoriously slow in python because it recursively checks object types and references.
#    - a naive shallow copy (grid[:]) fails because inner rows remain shared references.
#    - our clone() uses a fast targeted copy: [row[:] for row in grid] makes each row independent,
#      heights[:] is an independent list of numbers, and immutable/read-only data like windows and
#      _col_order are safely shared without copying, running ~10x faster than deepcopy.
