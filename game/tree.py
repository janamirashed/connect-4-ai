import math
from typing import List, Optional, Dict, Any


def _format(x: Optional[float]) -> str:
    # format alpha/beta/values for console: '-' for unset, 'inf' / '-inf' for infinities
    return "-" if x is None else f"{x:g}"


def _json_num(x: Optional[float]):
    # standard json has no Infinity, so convert float inf/-inf to strings 'inf'/'-inf'
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
        # a single node in the minimax search tree
        self.depth = depth
        self.player_type = player_type
        self.move_col = move_col
        self.heuristic_value = heuristic_value
        self.heuristic_parts: Optional[tuple] = None  # (fours, threats, center) at leaves
        self.minimax_value: Optional[float] = None
        self.alpha: Optional[float] = None
        self.beta: Optional[float] = None
        self.pruned: bool = False
        self.children: List["MinimaxTreeNode"] = []

    def add_child(self, child: "MinimaxTreeNode") -> None:
        # attach a child move to this node
        self.children.append(child)

    def to_dict(self) -> Dict[str, Any]:
        # serialize tree node and all its descendants into a dictionary for web gui json
        return {
            "depth": self.depth,
            "player_type": self.player_type,
            "move_col": self.move_col,
            "heuristic_value": _json_num(self.heuristic_value),
            "heuristic_parts": list(self.heuristic_parts) if self.heuristic_parts else None,
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
    # prints the entire minimax search tree to the terminal with branches |-- and `--
    node = root
    if _is_root:
        prefix, child_indent = "", ""
    else:
        prefix = indent + ("`-- " if is_last else "|-- ")
        child_indent = indent + ("    " if is_last else "|   ")

    move = "root" if node.move_col is None else f"col {node.move_col}"

    # if this branch was pruned by alpha-beta, mark it clearly
    if node.pruned:
        print(f"{prefix}[PRUNED] {node.player_type} d={node.depth} {move} (never explored)")
        return

    # print node details: depth, move column, alpha, beta, and minimax score
    line = (f"{prefix}{node.player_type} d={node.depth} {move} | "
            f"alpha={_format(node.alpha)} beta={_format(node.beta)} | "
            f"value={_format(node.minimax_value)}")
    if node.heuristic_value is not None:
        line += f"  <- leaf, heuristic={_format(node.heuristic_value)}"
        if node.heuristic_parts is not None:
            fours, threats, center = node.heuristic_parts
            line += (f" [fours={_format(fours)} threats={_format(threats)} "
                     f"center={_format(center)}]")
    print(line)

    if max_depth is not None and node.depth >= max_depth:
        if node.children:
            print(f"{child_indent}`-- ... {len(node.children)} child node(s) hidden (max_depth={max_depth})")
        return

    # recursively print all child nodes
    for i, child in enumerate(node.children):
        print_tree_console(child, child_indent, i == len(node.children) - 1, max_depth, _is_root=False)


# notes and explanations:
#
# 1. role of tree.py:
#    - the assignment requires showing the minimax tree in each turn in the console in a readable format.
#    - providing a gui visualization of the tree is granted a bonus.
#    - this file satisfies both requirements: it formats ascii tree logs for the console
#      and converts the tree to json for the interactive web visualizer.
#
# 2. json infinity handling (_json_num):
#    - python supports float('inf') and float('-inf'), but json standard does not.
#    - sending raw infinity causes json serialization errors in flask.
#    - _json_num converts infinities to 'inf' and '-inf' strings so javascript can read them safely.
#
# 3. tree node data:
#    - each node stores depth, player (max/min), move column, alpha, beta, minimax value,
#      heuristic breakdown (at leaves), and whether it was pruned.
