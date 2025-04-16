import sys
import time
import chess_engine
import utils as u

# --- Logging Function ---
def log(message):
    """Prints message to stderr for debugging."""
    print(message, file=sys.stderr, flush=True)

# --- Main UCI Loop ---
def uci_loop():
    log("UCI Engine Started")
    # Initialize engine state (or ensure chess_engine does it)
    # Important: Need board_array, cr, ep, turn accessible/modifiable
    current_board = None
    current_cr = None
    current_ep = None
    is_white_turn = True # Default, will be set by position cmd

    while True:
        line = sys.stdin.readline().strip()
        log(f"Received: {line}")
        if not line:
            continue # Skip empty lines

        parts = line.split()
        command = parts[0]

        if command == "uci":
            print("id name PyChessBot 0.1") # Replace with your engine name
            print("id author YourName")
            # Add options here if any
            print("uciok")
            sys.stdout.flush()
        elif command == "isready":
            # Perform any setup if needed
            print("readyok")
            sys.stdout.flush()
        elif command == "quit":
            log("Quitting.")
            break # Exit loop
        elif command == "ucinewgame":
            # Reset engine state for a new game
            try:
                chess_engine.reset_game_state()
                # Optional: Reset local copies if you maintain them separately
                current_board = None # Force reload on next position
                log("New game state reset.")
            except Exception as e:
                log(f"Error during ucinewgame reset: {e}")

        elif command == "position":
            # --- Position Parsing ---
            log("Parsing position command...")
            try:
                # Reset to a known state before applying moves
                chess_engine.reset_game_state() # Start fresh
                current_board = list(chess_engine.board_array) # Get initial board
                current_cr = chess_engine.castling_rights
                current_ep = chess_engine.en_passant_target
                is_white_turn = (chess_engine.side_to_move == 'w')
                log(f"  Initial state: Turn={'W' if is_white_turn else 'B'} CR={current_cr} EP={current_ep}")

                moves_start_index = -1
                if "startpos" in parts:
                    moves_start_index = parts.index("startpos") + 1
                elif "fen" in parts:
                    fen_start_index = parts.index("fen") + 1
                    # Basic FEN parsing (needs robust implementation)
                    fen_parts = parts[fen_start_index : fen_start_index + 6] # fen string can have spaces
                    fen_string = " ".join(fen_parts)
                    log(f"  FEN Received (basic parse): {fen_string}")
                    # TODO: Implement parse_fen(fen_string) to set board_array, turn, cr, ep
                    # current_board, is_white_turn, current_cr, current_ep = parse_fen(fen_string)
                    log("  FEN parsing needs implementation!")
                    moves_start_index = fen_start_index + 6 # Index after the FEN parts

                if moves_start_index != -1 and "moves" in parts[moves_start_index:]:
                    moves_index = parts.index("moves", moves_start_index) + 1
                    move_list = parts[moves_index:]
                    log(f"  Applying moves: {move_list}")
                    # Apply moves one by one
                    for move_uci in move_list:
                        log(f"    Applying: {move_uci}")
                        # TODO: Convert uci move (e.g., "e2e4", "e7e8q") to your engine's move tuple format
                        # This requires parsing squares and promotion char
                        try:
                            move_tuple = uci_move_to_tuple(current_board, move_uci) # Needs implementation
                            log(f"      Converted to tuple: {move_tuple}")
                            # Make move and update state *locally* for next move in sequence
                            _cap, next_cr, next_ep = chess_engine.make_move(current_board, move_tuple, current_cr, current_ep)
                            current_cr = next_cr
                            current_ep = next_ep
                            is_white_turn = (chess_engine.side_to_move == 'w') # Update turn based on engine's global change
                            log(f"      State after {move_uci}: Turn={'W' if is_white_turn else 'B'} CR={current_cr} EP={current_ep}")
                        except Exception as e:
                             log(f"      ERROR applying move {move_uci}: {e}")
                             # Decide how to handle error - maybe break?


            except Exception as e:
                log(f"ERROR parsing position command: {line} - {e}")

        elif command == "go":
            log("Received 'go' command")
            search_depth = 4 # Default or parse from command
            if "depth" in parts:
                try:
                    depth_index = parts.index("depth") + 1
                    search_depth = int(parts[depth_index])
                    log(f"  Search depth set to: {search_depth}")
                except (ValueError, IndexError):
                    log("  Error parsing depth, using default.")
                    search_depth = 4 # Fallback

            # Ensure board state is loaded correctly from previous 'position' command
            if current_board is None:
                 log("ERROR: 'go' received before 'position'. Cannot search.")
                 continue

            log(f"  Starting search: Depth={search_depth}, Turn={'W' if is_white_turn else 'B'}, CR={current_cr}, EP={current_ep}")
            try:
                start_time = time.time()
                best_move_tuple, eval_score = chess_engine.find_best_move(
                    current_board,
                    search_depth,
                    is_white_turn,
                    current_cr,
                    current_ep
                )
                end_time = time.time()
                log(f"  Search finished in {end_time - start_time:.2f}s. Result: {best_move_tuple}, Eval: {eval_score}")

                if best_move_tuple:
                    # Convert internal move tuple back to UCI format (e.g., "e2e4", "e7e8q")
                    uci_move_str = tuple_to_uci_move(best_move_tuple) # Needs implementation
                    print(f"bestmove {uci_move_str}")
                    sys.stdout.flush()
                    log(f"Sent: bestmove {uci_move_str}")
                else:
                    log("  Engine returned no best move (checkmate/stalemate?)")
                    # UCI doesn't specify output here, but maybe send null move if appropriate?
                    # print("bestmove 0000") # Consult UCI spec for best practice

            except Exception as e:
                log(f"ERROR during find_best_move: {e}")
                import traceback
                log(traceback.format_exc())


        else:
            log(f"Unknown command: {command}")

# --- Helper functions needed ----

def parse_fen(fen_string):
     # TODO: Implement FEN parser
     # Should return: board_array (list), is_white_turn (bool), castling_rights (str), en_passant_target (int or None)
     log("parse_fen needs implementation")
     # Placeholder: return starting position for now
     chess_engine.reset_game_state()
     return list(chess_engine.board_array), (chess_engine.side_to_move == 'w'), chess_engine.castling_rights, chess_engine.en_passant_target

def uci_move_to_tuple(board, uci_move):
    """Converts UCI move string (e.g., e2e4, e7e8q) to internal tuple format."""
    # TODO: Implement UCI move parser
    # Needs to handle standard moves, captures, and promotions
    log(f"uci_move_to_tuple needs implementation for: {uci_move}")
    if len(uci_move) < 4 or len(uci_move) > 5:
         raise ValueError(f"Invalid UCI move format: {uci_move}")

    from_sq = uci_move[0:2]
    to_sq = uci_move[2:4]
    promotion = uci_move[4].lower() if len(uci_move) == 5 else None

    from_idx = u.square_to_index_1d(from_sq)
    to_idx = u.square_to_index_1d(to_sq)

    # Determine move info (castling, ep, promotion) - this might require more context from board state
    move_info = None
    piece = board[from_idx]

    # Basic promotion check
    if promotion and abs(piece) == 1 and (to_idx // 8 == 0 or to_idx // 8 == 7):
         move_info = promotion
    # TODO: Add checks for castling and en passant based on move and board state
    # This is tricky, as UCI move doesn't explicitly state castling/ep

    if move_info:
        return (from_idx, to_idx, move_info)
    else:
        return (from_idx, to_idx)


def tuple_to_uci_move(move_tuple):
    """Converts internal move tuple back to UCI move string."""
    # TODO: Implement tuple to UCI converter
    log(f"tuple_to_uci_move needs implementation for: {move_tuple}")
    if not move_tuple or len(move_tuple) < 2:
        return "0000" # Null move for error/invalid tuple

    from_idx, to_idx = move_tuple[:2]
    move_info = move_tuple[2] if len(move_tuple) > 2 else None

    from_sq = u.index_1d_to_square(from_idx)
    to_sq = u.index_1d_to_square(to_idx)

    promotion_char = ""
    if move_info in ('q', 'r', 'n', 'b', 'Q', 'R', 'N', 'B'):
        promotion_char = move_info.lower()
    # Note: UCI doesn't use special notation for castling or EP in the move itself.
    # King move e1g1 IS kingside castle if legal. Pawn move e5f6 IS en passant if legal.

    return f"{from_sq}{to_sq}{promotion_char}"


if __name__ == "__main__":
    uci_loop()