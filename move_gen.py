import utils as u 
import sys

#constants
knight_move_offsets = [ (-2,1),(-2,-1),(2,1),(2,-1),(-1,2),(-1,-2),(1,2),(1,-2) ]
king_move_offsets = [ (-1,0),(1,0),(0,-1),(0,1),(-1,1),(-1,-1),(1,1),(1,-1) ]
rook_directions = [ (-1,0),(1,0),(0,-1),(0,1) ]
bishop_diagonal_directions = [ (-1,1),(-1,-1),(1,1),(1,-1) ]
pawn_attack_directions_white_rel = [(-1,-1),(-1,1)] 
pawn_attack_directions_black_rel = [(1,-1),(1,1)]


def generate_rook_moves(board, rook_index):
    moves = []
    p = board[rook_index]; is_w = p > 0
    if abs(p) not in [4, 5]: return moves
    r, f = divmod(rook_index, 8)
    for dr, df in rook_directions:
        cr, cf = r + dr, f + df
        while is_valid_square(cr, cf):
            ci = cr * 8 + cf; t = board[ci]
            if t == 0: moves.append((rook_index, ci))
            else:
                if (t > 0) != is_w: moves.append((rook_index, ci))
                break
            cr += dr; cf += df
    return moves

def generate_bishop_moves(board, bishop_index):
    moves = []
    p = board[bishop_index]; is_w = p > 0
    if abs(p) not in [3, 5]: return moves
    r, f = divmod(bishop_index, 8)
    for dr, df in bishop_diagonal_directions:
        cr, cf = r + dr, f + df
        while is_valid_square(cr, cf):
            ci = cr * 8 + cf; t = board[ci]
            if t == 0: moves.append((bishop_index, ci))
            else:
                if (t > 0) != is_w: moves.append((bishop_index, ci))
                break
            cr += dr; cf += df
    return moves

def generate_queen_moves(board, queen_index):
    if abs(board[queen_index]) != 5: return []
    return generate_rook_moves(board, queen_index) + generate_bishop_moves(board, queen_index)

def generate_knight_moves(board, knight_index):
    moves = []
    p = board[knight_index]; is_w = p > 0
    if abs(p) != 2: return moves
    r, f = divmod(knight_index, 8)
    for dr, df in knight_move_offsets:
        tr, tf = r + dr, f + df
        if is_valid_square(tr, tf):
            ti = tr * 8 + tf; t = board[ti]
            if t == 0 or ((t > 0) != is_w): moves.append((knight_index, ti))
    return moves


def generate_pawn_moves(board, pawn_index, ep_target_idx):
    moves = []
    p = board[pawn_index]
    if abs(p) != 1: return moves
    is_w = p > 0
    r, f = divmod(pawn_index, 8)
    dr_push = -1 if is_w else 1
    start_rank_idx = 6 if is_w else 1
    promo_rank_idx = 0 if is_w else 7
    promos = ['q', 'r', 'n', 'b']

    r1 = r + dr_push
    if 0 <= r1 <= 7:
        i1 = r1 * 8 + f
        if board[i1] == 0:
            if r1 == promo_rank_idx: [moves.append((pawn_index, i1, promo)) for promo in promos]
            else: moves.append((pawn_index, i1))
            if r == start_rank_idx:
                r2 = r + 2 * dr_push
                if 0 <= r2 <= 7:
                    i2 = r2 * 8 + f
                    if board[i2] == 0: moves.append((pawn_index, i2))

    capture_rel_dirs = pawn_attack_directions_white_rel if is_w else pawn_attack_directions_black_rel
    for dr_cap, df_cap in capture_rel_dirs:
        rc, fc = r + dr_cap, f + df_cap
        if is_valid_square(rc, fc):
            ic = rc * 8 + fc
            tc = board[ic]
            if tc != 0 and ((tc > 0) != is_w):
                if rc == promo_rank_idx: [moves.append((pawn_index, ic, promo)) for promo in promos]
                else: moves.append((pawn_index, ic))
            elif ic == ep_target_idx:
                 ep_rank_req = 3 if is_w else 4
                 if r == ep_rank_req and board[ic] == 0:
                      moves.append((pawn_index, ic, 'ep'))
                      
    return moves



def generate_king_moves(board, king_index, cr_str):
    moves = []
    p = board[king_index]
    if abs(p) != 6: return moves
    is_w = p > 0
    r, f = divmod(king_index, 8)
    opp_is_w = not is_w

    for dr, df in king_move_offsets:
        tr, tf = r + dr, f + df
        if is_valid_square(tr, tf):
            ti = tr * 8 + tf; t = board[ti]
            if t == 0 or ((t > 0) != is_w): moves.append((king_index, ti))

    if cr_str == '-': return moves
    home_idx = 60 if is_w else 4
    if king_index == home_idx and not is_square_attacked(board, home_idx, opp_is_w):
        k_char = 'K' if is_w else 'k'
        if k_char in cr_str:
            r_idx, expected_r = (63, 4) if is_w else (7, -4) 
            p1, p2 = home_idx + 1, home_idx + 2
            if board[r_idx] == expected_r and board[p1] == 0 and board[p2] == 0:
                if not is_square_attacked(board, p1, opp_is_w) and not is_square_attacked(board, p2, opp_is_w):
                    moves.append((king_index, p2, 'castle_k'))
        q_char = 'Q' if is_w else 'q'
        if q_char in cr_str:
            r_idx, expected_r = (56, 4) if is_w else (0, -4) 
            p1, p2, p3 = home_idx - 1, home_idx - 2, home_idx - 3 
            if board[r_idx] == expected_r and board[p1]==0 and board[p2]==0 and board[p3]==0:
                 if not is_square_attacked(board, p1, opp_is_w) and not is_square_attacked(board, p2, opp_is_w):
                     moves.append((king_index, p2, 'castle_q'))
                     
    return moves

def is_valid_square(rank, file):
    return 0 <= rank <= 7 and 0 <= file <= 7

def is_valid_index(index):
    return 0 <= index <= 63

def is_square_attacked(board, square_index, attacking_color_is_white):
    target_rank, target_file = divmod(square_index, 8)
    attacking_color_sign = 1 if attacking_color_is_white else -1
    expected_pawn_val = 1 * attacking_color_sign
    expected_knight_val = 2 * attacking_color_sign
    expected_king_val = 6 * attacking_color_sign

    pawn_search_dirs = pawn_attack_directions_black_rel if attacking_color_is_white else pawn_attack_directions_white_rel
    for dr, df in pawn_search_dirs:
        check_rank, check_file = target_rank + dr, target_file + df
        if is_valid_square(check_rank, check_file):
            if board[check_rank * 8 + check_file] == expected_pawn_val: return True

    for dr, df in knight_move_offsets: 
        check_rank, check_file = target_rank + dr, target_file + df
        if is_valid_square(check_rank, check_file):
            if board[check_rank * 8 + check_file] == expected_knight_val: return True

    all_sliding_directions = rook_directions + bishop_diagonal_directions 
    for dr, df in all_sliding_directions:
        is_diagonal_ray = (abs(dr) == abs(df) and dr != 0)
        is_hv_ray = (dr == 0 or df == 0) and not (dr == 0 and df == 0)
        current_rank, current_file = target_rank + dr, target_file + df
        while is_valid_square(current_rank, current_file):
            potential_attacker_idx = current_rank * 8 + current_file
            piece_on_board = board[potential_attacker_idx]
            if piece_on_board != 0: 
                piece_val_abs = abs(piece_on_board)
                piece_color_sign_on_board = 1 if piece_on_board > 0 else -1
                if piece_color_sign_on_board == attacking_color_sign: 
                    if piece_val_abs == 5: return True 
                    elif piece_val_abs == 4 and is_hv_ray: return True 
                    elif piece_val_abs == 3 and is_diagonal_ray: return True
                break 
            current_rank += dr
            current_file += df
            
    for dr, df in king_move_offsets: 
        check_rank, check_file = target_rank + dr, target_file + df
        if is_valid_square(check_rank, check_file):
            if board[check_rank * 8 + check_file] == expected_king_val: return True
                
    return False

def is_king_in_check(board, color_is_white):
    """ Checks if the king of the specified color is in check. """
    king_piece_value = 6 if color_is_white else -6
    king_index = -1
    for index in range(64):
        if board[index] == king_piece_value:
            king_index = index
            break
    if king_index == -1: return False 
    return is_square_attacked(board, king_index, not color_is_white)


def generate_pseudo_legal_moves(board, is_white_turn, current_cr_str, current_ep_idx):
    all_moves = []
    for index in range(64):
        piece = board[index]
        if piece == 0 or ((piece > 0) != is_white_turn): continue
        
        piece_type = abs(piece)
        moves_func = None
        if piece_type == 1: moves_func = generate_pawn_moves
        elif piece_type == 2: moves_func = generate_knight_moves
        elif piece_type == 3: moves_func = generate_bishop_moves
        elif piece_type == 4: moves_func = generate_rook_moves
        elif piece_type == 5: moves_func = generate_queen_moves
        elif piece_type == 6: moves_func = generate_king_moves
        
        if moves_func:
            if piece_type == 1: moves = moves_func(board, index, current_ep_idx)
            elif piece_type == 6: moves = moves_func(board, index, current_cr_str)
            else: moves = moves_func(board, index)
            if moves: all_moves.extend(moves)
                
    return all_moves