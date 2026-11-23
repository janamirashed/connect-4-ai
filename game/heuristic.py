from .board import Board, PLAYER_EMPTY, PLAYER_HUMAN, PLAYER_AI

#   four          : a completed four is permanent, so it dominates everything
#   three_playable: 3 discs + the empty cell can be dropped into right now
#   three         : 3 discs + the empty cell is still "in the air"
#   two / one     : weaker potential lines
#   center        : small tiebreaker for central columns
DEFAULT_WEIGHTS = {
    "four": 100,
    "three_playable": 10,
    "three": 5,
    "two": 2,
    "one": 0.5,
    "center": 0.3,
}


def evaluate_breakdown(board: Board, weights: dict = DEFAULT_WEIGHTS):
    """Return (fours, threats, center) from the AI's perspective.
    Kept separate so the tree printer / report can show each component."""
    grid, heights, rows = board.grid, board.heights, board.rows
    w3p, w3, w2, w1 = (weights["three_playable"], weights["three"],
                       weights["two"], weights["one"])

    fours = 0          # AI fours - human fours (overlapping fours count separately)
    threats = 0.0      # potential in windows that can still become a four

    for window in board.windows:
        ai = hum = 0
        empty_cell = None
        for r, c in window:
            v = grid[r][c]
            if v == PLAYER_AI: ai += 1
            elif v == PLAYER_HUMAN: hum += 1
            else: empty_cell = (r, c)

        if ai and hum:                 # both colors -> dead window
            continue
        if ai == 4:
            fours += 1
        elif hum == 4:
            fours -= 1
        else:
            count, sign = (ai, 1) if ai else (hum, -1)
            if count == 3:
                r, c = empty_cell
                playable = (rows - 1 - r) == heights[c]
                threats += sign * (w3p if playable else w3)
            elif count == 2:
                threats += sign * w2
            elif count == 1:
                threats += sign * w1

    # Center control: columns closer to the middle belong to more windows.
    mid = board.cols // 2
    center_units = 0                                  # integer sum avoids float noise
    for c in range(board.cols):
        w = mid - abs(c - mid)
        for r in range(rows - heights[c], rows):      # only the filled cells
            center_units += w if grid[r][c] == PLAYER_AI else -w

    return weights["four"] * fours, threats, center_units * weights["center"]


def evaluate_with_parts(board: Board, weights: dict = DEFAULT_WEIGHTS):
    """Return (score, (fours, threats, center)) in a single pass over the board."""
    parts = evaluate_breakdown(board, weights)
    fours, threats, center = parts

    # Full board: the game is over, so only the exact score counts.
    if board.is_full():
        return float(fours), parts

    return fours + threats + center, parts


def evaluate_board(board: Board) -> float:
    """Heuristic value from the AI's (MAX) perspective:"""
    return evaluate_with_parts(board)[0]