# --- START OF utils.py ---

# --- Module Level Definitions ---
# Moved starting_fen_pieces here so it can be imported
starting_fen_pieces = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"

# Piece representation dictionaries
piece_values_from_char = { # Used for parsing FEN
    'r': 4, 'n': 2, 'b': 3, 'q': 5, 'k': 6, 'p': 1
}
piece_char_from_int = { # Used for printing board
    0: '.', 1: 'P', -1: 'p', 2: 'N', -2: 'n', 3: 'B', -3: 'b',
    4: 'R', -4: 'r', 5: 'Q', -5: 'q', 6: 'K', -6: 'k'
}

# --- Functions ---

def get_starting_board_array():
    """
    Creates a 1D list (64 elements) representing the chessboard
    based on the starting FEN string's piece placement part.
    """
    board_1d = [0] * 64
    # Uses the module-level starting_fen_pieces
    fen_placement = starting_fen_pieces.split(' ')[0] # Get piece part if full FEN is ever used

    rank = 0
    file = 0
    index = 0 # Use index directly instead of calculating rank*8+file inside loop
    for char in fen_placement:
        if char == '/':
            # We expect exactly 8 squares per rank handled by digits/pieces
            continue # Move to next character
        elif char.isdigit():
            empty_squares = int(char)
            # No need for inner loop, just advance index
            index += empty_squares
        elif char.lower() in piece_values_from_char:
            if index < 64: # Ensure we don't go out of bounds
                piece_base_value = piece_values_from_char[char.lower()]
                # Assign positive for upper case (white), negative for lower (black)
                board_1d[index] = piece_base_value if char.isupper() else -piece_base_value
                index += 1
            else:
                 print(f"Warning: FEN parsing went beyond index 63 at char '{char}'")
                 break # Stop processing if index goes too far
        # Handle potential errors/unexpected characters if needed
    return board_1d


def square_to_index_1d(square_notation):
    """Converts algebraic notation (e.g., 'e4') to 0-63 index."""
    try:
        file_char = square_notation[0].lower()
        rank_char = square_notation[1]
        if not ('a' <= file_char <= 'h' and '1' <= rank_char <= '8'):
            raise ValueError("Invalid square format")
        file_index = ord(file_char) - ord('a')
        rank_abs = int(rank_char) # 1 to 8
        # Convert rank (1-8) to 0-7 index where 8->0, 1->7
        rank_index_from_top = 8 - rank_abs
        index_1d = rank_index_from_top * 8 + file_index
        return index_1d
    except (IndexError, ValueError, TypeError):
         raise ValueError(f"Invalid square notation: '{square_notation}'")


def index_1d_to_square(index_1d):
    """Converts 0-63 index to algebraic notation (e.g., 'e4')."""
    if not (0 <= index_1d <= 63):
        raise ValueError("Index out of range (0-63)")
    rank_index_from_top = index_1d // 8 # 0 to 7
    file_index = index_1d % 8 # 0 to 7
    file_char = chr(ord('a') + file_index)
    # Convert rank index (0-7) back to rank number (8-1)
    rank_char = str(8 - rank_index_from_top)
    return file_char + rank_char


def piece_int_to_char(piece_value):
    """Converts piece integer value to its character representation."""
    return piece_char_from_int.get(piece_value, '?') # Use '?' for unknown


def print_board(board):
    """Prints a simple ASCII representation of the board."""
    print("\n  a b c d e f g h")
    print(" +-----------------+")
    for rank in range(8):
        print(f"{8-rank}| ", end="")
        for file in range(8):
            index = rank * 8 + file
            piece = board[index]
            symbol = piece_int_to_char(piece)
            print(f"{symbol} ", end="")
        print(f"|{8-rank}")
    print(" +-----------------+")
    print("  a b c d e f g h")


def print_board_with_moves(board, possible_moves, piece_sq_notation=None):
    """Prints board highlighting potential move destinations ('x') for a given piece."""
    # Get indices of destination squares
    move_squares_indexes = set(move[1] for move in possible_moves)
    # Get index of the piece being considered (optional)
    piece_index_sq = None
    if piece_sq_notation:
        try:
            piece_index_sq = square_to_index_1d(piece_sq_notation)
        except ValueError:
            print(f"Warning: Invalid square notation '{piece_sq_notation}' provided.")

    print(f"\nBoard with moves for piece at {piece_sq_notation or 'N/A'}:")
    print("  a b c d e f g h")
    print(" +-----------------+")
    for rank_idx in range(8): # Iterate 0-7 for array indexing
        print(f"{8-rank_idx}| ", end="") # Print rank label 8 down to 1
        for file_idx in range(8): # Iterate 0-7
            index = rank_idx * 8 + file_idx
            symbol = piece_int_to_char(board[index])

            # Override symbol if it's a destination square
            if index in move_squares_indexes:
                symbol = 'x'
            # Optionally highlight the source piece (e.g., with '*')
            elif index == piece_index_sq:
                 symbol = '*' # Or keep original symbol if preferred

            print(f"{symbol} ", end="")
        print(f"|{8-rank_idx}")
    print(" +-----------------+")
    print("  a b c d e f g h")


# --- Main Execution Block (for testing utils.py directly) ---
if __name__ == "__main__":
    print("Testing utils.py functions...")

    # Test board generation
    start_board = get_starting_board_array()
    print("Generated starting board (1D array):")
    # print(start_board) # Keep commented unless needed, it's long
    print("Printing board:")
    print_board(start_board)

    # Test coordinate conversions
    print("\nTesting coordinate conversions:")
    test_squares = ["a1", "h8", "e4", "d5"]
    for sq in test_squares:
        idx = square_to_index_1d(sq)
        sq_back = index_1d_to_square(idx)
        print(f"{sq} -> Index {idx} -> {sq_back}")

    # Example test for print_board_with_moves (requires moves)
    # Simulate some moves for white pawn e2-e4
    # test_moves = [(square_to_index_1d('e2'), square_to_index_1d('e3')),
    #               (square_to_index_1d('e2'), square_to_index_1d('e4'))]
    # print_board_with_moves(start_board, test_moves, 'e2')

    print("\nUtils testing finished.")

# --- END OF utils.py ---