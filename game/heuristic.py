"""Heuristic Evaluation Skeleton.

Assignment notes:
- Game tree is truncated after K levels using a heuristic function.
- Better heuristic should return bigger number when computer is nearer to win
  and smaller number when human is nearer to win.
- The bonus is awarded to the best 3 heuristics across student submissions,
  so we design a single strong, competitive heuristic.
- Factors to consider:
  - Current scores (connected-fours count difference)
  - Potential candidate 4-in-a-row lines (3-in-a-row with open ends, 2-in-a-row)
  - Center column dominance and board positioning
  - Blocking opponent threats / candidate points
"""

from .board import Board, PLAYER_HUMAN, PLAYER_AI


def evaluate_board(board: Board) -> float:
    """Evaluate the current board state from the AI's perspective (MAX player).
    
    Returns:
        float: A positive score if AI is winning / in a favorable position,
               a negative score if Human is winning, or 0 for neutral.
    """
    # TODO: Implement the competitive evaluation function
    # Hint:
    # 1. Start with score difference: (ai_connected_fours - human_connected_fours) * weight
    # 2. Check 4-cell sliding windows horizontally, vertically, diagonally
    # 3. Add points for AI potential lines (e.g. 3 AI pieces + 1 empty)
    # 4. Subtract points for Human potential lines (e.g. 3 Human pieces + 1 empty)
    # 5. Favor center column control
    pass
