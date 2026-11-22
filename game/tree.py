"""Minimax Tree Data Structure & Visualizer Skeleton.

Assignment requirements:
- "it is required to show the minimax tree in each turn by printing it to the console in a readable form that we can trace."
- "show the values of board after applying the heuristic (you will lose marks if not) tree printing is a must"
- "Showing the tree using GUI will be granted a bonus."
"""

from typing import List, Optional, Dict, Any


class MinimaxTreeNode:
    def __init__(
        self,
        depth: int,
        player_type: str,  # 'MAX' (AI) or 'MIN' (Human)
        move_col: Optional[int] = None,
        heuristic_value: Optional[float] = None
    ):
        """A node in the Minimax search tree."""
        self.depth = depth
        self.player_type = player_type
        self.move_col = move_col
        self.heuristic_value = heuristic_value
        self.minimax_value: Optional[float] = None
        self.alpha: Optional[float] = None
        self.beta: Optional[float] = None
        self.pruned: bool = False
        self.children: List["MinimaxTreeNode"] = []

    def add_child(self, child: "MinimaxTreeNode") -> None:
        """Add child node to current node."""
        self.children.append(child)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize tree node and descendants to dictionary for GUI tree rendering."""
        # TODO: Serialize node fields and recursively serialize children
        pass


def print_tree_console(root: MinimaxTreeNode, indent: str = "", is_last: bool = True) -> None:
    """Print the minimax search tree to the console in a clear, traceable format.
    Must display:
    - Node player (MAX / MIN), depth, and move column
    - Minimax score and leaf heuristic evaluations
    - Alpha / Beta values and pruned branch markers
    """
    # TODO: Implement readable console tree printing
    pass
