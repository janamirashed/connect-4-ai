from typing import List, Tuple

PLAYER_EMPTY = 0
PLAYER_HUMAN = 1
PLAYER_AI = 2

def get_windows(rows: int, cols: int) -> Tuple[Tuple[Tuple[int, int], ...], ...]:
    """ All 4-cell lines (horizontal, vertical, both diagonals) on a rows x cols board."""
    """ Built once per Board."""
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
        self.heights = [0] * cols
        self.windows = get_windows(self.rows, self.cols)
        mid = cols // 2
        self._col_order = sorted(range(cols), key=lambda c: (abs(c - mid), c))

    def is_valid_location(self, col: int) -> bool:
        return 0 <= col < self.cols and self.heights[col] < self.rows

    def get_valid_locations(self) -> List[int]:
        return [c for c in self._col_order if self.heights[c] < self.rows]

    def drop_piece(self, col: int, player: int) -> bool:
        """Drop a piece for `player` into column `col`."""
        if not self.is_valid_location(col):
            return False
        self.grid[self.rows - 1 - self.heights[col]][col] = player
        self.heights[col] += 1
        return True

    def undo_move(self, col: int) -> bool:
        """Undo the top-most move in column `col` (for Minimax backtracking)."""
        if not (0 <= col < self.cols) or self.heights[col] == 0:
            return False
        self.heights[col] -= 1
        self.grid[self.rows - 1 - self.heights[col]][col] = PLAYER_EMPTY
        return True

    def landing_row(self, col: int) -> int:
        """Row index of the top piece in `col` (call right after drop_piece to learn where the piece landed). Returns -1 if the column is empty."""
        if self.heights[col] == 0:
            return -1
        return self.rows - self.heights[col]

    def is_full(self) -> bool:
        return all(h == self.rows for h in self.heights)


    def count_connected_fours(self, player: int) -> int:
        """Count total connected-4 sequences for `player`."""
        g = self.grid
        return sum(
            1
            for w in self.windows
            if all(g[r][c] == player for r, c in w)
        )

    def get_scores(self) -> Tuple[int, int]:
        """Return (human_score, ai_score)."""
        return (
            self.count_connected_fours(PLAYER_HUMAN),
            self.count_connected_fours(PLAYER_AI),
        )

    def clone(self) -> "Board":
        """Return an independent copy of the board"""
        b = Board.__new__(Board)                # empty shell, __init__ is skipped
        b.rows, b.cols = self.rows, self.cols   # ints: immutable, safe to copy directly
        b.grid = [row[:] for row in self.grid]  # copy each row: independent (list of lists)
        b.heights = self.heights[:]             # shallow copy is enough: flat list of ints
        b._col_order = self._col_order          # never modified after creation, so shared
        b.windows = self.windows
        return b

    def to_dict(self) -> dict:
        """Serialize board state for Flask JSON response."""
        human, ai = self.get_scores()
        return {
            "grid": [row[:] for row in self.grid],
            "rows": self.rows,
            "cols": self.cols,
            "heights": self.heights[:],
            "scores": {"human": human, "ai": ai},
            "is_full": self.is_full(),
        }
