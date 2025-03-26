import tkinter as tk
from PIL import Image, ImageTk
import utils as u
from chess_engine import create_test_board_minimax_start, find_best_move, make_move, get_legal_moves

class ChessGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Basic Chess Engine GUI")
        self.geometry("600x600")

        self.board_array = create_test_board_minimax_start()
        self.is_white_turn = True

        self.canvas = tk.Canvas(self, width=400, height=400, borderwidth=2, relief="solid") 
        self.canvas.pack(pady=20)

        self.canvas.bind("<Button-1>", self.on_square_click)
        self.from_square_index = None

        self.engine_move_label = tk.Label(self, text="Engine's Move:")
        self.engine_move_label.pack()
        self.engine_move_display = tk.Label(self, text="") 
        self.engine_move_display.pack()

        self.error_message_label = tk.Label(self, text="", fg="red")
        self.error_message_label.pack()

        self.draw_board()
        self.load_piece_images() 
        self.update_board_pieces()

    def load_piece_images(self):
        """Loads the images of the chess pieces."""
        self.piece_images = {}
        piece_filenames = {
            'P': 'wp.png', 'N': 'wN.png', 'B': 'wB.png', 'R': 'wR.png', 'Q': 'wQ.png', 'K': 'wK.png',
            'p': 'p.png', 'n': 'n.png', 'b': 'b.png', 'r': 'r.png', 'q': 'q.png', 'k': 'k.png'
        }
        for piece, filename in piece_filenames.items():
            image = Image.open(f"images/{filename}") 
            self.piece_images[piece] = ImageTk.PhotoImage(image)

    def on_square_click(self, event):
        file = int(event.x // (400 / 8)) 
        rank = int(event.y // (400 / 8))
        index_1d = rank * 8 + file

        square_notation = u.index_1d_to_square(index_1d) 

        print(f"Clicked on square: {square_notation} (Index: {index_1d})") 

        if self.from_square_index is None: 
            self.from_square_index = index_1d
            print(f"  Selected FROM square: {square_notation} (Index: {index_1d})")
            self.highlight_square(index_1d, "blue") 
        else:
            to_square_index = index_1d
            print(f"  Selected TO square: {u.index_1d_to_square(to_square_index)} (Index: {to_square_index})") 

            move = (self.from_square_index, to_square_index)
            self.handle_move(move)

            self.clear_square_highlight(self.from_square_index) 
            self.from_square_index = None 

    def handle_move(self, move):
        from_index, to_index = move

        self.error_message_label.config(text="")

        legal_moves = get_legal_moves(self.board_array, self.is_white_turn)

        is_move_legal = False
        move_to_check = (from_index, to_index)
        for legal_move in legal_moves:
            if legal_move[:2] == move_to_check[:2]:
                is_move_legal = True
                break

        if is_move_legal:
            try:

                captured_piece = make_move(self.board_array, move)
                self.update_board_pieces()
                print(f"White move done. is_white_turn BEFORE engine check: {self.is_white_turn}")  

                self.is_white_turn = False  

                
                if not self.is_white_turn:
                    print(f"--- Engine (Black) is thinking... is_white_turn BEFORE engine search: {self.is_white_turn} ---") 
                    engine_move = find_best_move(self.board_array, depth=3, is_maximizing_player=False)
                    if engine_move:
                        make_move(self.board_array, engine_move)
                        self.update_board_pieces()
                        engine_move_algebraic = u.index_1d_to_square(engine_move[0]) + "-" + u.index_1d_to_square(engine_move[1])
                        self.engine_move_display.config(text=engine_move_algebraic)
                        self.is_white_turn = True  
                        print(f"Engine (Black) move done: {engine_move_algebraic}. is_white_turn AFTER engine move: {self.is_white_turn}") # DEBUG
                    else:
                        self.engine_move_display.config(text="No engine move found (Checkmate/Stalemate?)")
                        print("Engine (Black) - No legal move found!")

            except Exception as e:
                self.error_message_label.config(text=f"Error making move: {e}")

        else:
            self.error_message_label.config(text="Illegal move!")
            print(f"Illegal move attempted: {u.index_1d_to_square(from_index)}-{u.index_1d_to_square(to_index)}")


    def highlight_square(self, index_1d, color):
        board_size = 400
        square_size = board_size / 8
        rank = index_1d // 8
        file = index_1d % 8
        x1 = file * square_size
        y1 = rank * square_size
        x2 = x1 + square_size
        y2 = y1 + square_size
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=3, tags="highlight") 


    def clear_square_highlight(self, index_1d):

        self.canvas.delete("highlight")

    def draw_board(self):

        board_size = 400 
        square_size = board_size / 8

        for rank in range(8):
            for file in range(8):
                x1 = file * square_size
                y1 = rank * square_size
                x2 = x1 + square_size
                y2 = y1 + square_size
                color = "white" if (rank + file) % 2 == 0 else "light gray" 
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color)

    def update_board_pieces(self):
        self.canvas.delete("piece") 

        board_size = 400
        square_size = board_size / 8
        piece_symbols = { 
            0: '', 1: 'P', -1: 'p', 2: 'N', -2: 'n', 3: 'B', -3: 'b', 4: 'R', -4: 'r', 5: 'Q', -5: 'q', 6: 'K', -6: 'k'
        }

        for index in range(64):
            piece_value = self.board_array[index]
            piece_symbol = piece_symbols[piece_value]
            if piece_symbol: 
                rank = index // 8
                file = index % 8
                x_center = (file * square_size) + square_size / 2
                y_center = (rank * square_size) + square_size / 2
                self.canvas.create_image(x_center, y_center, image=self.piece_images[piece_symbol], tags="piece") # Tag for easy deletion


    def handle_user_move(self):
        user_move_notation = self.move_entry.get()
        self.move_entry.delete(0, tk.END)

        self.error_message_label.config(text="") 

        try:
            from_sq_notation = user_move_notation[:2]
            to_sq_notation = user_move_notation[2:]
            from_index = u.square_to_index_1d(from_sq_notation)
            to_index = u.square_to_index_1d(to_sq_notation)
            move = (from_index, to_index)

            make_move(self.board_array, move)
            self.update_board_pieces()
            self.is_white_turn = not self.is_white_turn

            if not self.is_white_turn: 
                engine_move = find_best_move(self.board_array, depth=3)
                if engine_move:
                    make_move(self.board_array, engine_move)
                    self.update_board_pieces()
                    engine_move_algebraic = u.index_1d_to_square(engine_move[0]) + "-" + u.index_1d_to_square(engine_move[1])
                    self.engine_move_display.config(text=engine_move_algebraic)
                    self.is_white_turn = not self.is_white_turn
                else:
                    self.engine_move_display.config(text="No engine move found (Checkmate/Stalemate?)")

        except ValueError:
            self.error_message_label.config(text="Invalid move notation (e.g., e2e4)")

if __name__ == "__main__":
    gui = ChessGUI()
    gui.mainloop()