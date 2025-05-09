import sys
import time
import copy
import cProfile
import pstats
import random

from move_gen import (
    generate_knight_moves, generate_rook_moves,
    generate_bishop_moves, generate_queen_moves,
    generate_pawn_moves, generate_king_moves,
    generate_pseudo_legal_moves,
    is_king_in_check,
)
import utils as u
from opening_playbook import simple_playbook

board_array = None
side_to_move = 'w'
castling_rights = 'KQkq'
en_passant_target = None
halfmove_clock = 0
fullmove_number = 1
nodes_visited = 0

PIECE_CHAR_TO_TYPE = { 'p': 1, 'n': 2, 'b': 3, 'r': 4, 'q': 5, 'k': 6 }
PIECE_TYPE_TO_CHAR = {v: k for k, v in PIECE_CHAR_TO_TYPE.items()}

PIECE_BASE_VALUES_FROM_TYPE = { 1: 100, 2: 320, 3: 330, 4: 500, 5: 900, 6: 20000 }
PIECE_PHASE_VALUES = { 1: 0, 2: 1, 3: 1, 4: 2, 5: 4, 6: 0 }
MAX_PHASE_MATERIAL = 2 * (
    PIECE_PHASE_VALUES[2] * 2 +
    PIECE_PHASE_VALUES[3] * 2 +
    PIECE_PHASE_VALUES[4] * 2 +
    PIECE_PHASE_VALUES[5] * 1
)
if MAX_PHASE_MATERIAL == 0:
    MAX_PHASE_MATERIAL = 1

pawn_pst_mg = [ [0,0,0,0,0,0,0,0],[5,10,10,-5,-5,15,10,5],[5,5,10,20,20,10,5,5], [0,0,15,25,25,15,0,0], [5,5,10,25,25,10,5,5], [10,10,15,30,30,15,10,10], [50,50,50,60,60,50,50,50], [0,0,0,0,0,0,0,0] ]
knight_pst_mg = [ [-167,-89,-34,-49,61,-97,-15,-107],[-73,-41,72,36,23,62,7,-17],[-80,-18,51,33,56,31,-4,-53],[-55,-25,12,24,24,12,-25,-55],[-55,-25,12,24,24,12,-25,-55],[-80,-18,51,33,56,31,-4,-53],[-73,-41,72,36,23,62,7,-17],[-167,-89,-34,-49,61,-97,-15,-107] ]
bishop_pst_mg = [ [-29,-8,-25,-38,-27,-44,12,-9],[-43,-14,-42,-29,-11,-22,-9,-32],[-25,-12,-20,-16,-17,18,-4,-14],[-13,-3,-14,-15,-14,-5,-1,-13],[-13,-3,-14,-15,-14,-5,-1,-13],[-25,-12,-20,-16,-17,18,-4,-14],[-43,-14,-42,-29,-11,-22,-9,-32],[-29,-8,-25,-38,-27,-44,12,-9] ]
rook_pst_mg = [ [35,29,33,4,37,33,56,50],[55,29,56,55,55,62,56,55],[-2,4,16,51,47,12,26,28],[-3,-9,-2,12,14,-1,-3,-4],[-3,-9,-2,12,14,-1,-3,-4],[-2,4,16,51,47,12,26,28],[55,29,56,55,55,62,56,55],[35,29,33,4,37,33,56,50] ]
queen_pst_mg = [ [-9,22,22,27,27,22,22,-9],[-16,-16,-16,-7,-7,-16,-16,-16],[-16,-16,-17,13,14,-17,-16,-16],[-3,-14,-2,-5,-5,-2,-14,-3],[-3,-14,-2,-5,-5,-2,-14,-3],[-16,-16,-17,13,14,-17,-16,-16],[-16,-16,-16,-7,-7,-16,-16,-16],[-9,22,22,27,27,22,22,-9] ]
king_pst_mg = [ [-65,-23,-15,-15,-15,-15,-23,-65],[-44,-15,-13,-12,-12,-13,-15,-44],[-28,-8,-6,-7,-7,-6,-8,-28],[-15,-4,2,-8,-8,2,-4,-15],[-15,-4,2,-8,-8,2,-4,-15],[-28,-8,-6,-7,-7,-6,-8,-28],[-44,-15,-13,-12,-12,-13,-15,-44],[-65,-23,-15,-15,-15,-15,-23,-65] ]
pawn_pst_eg = [ [0,0,0,0,0,0,0,0], [10,15,20,25,25,20,15,10], [20,30,40,50,50,40,30,20], [30,40,55,70,70,55,40,30], [50,60,75,90,90,75,60,50],[80,90,110,130,130,110,90,80], [150,170,200,220,220,200,170,150], [0,0,0,0,0,0,0,0] ]
knight_pst_eg = [ [-50,-40,-30,-30,-30,-30,-40,-50],[-40,-20,0,5,5,0,-20,-40],[-30,5,10,15,15,10,5,-30],[-30,0,15,20,20,15,0,-30],[-30,5,15,20,20,15,5,-30],[-30,0,10,15,15,10,0,-30],[-40,-20,0,0,0,0,-20,-40],[-50,-40,-30,-30,-30,-30,-40,-50] ]
bishop_pst_eg = [ [-20,-10,-10,-10,-10,-10,-10,-20],[-10,5,0,0,0,0,5,-10],[-10, 10, 10, 10, 10, 10, 10,-10],[-10,0,10,10,10,10,0,-10],[-10,5,5,10,10,5,5,-10],[-10,0,5,10,10,5,0,-10],[-10,0,0,0,0,0,0,-10],[-20,-10,-10,-10,-10,-10,-10,-20] ]
rook_pst_eg = [ [0,0,0,5,5,0,0,0],[5,10,10,10,10,10,10,5],[0,5,5,5,5,5,5,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[25,30,30,30,30,30,30,25],[0,0,0,0,0,0,0,0] ]
queen_pst_eg = [ [-20,-10,-10, -5, -5,-10,-10,-20],[-10,0,5,0,0,0,0,-10],[-10,5,5,5,5,5,0,-10],[0,0,5,5,5,5,0,-5],[-5,0,5,5,5,5,0,-5],[-10,0,5,5,5,5,0,-10],[-10,0,0,0,0,0,0,-10],[-20,-10,-10,-5,-5,-10,-10,-20] ]
king_pst_eg = [ [-50,-30,-10,-10,-10,-10,-30,-50],[-30,-10,10,20,20,10,-10,-30],[-10,10,20,30,30,20,10,-10],[-10,10,30,40,40,30,10,-10],[-10,10,30,40,40,30,10,-10],[-10,10,20,30,30,20,10,-10],[-30,-10,10,20,20,10,-10,-30],[-50,-30,-10,-10,-10,-10,-30,-50] ]

PSTS_MG = { 1: pawn_pst_mg, 2: knight_pst_mg, 3: bishop_pst_mg, 4: rook_pst_mg, 5: queen_pst_mg, 6: king_pst_mg }
PSTS_EG = { 1: pawn_pst_eg, 2: knight_pst_eg, 3: bishop_pst_eg, 4: rook_pst_eg, 5: queen_pst_eg, 6: king_pst_eg }

ORDERING_PIECE_VALUES = {1: 100, 2: 300, 3: 300, 4: 500, 5: 900, 6: 0}

def board_to_fen_pieces(board_arr):
    fen_ranks = []
    for i in range(8):
        empty_count = 0
        fen_rank_str = ""
        for j in range(8):
            index = i * 8 + j
            piece_val = board_arr[index]
            if piece_val == 0:
                empty_count += 1
            else:
                if empty_count > 0:
                    fen_rank_str += str(empty_count)
                    empty_count = 0
                piece_type_abs = abs(piece_val)
                char = PIECE_TYPE_TO_CHAR.get(piece_type_abs, '?')
                fen_rank_str += char.upper() if piece_val > 0 else char.lower()
        if empty_count > 0:
            fen_rank_str += str(empty_count)
        fen_ranks.append(fen_rank_str)
    return "/".join(fen_ranks)

def generate_fen(board_arr, current_side_char, current_cr_str, current_ep_idx, current_halfmove_clock, current_fullmove_num):
    fen_pieces = board_to_fen_pieces(board_arr)
    fen_ep_target_sq = "-"
    if current_ep_idx is not None:
        try:
            fen_ep_target_sq = u.index_1d_to_square(current_ep_idx)
        except:
             pass
    return f"{fen_pieces} {current_side_char} {current_cr_str if current_cr_str else '-'} {fen_ep_target_sq} {current_halfmove_clock} {current_fullmove_num}"

def algebraic_move_to_tuple(algebraic_move_str, board_arr, is_white_to_move):
    promo_char = None
    if '=' in algebraic_move_str:
        parts = algebraic_move_str.split('=')
        move_part = parts[0]
        promo_char = parts[1].lower()
        if promo_char not in ('q', 'r', 'n', 'b'): return None
    elif algebraic_move_str.endswith(('q','r','n','b')) and len(algebraic_move_str) == 5 and algebraic_move_str[2] == algebraic_move_str[4]:
        promo_char = algebraic_move_str[-1].lower()
        move_part = algebraic_move_str[:-1]
    else:
        move_part = algebraic_move_str

    if len(move_part) != 4: return None

    from_sq_str = move_part[:2]
    to_sq_str = move_part[2:]

    try:
        from_idx = u.square_to_index_1d(from_sq_str)
        to_idx = u.square_to_index_1d(to_sq_str)
    except:
        return None

    if promo_char:
        piece_moving = board_arr[from_idx]
        if abs(piece_moving) == PIECE_CHAR_TO_TYPE['p']:
            dest_rank = to_idx // 8
            expected_promo_rank = 0 if is_white_to_move else 7
            if dest_rank == expected_promo_rank:
                return (from_idx, to_idx, promo_char)
        return None
    return (from_idx, to_idx)

def reset_game_state():
    global board_array, side_to_move, castling_rights, en_passant_target, halfmove_clock, fullmove_number
    board_array = u.get_starting_board_array()
    side_to_move = 'w'
    castling_rights = 'KQkq'
    en_passant_target = None
    halfmove_clock = 0
    fullmove_number = 1

def evaluate_board(board):
    current_total_phase_material = 0
    for piece_val_iter in board:
        if piece_val_iter == 0: continue
        piece_type_for_phase = abs(piece_val_iter)
        current_total_phase_material += PIECE_PHASE_VALUES.get(piece_type_for_phase, 0)

    game_phase_factor = current_total_phase_material / MAX_PHASE_MATERIAL
    game_phase_factor = max(0.0, min(1.0, game_phase_factor))

    current_score = 0
    for index, piece_val_on_sq in enumerate(board):
        if piece_val_on_sq == 0: continue
        piece_type = abs(piece_val_on_sq)
        is_white_piece = piece_val_on_sq > 0
        material_value = PIECE_BASE_VALUES_FROM_TYPE.get(piece_type, 0)
        pst_val_final = 0
        pst_table_mg_for_piece = PSTS_MG.get(piece_type)
        pst_table_eg_for_piece = PSTS_EG.get(piece_type)
        if pst_table_mg_for_piece and pst_table_eg_for_piece:
            rank, file_idx = divmod(index, 8)
            actual_row_for_pst = rank if is_white_piece else (7 - rank)
            pst_val_mg = pst_table_mg_for_piece[actual_row_for_pst][file_idx]
            pst_val_eg = pst_table_eg_for_piece[actual_row_for_pst][file_idx]
            pst_val_final = pst_val_mg * game_phase_factor + pst_val_eg * (1.0 - game_phase_factor)
        score_increment = material_value + pst_val_final
        if not is_white_piece:
            score_increment = -score_increment
        current_score += score_increment
    return int(round(current_score))

def get_legal_moves(board, is_white_turn, current_cr_str, current_ep_idx):
    global side_to_move, castling_rights, en_passant_target, halfmove_clock, fullmove_number
    legal_moves_list = []
    pseudo_legal_moves_list = generate_pseudo_legal_moves(board, is_white_turn, current_cr_str, current_ep_idx)

    original_engine_side = side_to_move
    original_engine_cr = castling_rights
    original_engine_ep = en_passant_target
    original_engine_halfmove = halfmove_clock
    original_engine_fullmove = fullmove_number

    for move_tuple in pseudo_legal_moves_list:
        temp_board = list(board)
        
        side_to_move = 'w' if is_white_turn else 'b'
        castling_rights = current_cr_str
        en_passant_target = current_ep_idx

        _captured, _next_cr_ignored, _next_ep_ignored = make_move(temp_board, move_tuple, current_cr_str, current_ep_idx)
        
        if not is_king_in_check(temp_board, is_white_turn):
            legal_moves_list.append(move_tuple)
        
    side_to_move = original_engine_side
    castling_rights = original_engine_cr
    en_passant_target = original_engine_ep
    halfmove_clock = original_engine_halfmove
    fullmove_number = original_engine_fullmove
    return legal_moves_list

def score_move_for_ordering(board, move_tuple):
    global ORDERING_PIECE_VALUES
    score = 0; from_idx, to_idx = move_tuple[:2]
    piece_moving_val = board[from_idx]
    if piece_moving_val == 0: return -100000
    piece_type_moving = abs(piece_moving_val)
    captured_piece_val = board[to_idx]
    captured_piece_type = abs(captured_piece_val)
    if len(move_tuple) > 2 and isinstance(move_tuple[2], str) and move_tuple[2].lower() in ('q','r','n','b'):
        promo_vals = {'q': 900, 'r': 500, 'n': 300, 'b': 300}
        return 10000 + promo_vals.get(move_tuple[2].lower(), 0)
    if captured_piece_type != 0:
        victim_value = ORDERING_PIECE_VALUES.get(captured_piece_type, 0)
        aggressor_value = ORDERING_PIECE_VALUES.get(piece_type_moving, 1000)
        return 5000 + (victim_value * 10) - aggressor_value
    return 1000

def order_moves(board_state, moves_list):
    if not moves_list: return []
    return sorted(moves_list, key=lambda m: score_move_for_ordering(board_state, m), reverse=True)

def find_best_move(board_state, depth, is_maximizing_player, current_cr, current_ep):
    global nodes_visited, side_to_move, castling_rights, en_passant_target, halfmove_clock, fullmove_number

    engine_current_side_char = side_to_move
    engine_current_cr = castling_rights
    engine_current_ep_idx = en_passant_target
    engine_current_halfmove = halfmove_clock
    engine_current_fullmove = fullmove_number
    side_char_for_fen = 'w' if is_maximizing_player else 'b'
    
    current_fen = generate_fen(
        board_state, side_char_for_fen, current_cr, current_ep,
        engine_current_halfmove, engine_current_fullmove
    )
    
    if current_fen in simple_playbook:
        book_moves_algebraic = simple_playbook[current_fen]
        if book_moves_algebraic:
            potential_book_moves_tuples = []
            for algebraic_m_str in book_moves_algebraic:
                move_tuple = algebraic_move_to_tuple(algebraic_m_str, board_state, is_maximizing_player)
                if move_tuple:
                    potential_book_moves_tuples.append(move_tuple)
            
            if potential_book_moves_tuples:
                legal_book_moves = []
                original_engine_globals = (side_to_move, castling_rights, en_passant_target, halfmove_clock, fullmove_number)
                for book_move_tuple in potential_book_moves_tuples:
                    temp_board_for_book = list(board_state)
                    side_to_move = side_char_for_fen
                    castling_rights = current_cr
                    en_passant_target = current_ep
                    _cap_b, _cr_b, _ep_b = make_move(temp_board_for_book, book_move_tuple, current_cr, current_ep)
                    if not is_king_in_check(temp_board_for_book, is_maximizing_player):
                        legal_book_moves.append(book_move_tuple)
                side_to_move, castling_rights, en_passant_target, halfmove_clock, fullmove_number = original_engine_globals

                if legal_book_moves:
                    chosen_book_move = random.choice(legal_book_moves)
                    print(f"Playbook: Using move {u.index_1d_to_square(chosen_book_move[0])}{u.index_1d_to_square(chosen_book_move[1])} from FEN: {current_fen}")
                    return chosen_book_move, 0
                else:
                    print(f"Playbook: Found FEN {current_fen}, but no book moves are legal. Falling back to search.")
            else:
                print(f"Playbook: Found FEN {current_fen}, but could not convert any book moves. Falling back to search.")

    nodes_visited = 0
    best_move_found = None
    alpha = -float('inf')
    beta = float('inf')
    current_best_value = -float('inf') if is_maximizing_player else float('inf')
    
    possible_moves = get_legal_moves(board_state, is_maximizing_player, current_cr, current_ep)

    if not possible_moves:
        if is_king_in_check(board_state, is_maximizing_player):
            return None, (-float('inf') if is_maximizing_player else float('inf'))
        else:
            return None, 0

    ordered_moves = order_moves(board_state, possible_moves)

    original_engine_side = side_to_move
    original_engine_cr = castling_rights
    original_engine_ep = en_passant_target
    original_engine_halfmove = halfmove_clock
    original_engine_fullmove = fullmove_number

    for move_tuple in ordered_moves:
        board_copy = list(board_state)

        iter_engine_side = side_to_move
        iter_engine_cr = castling_rights
        iter_engine_ep = en_passant_target
        iter_engine_half = halfmove_clock
        iter_engine_full = fullmove_number
        
        side_to_move = 'w' if is_maximizing_player else 'b'
        castling_rights = current_cr
        en_passant_target = current_ep

        _cap, next_cr_state, next_ep_state = make_move(board_copy, move_tuple, current_cr, current_ep)
        move_eval = alphabeta(board_copy, depth - 1, alpha, beta, not is_maximizing_player, next_cr_state, next_ep_state)

        side_to_move = iter_engine_side
        castling_rights = iter_engine_cr
        en_passant_target = iter_engine_ep
        halfmove_clock = iter_engine_half
        fullmove_number = iter_engine_full

        if is_maximizing_player:
            if move_eval > current_best_value:
                current_best_value = move_eval
                best_move_found = move_tuple
            alpha = max(alpha, current_best_value)
        else:
            if move_eval < current_best_value:
                current_best_value = move_eval
                best_move_found = move_tuple
            beta = min(beta, current_best_value)

        if beta <= alpha:
            break

    side_to_move = original_engine_side
    castling_rights = original_engine_cr
    en_passant_target = original_engine_ep
    halfmove_clock = original_engine_halfmove
    fullmove_number = original_engine_fullmove

    if best_move_found is None and ordered_moves:
        best_move_found = ordered_moves[0]
    return best_move_found, current_best_value

def alphabeta(board_state, depth, alpha, beta, is_maximizing_player, current_cr, current_ep):
    global nodes_visited, side_to_move, castling_rights, en_passant_target, halfmove_clock, fullmove_number
    nodes_visited += 1

    if depth == 0:
        return evaluate_board(board_state)

    possible_moves = get_legal_moves(board_state, is_maximizing_player, current_cr, current_ep)

    if not possible_moves:
        if is_king_in_check(board_state, is_maximizing_player):
            return -float('inf') if is_maximizing_player else float('inf')
        else:
            return 0

    ordered_moves = order_moves(board_state, possible_moves)

    original_engine_side = side_to_move
    original_engine_cr = castling_rights
    original_engine_ep = en_passant_target
    original_engine_halfmove = halfmove_clock
    original_engine_fullmove = fullmove_number

    if is_maximizing_player:
        max_eval = -float('inf')
        for move_tuple in ordered_moves:
            board_copy = list(board_state)
            iter_engine_side = side_to_move
            iter_engine_cr = castling_rights
            iter_engine_ep = en_passant_target
            iter_engine_half = halfmove_clock
            iter_engine_full = fullmove_number
            side_to_move = 'w' if is_maximizing_player else 'b'
            castling_rights = current_cr
            en_passant_target = current_ep
            _cap, next_cr_state, next_ep_state = make_move(board_copy, move_tuple, current_cr, current_ep)
            eval_score = alphabeta(board_copy, depth - 1, alpha, beta, False, next_cr_state, next_ep_state)
            side_to_move = iter_engine_side
            castling_rights = iter_engine_cr
            en_passant_target = iter_engine_ep
            halfmove_clock = iter_engine_half
            fullmove_number = iter_engine_full
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        side_to_move = original_engine_side
        castling_rights = original_engine_cr
        en_passant_target = original_engine_ep
        halfmove_clock = original_engine_halfmove
        fullmove_number = original_engine_fullmove
        return max_eval
    else: 
        min_eval = float('inf')
        for move_tuple in ordered_moves:
            board_copy = list(board_state)
            iter_engine_side = side_to_move
            iter_engine_cr = castling_rights
            iter_engine_ep = en_passant_target
            iter_engine_half = halfmove_clock
            iter_engine_full = fullmove_number
            side_to_move = 'w' if is_maximizing_player else 'b'
            castling_rights = current_cr
            en_passant_target = current_ep
            _cap, next_cr_state, next_ep_state = make_move(board_copy, move_tuple, current_cr, current_ep)
            eval_score = alphabeta(board_copy, depth - 1, alpha, beta, True, next_cr_state, next_ep_state)
            side_to_move = iter_engine_side
            castling_rights = iter_engine_cr
            en_passant_target = iter_engine_ep
            halfmove_clock = iter_engine_half
            fullmove_number = iter_engine_full
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        side_to_move = original_engine_side
        castling_rights = original_engine_cr
        en_passant_target = original_engine_ep
        halfmove_clock = original_engine_halfmove
        fullmove_number = original_engine_fullmove
        return min_eval

def make_move(board_ref, move_tuple, cr_before_move, ep_before_move):
    global side_to_move, castling_rights, en_passant_target, halfmove_clock, fullmove_number

    from_idx, to_idx = move_tuple[:2]
    move_info = move_tuple[2] if len(move_tuple) > 2 else None
    piece_moving = board_ref[from_idx]
    is_pawn_move = abs(piece_moving) == PIECE_CHAR_TO_TYPE['p']
    captured_piece_on_sq = board_ref[to_idx]
    is_capture_on_sq = captured_piece_on_sq != 0
    
    if is_pawn_move or is_capture_on_sq or (move_info == 'ep'):
        halfmove_clock = 0
    else:
        halfmove_clock += 1

    board_ref[to_idx] = piece_moving
    board_ref[from_idx] = 0
    actual_captured_val = captured_piece_on_sq

    if move_info == 'ep':
        capture_offset_for_ep_pawn = +8 if piece_moving > 0 else -8
        en_passant_capture_square_idx = to_idx + capture_offset_for_ep_pawn
        if 0 <= en_passant_capture_square_idx < 64:
            actual_captured_val = board_ref[en_passant_capture_square_idx]
            board_ref[en_passant_capture_square_idx] = 0
        else:
            actual_captured_val = 0
    elif move_info in ('q', 'r', 'n', 'b'):
        promo_piece_type = PIECE_CHAR_TO_TYPE.get(move_info.lower())
        if promo_piece_type:
            board_ref[to_idx] = promo_piece_type * (1 if piece_moving > 0 else -1)
    elif move_info == 'castle_k':
        rank_start_idx = (from_idx // 8) * 8
        rook_from_idx, rook_to_idx = rank_start_idx + 7, rank_start_idx + 5
        board_ref[rook_to_idx] = board_ref[rook_from_idx]
        board_ref[rook_from_idx] = 0
    elif move_info == 'castle_q':
        rank_start_idx = (from_idx // 8) * 8
        rook_from_idx, rook_to_idx = rank_start_idx + 0, rank_start_idx + 3
        board_ref[rook_to_idx] = board_ref[rook_from_idx]
        board_ref[rook_from_idx] = 0

    next_en_passant_target_for_state = None
    if is_pawn_move and abs(from_idx // 8 - to_idx // 8) == 2:
        next_en_passant_target_for_state = (from_idx + to_idx) // 2

    next_cr_list = list(cr_before_move) if cr_before_move and cr_before_move != '-' else []

    if piece_moving == PIECE_CHAR_TO_TYPE['k'] and from_idx == u.square_to_index_1d('e1'):
        if 'K' in next_cr_list: next_cr_list.remove('K')
        if 'Q' in next_cr_list: next_cr_list.remove('Q')
    elif piece_moving == -PIECE_CHAR_TO_TYPE['k'] and from_idx == u.square_to_index_1d('e8'):
        if 'k' in next_cr_list: next_cr_list.remove('k')
        if 'q' in next_cr_list: next_cr_list.remove('q')

    if (piece_moving == PIECE_CHAR_TO_TYPE['r'] and from_idx == u.square_to_index_1d('h1')) or \
       (captured_piece_on_sq == PIECE_CHAR_TO_TYPE['r'] and to_idx == u.square_to_index_1d('h1')):
        if 'K' in next_cr_list: next_cr_list.remove('K')
    if (piece_moving == PIECE_CHAR_TO_TYPE['r'] and from_idx == u.square_to_index_1d('a1')) or \
       (captured_piece_on_sq == PIECE_CHAR_TO_TYPE['r'] and to_idx == u.square_to_index_1d('a1')):
        if 'Q' in next_cr_list: next_cr_list.remove('Q')
    if (piece_moving == -PIECE_CHAR_TO_TYPE['r'] and from_idx == u.square_to_index_1d('h8')) or \
       (captured_piece_on_sq == -PIECE_CHAR_TO_TYPE['r'] and to_idx == u.square_to_index_1d('h8')):
        if 'k' in next_cr_list: next_cr_list.remove('k')
    if (piece_moving == -PIECE_CHAR_TO_TYPE['r'] and from_idx == u.square_to_index_1d('a8')) or \
       (captured_piece_on_sq == -PIECE_CHAR_TO_TYPE['r'] and to_idx == u.square_to_index_1d('a8')):
        if 'q' in next_cr_list: next_cr_list.remove('q')

    next_castling_rights_for_state = "".join(sorted(next_cr_list)) if next_cr_list else '-'

    if side_to_move == 'b':
        fullmove_number += 1
    side_to_move = 'b' if side_to_move == 'w' else 'w'
    
    castling_rights = next_castling_rights_for_state
    en_passant_target = next_en_passant_target_for_state
    
    return actual_captured_val, next_castling_rights_for_state, next_en_passant_target_for_state

if __name__ == "__main__":
    reset_game_state()
    depth_to_search = 5

    profiler = cProfile.Profile()
    profiler.enable()
    start_time = time.time()

    current_board_state_engine = list(board_array)
    current_player_is_white_engine = (side_to_move == 'w')
    current_cr_state_engine = castling_rights
    current_ep_state_engine = en_passant_target

    print(f"Initial engine state for find_best_move: Side: {side_to_move}, CR: {current_cr_state_engine}, EP: {current_ep_state_engine}, Half: {halfmove_clock}, Full: {fullmove_number}")

    best_move_found, best_eval = find_best_move(
        current_board_state_engine,
        depth_to_search,
        current_player_is_white_engine,
        current_cr_state_engine,
        current_ep_state_engine
    )
    end_time = time.time()
    profiler.disable()
    search_time = end_time - start_time

    print("\n--- Search Finished ---")
    if best_move_found:
        from_sq, to_sq = u.index_1d_to_square(best_move_found[0]), u.index_1d_to_square(best_move_found[1])
        promo_char_display = ""
        if len(best_move_found) > 2 and isinstance(best_move_found[2], str):
            if best_move_found[2].lower() in ('q','r','n','b'):
                promo_char_display = best_move_found[2].lower()
            elif 'castle' in best_move_found[2]:
                 promo_char_display = f" ({best_move_found[2]})"
        perspective_side = 'White' if current_player_is_white_engine else 'Black'
        print(f"Best move found: {from_sq}{to_sq}{promo_char_display}")
        print(f"Evaluation: {best_eval} (from {perspective_side}'s perspective)")
        print(f"Search Time: {search_time:.4f} seconds")
        print(f"Depth: {depth_to_search}")
        print(f"Nodes visited: {nodes_visited}")
        print(f"Engine state BEFORE applying best move: Side: {'w' if current_player_is_white_engine else 'b'}, CR: {current_cr_state_engine}, EP: {current_ep_state_engine}, Half: {halfmove_clock}, Full: {fullmove_number}")
        
        side_to_move = 'w' if current_player_is_white_engine else 'b'
        castling_rights = current_cr_state_engine
        en_passant_target = current_ep_state_engine

        _c, final_cr, final_ep = make_move(board_array, best_move_found, current_cr_state_engine, current_ep_state_engine)
        print(f"Engine state AFTER applying best move: Side: {side_to_move}, CR: {castling_rights}, EP: {en_passant_target}, Half: {halfmove_clock}, Full: {fullmove_number}")
    else:
        if best_eval == 0:
            print("Stalemate!")
        elif (current_player_is_white_engine and best_eval == -float('inf')) or \
             (not current_player_is_white_engine and best_eval == float('inf')):
            print("Checkmate!")
        else:
            print("No move found, but not clearly mate/stalemate by eval. Eval:", best_eval)
        print(f"Search Time: {search_time:.4f} seconds")
        print(f"Nodes visited: {nodes_visited}")

    print("\n--- Profiling Stats (Top 20 Cumulative Time) ---")
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(20)
    sys.stdout.flush()