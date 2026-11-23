from flask import Flask, render_template, request, jsonify
from game import Board, Minimax, PLAYER_HUMAN, PLAYER_AI

app = Flask(__name__)

# In-memory board state for the current session (or managed per request)
# Default dimensions: 6 rows x 7 cols
current_board = Board(rows=6, cols=7)
current_depth_k = 4


@app.route("/")
def index():
    """Render the Connect 4 GUI page."""
    return render_template("index.html")


@app.route("/api/reset", methods=["POST"])
def reset_game():
    """Reset the game board with optional custom dimensions and depth K."""
    global current_board, current_depth_k
    data = request.get_json() or {}
    rows = data.get("rows", 6)
    cols = data.get("cols", 7)
    current_depth_k = data.get("k", 4)

    # TODO: Reinitialize board with rows and cols
    # Return JSON with initial board state and scores
    pass


@app.route("/api/human-move", methods=["POST"])
def human_move():
    """Handle human player move."""
    global current_board
    data = request.get_json() or {}
    col = data.get("col")

    # TODO: Validate move, drop human piece, check full board
    # Return JSON with updated board, scores, and status
    pass

@app.route("/api/ai-move", methods=["POST"])
def ai_move():
    """Compute and play AI move."""
    global current_board, current_depth_k

    if current_board.is_full():
        return jsonify({"error": "Game is already over"}), 400

    # Run the search
    minimax = Minimax(depth_k=current_depth_k)
    col, value, tree, nodes, elapsed = minimax.get_best_move(current_board)

    # Play the chosen column
    if col is None or not current_board.drop_piece(col, PLAYER_AI):
        return jsonify({"error": "AI has no valid move"}), 400
    row = current_board.landing_row(col)

    state = current_board.to_dict()
    human, ai = state["scores"]["human"], state["scores"]["ai"]
    state.update({
        "row": row,
        "col": col,
        "value": value,
        "tree": tree.to_dict(),
        "time": elapsed,                 # seconds
        "nodes_expanded": nodes,
        "k": current_depth_k,
        "game_over": state["is_full"],
        "winner": (
            ("human" if human > ai else "ai" if ai > human else "draw")
            if state["is_full"] else None
        ),
    })
    return jsonify(state)

if __name__ == "__main__":
    app.run(debug=True, port=5000)