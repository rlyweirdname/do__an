import sys
import time
import chess_engine
import utils as u  
import io 
import traceback    

PIECE_MAP_FEN_TO_INT = {
    'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6,
    'p': -1, 'n': -2, 'b': -3, 'r': -4, 'q': -5, 'k': -6
}


def log(message):
    print(f"info string [UCI LOG] {message}", file=sys.stderr, flush=True)

def parse_fen_and_set_engine_state(fen_string):
    log(f"Attempting to parse FEN: {fen_string}")
    parts = fen_string.split()
    if len(parts) < 4: raise ValueError(f"Invalid FEN: Expected >= 4 parts. Got: {fen_string}")

    board_str, turn_char, cr_str, ep_str = parts[0:4]
    halfmove_str = parts[4] if len(parts) > 4 else "0"
    fullmove_str = parts[5] if len(parts) > 5 else "1"

    new_board_array = [0] * 64; rank, file_idx = 0, 0; squares_described = 0
    for char_fen in board_str:
        if rank >= 8: break
        if char_fen == '/':
            if file_idx != 8: raise ValueError(f"FEN Rank {rank+1} incomplete.")
            rank += 1; file_idx = 0
        elif char_fen.isdigit():
            num_empty = int(char_fen)
            if not (1 <= num_empty <= 8): raise ValueError(f"FEN invalid empty count '{num_empty}'.")
            if file_idx + num_empty > 8: raise ValueError(f"FEN Rank {rank+1} overflow with '{num_empty}'.")
            for _ in range(num_empty):
                if rank * 8 + file_idx < 64: new_board_array[rank * 8 + file_idx] = 0
                file_idx += 1
            squares_described += num_empty
        elif char_fen in PIECE_MAP_FEN_TO_INT:
            if file_idx >= 8: raise ValueError(f"FEN Rank {rank+1} overflow with piece '{char_fen}'.")
            if rank * 8 + file_idx < 64: new_board_array[rank * 8 + file_idx] = PIECE_MAP_FEN_TO_INT[char_fen]
            file_idx += 1; squares_described +=1
        else: raise ValueError(f"FEN invalid char '{char_fen}'.")
    if rank != 7 or file_idx != 8: raise ValueError("FEN board string incomplete.")
    if squares_described != 64: raise ValueError(f"FEN described {squares_described} squares, expected 64.")
    chess_engine.board_array = new_board_array

    if turn_char == 'w': chess_engine.side_to_move = 'w'
    elif turn_char == 'b': chess_engine.side_to_move = 'b'
    else: raise ValueError(f"FEN invalid turn '{turn_char}'.")

    if not all(c in 'KQkq-' for c in cr_str) or (cr_str != '-' and len(set(cr_str)) != len(cr_str)):
        raise ValueError(f"FEN invalid castling rights '{cr_str}'.")
    chess_engine.castling_rights = cr_str

    if ep_str == '-': chess_engine.en_passant_target = None
    else:
        try:
            ep_index = u.square_to_index_1d(ep_str)
            ep_rank_from_top = ep_index // 8
            valid_ep = (chess_engine.side_to_move == 'w' and ep_rank_from_top == 2) or \
                       (chess_engine.side_to_move == 'b' and ep_rank_from_top == 5)
            if valid_ep: chess_engine.en_passant_target = ep_index
            else:
                log(f"FEN Warning: EP target {ep_str} invalid for turn {chess_engine.side_to_move}. Setting EP to None.")
                chess_engine.en_passant_target = None
        except ValueError: raise ValueError(f"FEN invalid EP target square '{ep_str}'.")

    try:
        chess_engine.halfmove_clock = int(halfmove_str)
        chess_engine.fullmove_number = int(fullmove_str)
        if chess_engine.halfmove_clock < 0 or chess_engine.fullmove_number < 1: raise ValueError()
    except ValueError: raise ValueError(f"FEN invalid halfmove '{halfmove_str}' or fullmove '{fullmove_str}'.")
    log("FEN parsed successfully.")


def find_matching_move_tuple(board_state, uci_move_str, current_player_is_white, current_cr, current_ep):
    if len(uci_move_str) < 4 or len(uci_move_str) > 5: raise ValueError(f"Invalid UCI move length: {uci_move_str}")
    from_sq_str, to_sq_str = uci_move_str[0:2], uci_move_str[2:4]
    uci_promo_char = uci_move_str[4].lower() if len(uci_move_str) == 5 else None
    try:
        from_idx = u.square_to_index_1d(from_sq_str)
        to_idx = u.square_to_index_1d(to_sq_str)
    except ValueError: raise ValueError(f"Invalid square in UCI move: {uci_move_str}")

    pseudo_legal_moves = chess_engine.generate_pseudo_legal_moves(board_state, current_player_is_white, current_cr, current_ep)
    for move_tuple in pseudo_legal_moves:
        if move_tuple[0] == from_idx and move_tuple[1] == to_idx:
            engine_promo_char = None
            if len(move_tuple) > 2 and isinstance(move_tuple[2], str) and move_tuple[2].lower() in 'qrbn':
                engine_promo_char = move_tuple[2].lower()
            if uci_promo_char == engine_promo_char: return move_tuple
    raise ValueError(f"UCI move '{uci_move_str}' not found in pseudo-legal list.")


def tuple_to_uci_move(move_tuple):
    if not isinstance(move_tuple, tuple) or len(move_tuple) < 2: return "0000" 
    from_idx, to_idx = move_tuple[:2]
    move_info = move_tuple[2] if len(move_tuple) > 2 else None
    try: from_sq, to_sq = u.index_1d_to_square(from_idx), u.index_1d_to_square(to_idx)
    except ValueError: return "0000"
    promo = move_info.lower() if isinstance(move_info, str) and move_info.lower() in 'qrbn' else ""
    return f"{from_sq}{to_sq}{promo}"

def uci_loop():
    log("UCI Engine Booting...")
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                 log("Received EOF or empty line, exiting.")
                 break 
            line = line.strip() 
            if not line: continue 

        except Exception as e: 
            log(f"Input error or EOF: {e}. Exiting.")
            break
        
        log(f"Received: '{line}'")
        parts = line.split()
        if not parts: continue
        command = parts[0]

        try:
            #cmds:
            #position startpos moves e2e4 e7e5
            #uci
            #isready
            #quit
            #ucinewgame
            if command == "uci":
                print(f"id name {getattr(chess_engine, 'ENGINE_NAME', 'PyChessBot')}")
                print(f"id author {getattr(chess_engine, 'AUTHOR_NAME', 'Anonymous')}")
                print("uciok")
            elif command == "isready":
                print("readyok")
            elif command == "quit":
                log("Quit command received. Exiting.")
                break
            elif command == "ucinewgame":
                chess_engine.reset_game_state() 
                log("New game state initialized.")
            
            elif command == "position":
                moves_keyword_idx = -1
                try: moves_keyword_idx = parts.index("moves")
                except ValueError: pass 

                if "startpos" in parts:
                    log("  Processing 'startpos'")
                    chess_engine.reset_game_state()
                    moves_start_idx = moves_keyword_idx + 1 if moves_keyword_idx != -1 else len(parts)
                elif "fen" in parts:
                    fen_keyword_idx = parts.index("fen")
                    fen_parts_end_idx = moves_keyword_idx if moves_keyword_idx != -1 else len(parts)
                    if fen_keyword_idx + 1 >= fen_parts_end_idx: raise ValueError("No FEN string found after 'fen'.")
                    fen_string = " ".join(parts[fen_keyword_idx + 1 : fen_parts_end_idx])
                    log(f"  Processing 'fen': {fen_string}")
                    try:
                        parse_fen_and_set_engine_state(fen_string) 
                    except Exception as fen_e:
                        log(f"  Error parsing FEN '{fen_string}': {fen_e}. Resetting to startpos.")
                        chess_engine.reset_game_state()
                    moves_start_idx = moves_keyword_idx + 1 if moves_keyword_idx != -1 else len(parts)
                else:
                    raise ValueError("'position' command requires 'startpos' or 'fen'.")

                if moves_keyword_idx != -1 and moves_start_idx < len(parts):
                    move_list = parts[moves_start_idx:]
                    log(f"  Applying moves: {move_list}")
                    for uci_move_str in move_list:
                        log(f"    Attempting to apply: {uci_move_str}")
                        try:
                            board_state = list(chess_engine.board_array)
                            turn_is_white = chess_engine.side_to_move == 'w'
                            cr_state = chess_engine.castling_rights
                            ep_state = chess_engine.en_passant_target
                            
                            full_move_tuple = find_matching_move_tuple(board_state, uci_move_str, turn_is_white, cr_state, ep_state)
                            log(f"      Matched internal move: {full_move_tuple}")
                            
                            chess_engine.make_move(chess_engine.board_array, full_move_tuple, cr_state, ep_state)
                            log(f"      Move {uci_move_str} applied. New turn: {chess_engine.side_to_move}")
                        except ValueError as ve: 
                            log(f"    ERROR: Could not match UCI move '{uci_move_str}': {ve}. Stopping move application.")
                            raise 
                        except Exception as e_make:
                            log(f"    ERROR applying matched move '{uci_move_str}' ({full_move_tuple}): {e_make}. Stopping.")
                            raise
                log("Position setup complete.")

            elif command == "go":
                search_depth = 5 
                if "depth" in parts:
                    try: search_depth = int(parts[parts.index("depth") + 1])
                    except: pass 
                log(f"Starting search (Depth: {search_depth}) for side: {chess_engine.side_to_move}")
                start_time = time.time()
                best_m_tuple, _ = chess_engine.find_best_move(
                    list(chess_engine.board_array), 
                    search_depth, chess_engine.side_to_move == 'w',
                    chess_engine.castling_rights, chess_engine.en_passant_target
                )
                search_duration = time.time() - start_time
                log(f"Search completed in {search_duration:.3f}s.")
                uci_response_move = tuple_to_uci_move(best_m_tuple) if best_m_tuple else "0000"
                print(f"bestmove {uci_response_move}")
                log(f"Sent: bestmove {uci_response_move}")

            else:
                log(f"Unknown command: '{command}'")
        
        except Exception as cmd_e: 
             log(f"ERROR processing command '{line}': {cmd_e}")
             log(traceback.format_exc())
        finally:
             sys.stdout.flush() 



if __name__ == "__main__":
    try:
        uci_loop()
    except Exception as main_e: 
        log(f"FATAL ERROR in main UCI loop: {main_e}")
        log(traceback.format_exc())

