# --- START OF FILE chess_engine.py ---

# Keep these as the *current* state of the game
side_to_move = 'w'
castling_rights = "KQkq"
en_passant_target = None # Store the *target square index* (e.g., 24 for e3) or None

# --- Imports remain the same ---
from move_gen import (generate_knight_moves, generate_rook_moves,
                      generate_bishop_moves, generate_queen_moves,
                      generate_pawn_moves, generate_king_moves,
                      is_square_attacked,
                      # Assume move_gen also provides functions to generate ALL pseudo-legal moves
                      generate_pseudo_legal_moves # You'll need to implement this in move_gen
                     )
import utils as u
import cProfile
import pstats
import sys
import time
import copy # Needed for deep copies if we use a state object


# --- Evaluation function remains the same for now ---
def evaluate_board(board):
    # ... (Keep existing evaluation logic) ...
    piece_values = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000} # Using centipawns is common

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
    king_pst_values_mg = [ # Midgame king PST
    [ -65, -23, -15, -15, -15, -15, -23, -65],
    [ -44, -15, -13, -12, -12, -13, -15, -44],
    [ -28,  -8,  -6,  -7,  -7,  -6,  -8, -28],
    [ -15,  -4,   2,  -8,  -8,   2,  -4, -15],
    [ -15,  -4,   2,  -8,  -8,   2,  -4, -15],
    [ -28,  -8,  -6,  -7,  -7,  -6,  -8, -28],
    [ -44, -15, -13, -12, -12, -13, -15, -44],
    [ -65, -23, -15, -15, -15, -15, -23, -65]
    ]
    king_pst_values_eg = [ # Endgame king PST - encourage king activity
    [-50, -30, -10, -10, -10, -10, -30, -50],
    [-30, -10,  10,  20,  20,  10, -10, -30],
    [-10,  10,  20,  30,  30,  20,  10, -10],
    [-10,  10,  30,  40,  40,  30,  10, -10],
    [-10,  10,  30,  40,  40,  30,  10, -10],
    [-10,  10,  20,  30,  30,  20,  10, -10],
    [-30, -10,  10,  20,  20,  10, -10, -30],
    [-50, -30, -10, -10, -10, -10, -30, -50]
    ]

    # --- Simple check for endgame phase (e.g., based on material) ---
    # This is a very basic heuristic; more sophisticated methods exist.
    white_material = 0
    black_material = 0
    for piece_val in board:
        p_type = abs(piece_val)
        val = 0
        if p_type == 2 or p_type == 3: val = 3 # Knight/Bishop
        elif p_type == 4: val = 5 # Rook
        elif p_type == 5: val = 9 # Queen
        if piece_val > 0: white_material += val
        elif piece_val < 0: black_material += val

    is_endgame = (white_material < 13) and (black_material < 13) # Example threshold
    king_pst_to_use = king_pst_values_eg if is_endgame else king_pst_values_mg
    # --- End endgame check ---


    pst_tables = {
        1: pawn_pst_values, # Use absolute values for keys
        2: knight_pst_values,
        3: bishop_pst_values,
        4: rook_pst_values,
        5: queen_pst_values,
        6: king_pst_to_use # Use the selected king PST
    }


    white_score = 0
    black_score = 0
    total_material = 0 # Keep track for endgame check maybe

    for index in range(64):
        piece = board[index]
        if piece == 0: continue # Skip empty squares

        piece_type = abs(piece)
        piece_color_mult = 1 if piece > 0 else -1 # 1 for white, -1 for black
        rank = index // 8
        file = index % 8

        # 1. Material Score
        material_value = piece_values.get(u.piece_int_to_char(piece).lower(), 0) * 100 # Use centipawns

        # 2. Positional Score (PST)
        pst_value = 0
        if piece_type in pst_tables:
            pst_table = pst_tables[piece_type]
            # White PST access: pst_table[rank][file]
            # Black PST access: pst_table[7-rank][file] (flip rank)
            pst_value = pst_table[rank][file] if piece > 0 else pst_table[7-rank][file]

        score = material_value + pst_value

        if piece > 0:
            white_score += score
            if piece_type != 1 and piece_type != 6: # Exclude pawns and kings for simple endgame check
                 total_material += piece_values.get(u.piece_int_to_char(piece).lower(), 0)
        else:
            black_score += score
            if piece_type != 1 and piece_type != 6:
                 total_material += piece_values.get(u.piece_int_to_char(piece).lower(), 0)


    # Return score relative to the side to move
    # If it's white's turn, return white_score - black_score
    # If it's black's turn, return black_score - white_score (or -(white_score - black_score))
    # This requires knowing whose turn it is. Let's assume alphabeta handles this.
    final_score = white_score - black_score

    # Bonus for side to move (tempo) - small value
    # tempo_bonus = 10 # Example: 10 centipawns
    # if side_to_move == 'w':
    #     final_score += tempo_bonus
    # else:
    #     final_score -= tempo_bonus

    # Consider adding other evaluation terms:
    # - King safety (e.g., penalty for king being near center in middlegame, bonus for castling)
    # - Pawn structure (doubled pawns, isolated pawns, passed pawns)
    # - Rook on open/semi-open files
    # - Bishop pair bonus
    # - Mobility (number of legal moves available) - can be expensive to calculate

    return final_score # This score is from White's perspective


def is_king_in_check(board, color_is_white):
    king_piece_value = 6 if color_is_white else -6
    king_index = -1

    # Find the king
    for index in range(64):
        if board[index] == king_piece_value:
            king_index = index
            break

    if king_index == -1:
        # This should not happen in a legal game state!
        # print(f"Warning: King for {'White' if color_is_white else 'Black'} not found!")
        # u.print_board(board) # Debug print
        return False # Or raise an error

    # Check if the king's square is attacked by the opponent
    return is_square_attacked(board, king_index, not color_is_white)

# ******************************************
#       REVISED get_legal_moves
# ******************************************
def get_legal_moves(board, is_white_turn, current_castling_rights, current_en_passant_target):
    """
    Generates all legal moves for the current position.
    Uses pseudo-legal move generation and then validates each move.
    """
    legal_moves = []
    # 1. Generate all pseudo-legal moves for the side to move
    #    This function needs to be implemented in move_gen.py
    #    It should consider castling and en passant possibilities based on current state.
    pseudo_legal_moves = generate_pseudo_legal_moves(board, is_white_turn, current_castling_rights, current_en_passant_target)

    # 2. For each pseudo-legal move, check if it leaves the king in check
    for move in pseudo_legal_moves:
        # Create a temporary board copy to simulate the move
        temp_board = list(board) # Shallow copy is usually sufficient for the board array

        # Store state *before* making the move (needed for undo)
        # We pass the *current* rights/target to make_move, and it returns the *old* ones
        captured_piece, old_castling_rights, old_en_passant_target = make_move(
            temp_board, move, current_castling_rights, current_en_passant_target, is_simulation=True
        )

        # Check if the current player's king is in check *after* the move
        king_in_check_after_move = is_king_in_check(temp_board, is_white_turn)

        # We don't need to undo here because we used a temporary board.
        # If make_move modified globals (like the original did), we would need undo_move here.
        # The revised make_move below avoids modifying globals directly.

        if not king_in_check_after_move:
            legal_moves.append(move)

    return legal_moves

# ******************************************
#       REVISED find_best_move
# ******************************************
def find_best_move(board, depth, is_maximizing_player, current_castling_rights, current_en_passant_target):
    """
    Finds the best move using alphabeta search.
    Manages game state correctly during the search.
    """
    global nodes_visited # Optional: for performance tracking
    nodes_visited = 0

    best_move = None
    best_value = -float('inf') if is_maximizing_player else float('inf') # Use infinity

    # Get legal moves using the revised function
    possible_moves = get_legal_moves(board, is_maximizing_player, current_castling_rights, current_en_passant_target)

    if not possible_moves:
        # Checkmate or stalemate check (basic version)
        if is_king_in_check(board, is_maximizing_player):
             return None, -float('inf') if is_maximizing_player else float('inf') # Checkmate
        else:
             return None, 0 # Stalemate

    # --- Add randomness for variety ---
    import random
    random.shuffle(possible_moves)
    # --- End randomness ---


    alpha = -float('inf')
    beta = float('inf')

    # Store the *initial* state before starting the search loop
    # This isn't strictly necessary with the current make/undo returning state,
    # but good practice if state was more complex.
    # initial_castling_rights = current_castling_rights
    # initial_en_passant_target = current_en_passant_target

    for move in possible_moves:
        # Make the move on the board *copy* (or modify and undo on the main board)
        # Using copies within alphabeta is safer but potentially slower
        # Modifying the main board requires careful undo

        # --- Method 1: Modify main board and undo ---
        board_copy_before_move = list(board) # Keep a copy ONLY if undo fails
        captured_piece, old_castling, old_ep = make_move(board, move, current_castling_rights, current_en_passant_target)
        # The global/current castling/ep are now updated by make_move

        move_value = alphabeta(board, depth - 1, alpha, beta, not is_maximizing_player, castling_rights, en_passant_target) # Pass updated state

        undo_move(board, move, captured_piece, old_castling, old_ep) # Restore board and state
        # Verify restoration (optional debug check)
        # assert board == board_copy_before_move
        # assert castling_rights == current_castling_rights # Check if undo restored correctly
        # assert en_passant_target == current_en_passant_target

        # --- Update best move ---
        if is_maximizing_player:
            if move_value > best_value:
                best_value = move_value
                best_move = move
            alpha = max(alpha, best_value)
        else: # Minimizing player (though find_best_move is usually called for maximizing)
             if move_value < best_value:
                 best_value = move_value
                 best_move = move
             beta = min(beta, best_value)
             # Note: The alpha/beta logic inside find_best_move is only for the first level.
             # The main pruning happens within alphabeta.

        # (Optional: Pruning at the root)
        # if beta <= alpha:
        #    break


    #print(f"Nodes visited: {nodes_visited}") # Print nodes visited
    return best_move, best_value


# --- Minimax is likely redundant if using alphabeta, but keep if needed ---
# def minimax(board, depth, is_maximizing_player, current_castling_rights, current_en_passant_target):
    # ... (Needs similar state management updates as alphabeta) ...


# ******************************************
#       REVISED alphabeta
# ******************************************
def alphabeta(board, depth, alpha, beta, is_maximizing_player, current_castling_rights, current_en_passant_target):
    """ Recursive alphabeta function with state management. """
    global nodes_visited # Optional tracking
    nodes_visited += 1

    if depth == 0:
        # Evaluate from the perspective of the *initial* caller of find_best_move
        # The evaluation function itself should return a score relative to White.
        # The sign might need adjustment based on who's turn it *was* at depth 0.
        # Standard approach: evaluate always returns White's score - Black's score.
        # The minimax logic handles maximizing/minimizing this score.
        return evaluate_board(board)


    possible_moves = get_legal_moves(board, is_maximizing_player, current_castling_rights, current_en_passant_target)

    if not possible_moves:
        # Checkmate or stalemate
        if is_king_in_check(board, is_maximizing_player):
             # Current player is checkmated. Bad for them.
             return -float('inf') if is_maximizing_player else float('inf')
        else:
             # Stalemate
             return 0 # Draw score


    if is_maximizing_player:
        best_value = -float('inf')
        for move in possible_moves:
            # Store state before move
            board_copy_before_move = list(board)
            captured, old_castle, old_ep = make_move(board, move, current_castling_rights, current_en_passant_target) # This updates global state

            value = alphabeta(board, depth - 1, alpha, beta, False, castling_rights, en_passant_target) # Pass updated state

            undo_move(board, move, captured, old_castle, old_ep) # Restore state
            # assert board == board_copy_before_move # Debug check

            best_value = max(best_value, value)
            alpha = max(alpha, best_value)
            if beta <= alpha:
                break # Beta cut-off
        return best_value

    else: # Minimizing player
        best_value = float('inf')
        for move in possible_moves:
            # Store state before move
            board_copy_before_move = list(board)
            captured, old_castle, old_ep = make_move(board, move, current_castling_rights, current_en_passant_target) # Updates global state

            value = alphabeta(board, depth - 1, alpha, beta, True, castling_rights, en_passant_target) # Pass updated state

            undo_move(board, move, captured, old_castle, old_ep) # Restore state
            # assert board == board_copy_before_move # Debug check

            best_value = min(best_value, value)
            beta = min(beta, best_value)
            if beta <= alpha:
                break # Alpha cut-off
        return best_value


# ******************************************
#       REVISED make_move / undo_move
# ******************************************

# Ensure these are defined globally in chess_engine.py before any function definition
# Example initialization (adjust if needed):
castling_rights = "KQkq"
en_passant_target = None
side_to_move = 'w'

# ... (other functions like evaluate_board, find_best_move etc.) ...

def make_move(board, move, current_castling_rights, current_ep_target, is_simulation=False):
    """
    Makes a move on the board and updates the game state (castling, en passant, side_to_move).
    Modifies the global state variables if is_simulation is False.
    Returns the information needed to undo the move:
    (captured_piece, old_castling_rights, old_en_passant_target)
    """
    # --- Global declarations MUST be the very first statements ---
    global castling_rights, en_passant_target, side_to_move
    # --- Debug Print 1 ---
    # print(f"DEBUG make_move: Entry. is_simulation={is_simulation}. Current global side_to_move='{side_to_move}'") # Keep if needed

    # --- Initial Setup ---
    from_index, to_index = move[:2]
    move_info = move[2] if len(move) > 2 else None
    piece = board[from_index]
    captured_piece = board[to_index] # Piece initially at destination (might be 0)
    is_white = False
    if piece != 0:
         is_white = piece > 0

    # --- Store old state BEFORE any modifications ---
    old_castling_rights = current_castling_rights
    old_en_passant_target = current_ep_target

    # --- Update Board - Step 1: Basic Move ---
    board[to_index] = piece
    board[from_index] = 0

    # --- Handle Special Moves (Modifies board further, might update captured_piece) ---
    # En Passant Capture Logic...
    if move_info == 'ep':
        # Color of the pawn that just *landed* on the 'to_index' square
        capturing_pawn_is_white = board[to_index] > 0

        # Determine the index of the pawn being captured
        if capturing_pawn_is_white:
            # White pawn landed on rank 5 (index 32-39), captured Black pawn is on rank 4
            _cap_idx = to_index + 8 # CORRECT: One rank below landing square
        else:
            # Black pawn landed on rank 2 (index 16-23), captured White pawn is on rank 3
            _cap_idx = to_index - 8 # CORRECT: One rank above landing square

        if 0 <= _cap_idx < 64:
             captured_piece = board[_cap_idx] # Store the ACTUAL captured pawn
             board[_cap_idx] = 0 # Remove the captured pawn from the board
        else:
             print(f"ERROR: Invalid EP capture index calculation. Move: {move}, Target Index: {_cap_idx}")
             captured_piece = 0 # Should not happen with valid EP moves

    # Promotion Logic...
    elif move_info in ('q', 'r', 'n', 'b', 'Q', 'R', 'N', 'B'):
        _p_color = 1 if board[to_index] > 0 else -1
        _p_val = {'q': 5, 'r': 4, 'n': 2, 'b': 3}.get(move_info.lower())
        board[to_index] = _p_val * _p_color
        # 'captured_piece' remains whatever was on the square before promotion

    # Castling Logic...
    elif move_info == 'castle_k':
        _rank = from_index // 8; _r_from= _rank*8+7; _r_to=_rank*8+5
        board[_r_to] = board[_r_from]; board[_r_from] = 0
    elif move_info == 'castle_q':
        _rank = from_index // 8; _r_from= _rank*8+0; _r_to=_rank*8+3
        board[_r_to] = board[_r_from]; board[_r_from] = 0

    # --- Calculate New State (EP Target, Castling Rights) ---
    # Calculate new_ep_target
    new_ep_target = None
    _final_piece = board[to_index] # Piece actually on destination after special moves
    if abs(_final_piece) == 1 and abs(from_index // 8 - to_index // 8) == 2:
        new_ep_target = (from_index + to_index) // 2

    # Calculate new_castling_rights
    new_castling_rights = current_castling_rights
    if abs(piece) == 6: # Original piece moved was King
        if is_white: new_castling_rights = new_castling_rights.replace('K','').replace('Q','')
        else: new_castling_rights = new_castling_rights.replace('k','').replace('q','')
    elif abs(piece) == 4: # Original piece moved was Rook (use utils for clarity/correctness)
        if from_index == u.square_to_index_1d('a1'): new_castling_rights = new_castling_rights.replace('Q','')
        elif from_index == u.square_to_index_1d('h1'): new_castling_rights = new_castling_rights.replace('K','')
        elif from_index == u.square_to_index_1d('a8'): new_castling_rights = new_castling_rights.replace('q','')
        elif from_index == u.square_to_index_1d('h8'): new_castling_rights = new_castling_rights.replace('k','')
    # Check captures on rook home squares
    if captured_piece != 0 and abs(captured_piece) == 4:
        if to_index == u.square_to_index_1d('a1'): new_castling_rights = new_castling_rights.replace('Q','')
        elif to_index == u.square_to_index_1d('h1'): new_castling_rights = new_castling_rights.replace('K','')
        elif to_index == u.square_to_index_1d('a8'): new_castling_rights = new_castling_rights.replace('q','')
        elif to_index == u.square_to_index_1d('h8'): new_castling_rights = new_castling_rights.replace('k','')


    # --- Update Global State (only if not simulation) ---
    if not is_simulation:
        # --- Debug Print 2 ---
        # print(f"DEBUG make_move: Updating globals. BEFORE side_to_move='{side_to_move}'") # Keep if needed
        castling_rights = new_castling_rights
        en_passant_target = new_ep_target
        side_to_move = 'b' if side_to_move == 'w' else 'w'
        # --- Debug Print 3 ---
        # print(f"DEBUG make_move: Updated globals. AFTER side_to_move='{side_to_move}'") # Keep if needed
    # else:
        # --- Debug Print 4 ---
        # print(f"DEBUG make_move: Simulation=True, skipping global updates.") # Keep if needed

    # Return state needed for undo
    return captured_piece, old_castling_rights, old_en_passant_target


      
def undo_move(board, move, captured_piece, old_castling_rights, old_en_passant_target):
    """
    Restores the board and game state (castling, en passant) to how it was
    before the move was made.
    """
    global castling_rights, en_passant_target, side_to_move # Declare we will modify globals

    from_index, to_index = move[:2]
    move_info = move[2] if len(move) > 2 else None

    moved_piece = board[to_index] # The piece that moved *to* the square

    # --- Restore Board Pieces (Standard part) ---
    # This line might be problematic for EP, handle specially below
    # board[from_index] = moved_piece # Put moved piece back
    # board[to_index] = captured_piece # Put captured piece back (or 0 if empty)

    # --- Handle Special Moves Undo FIRST ---

    # Promotion
    if move_info in ('q', 'r', 'n', 'b', 'Q', 'R', 'N', 'B'):
        pawn_color = 1 if moved_piece > 0 else -1
        board[from_index] = pawn_color * 1 # Put PAWN back on original square
        board[to_index] = captured_piece   # Restore whatever was on destination
    # En Passant Capture
    elif move_info == 'ep':
         # 'captured_piece' holds the captured pawn value (-1 for black, 1 for white).
         # 'moved_piece' is the pawn that performed the capture.
         is_white_capturing_move = moved_piece > 0

         # Restore the capturing pawn to its original square
         board[from_index] = moved_piece
         # Clear the square the capturing pawn landed on
         board[to_index] = 0

         # Determine where the captured pawn *was* and put it back
         if is_white_capturing_move: # White captured, landing on rank 5. Captured black pawn was on rank 4.
             captured_pawn_index = to_index + 8 # CORRECTED
         else: # Black captured, landing on rank 2. Captured white pawn was on rank 3.
             captured_pawn_index = to_index - 8 # CORRECTED

         if 0 <= captured_pawn_index < 64:
             board[captured_pawn_index] = captured_piece # Put captured pawn back
         else:
             print(f"ERROR: Invalid EP undo calculation. Move: {move}, Captured Pawn Index: {captured_pawn_index}")

    # Castling
    elif move_info == 'castle_k': # Kingside
        # Restore King first
        board[from_index] = moved_piece # King back to e1/e8
        board[to_index] = 0             # Clear g1/g8
        # Restore Rook
        rank = from_index // 8
        rook_from = rank * 8 + 7 # Original rook square (h1/h8)
        rook_to = rank * 8 + 5   # Square rook moved to (f1/f8)
        rook_piece = board[rook_to]
        board[rook_to] = 0
        board[rook_from] = rook_piece # Put rook back
    elif move_info == 'castle_q': # Queenside
        # Restore King first
        board[from_index] = moved_piece # King back to e1/e8
        board[to_index] = 0             # Clear c1/c8
        # Restore Rook
        rank = from_index // 8
        rook_from = rank * 8 + 0 # Original rook square (a1/a8)
        rook_to = rank * 8 + 3   # Square rook moved to (d1/d8)
        rook_piece = board[rook_to]
        board[rook_to] = 0
        board[rook_from] = rook_piece # Put rook back
    else:
         # --- Standard Move Undo ---
         # (Only run if not a special move handled above)
         board[from_index] = moved_piece # Put moved piece back
         board[to_index] = captured_piece # Put captured piece back (or 0 if empty)


    # --- Restore Global State ---
    castling_rights = old_castling_rights
    en_passant_target = old_en_passant_target
    # Switch side_to_move back
    side_to_move = 'b' if side_to_move == 'w' else 'w'

    


def create_test_board_minimax_start():
    return u.get_starting_board_array()


# --- Main Execution Block ---
if __name__ == "__main__":
    current_board = create_test_board_minimax_start()
    side_to_move = 'w' # Start with white
    castling_rights = "KQkq"
    en_passant_target = None
    depth_to_search = 4 # Set desired depth

    print("Initial Board:")
    u.print_board(current_board)
    print(f"Side to move: {side_to_move}")
    print(f"Castling Rights: {castling_rights}")
    print(f"EP Target: {en_passant_target}")


    profiler = cProfile.Profile()
    profiler.enable()

    start_time = time.time()
    # Call find_best_move with the current state
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
        print(f"Evaluation: {best_eval:.2f} (from {'White' if is_white else 'Black'}'s perspective, approx centipawns)") # Eval is tricky, might need perspective adjust
        print(f"Search Time: {search_time:.4f} seconds")
        print(f"Depth: {depth_to_search}")

        # Make the move on the main board to show the result
        # Note: make_move now returns undo info, which we don't need here
        make_move(current_board, best_move_found, castling_rights, en_passant_target)
        # The global state (side_to_move, castling_rights, en_passant_target) is updated by make_move

        print("\nBoard after best move:")
        u.print_board(current_board)
        print(f"New Side to move: {side_to_move}")
        print(f"New Castling Rights: {castling_rights}")
        print(f"New EP Target: {en_passant_target} ({u.index_1d_to_square(en_passant_target) if en_passant_target is not None else 'None'})")

    else:
        # Check if it's checkmate or stalemate
        if is_king_in_check(current_board, is_white):
            print("Checkmate! {} wins.".format("Black" if is_white else "White"))
        else:
            print("Stalemate! Draw.")
        print(f"Search Time: {search_time:.4f} seconds")


    print("\n--- Profiling Stats (Top 20 Cumulative Time) ---")
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(20)
    sys.stdout.flush()


# --- (Commented out game loop for now) ---
# current_board = create_test_board_minimax_start()
# side_to_move = 'w'
# castling_rights = "KQkq"
# en_passant_target = None
# num_moves = 10 # Play 5 full moves

# print("Starting Board:")
# u.print_board(current_board)

# for move_number in range(1, num_moves * 2 + 1):
#     is_white_turn = (side_to_move == 'w')
#     player = "White" if is_white_turn else "Black"
#     print(f"\n--- Move { (move_number + 1) // 2 } - {player} to move ---")
#     print(f"State: Castle={castling_rights} EP={en_passant_target}")

#     start_time = time.time()
#     # Dynamically adjust depth? (Example: shallower early, deeper mid/end)
#     current_depth = 3 # Fixed depth for example
#     best_move_found, best_eval = find_best_move(current_board, current_depth, is_white_turn, castling_rights, en_passant_target)
#     end_time = time.time()
#     search_time = end_time - start_time

#     if best_move_found:
#         from_sq = u.index_1d_to_square(best_move_found[0])
#         to_sq = u.index_1d_to_square(best_move_found[1])
#         move_info = best_move_found[2] if len(best_move_found) > 2 else ""
#         move_algebraic = f"{from_sq}-{to_sq}{move_info}"
#         print(f"{player} best move: {move_algebraic} (eval: {best_eval:.2f}, depth {current_depth}, time: {search_time:.2f}s)")

#         # Make the move - this updates board and globals (side_to_move, castling_rights, en_passant_target)
#         captured, _, _ = make_move(current_board, best_move_found, castling_rights, en_passant_target)

#         print("Board after move:")
#         u.print_board(current_board)

#     else:
#         # Check for game end condition
#         if is_king_in_check(current_board, is_white_turn):
#             print(f"Checkmate! {('Black' if is_white_turn else 'White')} wins.")
#         else:
#             print("Stalemate! Draw.")
#         break # End game loop

# print("\n--- Game Over ---")