side_to_move = 'w'
castling_rights = "KQkq"
en_passant_target = None

from move_gen import generate_knight_moves, generate_rook_moves, generate_bishop_moves, generate_queen_moves, generate_pawn_moves, generate_king_moves, is_square_attacked
import utils as u
import cProfile
import pstats
import sys
import time



def evaluate_board(board):

    piece_values = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}

    knight_pst_values = [
    [-167, -89, -34, -49,  61, -97, -15, -107],
    [ -73, -41,  72,  36,  23,  62,   7,  -17],
    [-80, -18,  51,  33,  56,  31,  -4,  -53],
    [-55, -25,  12,  24,  24,  12,  -25, -55],
    [-55, -25,  12,  24,  24,  12,  -25, -55],
    [-80, -18,  51,  33,  56,  31,  -4,  -53],
    [ -73, -41,  72,  36,  23,  62,   7,  -17],
    [-167, -89, -34, -49,  61, -97, -15, -107]]
    pawn_pst_values = [
    [   0,   0,   0,   0,   0,   0,   0,   0],
    [  78,  83,  44,  10,  26,  53, -32,   1],
    [  56,  51,  24,  -5,  -6,  13,  -4, -11],
    [  52,  35,   1, -10, -19,   0,  10,  -8],
    [  46,  21,  -8, -17, -17,  -8,  19,  46],
    [  48,  22,  -8, -16, -16,  -9,  21,  48],
    [  43,  17,  -9,  -18, -18, -9,  17,  43],
    [   0,   0,   0,   0,   0,   0,   0,   0]]
    bishop_pst_values = [
    [ -29,  -8, -25, -38, -27, -44,  12,  -9],
    [ -43, -14, -42, -29, -11, -22,  -9, -32],
    [ -25, -12, -20, -16, -17,  18,  -4,  -14],
    [ -13,  -3, -14, -15, -14, -5,  -1,  -13],
    [ -13,  -3, -14, -15, -14, -5,  -1,  -13],
    [ -25, -12, -20, -16, -17,  18,  -4,  -14],
    [ -43, -14, -42, -29, -11, -22,  -9, -32],
    [ -29,  -8, -25, -38, -27, -44,  12,  -9]
    ]
    rook_pst_values = [
    [  35,  29,  33,   4,  37,  33,  56,  50],
    [  55,  29,  56,  55,  55,  62,  56,  55],
    [  -2,   4,  16,  51,  47,  12,  26,  28],
    [  -3,  -9,  -2,  12,  14,  -1,  -3,  -4],
    [  -3,  -9,  -2,  12,  14,  -1,  -3,  -4],
    [  -2,   4,  16,  51,  47,  12,  26,  28],
    [  55,  29,  56,  55,  55,  62,  56,  55],
    [  35,  29,  33,   4,  37,  33,  56,  50]
    ]
    queen_pst_values = [
    [  -9,  22,  22,  27,  27,  22,  22,  -9],
    [ -16, -16, -16,  -7,  -7, -16, -16, -16],
    [ -16, -16, -17,  13,  14, -17, -16, -16],
    [  -3, -14,  -2,  -5,  -5,  -2, -14,  -3],
    [  -3, -14,  -2,  -5,  -5,  -2, -14,  -3],
    [ -16, -16, -17,  13,  14, -17, -16, -16],
    [ -16, -16, -16,  -7,  -7, -16, -16, -16],
    [  -9,  22,  22,  27,  27,  22,  22,  -9]
    ]
    king_pst_values = [
    [ -65, -23, -15, -15, -15, -15, -23, -65],
    [ -44, -15, -13, -12, -12, -13, -15, -44],
    [ -28,  -8,  -6,  -7,  -7,  -6,  -8, -28],
    [ -15,  -4,   2,  -8,  -8,   2,  -4, -15],
    [ -15,  -4,   2,  -8,  -8,   2,  -4, -15],
    [ -28,  -8,  -6,  -7,  -7,  -6,  -8, -28],
    [ -44, -15, -13, -12, -12, -13, -15, -44],
    [ -65, -23, -15, -15, -15, -15, -23, -65]
    ]

    pst_tables = {
        'n': knight_pst_values,
        'p': pawn_pst_values,
        'b': bishop_pst_values,
        'r': rook_pst_values,
        'q': queen_pst_values,
        'k': king_pst_values
    }


    white_score = 0
    black_score = 0

    for index in range(64):
        piece = board[index]
        rank = index // 8
        file = index % 8

        if piece != 0: # Not an empty square
            piece_type_char = '.' # Initialize
            if piece > 0: # White pieces
                if piece == 1: piece_type_char = 'p'; white_score += piece_values['p']; white_score += pawn_pst_values[rank][file]
                elif piece == 2: piece_type_char = 'n'; white_score += piece_values['n']; white_score += knight_pst_values[rank][file]
                elif piece == 3: piece_type_char = 'b'; white_score += piece_values['b']; white_score += bishop_pst_values[rank][file]
                elif piece == 4: piece_type_char = 'r'; white_score += piece_values['r']; white_score += rook_pst_values[rank][file]
                elif piece == 5: piece_type_char = 'q'; white_score += piece_values['q']; white_score += queen_pst_values[rank][file]
                elif piece == 6: piece_type_char = 'k'; piece_char = 'K'; 
                white_score += king_pst_values[rank][file] 
            else: # Black pieces (piece < 0)
                if piece == -1: piece_type_char = 'p'; black_score += piece_values['p']; black_score += pawn_pst_values[7-rank][file] 
                elif piece == -2: piece_type_char = 'n'; black_score += piece_values['n']; black_score += knight_pst_values[7-rank][file] 
                elif piece == -3: piece_type_char = 'b'; black_score += piece_values['b']; black_score += bishop_pst_values[7-rank][file] 
                elif piece == -4: piece_type_char = 'r'; black_score += piece_values['r']; black_score += rook_pst_values[7-rank][file] 
                elif piece == -5: piece_type_char = 'q'; black_score += piece_values['q']; black_score += queen_pst_values[7-rank][file] 
                elif piece == -6: piece_type_char = 'k'; piece_char = 'k';
                black_score += king_pst_values[7-rank][file] 

    return white_score - black_score

def is_king_in_check(board, color_is_white):
    king_piece_value = 6 if color_is_white else -6 
    king_index = -1 


    for index in range(64):
        if board[index] == king_piece_value:
            king_index = index
            break

    if king_index == -1: 
        return False

    return is_square_attacked(board, king_index, not color_is_white)

def get_legal_moves(board, is_white_turn):
    legal_moves = []

    for from_index in range(64):
        piece = board[from_index]

        if piece != 0:
            if (is_white_turn and piece > 0) or (not is_white_turn and piece < 0): # Correct color piece

                piece_type = abs(piece)

                possible_piece_moves = []
                if piece_type == 1: possible_piece_moves = generate_pawn_moves(board, from_index)
                elif piece_type == 2: possible_piece_moves = generate_knight_moves(board, from_index)
                elif piece_type == 3: possible_piece_moves = generate_bishop_moves(board, from_index)
                elif piece_type == 4: 
                    possible_piece_moves = generate_rook_moves(board, from_index) 
                elif piece_type == 5: possible_piece_moves = generate_queen_moves(board, from_index)
                elif piece_type == 6: possible_piece_moves = generate_king_moves(board, from_index)

                for move in possible_piece_moves:
                    to_index = move[1]
                    temp_board = list(board)
                    moved_piece = temp_board[from_index]
                    captured_piece = temp_board[to_index]
                    temp_board[from_index] = 0
                    temp_board[to_index] = moved_piece

                    king_in_check_after_move = is_king_in_check(temp_board, is_white_turn)

                    if not king_in_check_after_move: 
                        legal_moves.append(move) 

    return legal_moves

def find_best_move(board, depth, is_maximizing_player=True):
    best_move = None
    best_value = -9999

    possible_moves = get_legal_moves(board, is_maximizing_player)
    if not possible_moves:
        return None

    alpha = -9999
    beta = +9999

    for move in possible_moves:
        from_index, to_index = move[:2]

        captured_piece = make_move(board, move)

        move_value = alphabeta(board, depth - 1, alpha, beta, not is_maximizing_player)

        undo_move(board, move, captured_piece)

        if move_value > best_value:
            best_value = move_value
            best_move = move

        alpha = max(alpha, best_value)

    return best_move


def minimax(board, depth, is_maximizing_player):
    if depth == 0:
        return evaluate_board(board)

    if is_maximizing_player:
        best_value = -9999
        possible_moves = get_legal_moves(board, True)
        for move in possible_moves:
            from_index, to_index = move[:2]
            captured_piece = make_move(board, move) 
            was_promotion_move = False 
            was_castling_move = None 
            if len(move) > 2:
                if isinstance(move[2], str) and move[2].startswith('castle'):
                    was_castling_move = move[2]
                else:
                    was_promotion_move = True 



            value = minimax(board, depth - 1, False)

  
            undo_move(board, move, captured_piece, was_promotion_move, was_castling_move) 

            best_value = max(best_value, value)
        return best_value

    else:
        best_value = +9999
        possible_moves = get_legal_moves(board, False)
        for move in possible_moves:
            from_index, to_index = move[:2]

            captured_piece = make_move(board, move)
            was_promotion_move = False
            was_castling_move = None 
            if len(move) > 2:
                if isinstance(move[2], str) and move[2].startswith('castle'):
                    was_castling_move = move[2] 
                else:
                    was_promotion_move = True

            value = minimax(board, depth - 1, True)

            undo_move(board, move, captured_piece, was_promotion_move, was_castling_move)

            best_value = min(best_value, value)
        return best_value


def alphabeta(board, depth, alpha, beta, is_maximizing_player):
    if depth == 0:
        return evaluate_board(board)

    if is_maximizing_player: 
        best_value = -9999
        possible_moves = get_legal_moves(board, True)
        for move in possible_moves:
            from_index, to_index = move[:2]

            
            captured_piece = make_move(board, move)
            was_promotion_move = False
            was_castling_move = None 
            if len(move) > 2:
                if isinstance(move[2], str) and move[2].startswith('castle'):
                    was_castling_move = move[2] 
                else:
                    was_promotion_move = True
            value = alphabeta(board, depth - 1, alpha, beta, not is_maximizing_player)
            undo_move(board, move, captured_piece, was_promotion_move, was_castling_move)

            best_value = max(best_value, value)
            alpha = max(alpha, best_value)
            if beta <= alpha:
                break
        return best_value

    else: 
        best_value = +9999
        possible_moves = get_legal_moves(board, False)
        for move in possible_moves:
            from_index, to_index = move[:2]


            captured_piece = make_move(board, move)


            value = alphabeta(board, depth - 1, alpha, beta, True)


            undo_move(board, move, captured_piece)

            best_value = min(best_value, value)
            beta = min(beta, best_value)
            if beta <= alpha:
                break
        return best_value

"""
core function
"""

def make_move(board, move):
    from_index, to_index = move[:2]
    promotion_piece = None
    castle_type = None 
    if len(move) > 2:
        if isinstance(move[2], str) and move[2].startswith('castle'):
            castle_type = move[2] 
        else:
            promotion_piece = move[2] 

    piece = board[from_index]
    is_white = piece > 0  
    captured_piece = board[to_index]

    board[to_index] = piece
    board[from_index] = 0

    if promotion_piece: 
        piece_color = 1 if piece > 0 else -1
        promotion_value = 0
        if promotion_piece.lower() == 'q':
            promotion_value = 5
        elif promotion_piece.lower() == 'r':
            promotion_value = 4
        elif promotion_piece.lower() == 'n':
            promotion_value = 2
        elif promotion_piece.lower() == 'b':
            promotion_value = 3
        board[to_index] = promotion_value * piece_color
    elif castle_type == 'castle_kingside': 
        rank = from_index // 8 
        rook_from_index = rank * 8 + 7  
        rook_to_index = rank * 8 + 5 
        rook_piece = board[rook_from_index]
        board[rook_from_index] = 0 
        board[rook_to_index] = rook_piece
    elif castle_type == 'castle_queenside': 
        rank = from_index // 8 
        rook_from_index = rank * 8 + 0 
        rook_to_index = rank * 8 + 3  
        rook_piece = board[rook_from_index]
        board[rook_from_index] = 0
        board[rook_to_index] = rook_piece


    global castling_rights


    if abs(piece) == 6:  
        if is_white:
            castling_rights = castling_rights.replace('K', '', 1).replace('Q', '', 1) 
        else:
            castling_rights = castling_rights.replace('k', '', 1).replace('q', '', 1)
    elif abs(piece) == 4: 
        if from_index == u.square_to_index_1d('a1'):  # White queenside rook
            castling_rights = castling_rights.replace('Q', '', 1)
        elif from_index == u.square_to_index_1d('h1'):  # White kingside rook
            castling_rights = castling_rights.replace('K', '', 1)
        elif from_index == u.square_to_index_1d('a8'):  # Black queenside rook
            castling_rights = castling_rights.replace('q', '', 1)
        elif from_index == u.square_to_index_1d('h8'):  # Black kingside rook
            castling_rights = castling_rights.replace('k', '', 1)

    return captured_piece


def undo_move(board, move, captured_piece, was_promotion=False, was_castling=None):

    from_index, to_index = move[:2]
    moved_piece = board[to_index]

    board[from_index] = moved_piece
    board[to_index] = captured_piece

    if was_promotion:
        original_pawn_value = 1 if moved_piece > 0 else -1
        board[from_index] = original_pawn_value
    elif was_castling == 'castle_kingside': 
        rank = from_index // 8
        rook_from_index = rank * 8 + 7
        rook_to_index = rank * 8 + 5 
        rook_piece = board[rook_to_index]
        board[rook_to_index] = 0
        board[rook_from_index] = rook_piece
    elif was_castling == 'castle_queenside':
        rank = from_index // 8
        rook_from_index = rank * 8 + 0 
        rook_to_index = rank * 8 + 3 
        rook_piece = board[rook_to_index]
        board[rook_to_index] = 0
        board[rook_from_index] = rook_piece

    

def create_test_board_minimax_start():

    return u.get_starting_board_array() 


test_board_minimax = create_test_board_minimax_start()
current_board = test_board_minimax

start_time = time.time() 
best_move_found = find_best_move(current_board, depth=4) 
end_time = time.time()
search_time = end_time - start_time

print(f"Nước đi hay nhất theo Minimax (depth 6): {best_move_found}")
print(f"Đánh giá Minimax của nước đi tốt nhất: {alphabeta(current_board, 6, +9999, -9999, True)}")
print(f"Thời gian tìm kiếm: {search_time:.4f} giây")

if best_move_found:
    from_sq = u.index_1d_to_square(best_move_found[0])
    to_sq = u.index_1d_to_square(best_move_found[1])
    print(f"Nước đi hay nhất theo ký hiệu đại số: {from_sq}-{to_sq}")

    captured_piece = make_move(current_board, best_move_found)
    print("\nBàn cờ sau khi engine đi:")
    u.print_board(current_board)
else:
    print("Không tìm thấy nước đi hợp lệ. Trò chơi kết thúc?")

# current_board = create_test_board_minimax_start()
# is_white_turn = True # White starts
# num_moves = 10

# print("Starting Board:")
# u.print_board(current_board)

# for move_number in range(1, num_moves + 1):
#     print(f"\n--- Move {move_number} - {'White' if is_white_turn else 'Black'} to move ---")
#     start_time = time.time()
#     best_move_found = find_best_move(current_board, depth=2 if move_number <= 2 else 3 if move_number <= 4 else 4) # Deeper search as game progresses (adjust depth as needed)
#     end_time = time.time()
#     search_time = end_time - start_time

#     if best_move_found:
#         from_sq = u.index_1d_to_square(best_move_found[0])
#         to_sq = u.index_1d_to_square(best_move_found[1])
#         move_algebraic = f"{from_sq}-{to_sq}"
#         print(f"{'White' if is_white_turn else 'Black'} best move: {move_algebraic} (depth {4}, time: {search_time:.2f}s)") 

#         captured_piece = make_move(current_board, best_move_found)
#         print("Board after move:")
#         u.print_board(current_board)
#         is_white_turn = not is_white_turn # Switch turns

#     else:
#         print("No legal moves found for {}! Game over.".format('White' if is_white_turn else 'Black'))
#         break 

# print("\n--- Game Over ---")

if __name__ == "__main__":
    current_board = create_test_board_minimax_start()

    profiler = cProfile.Profile()
    profiler.enable() 

    start_time = time.time()
    best_move_found = find_best_move(current_board, depth=4)
    end_time = time.time()

    profiler.disable()

    search_time = end_time - start_time

    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(20)
    sys.stdout.flush()
