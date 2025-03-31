import utils as u

#Constants
knight_move_offsets = [
    (-2, 1), (-2, -1), (2, 1), (2, -1),
    (-1, 2), (-1, -2), (1, 2), (1, -2)
]
king_move_offsets = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, 1), (-1, -1), (1, 1), (1, -1)
]
rook_directions = [(-1, 0), (1, 0), (0, -1), (0, 1)] 
bishop_diagonal_directions = [(-1, 1), (-1, -1), (1, 1), (1, -1)] 
pawn_attack_directions_white = [(-1, -1), (-1, 1)] 
pawn_attack_directions_black = [(1, -1), (1, 1)] 

def is_valid_square(rank, file):
    return 0 <= rank <= 7 and 0 <= file <= 7

def is_valid_index(index):
    return 0 <= index <= 63

def is_square_attacked(board, square_index, attacking_color_is_white):
    target_rank, target_file = divmod(square_index, 8)
    opponent_color_sign = 1 if attacking_color_is_white else -1

    pawn_attack_dirs = pawn_attack_directions_black if attacking_color_is_white else pawn_attack_directions_white
    for dr, df in pawn_attack_dirs:
        check_rank, check_file = target_rank + dr, target_file + df
        if is_valid_square(check_rank, check_file):
            check_index = check_rank * 8 + check_file
            piece = board[check_index]
            if piece == opponent_color_sign * 1:
                return True

    for dr, df in knight_move_offsets:
        check_rank, check_file = target_rank + dr, target_file + df
        if is_valid_square(check_rank, check_file):
            check_index = check_rank * 8 + check_file
            piece = board[check_index]
            if piece == opponent_color_sign * 2:
                return True

    sliding_directions = rook_directions + bishop_diagonal_directions
    for dr, df in sliding_directions:
        current_rank, current_file = target_rank + dr, target_file + df
        while is_valid_square(current_rank, current_file):
            current_index = current_rank * 8 + current_file
            piece = board[current_index]
            if piece != 0:
                piece_type = abs(piece)
                is_opponent_piece = (piece * opponent_color_sign > 0)

                if is_opponent_piece:
                    is_rook_move = (dr == 0 or df == 0)
                    is_bishop_move = (abs(dr) == abs(df))

                    if piece_type == 5: #Q
                        return True
                    if piece_type == 4 and is_rook_move: #R on r line
                        return True
                    if piece_type == 3 and is_bishop_move: #B on b line
                        return True
                break
            current_rank += dr
            current_file += df

    for dr, df in king_move_offsets:
        check_rank, check_file = target_rank + dr, target_file + df
        if is_valid_square(check_rank, check_file):
            check_index = check_rank * 8 + check_file
            piece = board[check_index]
            if piece == opponent_color_sign * 6:
                return True

    return False

#Piece Move Generators
def generate_rook_moves(board, rook_index):
    possible_moves = []
    rook_piece = board[rook_index]
    if abs(rook_piece) not in [4, 5]:
        return possible_moves
    is_white = rook_piece > 0
    start_rank, start_file = divmod(rook_index, 8)

    for dr, df in rook_directions:
        current_rank, current_file = start_rank + dr, start_file + df
        while is_valid_square(current_rank, current_file):
            current_index = current_rank * 8 + current_file
            target_piece = board[current_index]

            if target_piece == 0:
                possible_moves.append((rook_index, current_index))
            else:
                if (target_piece > 0 and not is_white) or (target_piece < 0 and is_white):
                    possible_moves.append((rook_index, current_index))
                break
            current_rank += dr
            current_file += df
    return possible_moves

def generate_bishop_moves(board, bishop_index):
    possible_moves = []
    bishop_piece = board[bishop_index]
    if abs(bishop_piece) not in [3, 5]:
        return possible_moves
    is_white = bishop_piece > 0
    start_rank, start_file = divmod(bishop_index, 8)

    for dr, df in bishop_diagonal_directions:
        current_rank, current_file = start_rank + dr, start_file + df
        while is_valid_square(current_rank, current_file):
            current_index = current_rank * 8 + current_file
            target_piece = board[current_index]

            if target_piece == 0:
                possible_moves.append((bishop_index, current_index))
            else:
                if (target_piece > 0 and not is_white) or (target_piece < 0 and is_white):
                    possible_moves.append((bishop_index, current_index))
                break
            current_rank += dr
            current_file += df
    return possible_moves

def generate_queen_moves(board, queen_index):
    if abs(board[queen_index]) != 5:
        return []
    possible_moves = generate_rook_moves(board, queen_index)
    possible_moves.extend(generate_bishop_moves(board, queen_index))
    return possible_moves

def generate_knight_moves(board, knight_index):
    possible_moves = []
    knight_piece = board[knight_index]
    if abs(knight_piece) != 2:
        return possible_moves
    is_white = knight_piece > 0
    start_rank, start_file = divmod(knight_index, 8)

    for dr, df in knight_move_offsets:
        target_rank, target_file = start_rank + dr, start_file + df
        if is_valid_square(target_rank, target_file):
            target_index = target_rank * 8 + target_file
            target_piece = board[target_index]
            if target_piece == 0 or \
               (target_piece > 0 and not is_white) or \
               (target_piece < 0 and is_white):
                possible_moves.append((knight_index, target_index))
    return possible_moves

def generate_pawn_moves(board, pawn_index, en_passant_target_index):
    possible_moves = []
    pawn_piece = board[pawn_index]
    if abs(pawn_piece) != 1:
        return possible_moves

    is_white = pawn_piece > 0
    start_rank, start_file = divmod(pawn_index, 8)
    direction = -1 if is_white else 1
    promotion_rank = 0 if is_white else 7
    promotion_pieces = ['q', 'r', 'n', 'b']

    one_forward_rank = start_rank + direction
    if is_valid_square(one_forward_rank, start_file):
        one_forward_index = one_forward_rank * 8 + start_file
        if board[one_forward_index] == 0:
            if one_forward_rank == promotion_rank:
                for promo_char in promotion_pieces:
                    possible_moves.append((pawn_index, one_forward_index, promo_char))
            else:
                possible_moves.append((pawn_index, one_forward_index))

            initial_rank = 6 if is_white else 1
            if start_rank == initial_rank:
                two_forward_rank = start_rank + 2 * direction
                two_forward_index = two_forward_rank * 8 + start_file
                if board[two_forward_index] == 0:
                    possible_moves.append((pawn_index, two_forward_index))

    capture_dirs = [(-1, -1), (-1, 1)] if is_white else [(1, -1), (1, 1)] 
    for dr, df in capture_dirs:
        capture_rank, capture_file = start_rank + dr, start_file + df
        if is_valid_square(capture_rank, capture_file):
            capture_index = capture_rank * 8 + capture_file
            target_piece = board[capture_index]

            if target_piece != 0 and ((target_piece > 0 and not is_white) or (target_piece < 0 and is_white)):
                if capture_rank == promotion_rank:
                     for promo_char in promotion_pieces:
                         possible_moves.append((pawn_index, capture_index, promo_char))
                else:
                    possible_moves.append((pawn_index, capture_index))

            correct_ep_rank = 3 if is_white else 4
            if capture_index == en_passant_target_index and start_rank == correct_ep_rank:

                 if is_valid_square(capture_rank, capture_file):
                    possible_moves.append((pawn_index, capture_index, 'ep'))
    return possible_moves


def generate_king_moves(board, king_index, current_castling_rights):
    possible_moves = []
    king_piece = board[king_index]
    if abs(king_piece) != 6:
        return possible_moves

    is_white = king_piece > 0
    start_rank, start_file = divmod(king_index, 8)
    opponent_is_white = not is_white

    for dr, df in king_move_offsets:
        target_rank, target_file = start_rank + dr, start_file + df
        if is_valid_square(target_rank, target_file):
            target_index = target_rank * 8 + target_file
            target_piece = board[target_index]
            if target_piece == 0 or \
               (target_piece > 0 and not is_white) or \
               (target_piece < 0 and is_white):
                possible_moves.append((king_index, target_index))


    king_char = 'K' if is_white else 'k'
    queen_char = 'Q' if is_white else 'q'
    king_home_index = u.square_to_index_1d('e1') if is_white else u.square_to_index_1d('e8')
    king_side_rook_index = u.square_to_index_1d('h1') if is_white else u.square_to_index_1d('h8')
    queen_side_rook_index = u.square_to_index_1d('a1') if is_white else u.square_to_index_1d('a8')
    rook_value = 4 if is_white else -4

    if king_index == king_home_index:
        castle_right = king_char in current_castling_rights
        rook_present = board[king_side_rook_index] == rook_value
        f_sq_idx = king_home_index + 1
        g_sq_idx = king_home_index + 2
        squares_empty = board[f_sq_idx] == 0 and board[g_sq_idx] == 0
        if castle_right and rook_present and squares_empty:
            king_not_in_check = not is_square_attacked(board, king_home_index, opponent_is_white)
            f_sq_safe = not is_square_attacked(board, f_sq_idx, opponent_is_white)
            g_sq_safe = not is_square_attacked(board, g_sq_idx, opponent_is_white)
            if king_not_in_check and f_sq_safe and g_sq_safe:
                possible_moves.append((king_index, g_sq_idx, 'castle_k'))

        castle_right = queen_char in current_castling_rights
        rook_present = board[queen_side_rook_index] == rook_value
        b_sq_idx = king_home_index - 3
        c_sq_idx = king_home_index - 2
        d_sq_idx = king_home_index - 1
        squares_empty = board[b_sq_idx] == 0 and board[c_sq_idx] == 0 and board[d_sq_idx] == 0
        if castle_right and rook_present and squares_empty:
            king_not_in_check = not is_square_attacked(board, king_home_index, opponent_is_white)
            d_sq_safe = not is_square_attacked(board, d_sq_idx, opponent_is_white)
            c_sq_safe = not is_square_attacked(board, c_sq_idx, opponent_is_white)
            if king_not_in_check and d_sq_safe and c_sq_safe:
                 possible_moves.append((king_index, c_sq_idx, 'castle_q')) 

    return possible_moves

def generate_pseudo_legal_moves(board, is_white_turn, current_castling_rights, current_en_passant_target):
    all_moves = []
    for index in range(64):
        piece = board[index]
        if piece == 0: continue 

        piece_is_white = piece > 0
        if piece_is_white == is_white_turn:
            piece_type = abs(piece)
            moves = []
            if piece_type == 1:
                moves = generate_pawn_moves(board, index, current_en_passant_target)
            elif piece_type == 2:
                moves = generate_knight_moves(board, index)
            elif piece_type == 3:
                moves = generate_bishop_moves(board, index)
            elif piece_type == 4:
                moves = generate_rook_moves(board, index)
            elif piece_type == 5:
                moves = generate_queen_moves(board, index)
            elif piece_type == 6:
                moves = generate_king_moves(board, index, current_castling_rights)
            if moves: 
                all_moves.extend(moves)

    return all_moves