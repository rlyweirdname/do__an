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

castling_rights = "KQkq"

import utils as u

def is_square_attacked(board, square_index, attacking_color_is_white):
    for attacker_index in range(64): 
        piece = board[attacker_index]
        if piece != 0:
            is_attacker_white = piece > 0
            if (attacking_color_is_white and piece > 0) or (not attacking_color_is_white and piece < 0): 
                piece_type = abs(piece)
                if piece_type == 1:
                    pawn_attack_dirs = pawn_attack_directions_white if is_attacker_white else pawn_attack_directions_black
                    attacker_rank = attacker_index // 8
                    attacker_file = attacker_index % 8
                    for rank_change, file_change in pawn_attack_dirs:
                        target_rank = attacker_rank + rank_change
                        target_file = attacker_file + file_change
                        if 0 <= target_rank <= 7 and 0 <= target_file <= 7:
                            target_index = target_rank * 8 + target_file
                            if target_index == square_index:
                                return True 

                elif piece_type == 2: 
                    attacker_rank = attacker_index // 8
                    attacker_file = attacker_index % 8
                    for rank_change, file_change in knight_move_offsets: 
                        target_rank = attacker_rank + rank_change
                        target_file = attacker_file + file_change
                        if 0 <= target_rank <= 7 and 0 <= target_file <= 7:
                            target_index = target_rank * 8 + target_file
                            if target_index == square_index:
                                return True 

                elif piece_type == 3:
                    attacker_rank = attacker_index // 8
                    attacker_file = attacker_index % 8
                    for rank_change, file_change in bishop_diagonal_directions:
                        current_rank, current_file = attacker_rank + rank_change, attacker_file + file_change
                        while 0 <= current_rank <= 7 and 0 <= current_file <= 7:
                            current_index = current_rank * 8 + current_file
                            if current_index == square_index:
                                return True 
                            if board[current_index] != 0: 
                                break
                            current_rank += rank_change
                            current_file += file_change

                elif piece_type == 4: 
                    attacker_rank = attacker_index // 8
                    attacker_file = attacker_index % 8
                    for rank_change, file_change in rook_directions:
                        current_rank, current_file = attacker_rank + rank_change, attacker_file + file_change
                        while 0 <= current_rank <= 7 and 0 <= current_file <= 7:
                            current_index = current_rank * 8 + current_file
                            if current_index == square_index:
                                return True 
                            if board[current_index] != 0:
                                break
                            current_rank += rank_change
                            current_file += file_change

                elif piece_type == 5:
                    attacker_rank = attacker_index // 8
                    attacker_file = attacker_index % 8
                    for rank_change, file_change in rook_directions + bishop_diagonal_directions: 
                        current_rank, current_file = attacker_rank + rank_change, attacker_file + file_change
                        while 0 <= current_rank <= 7 and 0 <= current_file <= 7:
                            current_index = current_rank * 8 + current_file
                            if current_index == square_index:
                                return True 
                            if board[current_index] != 0:
                                break
                            current_rank += rank_change
                            current_file += file_change

                elif piece_type == 6:
                    attacker_rank = attacker_index // 8
                    attacker_file = attacker_index % 8
                    for rank_change, file_change in king_move_offsets: 
                        target_rank = attacker_rank + rank_change
                        target_file = attacker_file + file_change
                        if 0 <= target_rank <= 7 and 0 <= target_file <= 7:
                            target_index = target_rank * 8 + target_file
                            if target_index == square_index:
                                return True 

    return False

def generate_queen_moves(board, queen_index):
    possible_moves = []
    queen_piece = board[queen_index]
    if abs(queen_piece) != 5: 
        return possible_moves


    rook_moves = generate_rook_moves(board, queen_index)
    possible_moves.extend(rook_moves) 


    bishop_moves = generate_bishop_moves(board, queen_index)
    possible_moves.extend(bishop_moves) 

    return possible_moves 

def generate_rook_moves(board, rook_index):
    possible_moves = []
    rook_piece = board[rook_index]

    if abs(rook_piece) != 4 and abs(rook_piece) != 5:
        return possible_moves
    is_white = rook_piece > 0

    directions = [-8, 8, 1, -1] # Up, Down, Right, Left

    original_rank = rook_index // 8
    original_file = rook_index % 8

    for direction in directions:
        current_rank = original_rank
        current_file = original_file

        while True:
            if direction == 1: 
                current_file += 1
            elif direction == -1: 
                current_file -= 1
            elif direction == -8:
                current_rank -= 1
            elif direction == 8:
                current_rank += 1

            if not (0 <= current_rank <= 7 and 0 <= current_file <= 7):
                break

            current_index = current_rank * 8 + current_file
            target_piece = board[current_index]

            if target_piece == 0:
                possible_moves.append((rook_index, current_index))
            else:
                if (target_piece > 0 and not is_white) or (target_piece < 0 and is_white):
                    possible_moves.append((rook_index, current_index))
                break

    return possible_moves

def generate_bishop_moves(board, bishop_index):

    possible_moves = []
    bishop_piece = board[bishop_index]

    if abs(bishop_piece) != 3 and abs(bishop_piece) != 5:
        return possible_moves
    is_white = bishop_piece > 0

    diagonal_directions = [(-1, 1), (-1, -1), (1, 1), (1, -1)] # Diagonal directions

    original_rank = bishop_index // 8
    original_file = bishop_index % 8

    for rank_change, file_change in diagonal_directions:
        current_rank = original_rank + rank_change
        current_file = original_file + file_change

        while 0 <= current_rank <= 7 and 0 <= current_file <= 7: 
            current_index = current_rank * 8 + current_file 

            target_piece = board[current_index]

            if target_piece == 0: 
                possible_moves.append((bishop_index, current_index))
            else: 
                if (target_piece > 0 and not is_white) or (target_piece < 0 and is_white): 
                    possible_moves.append((bishop_index, current_index))
                break 

            current_rank += rank_change 
            current_file += file_change
        
    return possible_moves

def is_valid_index(index):
    return 0 <= index <= 63


def generate_pawn_moves(board, pawn_index):
    possible_moves = []
    pawn_piece = board[pawn_index]
    if abs(pawn_piece) != 1:
        return possible_moves
    is_white = pawn_piece > 0
    pawn_direction = -8 if is_white else 8

    one_square_forward_index = pawn_index + pawn_direction
    if is_valid_index(one_square_forward_index) and board[one_square_forward_index] == 0:
        if (is_white and one_square_forward_index // 8 == 0) or (not is_white and one_square_forward_index // 8 == 7):
            possible_moves.append((pawn_index, one_square_forward_index, 'q'))
        else:
            possible_moves.append((pawn_index, one_square_forward_index))

    if (is_white and pawn_index // 8 == 6) or (not is_white and pawn_index // 8 == 1):
        two_squares_forward_index = pawn_index + 2 * pawn_direction
        if is_valid_index(two_squares_forward_index) and board[one_square_forward_index] == 0 and board[two_squares_forward_index] == 0:
            possible_moves.append((pawn_index, two_squares_forward_index))

    capture_directions = [pawn_direction - 1, pawn_direction + 1]
    for diagonal_direction in capture_directions:
        capture_index = pawn_index + diagonal_direction
        if is_valid_index(capture_index):
            target_piece = board[capture_index]
            if target_piece != 0 and ((target_piece > 0 and not is_white) or (target_piece < 0 and is_white)):
                if (is_white and capture_index // 8 == 0) or (not is_white and capture_index // 8 == 7):
                    possible_moves.append((pawn_index, capture_index, 'q'))
                else:
                    possible_moves.append((pawn_index, capture_index))

    return possible_moves

def generate_king_moves(board, king_index):

    possible_moves = []
    king_piece = board[king_index]
    if abs(king_piece) != 6:
        return possible_moves
    is_white = king_piece > 0
    original_rank = king_index // 8
    original_file = king_index % 8

    king_moves_no_castle = [ 
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, 1), (-1, -1), (1, 1), (1, -1)
    ]
    for rank_change, file_change in king_moves_no_castle:
        current_rank = original_rank + rank_change
        current_file = original_file + file_change
        if 0 <= current_rank <= 7 and 0 <= current_file <= 7:
            current_index = current_rank * 8 + current_file
            target_piece = board[current_index]
            if target_piece == 0 or (target_piece > 0 and not is_white) or (target_piece < 0 and is_white):
                possible_moves.append((king_index, current_index))

    # --- Castling ---
    if is_white:
        king_side_rook_index = u.square_to_index_1d('h1')
        queen_side_rook_index = u.square_to_index_1d('a1')
        king_home_index = u.square_to_index_1d('e1')

        if king_index == king_home_index:
            # King-side castling (O-O)
            if 'K' in castling_rights: 
                if (board[u.square_to_index_1d('f1')] == 0 and board[u.square_to_index_1d('g1')] == 0 and 
                        board[king_side_rook_index] == 4 and not is_square_attacked(board, u.square_to_index_1d('e1'), False) and 
                        not is_square_attacked(board, u.square_to_index_1d('f1'), False) and 
                        not is_square_attacked(board, u.square_to_index_1d('g1'), False)): 
                    possible_moves.append((king_index, u.square_to_index_1d('g1'), 'castle_kingside')) 

            # Queen-side castling (O-O-O)
            if 'Q' in castling_rights:
                if (board[u.square_to_index_1d('b1')] == 0 and board[u.square_to_index_1d('c1')] == 0 and board[u.square_to_index_1d('d1')] == 0 and 
                        board[queen_side_rook_index] == 4 and not is_square_attacked(board, u.square_to_index_1d('e1'), False) and 
                        not is_square_attacked(board, u.square_to_index_1d('d1'), False) and 
                        not is_square_attacked(board, u.square_to_index_1d('c1'), False)):
                    possible_moves.append((king_index, u.square_to_index_1d('c1'), 'castle_queenside')) 

    else: 
        
        king_side_rook_index = u.square_to_index_1d('h8')
        queen_side_rook_index = u.square_to_index_1d('a8')
        king_home_index = u.square_to_index_1d('e8')

        if king_index == king_home_index:
            
            # King-side castling (O-O)
            if 'k' in castling_rights: 
                if (board[u.square_to_index_1d('f8')] == 0 and board[u.square_to_index_1d('g8')] == 0 and 
                        board[king_side_rook_index] == -4 and not is_square_attacked(board, u.square_to_index_1d('e8'), True) and 
                        not is_square_attacked(board, u.square_to_index_1d('f8'), True) and 
                        not is_square_attacked(board, u.square_to_index_1d('g8'), True)): 
                    possible_moves.append((king_index, u.square_to_index_1d('g8'), 'castle_kingside')) 

            # Queen-side castling (O-O-O)
            if 'q' in castling_rights:
                if (board[u.square_to_index_1d('b8')] == 0 and board[u.square_to_index_1d('c8')] == 0 and board[u.square_to_index_1d('d8')] == 0 and 
                        board[queen_side_rook_index] == -4 and not is_square_attacked(board, u.square_to_index_1d('e8'), True) and 
                        not is_square_attacked(board, u.square_to_index_1d('d8'), True) and 
                        not is_square_attacked(board, u.square_to_index_1d('c8'), True)): 
                    possible_moves.append((king_index, u.square_to_index_1d('c8'), 'castle_queenside')) 


    return possible_moves

def generate_knight_moves(board, knight_index):
  
    possible_moves = []
    knight_piece = board[knight_index]
    if abs(knight_piece) != 2: 
        return possible_moves
    is_white = knight_piece > 0

    knight_move_offsets = [
        (-2, 1), (-2, -1), (2, 1), (2, -1),
        (-1, 2), (-1, -2), (1, 2), (1, -2)  
    ]

    original_rank = knight_index // 8
    original_file = knight_index % 8

    for rank_change, file_change in knight_move_offsets:
        current_rank = original_rank + rank_change
        current_file = original_file + file_change

        if 0 <= current_rank <= 7 and 0 <= current_file <= 7: 
            current_index = current_rank * 8 + current_file
            target_piece = board[current_index]
            if target_piece == 0: 
                possible_moves.append((knight_index, current_index))
            else:
                if (target_piece > 0 and not is_white) or (target_piece < 0 and is_white): 
                    possible_moves.append((knight_index, current_index))

    return possible_moves