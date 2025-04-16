starting_fen_pieces = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"


piece_values_from_char = { 
    'r': 4, 'n': 2, 'b': 3, 'q': 5, 'k': 6, 'p': 1
}
piece_char_from_int = { 
    0: '.', 1: 'P', -1: 'p', 2: 'N', -2: 'n', 3: 'B', -3: 'b',
    4: 'R', -4: 'r', 5: 'Q', -5: 'q', 6: 'K', -6: 'k'
}

def get_starting_board_array():

    board_1d = [0] * 64
    fen_placement = starting_fen_pieces.split(' ')[0] 

    rank = 0
    file = 0
    index = 0
    for char in fen_placement:
        if char == '/':
            continue 
        elif char.isdigit():
            empty_squares = int(char)
            index += empty_squares
        elif char.lower() in piece_values_from_char:
            if index < 64:
                piece_base_value = piece_values_from_char[char.lower()]
                board_1d[index] = piece_base_value if char.isupper() else -piece_base_value
                index += 1
            else:
                 print(f"Warning: FEN parsing went beyond index 63 at char '{char}'")
                 break 
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
        rank_index_from_top = 8 - rank_abs
        index_1d = rank_index_from_top * 8 + file_index
        return index_1d
    except (IndexError, ValueError, TypeError):
         raise ValueError(f"Invalid square notation: '{square_notation}'")


def index_1d_to_square(index_1d):
    """Converts 0-63 index to algebraic notation (e.g., 'e4')."""
    if not (0 <= index_1d <= 63):
        raise ValueError("Index out of range (0-63)")
    rank_index_from_top = index_1d // 8 
    file_index = index_1d % 8 
    file_char = chr(ord('a') + file_index)
    rank_char = str(8 - rank_index_from_top)
    return file_char + rank_char


def piece_int_to_char(piece_value):
    """Converts piece integer value to its character representation."""
    return piece_char_from_int.get(piece_value, '?')


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
    move_squares_indexes = set(move[1] for move in possible_moves)
    piece_index_sq = None
    if piece_sq_notation:
        try:
            piece_index_sq = square_to_index_1d(piece_sq_notation)
        except ValueError:
            print(f"Warning: Invalid square notation '{piece_sq_notation}' provided.")

    print(f"\nBoard with moves for piece at {piece_sq_notation or 'N/A'}:")
    print("  a b c d e f g h")
    print(" +-----------------+")
    for rank_idx in range(8):
        print(f"{8-rank_idx}| ", end="") 
        for file_idx in range(8): 
            index = rank_idx * 8 + file_idx
            symbol = piece_int_to_char(board[index])

            if index in move_squares_indexes:
                symbol = 'x'

            elif index == piece_index_sq:
                 symbol = '*'

            print(f"{symbol} ", end="")
        print(f"|{8-rank_idx}")
    print(" +-----------------+")
    print("  a b c d e f g h")


if __name__ == "__main__":
    print("Testing utils.py functions...")

    #Test board generation
    start_board = get_starting_board_array()
    print("Generated starting board (1D array):")
    # print(start_board)
    print("Printing board:")
    print_board(start_board)

    print("\nTesting coordinate conversions:")
    test_squares = ["a1", "h8", "e4", "d5"]
    for sq in test_squares:
        idx = square_to_index_1d(sq)
        sq_back = index_1d_to_square(idx)
        print(f"{sq} -> Index {idx} -> {sq_back}")

    # test_moves = [(square_to_index_1d('e2'), square_to_index_1d('e3')),
    #               (square_to_index_1d('e2'), square_to_index_1d('e4'))]
    # print_board_with_moves(start_board, test_moves, 'e2')

    print("\nUtils testing finished.")
