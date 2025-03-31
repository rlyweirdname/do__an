def get_starting_board_array():
    pieces = {
        'r': 4, 'n': 2, 'b': 3, 'q': 5, 'k': 6, 'p': 1
    } 

    starting_fen_pieces = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
    ranks = starting_fen_pieces.split('/')
    board_1d = [0] * 64
    index = 0
    for rank_str in ranks:
        for char in rank_str:
            if char.isdigit():
                empty_squares = int(char)
                for _ in range(empty_squares):
                    board_1d[index] = 0
                    index += 1
            elif char.lower() in pieces:
                piece_value = pieces[char.lower()]
                if char.isupper():
                    board_1d[index] = piece_value
                else:
                    board_1d[index] = -piece_value
                index += 1
    return board_1d

board = get_starting_board_array()
print(board) 



def square_to_index_1d(square_notation):
    file_char = square_notation[0].lower()
    rank_char = square_notation[1]
    file_index = ord(file_char) - ord('a') 
    rank_index = int(rank_char) 
    index_1d = (8 - rank_index) * 8 + file_index 
    return index_1d

def index_1d_to_square(index_1d):
    rank_index = 7 - (index_1d // 8)
    file_index = index_1d % 8 
    file_char = chr(ord('a') + file_index)
    rank_char = str(rank_index + 1) 
    return file_char + rank_char

def print_board(board):
    piece_symbols = {
        0: '.',
        1: 'P', -1: 'p',
        2: 'N', -2: 'n',
        3: 'B', -3: 'b',
        4: 'R', -4: 'r',
        5: 'Q', -5: 'q',
        6: 'K', -6: 'k'
    }
    for rank in range(8):
        row = ""
        for file in range(8):
            piece = board[rank * 8 + file]
            row += piece_symbols[piece] + " "
        print(row)
    print()

def print_board_with_moves(board, possible_moves, piece_sq_notation):
    move_squares_indexes = [move[1] for move in possible_moves]
    print(f"\nTest Board (Engine Move Visualization):")
    for rank in range(8):
        rank_str = ""
        for file in range(8):
            index = rank * 8 + file
            piece = board[index]
            piece_char = '.'
            if piece_sq_notation and piece_sq_notation.lower() != 'none':
                try:
                    piece_index_sq = square_to_index_1d(piece_sq_notation) 
                    if index == piece_index_sq:
                        piece_char = piece_str_from_value(piece)
                except ValueError:
                    print(f"Warning: Invalid square notation '{piece_sq_notation}' passed to print_board_with_moves.") 
                    pass 
            elif piece != 0:
                 piece_char = piece_str_from_value(piece) 

            if index in move_squares_indexes:
                piece_char = 'x'
            rank_str += piece_char + " "
        print(rank_str)


def piece_str_from_value(piece_value):
    piece_abs = abs(piece_value)
    piece_char = '.'
    if piece_abs == 1: piece_char = 'P' if piece_value > 0 else 'p'
    elif piece_abs == 2: piece_char = 'N' if piece_value > 0 else 'n'
    elif piece_abs == 3: piece_char = 'B' if piece_value > 0 else 'b'
    elif piece_abs == 4: 
        piece_char = 'R' if piece_value > 0 else 'r'
        print(f"Debug piece_str_from_value: Piece Value: {piece_value}, Piece Char: {piece_char}")
    elif piece_abs == 5: piece_char = 'Q' if piece_value > 0 else 'q'
    elif piece_abs == 6: piece_char = 'K' if piece_value > 0 else 'k'
    return piece_char

def piece_int_to_char(piece_value):
    piece_map = {
        1: 'P', 2: 'N', 3: 'B', 4: 'R', 5: 'Q', 6: 'K',
        -1: 'p', -2: 'n', -3: 'b', -4: 'r', -5: 'q', -6: 'k'
    }
    return piece_map.get(piece_value, '.')


