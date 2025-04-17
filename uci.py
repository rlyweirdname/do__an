import sys
import time
import chess_engine
import utils as u

def log(message):
    print(message, file=sys.stderr, flush=True)

def uci_loop():
    log("UCI Engine Started")
    current_board = None
    current_cr = None
    current_ep = None
    is_white_turn = True

    while True:
        line = sys.stdin.readline().strip()
        log(f"Received: {line}")
        if not line:
            continue

        parts = line.split()
        command = parts[0]

        if command == "uci":
            print("id name PyChessBot 0.1")
            print("id author YourName")
            print("uciok")
            sys.stdout.flush()
        elif command == "isready":
            print("readyok")
            sys.stdout.flush()
        elif command == "quit":
            log("Quitting.")
            break
        elif command == "ucinewgame":
            try:
                chess_engine.reset_game_state()
                current_board = None
                log("New game state reset.")
            except Exception as e:
                log(f"Error during ucinewgame reset: {e}")

        elif command == "position":
            log("Parsing position command...")
            try:
                chess_engine.reset_game_state()
                current_board = list(chess_engine.board_array) 
                current_cr = chess_engine.castling_rights
                current_ep = chess_engine.en_passant_target
                is_white_turn = (chess_engine.side_to_move == 'w')
                log(f"  Initial state: Turn={'W' if is_white_turn else 'B'} CR={current_cr} EP={current_ep}")

                moves_start_index = -1
                if "startpos" in parts:
                    moves_start_index = parts.index("startpos") + 1
                elif "fen" in parts:
                    fen_start_index = parts.index("fen") + 1
                    fen_parts = parts[fen_start_index : fen_start_index + 6] 
                    fen_string = " ".join(fen_parts)
                    log(f"  FEN Received (basic parse): {fen_string}")
                    log("  FEN parsing needs implementation!")
                    moves_start_index = fen_start_index + 6 

                if moves_start_index != -1 and "moves" in parts[moves_start_index:]:
                    moves_index = parts.index("moves", moves_start_index) + 1
                    move_list = parts[moves_index:]
                    log(f"  Applying moves: {move_list}")
                    for move_uci in move_list:
                        log(f"    Applying: {move_uci}")
                        try:
                            move_tuple = uci_move_to_tuple(current_board, move_uci) 
                            log(f"      Converted to tuple: {move_tuple}")
                            _cap, next_cr, next_ep = chess_engine.make_move(current_board, move_tuple, current_cr, current_ep)
                            current_cr = next_cr
                            current_ep = next_ep
                            is_white_turn = (chess_engine.side_to_move == 'w')
                            log(f"      State after {move_uci}: Turn={'W' if is_white_turn else 'B'} CR={current_cr} EP={current_ep}")
                        except Exception as e:
                             log(f"      ERROR applying move {move_uci}: {e}")
                             break


            except Exception as e:
                log(f"ERROR parsing position command: {line} - {e}")

        elif command == "go":
            log("Received 'go' command")
            search_depth = 4
            if "depth" in parts:
                try:
                    depth_index = parts.index("depth") + 1
                    search_depth = int(parts[depth_index])
                    log(f"  Search depth set to: {search_depth}")
                except (ValueError, IndexError):
                    log("  Error parsing depth, using default.")
                    search_depth = 4 

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
                    uci_move_str = tuple_to_uci_move(best_move_tuple)
                    print(f"bestmove {uci_move_str}")
                    sys.stdout.flush()
                    log(f"Sent: bestmove {uci_move_str}")
                else:
                    log("  Engine returned no best move (checkmate/stalemate?)")

            except Exception as e:
                log(f"ERROR during find_best_move: {e}")
                import traceback
                log(traceback.format_exc())


        else:
            log(f"Unknown command: {command}")

def parse_fen(fen_string):
     log("parse_fen needs implementation")
     chess_engine.reset_game_state()
     return list(chess_engine.board_array), (chess_engine.side_to_move == 'w'), chess_engine.castling_rights, chess_engine.en_passant_target

def uci_move_to_tuple(board, uci_move):
    log(f"uci_move_to_tuple needs implementation for: {uci_move}")
    if len(uci_move) < 4 or len(uci_move) > 5:
         raise ValueError(f"Invalid UCI move format: {uci_move}")

    from_sq = uci_move[0:2]
    to_sq = uci_move[2:4]
    promotion = uci_move[4].lower() if len(uci_move) == 5 else None

    from_idx = u.square_to_index_1d(from_sq)
    to_idx = u.square_to_index_1d(to_sq)

    move_info = None
    piece = board[from_idx]

    if promotion and abs(piece) == 1 and (to_idx // 8 == 0 or to_idx // 8 == 7):
         move_info = promotion
    if move_info:
        return (from_idx, to_idx, move_info)
    else:
        return (from_idx, to_idx)


def tuple_to_uci_move(move_tuple):
    log(f"tuple_to_uci_move needs implementation for: {move_tuple}")
    if not move_tuple or len(move_tuple) < 2:
        return "0000"

    from_idx, to_idx = move_tuple[:2]
    move_info = move_tuple[2] if len(move_tuple) > 2 else None

    from_sq = u.index_1d_to_square(from_idx)
    to_sq = u.index_1d_to_square(to_idx)

    promotion_char = ""
    if move_info in ('q', 'r', 'n', 'b', 'Q', 'R', 'N', 'B'):
        promotion_char = move_info.lower()

    return f"{from_sq}{to_sq}{promotion_char}"


if __name__ == "__main__":
    uci_loop()