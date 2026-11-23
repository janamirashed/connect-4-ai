import argparse
import itertools
import random
import time
from functools import partial

from game.board import Board, PLAYER_AI, PLAYER_HUMAN
from game.heuristic import DEFAULT_WEIGHTS, evaluate_with_parts
from game.minimax import Minimax

# ---- Weight sets under test (edit freely) ----
WEIGHT_SETS = {
    "baseline":   DEFAULT_WEIGHTS,
    "playable_x3": {**DEFAULT_WEIGHTS, "three_playable": 30},
    "no_playable": {**DEFAULT_WEIGHTS, "three_playable": DEFAULT_WEIGHTS["three"]},
    "no_center":  {**DEFAULT_WEIGHTS, "center": 0},
}

_SWAP = {0: 0, PLAYER_HUMAN: PLAYER_AI, PLAYER_AI: PLAYER_HUMAN}


def mirrored(board: Board) -> Board:
    """Copy of the board with the two colors swapped. Minimax always plays as
    PLAYER_AI, so the agent sitting on the PLAYER_HUMAN discs searches this view."""
    b = board.clone()
    b.grid = [[_SWAP[v] for v in row] for row in b.grid]
    return b


def play_game(agent_ai: Minimax, agent_hum: Minimax, opening):
    """agent_ai plays the PLAYER_AI discs, agent_hum the PLAYER_HUMAN discs.
    `opening` is a list of forced columns played first, alternating AI/HUMAN.
    Returns (human_fours, ai_fours)."""
    board = Board()
    turn = PLAYER_AI                       # PLAYER_AI discs move first
    for col in opening:
        board.drop_piece(col, turn)
        turn = PLAYER_HUMAN if turn == PLAYER_AI else PLAYER_AI

    while not board.is_full():
        if turn == PLAYER_AI:
            col = agent_ai.get_best_move(board)[0]
        else:
            col = agent_hum.get_best_move(mirrored(board))[0]
        board.drop_piece(col, turn)
        turn = PLAYER_HUMAN if turn == PLAYER_AI else PLAYER_AI
    return board.get_scores()


def random_opening(rng: random.Random, plies: int):
    """A few random legal columns, so repeated games are not identical."""
    b = Board()
    cols = []
    for _ in range(plies):
        c = rng.choice(b.get_valid_locations())
        b.drop_piece(c, PLAYER_AI)
        cols.append(c)
    return cols


def make_agent(weights, k):
    return Minimax(depth_k=k, evaluate=partial(evaluate_with_parts, weights=weights),
                   show_tree=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ks", type=int, nargs="+", default=[2, 4], help="depths to test")
    ap.add_argument("--openings", type=int, default=5, help="random openings per pair")
    ap.add_argument("--plies", type=int, default=2, help="random plies per opening")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    openings = [random_opening(rng, args.plies) for _ in range(args.openings)]
    totals = {name: [0, 0, 0] for name in WEIGHT_SETS}       # wins, losses, draws

    print(f"{'A':<12} {'B':<12} {'K':>2}  {'A wins':>6} {'B wins':>6} {'draws':>5}  time")
    for k in args.ks:
        for a, b in itertools.combinations(WEIGHT_SETS, 2):
            aw = bw = dr = 0
            start = time.perf_counter()
            for opening in openings:
                for a_first in (True, False):                # swap who moves first
                    ag_a = make_agent(WEIGHT_SETS[a], k)
                    ag_b = make_agent(WEIGHT_SETS[b], k)
                    if a_first:
                        hum, ai = play_game(ag_a, ag_b, opening)
                        a_score, b_score = ai, hum
                    else:
                        hum, ai = play_game(ag_b, ag_a, opening)
                        a_score, b_score = hum, ai
                    if a_score > b_score:
                        aw += 1
                    elif b_score > a_score:
                        bw += 1
                    else:
                        dr += 1
            totals[a][0] += aw; totals[a][1] += bw; totals[a][2] += dr
            totals[b][0] += bw; totals[b][1] += aw; totals[b][2] += dr
            print(f"{a:<12} {b:<12} {k:>2}  {aw:>6} {bw:>6} {dr:>5}  "
                  f"{time.perf_counter() - start:.1f}s", flush=True)

    print("\nOverall standings (all pairs, all K):")
    print(f"{'weight set':<12} {'wins':>5} {'losses':>6} {'draws':>5}")
    for name, (w, l, d) in sorted(totals.items(), key=lambda kv: (-kv[1][0], kv[1][1])):
        print(f"{name:<12} {w:>5} {l:>6} {d:>5}")


if __name__ == "__main__":
    main()