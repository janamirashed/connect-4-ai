from flask import Flask, render_template, request, jsonify
from game import Board, Minimax, PLAYER_HUMAN, PLAYER_AI

app = Flask(__name__)

# in-memory game state: standard 6 rows x 7 cols
ROWS, COLS = 6, 7
current_board = Board(rows=ROWS, cols=COLS)
current_depth_k = 4


def error(message, status=400):
    # helper to return json error responses with http status codes
    return jsonify({"error": message}), status


def winner_label(human, ai):
    # decides winner when board is full based on who has more 4-in-a-rows
    return "human" if human > ai else "ai" if ai > human else "draw"


def board_payload(extra=None):
    # bundles current board state, scores, k value, and game status into a json response
    payload = current_board.to_dict()           # grid, rows, cols, heights, scores, is_full
    payload["k"] = current_depth_k
    payload["game_over"] = payload["is_full"]
    payload["winner"] = (
        winner_label(payload["scores"]["human"], payload["scores"]["ai"])
        if payload["is_full"] else None
    )
    if extra:
        payload.update(extra)                   # adds row, col, tree, time_taken, nodes
    return payload


@app.route("/")
def index():
    # serves the html web gui to the browser
    return render_template("index.html")


@app.route("/api/reset", methods=["POST"])
def reset_game():
    # resets the board and starts a fresh game with chosen depth k
    global current_board, current_depth_k
    data = request.get_json() or {}

    try:
        k = int(data.get("k", 4))
    except (TypeError, ValueError):
        return error("k must be an integer")
    if k < 1:
        return error("k must be at least 1")

    current_depth_k = k
    current_board = Board(rows=ROWS, cols=COLS)
    return jsonify(board_payload())


@app.route("/api/human-move", methods=["POST"])
def human_move():
    # handles the human player clicking a column
    global current_board
    data = request.get_json() or {}
    col = data.get("col")

    if current_board.is_full():
        return error("Game is already over")
    if not isinstance(col, int) or not (0 <= col < current_board.cols):
        return error("Invalid column")
    if not current_board.drop_piece(col, PLAYER_HUMAN):
        return error("Column is full")

    row = current_board.landing_row(col)
    return jsonify(board_payload({"row": row, "col": col}))


@app.route("/api/ai-move", methods=["POST"])
def ai_move():
    # triggers minimax to calculate the optimal ai move
    global current_board, current_depth_k
    if current_board.is_full():
        return error("Game is already over")

    data = request.get_json() or {}
    if "k" in data:
        try:
            current_depth_k = max(1, int(data["k"]))
        except (TypeError, ValueError):
            pass

    # run minimax search on the board state
    minimax = Minimax(depth_k=current_depth_k)
    col, value, tree, nodes, elapsed = minimax.get_best_move(current_board)

    if col is None or not current_board.drop_piece(col, PLAYER_AI):
        return error("AI has no valid move")

    # send back updated board, chosen move, tree json, execution time, and nodes expanded
    return jsonify(board_payload({
        "success": True,
        "row": current_board.landing_row(col),
        "col": col,
        "value": value,
        "minimax_value": value,
        "tree": tree.to_dict(),
        "time": elapsed,
        "time_taken": elapsed,
        "nodes_expanded": nodes,
    }))


if __name__ == "__main__":
    app.run(debug=True, port=5000)


# notes and explanations:
#
# 1. role of app.py:
#    - acts as the bridge (rest api) between the python ai backend and the web browser frontend.
#
# 2. main endpoints:
#    - GET  /              : loads index.html (connect-4 board, tree visualizer, metrics panel).
#    - POST /api/reset     : clears the board and sets new depth k.
#    - POST /api/human-move: validates the clicked column and drops player 1's piece.
#    - POST /api/ai-move   : executes minimax with alpha-beta, drops player 2's piece, and returns
#                            the search tree json, nodes expanded count, and computation time.
#
# 3. game-over condition:
#    - game_over is strictly when is_full is true (all 42 slots filled).
#    - winner is computed by comparing total connected-4 scores (human vs ai).
