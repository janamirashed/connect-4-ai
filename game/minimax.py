import time
import math
from typing import Tuple
from .board import Board, PLAYER_AI, PLAYER_HUMAN
from .heuristic import evaluate_with_parts
from .tree import MinimaxTreeNode, print_tree_console


class Minimax:
    def __init__(self, depth_k: int = 4, evaluate=evaluate_with_parts, show_tree: bool = True):
        """`evaluate(board) -> (score, parts)` is the heuristic (swappable for self-play);
        `show_tree=False` silences the per-turn console tree (used by selfplay.py)."""
        self.depth_k = depth_k
        self.evaluate = evaluate
        self.show_tree = show_tree
        self.nodes_expanded = 0

    def get_best_move(self, board: Board) -> Tuple[int, float, MinimaxTreeNode, int, float]:
        """Find the optimal column for the AI agent."""
        self.nodes_expanded = 0
        root = MinimaxTreeNode(depth=0, player_type="MAX")
        start = time.perf_counter()
        best_value = self.minimax_alpha_beta(board, self.depth_k, -math.inf, math.inf, True, root)
        elapsed_time = time.perf_counter() - start

        # show the traced tree on the console every turn
        if self.show_tree:
            print_tree_console(root)
        best_col = next(
            (c.move_col for c in root.children if not c.pruned and c.minimax_value == best_value),
            None,
        )
        return best_col, best_value, root, self.nodes_expanded, elapsed_time

    def minimax_alpha_beta(
        self,
        board: Board,
        remaining_depth: int,
        alpha: float,
        beta: float,
        maximizing_player: bool,
        node: MinimaxTreeNode
    ) -> float:
        """Recursive Minimax with Alpha-Beta pruning."""
        self.nodes_expanded += 1
        # Record initial alpha/beta for this node
        node.alpha, node.beta = alpha, beta
        # Base case: depth limit reached or board full -> heuristic value
        if remaining_depth == 0 or board.is_full():
            score, parts = self.evaluate(board)  # one pass gives value + breakdown
            node.heuristic_value = score
            node.heuristic_parts = parts               # shown in the printed tree
            node.minimax_value = score
            return score

        valid_cols = board.get_valid_locations()  # center-out order

        if maximizing_player:
            best = -math.inf
            for i, col in enumerate(valid_cols):
                board.drop_piece(col, PLAYER_AI)
                child = MinimaxTreeNode(depth=node.depth + 1, player_type="MIN", move_col=col)
                node.add_child(child)
                value = self.minimax_alpha_beta(board, remaining_depth - 1, alpha, beta, False, child)
                board.undo_move(col)  # backtrack

                if value > best:
                    best = value
                alpha = max(alpha, best)
                if beta <= alpha:  # beta cut-off
                    self._mark_pruned(node, valid_cols[i + 1:], "MIN")
                    break
        else:
            best = math.inf
            for i, col in enumerate(valid_cols):
                board.drop_piece(col, PLAYER_HUMAN)
                child = MinimaxTreeNode(depth=node.depth + 1, player_type="MAX", move_col=col)
                node.add_child(child)
                value = self.minimax_alpha_beta(board, remaining_depth - 1, alpha, beta, True, child)
                board.undo_move(col)  # backtrack

                if value < best:
                    best = value
                beta = min(beta, best)
                if beta <= alpha:  # alpha cut-off
                    self._mark_pruned(node, valid_cols[i + 1:], "MAX")
                    break

        node.minimax_value = best
        return best

    @staticmethod
    def _mark_pruned(node: MinimaxTreeNode, skipped_cols, child_player: str) -> None:
        for col in skipped_cols:
            placeholder = MinimaxTreeNode(depth=node.depth + 1, player_type=child_player, move_col=col)
            placeholder.pruned = True
            node.add_child(placeholder)