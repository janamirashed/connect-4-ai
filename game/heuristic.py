from .board import Board, PLAYER_HUMAN, PLAYER_AI

# weights used to score non-terminal board states:
# four: completed 4-in-a-row (permanent score)
# three_playable: 3 discs and the empty spot can be played right now
# three: 3 discs but the empty spot is floating in the air
# two / one: weaker potential lines
# center: small bonus for controlling middle columns
DEFAULT_WEIGHTS = {
    "four": 100,
    "three_playable": 10,
    "three": 5,
    "two": 2,
    "one": 0.5,
    "center": 0.3,
}
W_TERMINAL = 10_000   # exact final win/loss score must dominate any heuristic guess

def evaluate_breakdown(board: Board, weights: dict = DEFAULT_WEIGHTS):
    # returns (fours, threats, center) from the ai's perspective
    # kept separate so the tree printer and gui can show each part
    grid, heights, rows = board.grid, board.heights, board.rows
    w3p, w3, w2, w1 = (weights["three_playable"], weights["three"],
                       weights["two"], weights["one"])

    fours = 0          # ai fours minus human fours
    threats = 0.0      # potential in windows that can still become a 4

    for window in board.windows:
        ai = hum = 0
        empty_cell = None
        for r, c in window:
            v = grid[r][c]
            if v == PLAYER_AI: ai += 1
            elif v == PLAYER_HUMAN: hum += 1
            else: empty_cell = (r, c)

        if ai and hum:                 # both colors inside window means it's blocked / dead
            continue
        if ai == 4:
            fours += 1
        elif hum == 4:
            fours -= 1
        else:
            count, sign = (ai, 1) if ai else (hum, -1)
            if count == 3:
                r, c = empty_cell
                # playable if the empty spot lands directly on top of the column height
                playable = (rows - 1 - r) == heights[c]
                threats += sign * (w3p if playable else w3)
            elif count == 2:
                threats += sign * w2
            elif count == 1:
                threats += sign * w1

    # center control: columns closer to middle belong to more winning windows
    mid = board.cols // 2
    center_units = 0
    for c in range(board.cols):
        w = mid - abs(c - mid)
        for r in range(rows - heights[c], rows):      # check only filled pieces in col
            center_units += w if grid[r][c] == PLAYER_AI else -w

    return weights["four"] * fours, threats, center_units * weights["center"]


def evaluate_with_parts(board: Board, weights: dict = DEFAULT_WEIGHTS):
    # returns (score, (fours, threats, center)) in a single pass
    parts = evaluate_breakdown(board, weights)
    fours, threats, center = parts

    # full board: game is over, only the exact final score difference counts
    if board.is_full():
        diff = round(fours / weights["four"])  # ai fours minus human fours
        value = float(W_TERMINAL * diff)
        return value, (value, 0.0, 0.0)

    return fours + threats + center, parts


def evaluate_board(board: Board) -> float:
    # heuristic value from the ai (max) perspective as a single number
    return evaluate_with_parts(board)[0]


# notes and explanations:
#
# 1. why heuristic is needed:
#    - connect-4 has ~10^35 states, impossible to search to the end every turn.
#    - minimax searches to depth k, and uses this heuristic to score leaf boards.
#    - positive score = ai is winning, negative score = human is winning.
#
# 2. dead windows:
#    - if a 4-slot window contains both ai and human pieces, neither can ever
#      make a 4-in-a-row there, so it is skipped immediately (dead window).
#
# 3. playable vs floating 3-in-a-row:
#    - playable 3 (weight 10): the 4th empty slot is at the column's current height,
#      meaning a player can drop into it on their very next turn (immediate threat).
#    - floating 3 (weight 5): the 4th empty slot is higher up in the air and cannot
#      be played until slots beneath it are filled first (future threat).
#
# 4. center control (weight 0.3):
#    - center column (col 3) has weight 3, cols 2 & 4 have weight 2, cols 1 & 5 have weight 1, edges have weight 0.
#    - encourages the ai to occupy center columns because they participate in more 4-windows.
#
# 5. terminal score (w_terminal = 10,000):
#    - when the board is full, winning by having more connected-fours is multiplied
#      by 10,000 (e.g. +2 diff -> +20,000) so a real final win always beats heuristic guesses.
