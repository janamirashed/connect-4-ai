import time
import math
from typing import Tuple
from .board import Board, PLAYER_AI, PLAYER_HUMAN
from .heuristic import evaluate_with_parts
from .tree import MinimaxTreeNode, print_tree_console


class Minimax:
    def __init__(self, depth_k: int = 4, evaluate=evaluate_with_parts, show_tree: bool = True):
        # depth_k: how many turns ahead the ai looks (lookahead depth)
        # evaluate: heuristic function that scores leaf boards
        # show_tree: whether to print the ascii search tree to terminal
        self.depth_k = depth_k
        self.evaluate = evaluate
        self.show_tree = show_tree
        self.nodes_expanded = 0

    def get_best_move(self, board: Board) -> Tuple[int, float, MinimaxTreeNode, int, float]:
        # main entry point: returns (best_column, score, root_tree_node, total_nodes, time_spent)
        self.nodes_expanded = 0
        root = MinimaxTreeNode(depth=0, player_type="MAX")
        start = time.perf_counter()
        best_value = self.minimax_alpha_beta(board, self.depth_k, -math.inf, math.inf, True, root)
        elapsed_time = time.perf_counter() - start

        # print the traced tree to console every turn
        if self.show_tree:
            print_tree_console(root)

        # pick the column whose child node achieved the highest (best) minimax value
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
        # recursive minimax search with alpha-beta pruning bounds
        self.nodes_expanded += 1
        node.alpha, node.beta = alpha, beta

        # base case: depth limit reached or board is completely full -> evaluate leaf
        if remaining_depth == 0 or board.is_full():
            score, parts = self.evaluate(board)
            node.heuristic_value = score
            node.heuristic_parts = parts
            node.minimax_value = score
            return score

        # get open columns in center-out order [3, 2, 4, 1, 5, 0, 6]
        valid_cols = board.get_valid_locations()

        if maximizing_player:
            # ai wants the highest possible score
            best = -math.inf
            for i, col in enumerate(valid_cols):
                board.drop_piece(col, PLAYER_AI)
                child = MinimaxTreeNode(depth=node.depth + 1, player_type="MIN", move_col=col)
                node.add_child(child)

                value = self.minimax_alpha_beta(board, remaining_depth - 1, alpha, beta, False, child)
                board.undo_move(col)  # backtrack without copying board

                if value > best:
                    best = value
                alpha = max(alpha, best)

                # beta cutoff: human will never allow this branch, prune remaining siblings
                if beta <= alpha:
                    self._mark_pruned(node, valid_cols[i + 1:], "MIN")
                    break
        else:
            # human wants to minimize ai's score
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

                # alpha cutoff: ai will never choose this branch, prune remaining siblings
                if beta <= alpha:
                    self._mark_pruned(node, valid_cols[i + 1:], "MAX")
                    break

        node.minimax_value = best
        return best

    @staticmethod
    def _mark_pruned(node: MinimaxTreeNode, skipped_cols, child_player: str) -> None:
        # saves skipped moves as pruned nodes so console and gui tree can display them
        for col in skipped_cols:
            placeholder = MinimaxTreeNode(depth=node.depth + 1, player_type=child_player, move_col=col)
            placeholder.pruned = True
            node.add_child(placeholder)


# notes and explanations:
#
# 1. what is minimax:
#    - a zero-sum game tree search where ai is max (aims for highest score)
#      and human is min (aims to give ai the lowest score).
#    - depth_k controls how many levels deep it searches before calling the heuristic.
#
# 2. alpha and beta bounds:
#    - alpha: the best (highest) score guaranteed for max so far along the path (starts at -infinity).
#    - beta:  the best (lowest) score guaranteed for min so far along the path (starts at +infinity).
#    - whenever beta <= alpha, a cutoff occurs because rational players will never let play reach here.
#
# 3. backtracking efficiency:
#    - instead of copying the board object at every node (which is slow),
#      we drop_piece(col), search the child, and immediately undo_move(col).
#
# 4. center-out move ordering:
#    - exploring columns in order [3, 2, 4, 1, 5, 0, 6] tests strong central moves first.
#    - this raises alpha quickly at max nodes, triggering far more cutoffs on weaker edge columns.
#
# 5. visual tree tracking:
#    - _mark_pruned saves the skipped sibling columns with pruned=true.
#    - this allows both the console tree and the web gui tree visualizer to show where branches were cut off.
