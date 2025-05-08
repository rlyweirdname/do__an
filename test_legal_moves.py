import sys
import time
import copy
import chess_engine
import utils as u

PIECE_MAP_FEN_TO_INT = {
    'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6,
    'p': -1, 'n': -2, 'b': -3, 'r': -4, 'q': -5, 'k': -6
}
PIECE_MAP_CHAR_TO_FEN_PROMO = {
    'q': 'q', 'r': 'r', 'n': 'n', 'b': 'b',
    'Q': 'q', 'R': 'r', 'N': 'n', 'B': 'b',
}

def log(message):
    print(message, file=sys.stderr, flush=True)

def parse_fen_and_set_engine_state(fen_string):
    try:
        parts = fen_string.split()
        if len(parts) < 4:
             raise ValueError(f"Invalid FEN format, expected at least 4 parts, got {len(parts)}")
        board_str, turn_char, cr_str, ep_str = parts[0:4]
        new_board_array = [0] * 64
        rank = 0
        file = 0
        for char in board_str:
            if char == '/':
                rank += 1
                file = 0
                if rank >= 8:
                     raise ValueError(f"Invalid FEN board string, too many ranks: {board_str}")
            elif char.isdigit():
                num_empty = int(char)
                if file + num_empty > 8:
                     raise ValueError(f"Invalid FEN board string, rank overflow: {board_str} at rank {rank}, file {file} with {num_empty} empty")
                file += num_empty
            elif char in PIECE_MAP_FEN_TO_INT:
                index_1d = rank * 8 + file
                if not (0 <= index_1d < 64):
                    raise ValueError(f"FEN board parsing error: Calculated index out of bounds {index_1d}")
                new_board_array[index_1d] = PIECE_MAP_FEN_TO_INT[char]
                file += 1
                if file > 8:
                     raise ValueError(f"Invalid FEN board string, rank overflow: {board_str} at rank {rank}, file {file}")
            else:
                raise ValueError(f"Invalid character '{char}' in FEN board string: {board_str}")
        squares_count = sum(int(c) if c.isdigit() else 1 for c in board_str if c != '/')
        if squares_count != 64:
             raise ValueError(f"Invalid FEN board string, total squares parsed ({squares_count}) is not 64.")
        chess_engine.board_array = new_board_array
        if turn_char == 'w':
            chess_engine.side_to_move = 'w'
        elif turn_char == 'b':
            chess_engine.side_to_move = 'b'
        else:
             raise ValueError(f"Invalid turn character '{turn_char}' in FEN")
        if not all(c in 'KQkq-' for c in cr_str):
             raise ValueError(f"Invalid castling rights string '{cr_str}' in FEN")
        chess_engine.castling_rights = cr_str
        if ep_str == '-':
            chess_engine.en_passant_target = None
        else:
            try:
                ep_index = u.square_to_index_1d(ep_str)
                ep_rank = ep_index // 8
                valid_ep = False
                if turn_char == 'w' and ep_rank == 2: valid_ep = True
                elif turn_char == 'b' and ep_rank == 5: valid_ep = True
                if not valid_ep:
                    chess_engine.en_passant_target = None
                else:
                     chess_engine.en_passant_target = ep_index
            except Exception as e:
                 raise ValueError(f"Invalid EP target square string '{ep_str}' in FEN: {e}") from e
        try:
            if len(parts) > 4:
                chess_engine.halfmove_clock = int(parts[4])
            if len(parts) > 5:
                chess_engine.fullmove_number = int(parts[5])
        except (ValueError, IndexError):
            pass
    except ValueError as ve:
        print(f"FEN Validation Error during parsing: {ve}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"FATAL UNCAUGHT ERROR during FEN parsing: {e}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        raise

def tuple_to_uci_move(move_tuple):
    if not isinstance(move_tuple, tuple) or len(move_tuple) < 2:
        return "0000"
    from_idx, to_idx = move_tuple[:2]
    move_info = move_tuple[2] if len(move_tuple) > 2 else None
    try:
        from_sq = u.index_1d_to_square(from_idx)
        to_sq = u.index_1d_to_square(to_idx)
    except Exception as e:
         return "0000"
    promotion_char = ""
    if isinstance(move_info, str) and move_info.lower() in PIECE_MAP_CHAR_TO_FEN_PROMO:
        promotion_char = move_info.lower()
    return f"{from_sq}{to_sq}{promotion_char}"

def run_legal_moves_test(fen, expected_moves_uci, test_name):
    test_passed = False
    try:
        parse_fen_and_set_engine_state(fen)
        current_board_state = list(chess_engine.board_array)
        current_side = chess_engine.side_to_move
        current_cr = chess_engine.castling_rights
        current_ep = chess_engine.en_passant_target
        generated_moves_tuple = chess_engine.get_legal_moves(
             current_board_state,
             (current_side == 'w'),
             current_cr,
             current_ep
        )
        generated_moves_uci = [tuple_to_uci_move(move) for move in generated_moves_tuple]
        generated_moves_uci_sorted = sorted(generated_moves_uci)
        expected_moves_uci_sorted = sorted(expected_moves_uci)
        if generated_moves_uci_sorted == expected_moves_uci_sorted:
            test_passed = True
        else:
            generated_set = set(generated_moves_uci_sorted)
            expected_set = set(expected_moves_uci_sorted)
            missing_moves = sorted(list(expected_set - generated_set))
            extra_moves = sorted(list(generated_set - expected_set))
    except Exception as e:
        import traceback
        traceback.print_exc()
        test_passed = False
    finally:
         try:
             chess_engine.reset_game_state()
         except Exception as e:
              pass
    return test_passed

def run_all_tests():
    tests = [
        {
            'name': 'Start Position (White)',
            'fen': 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
            'expected_uci': [
                'a2a3', 'a2a4', 'b2b3', 'b2b4', 'c2c3', 'c2c4', 'd2d3', 'd2d4',
                'e2e3', 'e2e4', 'f2f3', 'f2f4', 'g2g3', 'g2g4', 'h2h3', 'h2h4',
                'b1a3', 'b1c3', 'g1f3', 'g1h3'
            ]
        },
        {
            'name': 'Checkmate (Black)',
            'fen': '8/8/8/8/2k5/4R3/8/3K4 b - - 0 1',
            'expected_uci': []
        },
        {
            'name': 'Pinned Piece Cannot Move',
            'fen': '8/8/3q4/8/3R4/3K4/8/8 w - - 0 1',
            'expected_uci': ['d3c2', 'd3c3', 'd3c4', 'd3e2', 'd3e3', 'd3e4', 'd4d6']
        },
        {
            'name': 'Pawn Promotion (White)',
            'fen': '8/P7/k7/8/8/K7/8/8 w - - 0 1',
            'expected_uci': [
                'a7a8q', 'a7a8r', 'a7a8n', 'a7a8b',
                'a3a2', 'a3b2', 'a3b3', 'a3b4', 'a3a4'
            ]
        },
        {
            'name': 'Pawn Promotion Capture (White)',
            'fen': '4r3/P1k5/8/8/8/K7/8/8 w - - 0 1',
            'expected_uci': [
                'a7a8q', 'a7a8r', 'a7a8n', 'a7a8b',
                'a3a2', 'a3b2', 'a3b3', 'a3b4', 'a3a4'
            ]
        }
    ]
    results = []
    for test_case in tests:
        passed = run_legal_moves_test(
             test_case['fen'],
             test_case['expected_uci'],
             test_case['name']
         )
        results.append((test_case['name'], passed))
    all_passed = True
    for name, passed in results:
        if not passed:
            all_passed = False
    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()