from move_gen import (generate_knight_moves, generate_rook_moves,
                      generate_bishop_moves, generate_queen_moves,
                      generate_pawn_moves, generate_king_moves,
                      is_square_attacked,
                      generate_pseudo_legal_moves 
                     )
import utils as u
board_array = None
import cProfile
import pstats
import sys
import time
import copy 

def reset_game_state():
    global board_array, side_to_move, castling_rights, en_passant_target, halfmove_clock, fullmove_number
    # Re-initialize from starting FEN or defaults
    board_array = u.get_starting_board_array()
    side_to_move = 'w'
    castling_rights = 'KQkq'
    en_passant_target = None
    halfmove_clock = 0
    fullmove_number = 1

def evaluate_board(board):
    piece_values = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000}

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
    king_pst_values_mg = [#Midgame king PST
    [ -65, -23, -15, -15, -15, -15, -23, -65],
    [ -44, -15, -13, -12, -12, -13, -15, -44],
    [ -28,  -8,  -6,  -7,  -7,  -6,  -8, -28],
    [ -15,  -4,   2,  -8,  -8,   2,  -4, -15],
    [ -15,  -4,   2,  -8,  -8,   2,  -4, -15],
    [ -28,  -8,  -6,  -7,  -7,  -6,  -8, -28],
    [ -44, -15, -13, -12, -12, -13, -15, -44],
    [ -65, -23, -15, -15, -15, -15, -23, -65]
    ]
    king_pst_values_eg = [#Endgame king PST
    [-50, -30, -10, -10, -10, -10, -30, -50],
    [-30, -10,  10,  20,  20,  10, -10, -30],
    [-10,  10,  20,  30,  30,  20,  10, -10],
    [-10,  10,  30,  40,  40,  30,  10, -10],
    [-10,  10,  30,  40,  40,  30,  10, -10],
    [-10,  10,  20,  30,  30,  20,  10, -10],
    [-30, -10,  10,  20,  20,  10, -10, -30],
    [-50, -30, -10, -10, -10, -10, -30, -50]
    ]

    white_material = 0
    black_material = 0
    for piece_val in board:
        p_type = abs(piece_val)
        val = 0
        if p_type == 2 or p_type == 3: val = 3 #K/B
        elif p_type == 4: val = 5 #R
        elif p_type == 5: val = 9 #Q
        if piece_val > 0: white_material += val
        elif piece_val < 0: black_material += val

    is_endgame = (white_material < 13) and (black_material < 13)
    king_pst_to_use = king_pst_values_eg if is_endgame else king_pst_values_mg

    pst_tables = {
        1: pawn_pst_values,
        2: knight_pst_values,
        3: bishop_pst_values,
        4: rook_pst_values,
        5: queen_pst_values,
        6: king_pst_to_use
    }


    white_score = 0
    black_score = 0
    total_material = 0

    for index in range(64):
        piece = board[index]
        if piece == 0: continue

        piece_type = abs(piece)
        piece_color_mult = 1 if piece > 0 else -1
        rank = index // 8
        file = index % 8

        material_value = piece_values.get(u.piece_int_to_char(piece).lower(), 0) * 100 

        pst_value = 0
        if piece_type in pst_tables:
            pst_table = pst_tables[piece_type]
            pst_value = pst_table[rank][file] if piece > 0 else pst_table[7-rank][file]

        score = material_value + pst_value

        if piece > 0:
            white_score += score
            if piece_type != 1 and piece_type != 6:
                 total_material += piece_values.get(u.piece_int_to_char(piece).lower(), 0)
        else:
            black_score += score
            if piece_type != 1 and piece_type != 6:
                 total_material += piece_values.get(u.piece_int_to_char(piece).lower(), 0)

    final_score = white_score - black_score

    return final_score


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

def get_legal_moves(board, is_white_turn, current_castling_rights, current_en_passant_target):
    legal_moves = []
    # Generate moves that are legal except for checks
    pseudo_legal_moves = generate_pseudo_legal_moves(board, is_white_turn, current_castling_rights, current_en_passant_target)

    for move in pseudo_legal_moves:
        # Work on a copy of the board to avoid side effects
        temp_board = list(board)

        # Make the move on the temporary board. Ignore returned state variables.
        # Remove the is_simulation argument from the call:
        _, _, _ = make_move(
            temp_board, move, current_castling_rights, current_en_passant_target
        )
        # Note: make_move still flips the global side_to_move here. This is a minor
        # side effect within get_legal_moves, but shouldn't break the search logic
        # as long as the search itself handles the turn correctly. Ideally, make_move
        # wouldn't modify ANY globals, but we'll leave side_to_move for now.

        # Check if the king of the player who just moved is now in check
        king_in_check_after_move = is_king_in_check(temp_board, is_white_turn)

        # If the king is NOT in check, the move is fully legal
        if not king_in_check_after_move:
            legal_moves.append(move)

        # Since make_move flipped global side_to_move, flip it back here
        # to ensure the check for the *next* pseudo_legal_move is done
        # with the correct original side_to_move context if is_king_in_check
        # somehow depends on it (it shouldn't, but good practice).
        global side_to_move
        side_to_move = 'b' if side_to_move == 'w' else 'w' # Flip back

    return legal_moves

def find_best_move(board, depth, is_maximizing_player, current_castling_rights, current_en_passant_target):
    global nodes_visited # Keep this global if you need it
    nodes_visited = 0
    best_move = None
    best_value = -float('inf') if is_maximizing_player else float('inf')

    possible_moves = get_legal_moves(board, is_maximizing_player, current_castling_rights, current_en_passant_target)

    if not possible_moves:
        if is_king_in_check(board, is_maximizing_player):
             return None, (-float('inf') if is_maximizing_player else float('inf'))
        else:
             return None, 0

    import random
    random.shuffle(possible_moves)

    alpha = -float('inf')
    beta = float('inf')

    for move in possible_moves:
        board_copy = list(board)
        _captured_piece_info, next_cr, next_ep = make_move(board_copy, move, current_castling_rights, current_en_passant_target) # make_move flips global side_to_move
        move_value = alphabeta(board_copy, depth - 1, alpha, beta, not is_maximizing_player, next_cr, next_ep)

        # ***** REMOVE THE FLIP-BACK *****
        # global side_to_move   # REMOVE
        # side_to_move = 'b' if side_to_move == 'w' else 'w' # REMOVE

        if is_maximizing_player:
            if move_value > best_value:
                best_value = move_value
                best_move = move
            alpha = max(alpha, best_value)
        else:
             if move_value < best_value:
                 best_value = move_value
                 best_move = move
             beta = min(beta, best_value)

        if beta <= alpha:
            break

    if best_move is None and possible_moves:
        print(f"WARNING: find_best_move finished loop but best_move is None. best_value={best_value}. Returning first move.")
        best_move = possible_moves[0]

    return best_move, best_value


def alphabeta(board, depth, alpha, beta, is_maximizing_player, current_castling_rights, current_en_passant_target):
    global nodes_visited # Keep this global if you need it
    nodes_visited += 1

    if depth == 0:
        return evaluate_board(board)

    possible_moves = get_legal_moves(board, is_maximizing_player, current_castling_rights, current_en_passant_target)

    if not possible_moves:
        if is_king_in_check(board, is_maximizing_player):
             return -float('inf') if is_maximizing_player else float('inf')
        else:
             return 0

    if is_maximizing_player:
        best_value = -float('inf')
        for move in possible_moves:
            board_copy = list(board)
            _captured, next_cr, next_ep = make_move(board_copy, move, current_castling_rights, current_en_passant_target) # make_move flips global side_to_move
            value = alphabeta(board_copy, depth - 1, alpha, beta, False, next_cr, next_ep)

            # ***** REMOVE THE FLIP-BACK *****
            # global side_to_move   # REMOVE
            # side_to_move = 'b' if side_to_move == 'w' else 'w' # REMOVE

            best_value = max(best_value, value)
            alpha = max(alpha, best_value)
            if beta <= alpha:
                break
        return best_value

    else: # Minimizing player
        best_value = float('inf')
        for move in possible_moves:
            board_copy = list(board)
            _captured, next_cr, next_ep = make_move(board_copy, move, current_castling_rights, current_en_passant_target) # make_move flips global side_to_move
            value = alphabeta(board_copy, depth - 1, alpha, beta, True, next_cr, next_ep)

            # ***** REMOVE THE FLIP-BACK *****
            # global side_to_move   # REMOVE
            # side_to_move = 'b' if side_to_move == 'w' else 'w' # REMOVE

            best_value = min(best_value, value)
            beta = min(beta, best_value)
            if beta <= alpha:
                break
        return best_value

def make_move(board, move, current_castling_rights, current_ep_target):
    # Keep the global side_to_move for now, but ideally this would also be returned/managed
    global side_to_move

    from_index, to_index = move[:2]
    move_info = move[2] if len(move) > 2 else None
    piece = board[from_index]
    captured_piece = board[to_index] # Potential capture
    is_white_moving = piece > 0 # Check color before moving

    # Calculate old state needed for undo IF NOT USING COPIES, but we will use copies
    # old_castling_rights = current_castling_rights
    # old_en_passant_target = current_ep_target

    # Apply move to board
    board[to_index] = piece
    board[from_index] = 0

    # --- Handle special moves (EP, Promotion, Castling) ---
    actual_captured_piece = captured_piece # Store originally captured piece

    if move_info == 'ep':
        capture_index = to_index + 8 if is_white_moving else to_index - 8
        if 0 <= capture_index < 64:
             actual_captured_piece = board[capture_index] # The pawn being captured EP
             board[capture_index] = 0
        else:
             print(f"ERROR: Invalid EP capture index. Move: {move}, Target Index: {capture_index}")
             actual_captured_piece = 0 # Should not happen

    elif move_info in ('q', 'r', 'n', 'b', 'Q', 'R', 'N', 'B'):
        # Promotion
        _p_color = 1 if is_white_moving else -1
        _p_val = {'q': 5, 'r': 4, 'n': 2, 'b': 3}.get(move_info.lower())
        board[to_index] = _p_val * _p_color

    elif move_info == 'castle_k':
        _rank = from_index // 8; _r_from= _rank*8+7; _r_to=_rank*8+5
        board[_r_to] = board[_r_from]; board[_r_from] = 0
    elif move_info == 'castle_q':
        _rank = from_index // 8; _r_from= _rank*8+0; _r_to=_rank*8+3
        board[_r_to] = board[_r_from]; board[_r_from] = 0

    # --- Calculate next state (EP target, Castling rights) ---
    new_ep_target = None
    piece_after_move = board[to_index] # Piece might have changed due to promotion
    if abs(piece_after_move) == 1 and abs(from_index // 8 - to_index // 8) == 2: # Pawn double push
        new_ep_target = (from_index + to_index) // 2

    new_castling_rights = current_castling_rights
    # King move
    if abs(piece) == 6:
        if is_white_moving: new_castling_rights = new_castling_rights.replace('K','').replace('Q','')
        else: new_castling_rights = new_castling_rights.replace('k','').replace('q','')
    # Rook move
    elif abs(piece) == 4:
        if from_index == u.square_to_index_1d('a1'): new_castling_rights = new_castling_rights.replace('Q','')
        elif from_index == u.square_to_index_1d('h1'): new_castling_rights = new_castling_rights.replace('K','')
        elif from_index == u.square_to_index_1d('a8'): new_castling_rights = new_castling_rights.replace('q','')
        elif from_index == u.square_to_index_1d('h8'): new_castling_rights = new_castling_rights.replace('k','')
    # Rook capture
    if actual_captured_piece != 0 and abs(actual_captured_piece) == 4:
        if to_index == u.square_to_index_1d('a1'): new_castling_rights = new_castling_rights.replace('Q','')
        elif to_index == u.square_to_index_1d('h1'): new_castling_rights = new_castling_rights.replace('K','')
        elif to_index == u.square_to_index_1d('a8'): new_castling_rights = new_castling_rights.replace('q','')
        elif to_index == u.square_to_index_1d('h8'): new_castling_rights = new_castling_rights.replace('k','')

    # Flip global side_to_move (can be kept for simplicity if CLI updates based on it)
    # Consider returning the next side to move as well for better encapsulation
    side_to_move = 'b' if side_to_move == 'w' else 'w'

    # Return the actual captured piece and the calculated next state
    return actual_captured_piece, new_castling_rights, new_ep_target


#test/debug board
def create_test_board_minimax_start():
    return u.get_starting_board_array()

if __name__ == "__main__":
    current_board = create_test_board_minimax_start()
    side_to_move = 'w'
    castling_rights = "KQkq"
    en_passant_target = None
    depth_to_search = 4 

    print("Initial Board:")
    u.print_board(current_board)
    print(f"Side to move: {side_to_move}")
    print(f"Castling Rights: {castling_rights}")
    print(f"EP Target: {en_passant_target}")


    profiler = cProfile.Profile()
    profiler.enable()

    start_time = time.time()
    is_white = (side_to_move == 'w')
    best_move_found, best_eval = find_best_move(current_board, depth_to_search, is_white, castling_rights, en_passant_target)
    end_time = time.time()

    profiler.disable()

    search_time = end_time - start_time

    print("\n--- Search Finished ---")
    if best_move_found:
        from_sq = u.index_1d_to_square(best_move_found[0])
        to_sq = u.index_1d_to_square(best_move_found[1])
        move_info = best_move_found[2] if len(best_move_found) > 2 else ""
        print(f"Best move found: {from_sq}-{to_sq} {move_info}")
        print(f"Evaluation: {best_eval:.2f} (from {'White' if is_white else 'Black'}'s perspective, approx centipawns)")
        print(f"Search Time: {search_time:.4f} seconds")
        print(f"Depth: {depth_to_search}")
        make_move(current_board, best_move_found, castling_rights, en_passant_target)

        print("\nBoard after best move:")
        u.print_board(current_board)
        print(f"New Side to move: {side_to_move}")
        print(f"New Castling Rights: {castling_rights}")
        print(f"New EP Target: {en_passant_target} ({u.index_1d_to_square(en_passant_target) if en_passant_target is not None else 'None'})")

    else:
        if is_king_in_check(current_board, is_white):
            print("Checkmate! {} wins.".format("Black" if is_white else "White"))
        else:
            print("Stalemate! Draw.")
        print(f"Search Time: {search_time:.4f} seconds")


    print("\n--- Profiling Stats (Top 20 Cumulative Time) ---")
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(20)
    sys.stdout.flush()