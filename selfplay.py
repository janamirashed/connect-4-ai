import itertools
import random
import time
from functools import partial

from game.board import Board, PLAYER_AI, PLAYER_HUMAN
from game.heuristic import DEFAULT_WEIGHTS, evaluate_with_parts
from game.minimax import Minimax


def _score_key():
    """Name of the 'connected fours already scored' weight in DEFAULT_WEIGHTS."""
    for key in DEFAULT_WEIGHTS:
        if "score" in key.lower() or "four" in key.lower():
            return key
    raise SystemExit(
        "Could not find the connected-fours weight in DEFAULT_WEIGHTS "
        f"(keys: {list(DEFAULT_WEIGHTS)}). Set SCORE_KEY by hand below."
    )


SCORE_KEY = _score_key()

DEPTHS_K = [2, 4]        # Minimax search depths to test
NUM_OPENINGS = 5         # Random starting positions per pair
OPENING_PLIES = 2        # Random moves played before AI takes over (keep even)
RANDOM_SEED = 1233       # Seed for reproducible random openings

WEIGHT_SETS = {
    "baseline":    DEFAULT_WEIGHTS,
    "playable_x3": {**DEFAULT_WEIGHTS, "three_playable": 30},
    "no_playable": {**DEFAULT_WEIGHTS, "three_playable": DEFAULT_WEIGHTS["three"]},
    "no_center":   {**DEFAULT_WEIGHTS, "center": 0},
    # naive reference: only the current connected-fours difference counts
    "score_only":  {key: (DEFAULT_WEIGHTS[key] if key == SCORE_KEY else 0) for key in DEFAULT_WEIGHTS},
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
    turn = PLAYER_AI
    for _ in range(plies):
        valid = b.get_valid_locations()
        if not valid:
            break
        c = rng.choice(valid)
        b.drop_piece(c, turn)
        cols.append(c)
        turn = PLAYER_HUMAN if turn == PLAYER_AI else PLAYER_AI
    return cols


def make_agent(weights, k):
    return Minimax(depth_k=k, evaluate=partial(evaluate_with_parts, weights=weights),
                   show_tree=False)


def main():
    rng = random.Random(RANDOM_SEED)
    openings = [random_opening(rng, OPENING_PLIES) for _ in range(NUM_OPENINGS)]
    # per weight set: wins, losses, draws, sum of (own fours - opponent fours), games played
    totals = {name: [0, 0, 0, 0, 0] for name in WEIGHT_SETS}

    print(f"{'A':<12} {'B':<12} {'K':>2}  {'A wins':>6} {'B wins':>6} {'draws':>5} "
          f"{'avg margin (A-B)':>17}  time")
    for k in DEPTHS_K:
        for a, b in itertools.combinations(WEIGHT_SETS, 2):
            aw = bw = dr = 0
            margin_sum = games = 0
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
                    margin_sum += a_score - b_score
                    games += 1
            totals[a][0] += aw; totals[a][1] += bw; totals[a][2] += dr
            totals[b][0] += bw; totals[b][1] += aw; totals[b][2] += dr
            totals[a][3] += margin_sum; totals[b][3] -= margin_sum
            totals[a][4] += games;      totals[b][4] += games
            print(f"{a:<12} {b:<12} {k:>2}  {aw:>6} {bw:>6} {dr:>5} "
                  f"{margin_sum / games:>+17.2f}  {time.perf_counter() - start:.1f}s", flush=True)

    print("\nOverall standings (all pairs, all K), sorted by average fours margin per game:")
    print(f"{'weight set':<12} {'avg margin':>10} {'wins':>5} {'losses':>6} {'draws':>5} {'games':>5}")
    for name, (w, l, d, m, g) in sorted(totals.items(), key=lambda kv: -kv[1][3] / kv[1][4]):
        print(f"{name:<12} {m / g:>+10.2f} {w:>5} {l:>6} {d:>5} {g:>5}")


if __name__ == "__main__":
    main()