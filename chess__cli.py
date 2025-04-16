import time
import chess_engine
from chess_engine import (
    find_best_move,
    make_move,
    get_legal_moves,
    is_king_in_check,
    reset_game_state,

)
import utils as u


DEFAULT_SEARCH_DEPTH = 6 
MAX_MOVES = 150

# --- Helper Functions ---

def print_board_ascii(board_array):
    if not isinstance(board_array, list) or len(board_array) != 64:
        print("Error: Invalid board_array passed to print_board_ascii.")
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
                symbol = piece_symbols.get(piece_value, '?') 
            except IndexError:
                symbol = 'X'
            except TypeError:
                symbol = 'T' 
            print(f"{symbol} ", end="")
        print(f"|{8-rank}")
    print(" +-----------------+")
    print("  a b c d e f g h")


def format_move_algebraic(move_tuple):
    if not move_tuple or not isinstance(move_tuple, tuple) or len(move_tuple) < 2:
        return "InvalidMove(None)"
    try:
        from_sq = u.index_1d_to_square(move_tuple[0])
        to_sq = u.index_1d_to_square(move_tuple[1])
    except (ValueError, IndexError, TypeError):
         return f"InvalidMoveIndices({move_tuple})"
    move_info = move_tuple[2] if len(move_tuple) > 2 else None

    if move_info == 'castle_k': return "O-O"
    elif move_info == 'castle_q': return "O-O-O"
    elif move_info == 'ep': return f"{from_sq}x{to_sq} e.p."
    elif move_info in ('q', 'r', 'n', 'b', 'Q', 'R', 'N', 'B'): return f"{from_sq}-{to_sq}={move_info.upper()}"
    else: return f"{from_sq}-{to_sq}"

def run_game(white_depth=DEFAULT_SEARCH_DEPTH, black_depth=DEFAULT_SEARCH_DEPTH, verbose=True):
    try:
        chess_engine.reset_game_state()
    except Exception as e:
        print(f"Error during chess_engine.reset_game_state: {e}")
        return "Error"

    if not hasattr(chess_engine, 'board_array') or chess_engine.board_array is None:
        print("Error: chess_engine.board_array not initialized after reset.")
        return "Error"
    if not isinstance(chess_engine.board_array, list) or len(chess_engine.board_array) != 64:
         print(f"Error: chess_engine.board_array has invalid format after reset: {type(chess_engine.board_array)}, len={len(chess_engine.board_array) if isinstance(chess_engine.board_array, list) else 'N/A'}")
         return "Error"

    board_array = list(chess_engine.board_array)
    current_castling_rights = chess_engine.castling_rights
    current_en_passant_target = chess_engine.en_passant_target
    is_white_turn = (chess_engine.side_to_move == 'w')

    move_history = []
    full_move_number = 0 

    if verbose: print("Starting new game...")

    move_counter = 0 
    while full_move_number < MAX_MOVES: 
        move_counter += 1
        if is_white_turn:
            full_move_number += 1

        if verbose:
            print_board_ascii(board_array)
            turn_color = "White" if is_white_turn else "Black"
            print(f"\nMove {full_move_number}, {turn_color}'s turn")
            ep_sq = u.index_1d_to_square(current_en_passant_target) if current_en_passant_target is not None else '-'
            print(f"State: CR='{current_castling_rights}', EP={ep_sq}")

        legal_moves = get_legal_moves(board_array, is_white_turn, current_castling_rights, current_en_passant_target)
        if not legal_moves:
            king_in_check = is_king_in_check(board_array, is_white_turn)
            if king_in_check:
                result = '0-1' if is_white_turn else '1-0' 
                winner = "Black" if is_white_turn else "White"
                if verbose: print(f"\nCheckmate! {winner} wins.")
                return result
            else:
                result = '1/2-1/2' 
                if verbose: print("\nStalemate! Draw.")
                return result

        depth = white_depth if is_white_turn else black_depth
        start_time = time.time()
        try:
            best_move, engine_eval = find_best_move(
                board_array,
                depth=depth,
                is_maximizing_player=is_white_turn,
                current_castling_rights=current_castling_rights, 
                current_en_passant_target=current_en_passant_target 
            )
        except Exception as e:
            print(f"\n--- ERROR during find_best_move ---")
            import traceback; traceback.print_exc()
            print("Aborting game due to find_best_move error.")
            return "Error"
        end_time = time.time()

        if best_move is None:
            print("ERROR: Engine returned None move unexpectedly. Check engine logic. Declaring draw.")
            return '1/2-1/2'

        move_str = format_move_algebraic(best_move)
        if verbose:
            print(f"Engine ({'White' if is_white_turn else 'Black'}) chose: {move_str} (Eval: {engine_eval:.2f}, Time: {end_time - start_time:.2f}s)")

        try:

            _captured, next_cr, next_ep = make_move(
                board_array,
                best_move,
                current_castling_rights,
                current_en_passant_target
            )
            current_castling_rights = next_cr
            current_en_passant_target = next_ep

        except Exception as e:
             print(f"\n--- ERROR during make_move in CLI ---")
             print(f"Move: {best_move}, Board: {board_array[:16]}...")
             print(f"CR: {current_castling_rights}, EP: {current_en_passant_target}")
             import traceback; traceback.print_exc()
             print("Aborting game due to make_move error.")
             return "Error"

        is_white_turn = (chess_engine.side_to_move == 'w')
        move_history.append(best_move)


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
            result = '1-0' if not is_white_turn else '0-1' 
            winner = "White" if not is_white_turn else "Black"
            if verbose:
                 print(f"\nKing captured! {winner} wins.")
                 print_board_ascii(board_array) 
            return result
        else:
            current_player_legal_moves = get_legal_moves(board_array, is_white_turn, current_castling_rights, current_en_passant_target)

            if not current_player_legal_moves:
                king_in_check = is_king_in_check(board_array, is_white_turn) 
                if king_in_check:
                    result = '1-0' if not is_white_turn else '0-1' 
                    winner = "White" if not is_white_turn else "Black"
                    if verbose:
                        print(f"\nCheckmate! {winner} wins.")
                        print_board_ascii(board_array)
                    return result
                else:
                    result = '1/2-1/2'
                    if verbose:
                        print("\nStalemate! Draw.")
                        print_board_ascii(board_array)
                    return result

    if verbose:
        print_board_ascii(board_array)
        print(f"\nGame terminated after {full_move_number} full moves ({MAX_MOVES} move limit reached). Declaring draw.")
    return '1/2-1/2'


if __name__ == "__main__":
    game_result = run_game(white_depth=3, black_depth=3, verbose=True)
    print(f"\nFinal Game Result: {game_result}")