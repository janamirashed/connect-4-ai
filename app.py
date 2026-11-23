from flask import Flask, render_template, request, jsonify
from game import Board, Minimax, PLAYER_HUMAN, PLAYER_AI

app = Flask(__name__)

# In-memory board state for the current session (or managed per request)
ROWS, COLS = 6, 7
current_board = Board(rows=ROWS, cols=COLS)
current_depth_k = 4


def error(message, status=400):
    return jsonify({"error": message}), status

def winner_label(human, ai):
    return "human" if human > ai else "ai" if ai > human else "draw"


def board_payload(extra=None):
    payload = current_board.to_dict()           # grid, rows, cols, heights, scores, is_full
    payload["k"] = current_depth_k
    payload["game_over"] = payload["is_full"]
    payload["winner"] = (
        winner_label(payload["scores"]["human"], payload["scores"]["ai"])
        if payload["is_full"] else None
    )
    if extra:
        payload.update(extra)                   # e.g. row, col, value, tree, time
    return payload

@app.route("/")
def index():
    """Render the Connect 4 GUI page."""
    return render_template("index.html")


@app.route("/api/reset", methods=["POST"])
def reset_game():
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
    """Handle human player move."""
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
    """Compute and play AI move."""
    global current_board, current_depth_k
    if current_board.is_full():
        return error("Game is already over")

    minimax = Minimax(depth_k=current_depth_k)
    col, value, tree, nodes, elapsed = minimax.get_best_move(current_board)

    if col is None or not current_board.drop_piece(col, PLAYER_AI):
        return error("AI has no valid move")

    return jsonify(board_payload({
        "row": current_board.landing_row(col),
        "col": col,
        "value": value,
        "tree": tree.to_dict(),
        "time": elapsed,
        "nodes_expanded": nodes,
    }))

if __name__ == "__main__":
    app.run(debug=True, port=5000)