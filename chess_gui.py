import tkinter as tk
from PIL import Image, ImageTk 
import utils as u
import time
import chess_engine 
from chess_engine import ( 
    create_test_board_minimax_start,
    find_best_move,
    make_move,
    get_legal_moves,
    is_king_in_check,
)

class ChessGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chess Engine GUI")
        self.geometry("600x640")

        self.board_array = u.get_starting_board_array()
        self.castling_rights = chess_engine.castling_rights
        self.en_passant_target = chess_engine.en_passant_target
        self.is_white_turn = (chess_engine.side_to_move == 'w')

        self.canvas = tk.Canvas(self, width=480, height=480, borderwidth=1, relief="solid")
        self.canvas.pack(pady=10)
        self.square_size = 480 / 8

        self.status_label = tk.Label(self, text="White to move", font=("Arial", 12))
        self.status_label.pack()

        self.engine_move_display = tk.Label(self, text="Engine's Last Move: None", font=("Arial", 10))
        self.engine_move_display.pack()

        self.error_message_label = tk.Label(self, text="", fg="red", font=("Arial", 10))
        self.error_message_label.pack()

        history_frame = tk.Frame(self) 
        history_frame.pack(pady=5, fill=tk.X, expand=False, padx=20) 

        history_label = tk.Label(history_frame, text="Move History:", font=("Arial", 10))
        history_label.pack(side=tk.TOP, anchor='w')

        self.history_scrollbar = tk.Scrollbar(history_frame, orient=tk.VERTICAL)
        self.history_text = tk.Text(
            history_frame,
            height=6,
            width=40, 
            wrap=tk.WORD,
            yscrollcommand=self.history_scrollbar.set,
            font=("Courier New", 9),
            state='disabled'
        )
        self.history_scrollbar.config(command=self.history_text.yview)

        self.history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.on_square_click)
        self.from_square_index = None
        self.possible_moves_from_selected = []

        self.move_history = []

        self.piece_images_pil = {}
        self.piece_images_tk = {}
        self.load_piece_images()
        self.draw_board()
        self.update_board_pieces()
        self.update_status_label()


    def load_piece_images(self):
        piece_filenames = {
            'P': 'wp.png', 'N': 'wN.png', 'B': 'wB.png', 'R': 'wR.png', 'Q': 'wQ.png', 'K': 'wK.png',
            'p': 'p.png', 'n': 'n.png', 'b': 'b.png', 'r': 'r.png', 'q': 'q.png', 'k': 'k.png'
        }
        target_size = int(self.square_size * 0.8)
        try:
            for piece_char, filename in piece_filenames.items():
                path = f"images/{filename}"
                image = Image.open(path).convert("RGBA")
                image = image.resize((target_size, target_size), Image.Resampling.LANCZOS)
                self.piece_images_pil[piece_char] = image
                self.piece_images_tk[piece_char] = ImageTk.PhotoImage(image)
            print("Piece images loaded successfully.")
        except FileNotFoundError as e:
            print(f"Error loading image: {e}. Make sure 'images' directory exists and contains all piece PNGs (wp.png, bp.png, etc.).")
            self.error_message_label.config(text=f"Error loading image: {e}")
            self.destroy()
        except Exception as e:
            print(f"An error occurred during image loading: {e}")
            self.error_message_label.config(text=f"Image loading error: {e}")
            self.destroy()


    def draw_board(self):
        for rank in range(8):
            for file in range(8):
                x1, y1 = file * self.square_size, rank * self.square_size
                x2, y2 = x1 + self.square_size, y1 + self.square_size
                color = "white" if (rank + file) % 2 == 0 else "#D3D3D3"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, tags="square")


    def update_board_pieces(self):
        self.canvas.delete("piece")
        piece_symbols = { 1:'P',-1:'p', 2:'N',-2:'n', 3:'B',-3:'b', 4:'R',-4:'r', 5:'Q',-5:'q', 6:'K',-6:'k'}
        for index in range(64):
            piece_value = self.board_array[index]
            piece_symbol = piece_symbols.get(piece_value)
            if piece_symbol and piece_symbol in self.piece_images_tk:
                rank, file = divmod(index, 8)
                x_center = (file * self.square_size) + self.square_size / 2
                y_center = (rank * self.square_size) + self.square_size / 2
                self.canvas.create_image(x_center, y_center, image=self.piece_images_tk[piece_symbol], tags="piece")


    def highlight_square(self, index_1d, color, tag="highlight"):
        rank, file = divmod(index_1d, 8)
        x1, y1 = file * self.square_size, rank * self.square_size
        x2, y2 = x1 + self.square_size, y1 + self.square_size
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=3, tags=tag)


    def highlight_legal_moves(self, moves):
        self.canvas.delete("legal_move_highlight")
        radius = self.square_size / 8
        for move in moves:
            to_index = move[1]
            rank, file = divmod(to_index, 8)
            x_center = (file * self.square_size) + self.square_size / 2
            y_center = (rank * self.square_size) + self.square_size / 2
            x1, y1 = x_center - radius, y_center - radius
            x2, y2 = x_center + radius, y_center + radius
            self.canvas.create_oval(x1, y1, x2, y2, fill='gray', outline="", tags="legal_move_highlight")


    def clear_highlights(self):
        self.canvas.delete("highlight")
        self.canvas.delete("legal_move_highlight")


    def update_status_label(self):
        turn_text = "White to move" if self.is_white_turn else ""
        self.status_label.config(text=turn_text)

    def format_move_algebraic(self, move_tuple):
        from_sq = u.index_1d_to_square(move_tuple[0])
        to_sq = u.index_1d_to_square(move_tuple[1])
        move_info = move_tuple[2] if len(move_tuple) > 2 else None

        if move_info == 'castle_k': return "O-O"
        elif move_info == 'castle_q': return "O-O-O"
        elif move_info == 'ep': return f"{from_sq}x{to_sq} e.p."
        elif move_info in ('q', 'r', 'n', 'b', 'Q', 'R', 'N', 'B'): return f"{from_sq}-{to_sq}={move_info.upper()}"
        else: return f"{from_sq}-{to_sq}"

    def update_history_display(self):
        self.history_text.config(state='normal')
        self.history_text.delete('1.0', tk.END)

        full_move_number = 1
        for i, move_tuple in enumerate(self.move_history):
            move_str = self.format_move_algebraic(move_tuple)
            if i % 2 == 0:
                if i > 0: self.history_text.insert(tk.END, "\n")
                self.history_text.insert(tk.END, f"{full_move_number}. {move_str}")
            else: 
                self.history_text.insert(tk.END, f"  {move_str}") 
                full_move_number += 1

        self.history_text.see(tk.END)
        self.history_text.config(state='disabled')


    def on_square_click(self, event):
        if not self.is_white_turn:
            print("Ignoring click - Not player's turn.")
            return

        file = int(event.x // self.square_size)
        rank = int(event.y // self.square_size)
        if not (0 <= file <= 7 and 0 <= rank <= 7): return
        index_1d = rank * 8 + file
        clicked_piece_value = self.board_array[index_1d]
        square_notation = u.index_1d_to_square(index_1d)

        print(f"Clicked on {square_notation} (Index: {index_1d})")
        self.error_message_label.config(text="")

        if self.from_square_index is None:

            if clicked_piece_value > 0:
                self.from_square_index = index_1d
                print(f"  Selected FROM: {square_notation} (Value: {clicked_piece_value})")
                self.clear_highlights()
                self.highlight_square(index_1d, "blue")
                try:
                    all_legal_moves = get_legal_moves(self.board_array, True, self.castling_rights, self.en_passant_target)
                    self.possible_moves_from_selected = [m for m in all_legal_moves if m[0] == self.from_square_index]
                    self.highlight_legal_moves(self.possible_moves_from_selected)
                    if not self.possible_moves_from_selected:
                         print(f"  No legal moves for piece at {square_notation}")
                         self.error_message_label.config(text="No legal moves")
                         self.clear_highlights(); self.from_square_index = None
                except Exception as e:
                    print(f"Error getting legal moves: {e}")
                    self.error_message_label.config(text=f"Err checking moves")
                    self.clear_highlights(); self.from_square_index = None
            else:
                self.clear_highlights(); self.from_square_index = None
        else:

            to_square_index = index_1d
            print(f"  Selected TO: {u.index_1d_to_square(to_square_index)}")
            complete_move_tuple = None
            for move in self.possible_moves_from_selected:
                if move[1] == to_square_index: complete_move_tuple = move; break
            self.clear_highlights()

            if complete_move_tuple:
                print(f"  Attempting legal move: {complete_move_tuple}")

                if abs(self.board_array[complete_move_tuple[0]]) == 1 and (to_square_index // 8) == 0 :
                    if len(complete_move_tuple) < 3 or complete_move_tuple[2] not in ('q','r','n','b'):
                         print("  (Promotion detected: defaulting to Queen)")
                         complete_move_tuple = (complete_move_tuple[0], complete_move_tuple[1], 'q')
                    elif len(complete_move_tuple) > 2: print(f"  (Promotion move: {complete_move_tuple[2]})")
                self.handle_user_turn(complete_move_tuple)

            elif clicked_piece_value > 0 and index_1d != self.from_square_index:

                self.from_square_index = index_1d
                print(f"  Changed selection TO: {square_notation} (Value: {clicked_piece_value})")
                self.highlight_square(index_1d, "blue")
                try:
                    all_legal_moves = get_legal_moves(self.board_array, True, self.castling_rights, self.en_passant_target)
                    self.possible_moves_from_selected = [m for m in all_legal_moves if m[0] == self.from_square_index]
                    self.highlight_legal_moves(self.possible_moves_from_selected)
                    if not self.possible_moves_from_selected:
                         print(f"  No legal moves for piece at {square_notation}")
                         self.error_message_label.config(text="No legal moves")
                         self.clear_highlights(); self.from_square_index = None
                except Exception as e:
                    print(f"Error getting legal moves: {e}")
                    self.error_message_label.config(text=f"Err checking moves")
                    self.clear_highlights(); self.from_square_index = None
                return
            else:
                print("  Invalid destination or deselecting.")

            self.from_square_index = None; self.possible_moves_from_selected = []


    def handle_user_turn(self, move_tuple):
        """Makes the user's move, updates state, checks game end, and triggers engine."""
        if not self.is_white_turn: return

        print(f"Making user move: {move_tuple}")
        try:
            _ = make_move(self.board_array, move_tuple, self.castling_rights, self.en_passant_target)


            self.move_history.append(move_tuple)
            self.update_history_display()

            self.castling_rights = chess_engine.castling_rights
            self.en_passant_target = chess_engine.en_passant_target
            self.is_white_turn = (chess_engine.side_to_move == 'w')
            print(f"  State after user move: CR='{self.castling_rights}', EP={self.en_passant_target}, Turn={'W' if self.is_white_turn else 'B'}")
            
            self.update_board_pieces()
            self.update_status_label()

            is_game_over = self.check_game_over(for_engine_turn=True)
            if not is_game_over:
                print("Scheduling engine move...")
                self.after(100, lambda: self.trigger_engine_move())
            else:
                print("Game over detected after player move.")

        except Exception as e:
            print(f"Error during user move execution: {e}")
            import traceback; traceback.print_exc()
            self.error_message_label.config(text=f"Error making move: {e}")


    def trigger_engine_move(self):
        print("\n--- Debug: Entering trigger_engine_move ---")
        if self.is_white_turn: return

        print(f"Debug: Engine (Black) thinking... Current State:")
        print(f"  Turn: B, CR='{self.castling_rights}', EP={self.en_passant_target}")
        self.status_label.config(text="Engine thinking...")
        self.update_idletasks()

        try:
            search_depth = 4
            print(f"Debug: Calling find_best_move (depth={search_depth}, is_maximizing=False)")
            engine_best_move, engine_eval = find_best_move(
                self.board_array, depth=search_depth, is_maximizing_player=False,
                current_castling_rights=self.castling_rights,
                current_en_passant_target=self.en_passant_target
            )
            print(f"Debug: find_best_move returned: move={engine_best_move}, eval={engine_eval}")

            if engine_best_move:
                engine_move_str_formatted = self.format_move_algebraic(engine_best_move)
                self.engine_move_display.config(text=f"Engine's Last Move: {engine_move_str_formatted}")

                _ = make_move(self.board_array, engine_best_move, self.castling_rights, self.en_passant_target)

                self.move_history.append(engine_best_move)
                self.update_history_display()

                self.castling_rights = chess_engine.castling_rights
                self.en_passant_target = chess_engine.en_passant_target
                self.is_white_turn = (chess_engine.side_to_move == 'w')
                print(f"Debug: State AFTER engine move: CR='{self.castling_rights}', EP={self.en_passant_target}, Turn=W")

                self.update_board_pieces()
                self.update_status_label()

                self.check_game_over(for_engine_turn=False)
            else:
                print("Debug: Engine returned no move. Game Over.")
                self.check_game_over(for_engine_turn=True)

        except Exception as e:
            print(f"\n--- ERROR during engine move logic ---")
            import traceback; traceback.print_exc()
            self.error_message_label.config(text=f"Engine Error: {e}")
            self.status_label.config(text="Engine Error!")


    def check_game_over(self, for_engine_turn):
        """Checks if the player whose turn it is has legal moves, updates status if over."""
        player_is_white = not for_engine_turn
        current_player_legal_moves = get_legal_moves(
            self.board_array, player_is_white, self.castling_rights, self.en_passant_target
        )

        if not current_player_legal_moves:
            try:
                king_in_check = is_king_in_check(self.board_array, player_is_white)
                if king_in_check:
                    winner = "Black" if player_is_white else "White"
                    print(f"Checkmate! {winner} wins.")
                    self.status_label.config(text=f"Checkmate! {winner} wins.")
                else:
                    print("Stalemate! Draw.")
                    self.status_label.config(text="Stalemate! Draw.")
                self.engine_move_display.config(text="Game Over")
                self.canvas.unbind("<Button-1>")
                return True
            except Exception as check_err:
                 print(f"Debug: Error during is_king_in_check: {check_err}")
                 self.status_label.config(text="Error checking game end")
                 return False
        return False




if __name__ == "__main__":
    gui = ChessGUI()
    gui.mainloop()