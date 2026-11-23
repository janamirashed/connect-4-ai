"""Flask Web Application for Connect 4 AI (GUI & API).

Provides:
- Web GUI interface for Human vs Computer gameplay
- Visual representation of the Connect 4 grid, scores, and status
- Display of the Minimax search tree (Bonus)
"""

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
    """Compute and play AI move using Minimax with Alpha-Beta pruning."""
    global current_board, current_depth_k

    # TODO:
    # 1. Instantiate Minimax(depth_k=current_depth_k)
    # 2. Run minimax.get_best_move(current_board)
    # 3. Drop AI piece into the chosen column
    # 4. Print minimax tree to console (as required by assignment)
    # 5. Return JSON with chosen column, updated board, scores, tree data, time, and nodes expanded
    pass


if __name__ == "__main__":
    app.run(debug=True, port=5000)