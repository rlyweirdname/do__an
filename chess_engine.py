import sys
import time
import copy
import cProfile
import pstats

from move_gen import (
    generate_knight_moves, generate_rook_moves,
    generate_bishop_moves, generate_queen_moves,
    generate_pawn_moves, generate_king_moves,
    generate_pseudo_legal_moves,
    is_king_in_check, 
)
import utils as u

board_array = None
side_to_move = 'w'
castling_rights = 'KQkq' 
en_passant_target = None 
halfmove_clock = 0
fullmove_number = 1
nodes_visited = 0

PIECE_CHAR_TO_TYPE = { 'p': 1, 'n': 2, 'b': 3, 'r': 4, 'q': 5, 'k': 6 }
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

pawn_pst_mg = [ [0,0,0,0,0,0,0,0],[78,83,44,10,26,53,-32,1],[56,51,24,-5,-6,13,-4,-11],[52,35,1,-10,-19,0,10,-8],[46,21,-8,-17,-17,-8,19,46],[48,22,-8,-16,-16,-9,21,48],[43,17,-9,-18,-18,-9,17,43],[0,0,0,0,0,0,0,0] ]
knight_pst_mg = [ [-167,-89,-34,-49,61,-97,-15,-107],[-73,-41,72,36,23,62,7,-17],[-80,-18,51,33,56,31,-4,-53],[-55,-25,12,24,24,12,-25,-55],[-55,-25,12,24,24,12,-25,-55],[-80,-18,51,33,56,31,-4,-53],[-73,-41,72,36,23,62,7,-17],[-167,-89,-34,-49,61,-97,-15,-107] ]
bishop_pst_mg = [ [-29,-8,-25,-38,-27,-44,12,-9],[-43,-14,-42,-29,-11,-22,-9,-32],[-25,-12,-20,-16,-17,18,-4,-14],[-13,-3,-14,-15,-14,-5,-1,-13],[-13,-3,-14,-15,-14,-5,-1,-13],[-25,-12,-20,-16,-17,18,-4,-14],[-43,-14,-42,-29,-11,-22,-9,-32],[-29,-8,-25,-38,-27,-44,12,-9] ]
rook_pst_mg = [ [35,29,33,4,37,33,56,50],[55,29,56,55,55,62,56,55],[-2,4,16,51,47,12,26,28],[-3,-9,-2,12,14,-1,-3,-4],[-3,-9,-2,12,14,-1,-3,-4],[-2,4,16,51,47,12,26,28],[55,29,56,55,55,62,56,55],[35,29,33,4,37,33,56,50] ]
queen_pst_mg = [ [-9,22,22,27,27,22,22,-9],[-16,-16,-16,-7,-7,-16,-16,-16],[-16,-16,-17,13,14,-17,-16,-16],[-3,-14,-2,-5,-5,-2,-14,-3],[-3,-14,-2,-5,-5,-2,-14,-3],[-16,-16,-17,13,14,-17,-16,-16],[-16,-16,-16,-7,-7,-16,-16,-16],[-9,22,22,27,27,22,22,-9] ]
king_pst_mg = [ [-65,-23,-15,-15,-15,-15,-23,-65],[-44,-15,-13,-12,-12,-13,-15,-44],[-28,-8,-6,-7,-7,-6,-8,-28],[-15,-4,2,-8,-8,2,-4,-15],[-15,-4,2,-8,-8,2,-4,-15],[-28,-8,-6,-7,-7,-6,-8,-28],[-44,-15,-13,-12,-12,-13,-15,-44],[-65,-23,-15,-15,-15,-15,-23,-65] ]

pawn_pst_eg = [
    [0,0,0,0,0,0,0,0], [100,120,140,160,160,140,120,100], [80,100,120,140,140,120,100,80], [60,80,100,120,120,100,80,60],
    [80,100,120,140,140,120,100,80], [150,180,220,260,260,220,180,150], [300,350,400,450,450,400,350,300], [0,0,0,0,0,0,0,0]
]
knight_pst_eg = [
    [-50,-40,-30,-30,-30,-30,-40,-50], [-40,-20,  0,  5,  5,  0,-20,-40], [-30,  5, 10, 15, 15, 10,  5,-30], [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30], [-30,  0, 10, 15, 15, 10,  0,-30], [-40,-20,  0,  0,  0,  0,-20,-40], [-50,-40,-30,-30,-30,-30,-40,-50]
]
bishop_pst_eg = [
    [-20,-10,-10,-10,-10,-10,-10,-20], [-10,  5,  0,  0,  0,  0,  5,-10], [-10, 10, 10, 10, 10, 10, 10,-10], [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10], [-10,  0,  5, 10, 10,  5,  0,-10], [-10,  0,  0,  0,  0,  0,  0,-10], [-20,-10,-10,-10,-10,-10,-10,-20]
]
rook_pst_eg = [
    [0,  0,  0,  5,  5,  0,  0,  0], [5, 10, 10, 10, 10, 10, 10,  5], [0,  5,  5,  5,  5,  5,  5,  0], [0,  0,  0,  0,  0,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0], [0,  0,  0,  0,  0,  0,  0,  0], [25, 30, 30, 30, 30, 30, 30, 25], [0,  0,  0,  0,  0,  0,  0,  0]
]
queen_pst_eg = [
    [-20,-10,-10, -5, -5,-10,-10,-20], [-10,  0,  5,  0,  0,  0,  0,-10], [-10,  5,  5,  5,  5,  5,  0,-10], [  0,  0,  5,  5,  5,  5,  0, -5],
    [ -5,  0,  5,  5,  5,  5,  0, -5], [-10,  0,  5,  5,  5,  5,  0,-10], [-10,  0,  0,  0,  0,  0,  0,-10], [-20,-10,-10, -5, -5,-10,-10,-20]
]
king_pst_eg = [ [-50,-30,-10,-10,-10,-10,-30,-50],[-30,-10,10,20,20,10,-10,-30],[-10,10,20,30,30,20,10,-10],[-10,10,30,40,40,30,10,-10],[-10,10,30,40,40,30,10,-10],[-10,10,20,30,30,20,10,-10],[-30,-10,10,20,20,10,-10,-30],[-50,-30,-10,-10,-10,-10,-30,-50] ]

PSTS_MG = { 1: pawn_pst_mg, 2: knight_pst_mg, 3: bishop_pst_mg, 4: rook_pst_mg, 5: queen_pst_mg, 6: king_pst_mg }
PSTS_EG = { 1: pawn_pst_eg, 2: knight_pst_eg, 3: bishop_pst_eg, 4: rook_pst_eg, 5: queen_pst_eg, 6: king_pst_eg }

ORDERING_PIECE_VALUES = {1: 100, 2: 300, 3: 300, 4: 500, 5: 900, 6: 0} 

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

    original_global_side = side_to_move
    original_global_cr = castling_rights
    original_global_ep = en_passant_target
    original_global_halfmove = halfmove_clock
    original_global_fullmove = fullmove_number

    for move_tuple in pseudo_legal_moves_list:
        temp_board = list(board) 
        
        temp_side = side_to_move
        temp_cr = castling_rights
        temp_ep = en_passant_target
        temp_half = halfmove_clock
        temp_full = fullmove_number

        _captured, _next_cr_ignored, _next_ep_ignored = make_move(temp_board, move_tuple, current_cr_str, current_ep_idx)
        
        if not is_king_in_check(temp_board, is_white_turn):
            legal_moves_list.append(move_tuple)
        
        side_to_move = temp_side
        castling_rights = temp_cr
        en_passant_target = temp_ep
        halfmove_clock = temp_half
        fullmove_number = temp_full
        
    side_to_move = original_global_side
    castling_rights = original_global_cr
    en_passant_target = original_global_ep
    halfmove_clock = original_global_halfmove
    fullmove_number = original_global_fullmove
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
    
    original_global_side = side_to_move
    original_global_cr = castling_rights
    original_global_ep = en_passant_target
    original_global_halfmove = halfmove_clock
    original_global_fullmove = fullmove_number

    for move_tuple in ordered_moves: 
        board_copy = list(board_state)
        
        current_iter_side = side_to_move
        current_iter_cr = castling_rights
        current_iter_ep = en_passant_target
        current_iter_half = halfmove_clock
        current_iter_full = fullmove_number

        _cap, next_cr_state, next_ep_state = make_move(board_copy, move_tuple, current_cr, current_ep) 
        move_eval = alphabeta(board_copy, depth - 1, alpha, beta, not is_maximizing_player, next_cr_state, next_ep_state) 
        
        side_to_move = current_iter_side
        castling_rights = current_iter_cr
        en_passant_target = current_iter_ep
        halfmove_clock = current_iter_half
        fullmove_number = current_iter_full

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
            
    side_to_move = original_global_side
    castling_rights = original_global_cr
    en_passant_target = original_global_ep
    halfmove_clock = original_global_halfmove
    fullmove_number = original_global_fullmove

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
    
    original_global_side = side_to_move
    original_global_cr = castling_rights
    original_global_ep = en_passant_target
    original_global_halfmove = halfmove_clock
    original_global_fullmove = fullmove_number

    if is_maximizing_player:
        max_eval = -float('inf')
        for move_tuple in ordered_moves:
            board_copy = list(board_state)
            
            current_iter_side = side_to_move
            current_iter_cr = castling_rights
            current_iter_ep = en_passant_target
            current_iter_half = halfmove_clock
            current_iter_full = fullmove_number
            
            _cap, next_cr_state, next_ep_state = make_move(board_copy, move_tuple, current_cr, current_ep)
            eval_score = alphabeta(board_copy, depth - 1, alpha, beta, False, next_cr_state, next_ep_state)
            
            side_to_move = current_iter_side
            castling_rights = current_iter_cr
            en_passant_target = current_iter_ep
            halfmove_clock = current_iter_half
            fullmove_number = current_iter_full

            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        side_to_move = original_global_side
        castling_rights = original_global_cr
        en_passant_target = original_global_ep
        halfmove_clock = original_global_halfmove
        fullmove_number = original_global_fullmove
        return max_eval
    else:
        min_eval = float('inf')
        for move_tuple in ordered_moves:
            board_copy = list(board_state)

            current_iter_side = side_to_move
            current_iter_cr = castling_rights
            current_iter_ep = en_passant_target
            current_iter_half = halfmove_clock
            current_iter_full = fullmove_number

            _cap, next_cr_state, next_ep_state = make_move(board_copy, move_tuple, current_cr, current_ep)
            eval_score = alphabeta(board_copy, depth - 1, alpha, beta, True, next_cr_state, next_ep_state)
            
            side_to_move = current_iter_side
            castling_rights = current_iter_cr
            en_passant_target = current_iter_ep
            halfmove_clock = current_iter_half
            fullmove_number = current_iter_full
            
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        side_to_move = original_global_side
        castling_rights = original_global_cr
        en_passant_target = original_global_ep
        halfmove_clock = original_global_halfmove
        fullmove_number = original_global_fullmove
        return min_eval

def make_move(board_ref, move_tuple, cr_before_move, ep_before_move):
    global side_to_move, castling_rights, en_passant_target, halfmove_clock, fullmove_number
    
    from_idx, to_idx = move_tuple[:2]
    move_info = move_tuple[2] if len(move_tuple) > 2 else None
    
    piece_moving = board_ref[from_idx]
    is_pawn_move = abs(piece_moving) == PIECE_CHAR_TO_TYPE['p']
    captured_piece_on_sq = board_ref[to_idx]
    is_capture_on_sq = captured_piece_on_sq != 0
    
    if is_pawn_move or is_capture_on_sq or move_info == 'ep':
        halfmove_clock = 0
    else:
        halfmove_clock += 1

    board_ref[to_idx] = piece_moving
    board_ref[from_idx] = 0
    actual_captured_val = captured_piece_on_sq

    if move_info == 'ep':
        capture_offset = +8 if piece_moving > 0 else -8
        en_passant_capture_square_idx = to_idx + capture_offset
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
        
    next_en_passant_target = None
    if is_pawn_move and abs(from_idx // 8 - to_idx // 8) == 2:
        next_en_passant_target = (from_idx + to_idx) // 2
        
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
        
    next_castling_rights_str = "".join(sorted(next_cr_list)) if next_cr_list else '-'

    if side_to_move == 'b':
        fullmove_number += 1
    side_to_move = 'b' if side_to_move == 'w' else 'w'
    
    castling_rights = next_castling_rights_str
    en_passant_target = next_en_passant_target
    
    return actual_captured_val, next_castling_rights_str, next_en_passant_target

if __name__ == "__main__":
    reset_game_state() 
    depth_to_search = 5

    profiler = cProfile.Profile()
    profiler.enable()
    start_time = time.time()
    
    current_board_state = list(board_array)
    current_player_is_white = (side_to_move == 'w')
    current_cr_state = castling_rights
    current_ep_state = en_passant_target
    
    best_move_found, best_eval = find_best_move(
        current_board_state,
        depth_to_search, 
        current_player_is_white, 
        current_cr_state,
        current_ep_state
    )
    end_time = time.time()
    profiler.disable()
    search_time = end_time - start_time

    print("\n--- Search Finished ---")
    if best_move_found:
        from_sq, to_sq = u.index_1d_to_square(best_move_found[0]), u.index_1d_to_square(best_move_found[1])
        promo_char = ""
        if len(best_move_found) > 2 and isinstance(best_move_found[2], str):
            if best_move_found[2].lower() in ('q','r','n','b'):
                promo_char = best_move_found[2].lower()
            elif 'castle' in best_move_found[2]:
                 promo_char = f" ({best_move_found[2]})"

        print(f"Best move found: {from_sq}{to_sq}{promo_char}")
        print(f"Evaluation: {best_eval:.2f} (from {side_to_move}'s perspective before move)") 
        print(f"Search Time: {search_time:.4f} seconds")
        print(f"Depth: {depth_to_search}")
        print(f"Nodes visited: {nodes_visited}") 
        
        print(f"Game state BEFORE applying best move: Side: {side_to_move}, CR: {castling_rights}, EP: {en_passant_target}")
        _c, final_cr, final_ep = make_move(board_array, best_move_found, current_cr_state, current_ep_state) 
        print(f"Game state AFTER applying best move: Side: {side_to_move}, CR: {castling_rights}, EP: {en_passant_target}")
    else:
        if best_eval == 0:
            print("Stalemate!")
        elif (current_player_is_white and best_eval == -float('inf')) or \
             (not current_player_is_white and best_eval == float('inf')):
            print("Checkmate!")
        else:
            print("No move found, but not clearly mate/stalemate by eval. Eval:", best_eval)

        print(f"Search Time: {search_time:.4f} seconds")
        print(f"Nodes visited: {nodes_visited}")

    print("\n--- Profiling Stats (Top 20 Cumulative Time) ---")
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(20)
    sys.stdout.flush()