"""Minimax Algorithm with Alpha-Beta Pruning Skeleton.

Assignment requirements:
- AI uses Minimax with alpha-beta pruning.
- Truncate search at depth K using the heuristic function.
- Track nodes expanded and execution time for the report.
- Trace the search tree each turn.
"""

from typing import Tuple, Optional
from .board import Board, PLAYER_AI, PLAYER_HUMAN
from .heuristic import evaluate_board
from .tree import MinimaxTreeNode, print_tree_console


class Minimax:
    def __init__(self, depth_k: int = 4):
        """Initialize with depth limit K."""
        self.depth_k = depth_k
        self.nodes_expanded = 0

    def get_best_move(self, board: Board) -> Tuple[int, float, MinimaxTreeNode, int, float]:
        """Find the optimal column for the AI agent.
        
        Returns:
            best_col: Chosen column index
            best_value: Minimax evaluation of the chosen move
            tree_root: The traced Minimax search tree
            nodes_expanded: Number of nodes visited
            elapsed_time: Search execution time in seconds
        """
        self.nodes_expanded = 0
        # TODO: Initialize root MinimaxTreeNode
        # TODO: Call minimax_alpha_beta(...)
        # TODO: Print the tree to console (mandatory requirement)
        # TODO: Return (best_col, best_value, tree_root, nodes_expanded, elapsed_time)
        pass

    def minimax_alpha_beta(
        self,
        board: Board,
        depth: int,
        alpha: float,
        beta: float,
        maximizing_player: bool,
        node: Optional[MinimaxTreeNode] = None
    ) -> float:
        """Recursive Minimax with Alpha-Beta pruning.
        
        Args:
            board: Current game board state
            depth: Remaining depth levels (stops at 0)
            alpha: Best score MAX player can guarantee
            beta: Best score MIN player can guarantee
            maximizing_player: True for AI (MAX), False for Human (MIN)
            node: Current node in the search tree
            
        Returns:
            float: Minimax value
        """
        # TODO: Base case: if depth == 0 or board.is_full():
        #       - evaluate board using evaluate_board(board)
        #       - record heuristic value on node
        #       - return evaluated score
        # TODO: If maximizing_player:
        #       - iterate over board.get_valid_locations()
        #       - drop piece, recurse, undo move
        #       - update alpha, prune if beta <= alpha
        # TODO: If minimizing_player:
        #       - iterate over board.get_valid_locations()
        #       - drop piece, recurse, undo move
        #       - update beta, prune if beta <= alpha
        pass
