"""Connect 4 Board Representation Skeleton.

Assignment rules:
- Connect 4 is played UNTIL THE BOARD IS FULL.
- The winner is the player having the GREATER NUMBER of connected-fours.
- Board dimensions: width >= 7, length (rows) >= 6 (default: 6x7).
"""

from typing import List, Tuple, Optional

PLAYER_EMPTY = 0
PLAYER_HUMAN = 1
PLAYER_AI = 2


class Board:
    def __init__(self, rows: int = 6, cols: int = 7):
        """Initialize the board with given rows (>=6) and cols (>=7)."""
        self.rows = rows
        self.cols = cols
        # TODO: Initialize 2D grid/board data structure (e.g. rows x cols with PLAYER_EMPTY)
        self.grid = None
        pass

    def is_valid_location(self, col: int) -> bool:
        """Check if dropping a piece in `col` is valid (column not full)."""
        # TODO: Implement column boundary and availability check
        pass

    def get_valid_locations(self) -> List[int]:
        """Return list of columns that are not yet full."""
        # TODO: Return valid column indices (optionally ordered center-out for better pruning)
        pass

    def drop_piece(self, col: int, player: int) -> bool:
        """Drop a piece for `player` into column `col`. Returns True on success."""
        # TODO: Place piece in the lowest empty slot in column `col`
        pass

    def undo_move(self, col: int) -> bool:
        """Undo the top-most move in column `col` (for Minimax backtracking)."""
        # TODO: Remove top piece from column `col`
        pass

    def is_full(self) -> bool:
        """Check if the board is completely full (game over)."""
        # TODO: Check if no valid moves remain
        pass

    def count_connected_fours(self, player: int) -> int:
        """Count total connected-4 sequences for `player`.
        Must check:
        - Horizontal
        - Vertical
        - Diagonal (/)
        - Diagonal (\\)
        Overlapping 4s must be counted (e.g., 5 in a row = 2 connected-fours).
        """
        # TODO: Implement 4-in-a-row counter
        pass

    def get_scores(self) -> Tuple[int, int]:
        """Return (human_score, ai_score) based on connected-4 counts."""
        # TODO: Return tuple (human_connected_fours, ai_connected_fours)
        pass

    def clone(self) -> "Board":
        """Return a deep copy of the board."""
        # TODO: Return cloned board instance
        pass

    def to_dict(self) -> dict:
        """Serialize board state for Flask JSON response."""
        # TODO: Return dictionary representation (grid, scores, is_full, etc.)
        pass
