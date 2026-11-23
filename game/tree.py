import math
from typing import List, Optional, Dict, Any

def _format(x: Optional[float]) -> str:
    """Format alpha/beta/values for the console: '-' for unset, 'inf' / '-inf' for infinities."""
    return "-" if x is None else f"{x:g}"


def _json_num(x: Optional[float]):
    """JSON has no Infinity, so send infinities as the strings 'inf' / '-inf' (None stays None)."""
    if x is not None and math.isinf(x):
        return str(x)
    return x

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
        return {
            "depth": self.depth,
            "player_type": self.player_type,
            "move_col": self.move_col,
            "heuristic_value": _json_num(self.heuristic_value),
            "minimax_value": _json_num(self.minimax_value),
            "alpha": _json_num(self.alpha),
            "beta": _json_num(self.beta),
            "pruned": self.pruned,
            "children": [child.to_dict() for child in self.children],
        }


def print_tree_console(
    root: MinimaxTreeNode,
    indent: str = "",
    is_last: bool = True,
    max_depth: Optional[int] = None,
    _is_root: bool = True,
) -> None:
    """Print the minimax search tree to the console in a clear, traceable format."""
    node = root
    if _is_root:
        prefix, child_indent = "", ""
    else:
        prefix = indent + ("`-- " if is_last else "|-- ")
        child_indent = indent + ("    " if is_last else "|   ")

    move = "root" if node.move_col is None else f"col {node.move_col}"

    if node.pruned:
        print(f"{prefix}[PRUNED] {node.player_type} d={node.depth} {move} (never explored)")
        return

    line = (f"{prefix}{node.player_type} d={node.depth} {move} | "
            f"alpha={_format(node.alpha)} beta={_format(node.beta)} | "
            f"value={_format(node.minimax_value)}")
    if node.heuristic_value is not None:
        line += f"  <- leaf, heuristic={_format(node.heuristic_value)}"
    print(line)

    if max_depth is not None and node.depth >= max_depth:
        if node.children:
            print(f"{child_indent}`-- ... {len(node.children)} child node(s) hidden (max_depth={max_depth})")
        return

    for i, child in enumerate(node.children):
        print_tree_console(child, child_indent, i == len(node.children) - 1, max_depth, _is_root=False)
