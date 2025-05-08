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

#constants
PIECE_CHAR_TO_TYPE = { 'p': 1, 'n': 2, 'b': 3, 'r': 4, 'q': 5, 'k': 6 }
PIECE_BASE_VALUES_FROM_TYPE = { 1: 100, 2: 320, 3: 330, 4: 500, 5: 900, 6: 20000 }
PIECE_MATERIAL_FOR_ENDGAME_CHECK = {2:3, 3:3, 4:5, 5:9} 
knight_pst_values = [ [-167,-89,-34,-49,61,-97,-15,-107],[-73,-41,72,36,23,62,7,-17],[-80,-18,51,33,56,31,-4,-53],[-55,-25,12,24,24,12,-25,-55],[-55,-25,12,24,24,12,-25,-55],[-80,-18,51,33,56,31,-4,-53],[-73,-41,72,36,23,62,7,-17],[-167,-89,-34,-49,61,-97,-15,-107] ]
pawn_pst_values = [ [0,0,0,0,0,0,0,0],[78,83,44,10,26,53,-32,1],[56,51,24,-5,-6,13,-4,-11],[52,35,1,-10,-19,0,10,-8],[46,21,-8,-17,-17,-8,19,46],[48,22,-8,-16,-16,-9,21,48],[43,17,-9,-18,-18,-9,17,43],[0,0,0,0,0,0,0,0] ]
bishop_pst_values = [ [-29,-8,-25,-38,-27,-44,12,-9],[-43,-14,-42,-29,-11,-22,-9,-32],[-25,-12,-20,-16,-17,18,-4,-14],[-13,-3,-14,-15,-14,-5,-1,-13],[-13,-3,-14,-15,-14,-5,-1,-13],[-25,-12,-20,-16,-17,18,-4,-14],[-43,-14,-42,-29,-11,-22,-9,-32],[-29,-8,-25,-38,-27,-44,12,-9] ]
rook_pst_values = [ [35,29,33,4,37,33,56,50],[55,29,56,55,55,62,56,55],[-2,4,16,51,47,12,26,28],[-3,-9,-2,12,14,-1,-3,-4],[-3,-9,-2,12,14,-1,-3,-4],[-2,4,16,51,47,12,26,28],[55,29,56,55,55,62,56,55],[35,29,33,4,37,33,56,50] ]
queen_pst_values = [ [-9,22,22,27,27,22,22,-9],[-16,-16,-16,-7,-7,-16,-16,-16],[-16,-16,-17,13,14,-17,-16,-16],[-3,-14,-2,-5,-5,-2,-14,-3],[-3,-14,-2,-5,-5,-2,-14,-3],[-16,-16,-17,13,14,-17,-16,-16],[-16,-16,-16,-7,-7,-16,-16,-16],[-9,22,22,27,27,22,22,-9] ]
king_pst_values_mg = [ [-65,-23,-15,-15,-15,-15,-23,-65],[-44,-15,-13,-12,-12,-13,-15,-44],[-28,-8,-6,-7,-7,-6,-8,-28],[-15,-4,2,-8,-8,2,-4,-15],[-15,-4,2,-8,-8,2,-4,-15],[-28,-8,-6,-7,-7,-6,-8,-28],[-44,-15,-13,-12,-12,-13,-15,-44],[-65,-23,-15,-15,-15,-15,-23,-65] ]
king_pst_values_eg = [ [-50,-30,-10,-10,-10,-10,-30,-50],[-30,-10,10,20,20,10,-10,-30],[-10,10,20,30,30,20,10,-10],[-10,10,30,40,40,30,10,-10],[-10,10,30,40,40,30,10,-10],[-10,10,20,30,30,20,10,-10],[-30,-10,10,20,20,10,-10,-30],[-50,-30,-10,-10,-10,-10,-30,-50] ]
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
    global knight_pst_values, pawn_pst_values, bishop_pst_values, rook_pst_values, queen_pst_values, king_pst_values_mg, king_pst_values_eg
    global PIECE_BASE_VALUES_FROM_TYPE, PIECE_MATERIAL_FOR_ENDGAME_CHECK
    
    white_material_sum = 0; black_material_sum = 0
    for piece_val_iter in board:
        if piece_val_iter == 0: continue
        material = PIECE_MATERIAL_FOR_ENDGAME_CHECK.get(abs(piece_val_iter), 0)
        if piece_val_iter > 0: white_material_sum += material
        else: black_material_sum += material
    is_endgame = (white_material_sum < 13) and (black_material_sum < 13)
    current_king_pst = king_pst_values_eg if is_endgame else king_pst_values_mg
    pst_tables_map = { 1: pawn_pst_values, 2: knight_pst_values, 3: bishop_pst_values, 4: rook_pst_values, 5: queen_pst_values, 6: current_king_pst }
    current_score = 0
    for index, piece in enumerate(board):
        if piece == 0: continue
        piece_type = abs(piece)
        material_value = PIECE_BASE_VALUES_FROM_TYPE.get(piece_type, 0)
        pst_val = 0
        pst_table_for_piece = pst_tables_map.get(piece_type)
        if pst_table_for_piece:
            rank, file_idx = divmod(index, 8)
            pst_val = pst_table_for_piece[rank][file_idx] if piece > 0 else pst_table_for_piece[7 - rank][file_idx]
        score_increment = material_value + pst_val
        if piece < 0: score_increment = -score_increment
        current_score += score_increment
    return current_score

def get_legal_moves(board, is_white_turn, current_cr_str, current_ep_idx):
    global side_to_move, castling_rights, en_passant_target 
    legal_moves_list = []
    pseudo_legal_moves_list = generate_pseudo_legal_moves(board, is_white_turn, current_cr_str, current_ep_idx) # Uses local function
    original_global_side = side_to_move
    original_global_cr = castling_rights
    original_global_ep = en_passant_target
    for move_tuple in pseudo_legal_moves_list:
        temp_board = list(board) 
        _captured, _next_cr_ignored, _next_ep_ignored = make_move(temp_board, move_tuple, current_cr_str, current_ep_idx) # Uses local function
        side_to_move = original_global_side
        castling_rights = original_global_cr
        en_passant_target = original_global_ep
        if not is_king_in_check(temp_board, is_white_turn):
            legal_moves_list.append(move_tuple)
    side_to_move = original_global_side
    castling_rights = original_global_cr
    en_passant_target = original_global_ep
    return legal_moves_list

def score_move_for_ordering(board, move_tuple):
    global ORDERING_PIECE_VALUES
    score = 0; from_idx, to_idx = move_tuple[:2]
    piece_moving = board[from_idx]; piece_type_moving = abs(piece_moving)
    captured_piece = board[to_idx]; captured_piece_type = abs(captured_piece)
    if piece_moving == 0: return -1 
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
    global nodes_visited 
    nodes_visited = 0 
    best_move_found = None
    best_value = -float('inf') if is_maximizing_player else float('inf')
    alpha, beta = -float('inf'), float('inf')
    possible_moves = get_legal_moves(board_state, is_maximizing_player, current_cr, current_ep)
    if not possible_moves: 
        if is_king_in_check(board_state, is_maximizing_player): return None, (-float('inf') if is_maximizing_player else float('inf'))
        else: return None, 0 
    ordered_moves = order_moves(board_state, possible_moves)
    for move_tuple in ordered_moves: 
        board_copy = list(board_state) 
        _cap, next_cr, next_ep = make_move(board_copy, move_tuple, current_cr, current_ep) 
        move_eval = alphabeta(board_copy, depth - 1, alpha, beta, not is_maximizing_player, next_cr, next_ep) 
        if is_maximizing_player:
            if move_eval > best_value: best_value, best_move_found = move_eval, move_tuple
            alpha = max(alpha, best_value)
        else: 
            if move_eval < best_value: best_value, best_move_found = move_eval, move_tuple
            beta = min(beta, best_value)
        if beta <= alpha: break 
    if best_move_found is None and ordered_moves: best_move_found = ordered_moves[0] #fallback
    return best_move_found, best_value

def alphabeta(board_state, depth, alpha, beta, is_maximizing_player, current_cr, current_ep):
    global nodes_visited
    nodes_visited += 1
    if depth == 0: return evaluate_board(board_state) 
    possible_moves = get_legal_moves(board_state, is_maximizing_player, current_cr, current_ep) 
    if not possible_moves:
        if is_king_in_check(board_state, is_maximizing_player): return -float('inf') if is_maximizing_player else float('inf')
        else: return 0 
    ordered_moves = order_moves(board_state, possible_moves) 
    best_eval = -float('inf') if is_maximizing_player else float('inf')
    for move_tuple in ordered_moves:
        board_copy = list(board_state)
        _cap, next_cr, next_ep = make_move(board_copy, move_tuple, current_cr, current_ep)
        eval_score = alphabeta(board_copy, depth - 1, alpha, beta, not is_maximizing_player, next_cr, next_ep)
        if is_maximizing_player:
            best_eval = max(best_eval, eval_score)
            alpha = max(alpha, eval_score)
        else:
            best_eval = min(best_eval, eval_score)
            beta = min(beta, eval_score)
        if beta <= alpha: break
    return best_eval

def make_move(board_ref, move_tuple, cr_before_move, ep_before_move):
    global side_to_move, castling_rights, en_passant_target, halfmove_clock, fullmove_number
    
    from_idx, to_idx = move_tuple[:2]
    move_info = move_tuple[2] if len(move_tuple) > 2 else None
    piece_moving = board_ref[from_idx]
    is_pawn = abs(piece_moving) == 1
    cap_piece = board_ref[to_idx]
    is_capture = cap_piece != 0 or move_info == 'ep'

    original_halfmove = halfmove_clock 
    if is_pawn or is_capture: halfmove_clock = 0
    else: halfmove_clock += 1

    board_ref[to_idx] = piece_moving
    board_ref[from_idx] = 0
    actual_captured_val = cap_piece 

    if move_info == 'ep':
        cap_offset = +8 if piece_moving > 0 else -8 
        ep_cap_idx = to_idx + cap_offset
        if 0 <= ep_cap_idx < 64: 
            actual_captured_val = board_ref[ep_cap_idx]
            board_ref[ep_cap_idx] = 0
        else: actual_captured_val = 0 
    elif move_info in ('q', 'r', 'n', 'b'): 
        promo_type = {'q': 5, 'r': 4, 'n': 2, 'b': 3}.get(move_info.lower())
        if promo_type: board_ref[to_idx] = promo_type * (1 if piece_moving > 0 else -1)
    elif move_info == 'castle_k': 
        rank_idx = from_idx // 8
        r_from, r_to = rank_idx*8+7, rank_idx*8+5
        board_ref[r_to], board_ref[r_from] = board_ref[r_from], 0
    elif move_info == 'castle_q': 
        rank_idx = from_idx // 8
        r_from, r_to = rank_idx*8+0, rank_idx*8+3
        board_ref[r_to], board_ref[r_from] = board_ref[r_from], 0
        
    next_ep = None
    if is_pawn and abs(from_idx // 8 - to_idx // 8) == 2:
        next_ep = (from_idx + to_idx) // 2
        
    next_cr = list(cr_before_move) if cr_before_move != '-' else []
    K_idx, Q_idx, k_idx, q_idx = 60, 60, 4, 4 
    h1_idx, a1_idx, h8_idx, a8_idx = 63, 56, 7, 0 

    if piece_moving == 6 and from_idx == K_idx:
        if 'K' in next_cr: next_cr.remove('K')
        if 'Q' in next_cr: next_cr.remove('Q')
    elif piece_moving == -6 and from_idx == k_idx: 
        if 'k' in next_cr: next_cr.remove('k')
        if 'q' in next_cr: next_cr.remove('q')
    
    if piece_moving == 4:
        if from_idx == h1_idx and 'K' in next_cr: next_cr.remove('K')
        elif from_idx == a1_idx and 'Q' in next_cr: next_cr.remove('Q')
    elif piece_moving == -4:
        if from_idx == h8_idx and 'k' in next_cr: next_cr.remove('k')
        elif from_idx == a8_idx and 'q' in next_cr: next_cr.remove('q')
        
    if cap_piece == 4:
        if to_idx == h1_idx and 'K' in next_cr: next_cr.remove('K')
        if to_idx == a1_idx and 'Q' in next_cr: next_cr.remove('Q')
    elif cap_piece == -4:
        if to_idx == h8_idx and 'k' in next_cr: next_cr.remove('k')
        if to_idx == a8_idx and 'q' in next_cr: next_cr.remove('q')

    next_cr_str = "".join(sorted(next_cr)) if next_cr else '-'

    if side_to_move == 'b': fullmove_number += 1
    side_to_move = 'b' if side_to_move == 'w' else 'w'
    castling_rights = next_cr_str
    en_passant_target = next_ep
    
    return actual_captured_val, next_cr_str, next_ep

if __name__ == "__main__":
    reset_game_state() 
    depth_to_search = 4 

    profiler = cProfile.Profile()
    profiler.enable()
    start_time = time.time()
    is_white_current_player = (side_to_move == 'w')
    
    best_move_found, best_eval = find_best_move(
        board_array, depth_to_search, is_white_current_player, 
        castling_rights, en_passant_target
    )
    end_time = time.time()
    profiler.disable()
    search_time = end_time - start_time

    print("\n--- Search Finished ---")
    if best_move_found:
        from_sq, to_sq = u.index_1d_to_square(best_move_found[0]), u.index_1d_to_square(best_move_found[1])
        promo = best_move_found[2].lower() if len(best_move_found) > 2 and isinstance(best_move_found[2], str) and best_move_found[2].lower() in ('q','r','n','b') else ""
        print(f"Best move found: {from_sq}{to_sq}{promo}")
        print(f"Evaluation: {best_eval:.2f}") 
        print(f"Search Time: {search_time:.4f} seconds")
        print(f"Depth: {depth_to_search}")
        print(f"Nodes visited: {nodes_visited}") 
        
        reset_game_state()
        _c, final_cr, final_ep = make_move(board_array, best_move_found, 'KQkq', None) 
    else:
        is_check = is_king_in_check(board_array, is_white_current_player)
        print("Checkmate!" if is_check else "Stalemate!")
        print(f"Search Time: {search_time:.4f} seconds")
        print(f"Nodes visited: {nodes_visited}")

    print("\n--- Profiling Stats (Top 20 Cumulative Time) ---")
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(20)
    sys.stdout.flush()