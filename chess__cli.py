import time
import chess_engine
from chess_engine import (
    find_best_move,
    make_move,
    get_legal_moves,
    is_king_in_check,
    reset_game_state, # Make sure this is correctly implemented in chess_engine.py
    # side_to_move is accessed via chess_engine.side_to_move
)
import utils as u # Assuming utils.py has get_starting_board_array and index_1d_to_square

# --- Constants and Configuration ---
DEFAULT_SEARCH_DEPTH = 4  # Adjust as needed for engine strength/speed
MAX_MOVES = 150 # Add a limit to prevent infinitely long games (draw after N full moves)

# --- Helper Functions ---

def print_board_ascii(board_array):
    """Prints a simple ASCII representation of the board."""
    if not isinstance(board_array, list) or len(board_array) != 64:
        print("Error: Invalid board_array passed to print_board_ascii.")
        # Optionally print the invalid data for debugging
        # print(f"Invalid board data: {board_array}")
        return
    piece_symbols = { 0:'.', 1:'P',-1:'p', 2:'N',-2:'n', 3:'B',-3:'b', 4:'R',-4:'r', 5:'Q',-5:'q', 6:'K',-6:'k'}
    print("\n  a b c d e f g h")
    print(" +-----------------+")
    for rank in range(8):
        print(f"{8-rank}| ", end="")
        for file in range(8):
            index_1d = rank * 8 + file
            try:
                piece_value = board_array[index_1d]
                symbol = piece_symbols.get(piece_value, '?') # Use '?' for unknown values
            except IndexError:
                symbol = 'X' # Indicate out-of-bounds error if board size is wrong
            except TypeError:
                symbol = 'T' # Indicate wrong data type in board array
            print(f"{symbol} ", end="")
        print(f"|{8-rank}")
    print(" +-----------------+")
    print("  a b c d e f g h")


def format_move_algebraic(move_tuple):
    """Formats a move tuple into readable algebraic-like notation."""
    if not move_tuple or not isinstance(move_tuple, tuple) or len(move_tuple) < 2:
        return "InvalidMove(None)"
    try:
        from_sq = u.index_1d_to_square(move_tuple[0])
        to_sq = u.index_1d_to_square(move_tuple[1])
    except (ValueError, IndexError, TypeError):
         # Handle cases where indices are invalid
         return f"InvalidMoveIndices({move_tuple})"
    move_info = move_tuple[2] if len(move_tuple) > 2 else None

    if move_info == 'castle_k': return "O-O"
    elif move_info == 'castle_q': return "O-O-O"
    elif move_info == 'ep': return f"{from_sq}x{to_sq} e.p."
    elif move_info in ('q', 'r', 'n', 'b', 'Q', 'R', 'N', 'B'): return f"{from_sq}-{to_sq}={move_info.upper()}"
    else: return f"{from_sq}-{to_sq}" # Assumes standard move or capture

# --- Main Game Logic ---

def run_game(white_depth=DEFAULT_SEARCH_DEPTH, black_depth=DEFAULT_SEARCH_DEPTH, verbose=True):
    """
    Runs a single game between two engine instances (can have different depths).
    Returns the result: '1-0' (White wins), '0-1' (Black wins), '1/2-1/2' (Draw), 'Error'.
    """
    # Initialize game state using chess_engine's reset function
    try:
        chess_engine.reset_game_state() # Ensure engine starts fresh
    except Exception as e:
        print(f"Error during chess_engine.reset_game_state: {e}")
        return "Error"

    # Get the initial state *after* resetting the engine
    if not hasattr(chess_engine, 'board_array') or chess_engine.board_array is None:
        print("Error: chess_engine.board_array not initialized after reset.")
        return "Error"
    if not isinstance(chess_engine.board_array, list) or len(chess_engine.board_array) != 64:
         print(f"Error: chess_engine.board_array has invalid format after reset: {type(chess_engine.board_array)}, len={len(chess_engine.board_array) if isinstance(chess_engine.board_array, list) else 'N/A'}")
         return "Error"

    # Use a copy for the CLI state to avoid modifying engine's internal state directly if unnecessary
    board_array = list(chess_engine.board_array)
    current_castling_rights = chess_engine.castling_rights
    current_en_passant_target = chess_engine.en_passant_target
    is_white_turn = (chess_engine.side_to_move == 'w')

    move_history = []
    full_move_number = 0 # Tracks pairs of moves (White + Black)

    if verbose: print("Starting new game...")

    move_counter = 0 # Tracks half-moves
    while full_move_number < MAX_MOVES: # Check against full move count limit
        move_counter += 1
        # Calculate full move number for display
        if is_white_turn:
            full_move_number += 1

        if verbose:
            print_board_ascii(board_array)
            turn_color = "White" if is_white_turn else "Black"
            print(f"\nMove {full_move_number}, {turn_color}'s turn")
            ep_sq = u.index_1d_to_square(current_en_passant_target) if current_en_passant_target is not None else '-'
            print(f"State: CR='{current_castling_rights}', EP={ep_sq}")

        # --- Check for Game Over BEFORE finding move ---
        # Checks if the current player has any legal moves
        legal_moves = get_legal_moves(board_array, is_white_turn, current_castling_rights, current_en_passant_target)
        if not legal_moves:
            king_in_check = is_king_in_check(board_array, is_white_turn)
            if king_in_check:
                result = '0-1' if is_white_turn else '1-0' # Checkmated
                winner = "Black" if is_white_turn else "White"
                if verbose: print(f"\nCheckmate! {winner} wins.")
                return result
            else:
                result = '1/2-1/2' # Stalemate
                if verbose: print("\nStalemate! Draw.")
                return result
        # --- End of Pre-Move Check ---

        # 2. Find the best move using the engine
        depth = white_depth if is_white_turn else black_depth
        start_time = time.time()
        try:
            best_move, engine_eval = find_best_move(
                board_array, # Pass the current board state
                depth=depth,
                is_maximizing_player=is_white_turn,
                current_castling_rights=current_castling_rights, # Pass current CR
                current_en_passant_target=current_en_passant_target # Pass current EP
            )
        except Exception as e:
            print(f"\n--- ERROR during find_best_move ---")
            import traceback; traceback.print_exc()
            print("Aborting game due to find_best_move error.")
            return "Error"
        end_time = time.time()

        if best_move is None:
            # This should theoretically be caught by the checkmate/stalemate check above.
            # If it happens here, it indicates a deeper engine bug.
            print("ERROR: Engine returned None move unexpectedly. Check engine logic. Declaring draw.")
            # Optionally print state for debugging
            # print_board_ascii(board_array)
            # print(f"State: CR='{current_castling_rights}', EP={current_en_passant_target}, Turn={'W' if is_white_turn else 'B'}")
            return '1/2-1/2'

        move_str = format_move_algebraic(best_move)
        if verbose:
            print(f"Engine ({'White' if is_white_turn else 'Black'}) chose: {move_str} (Eval: {engine_eval:.2f}, Time: {end_time - start_time:.2f}s)")

        # 3. Make the move AND UPDATE THE STATE
        try:
            # Call make_move on the CLI's board state
            # It modifies board_array in-place and returns next state vars
            _captured, next_cr, next_ep = make_move(
                board_array, # The board managed by this run_game function
                best_move,
                current_castling_rights,
                current_en_passant_target
            )
            # *** Update the state variables for the next iteration ***
            current_castling_rights = next_cr
            current_en_passant_target = next_ep

        except Exception as e:
             print(f"\n--- ERROR during make_move in CLI ---")
             print(f"Move: {best_move}, Board: {board_array[:16]}...")
             print(f"CR: {current_castling_rights}, EP: {current_en_passant_target}")
             import traceback; traceback.print_exc()
             print("Aborting game due to make_move error.")
             return "Error"

        # 4. Update whose turn it is based on the global state from chess_engine
        # (make_move should have flipped chess_engine.side_to_move)
        is_white_turn = (chess_engine.side_to_move == 'w')
        move_history.append(best_move)


        # --- REFINED POST-MOVE GAME OVER CHECK ---
        # Check the status for the player whose turn it is NOW (after the move was made)

        # First, check if the current player's King is even on the board.
        current_player_king_val = 6 if is_white_turn else -6
        current_player_king_present = False
        try:
            for piece_val in board_array:
                if piece_val == current_player_king_val:
                    current_player_king_present = True
                    break
        except TypeError:
             print("Error: Board array contains non-integer values during king check.")
             print_board_ascii(board_array)
             return "Error"


        if not current_player_king_present:
            # The player whose turn it is supposed to be has no king! Opponent wins.
            result = '1-0' if not is_white_turn else '0-1' # The player who JUST moved wins
            winner = "White" if not is_white_turn else "Black"
            if verbose:
                 print(f"\nKing captured! {winner} wins.")
                 print_board_ascii(board_array) # Show final board
            return result
        else:
            # King is present, now check for legal moves (checkmate/stalemate)
            current_player_legal_moves = get_legal_moves(board_array, is_white_turn, current_castling_rights, current_en_passant_target)

            if not current_player_legal_moves:
                # No legal moves for the player whose turn it is.
                king_in_check = is_king_in_check(board_array, is_white_turn) # Is their own king attacked?
                if king_in_check:
                    # Checkmate! The player whose turn it is now is checkmated.
                    result = '1-0' if not is_white_turn else '0-1' # Winner is opponent
                    winner = "White" if not is_white_turn else "Black"
                    if verbose:
                        print(f"\nCheckmate! {winner} wins.")
                        print_board_ascii(board_array) # Show final board
                    return result
                else:
                    # Stalemate! No legal moves, but not in check.
                    result = '1/2-1/2'
                    if verbose:
                        print("\nStalemate! Draw.")
                        print_board_ascii(board_array) # Show final board
                    return result
        # --- End of Refined Post-Move Check ---

        # 5. TODO: Add checks for 50-move rule and 3-fold repetition if needed for robust draws

    # Game ended due to move limit (full_move_number reached MAX_MOVES)
    if verbose:
        print_board_ascii(board_array) # Print final board
        print(f"\nGame terminated after {full_move_number} full moves ({MAX_MOVES} move limit reached). Declaring draw.")
    return '1/2-1/2'


if __name__ == "__main__":
    # Example: Run a single game with default depth and print results
    # Set verbose=False for faster execution in ELO testing loops
    # Use verbose=True when debugging
    game_result = run_game(white_depth=3, black_depth=3, verbose=True)
    print(f"\nFinal Game Result: {game_result}")