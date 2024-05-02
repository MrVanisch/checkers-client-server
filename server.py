import socket
from _thread import *

server = '127.0.0.1'
port = 2137

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Symulowany stan planszy, gdzie 0 oznacza puste pole
board = [[0 for _ in range(8)] for _ in range(8)]

def read_pos(data_str):
    # Rozdzielenie ciągu znaków na podstawie przecinka
    parts = data_str.split(',')
    # Konwersja na liczby całkowite
    x = int(parts[0])
    y = int(parts[1])
    # Zwrócenie krotki (tuple)
    return (x, y)


def make_pos(board):
    # Generowanie ciągu znaków przedstawiającego stan planszy
    return ';'.join(','.join(str(cell) for cell in row) for row in board)

try:
    s.bind((server, port))
except socket.error as e:
    print(e)

s.listen(2)
print("Waiting for players to join the game!")
connections = []



def thread_client(conn, player):
    global board, current_player
    conn.sendall(str.encode(make_pos(board)))
    while True:
        try:
            data = conn.recv(2048).decode()
            if not data:
                break
            if data == "check_player":
                if len(connections) == 2:
                    conn.sendall(str.encode("start"))
                else:
                    conn.sendall(str.encode("waiting"))
            elif data == "get_board_state":
                conn.sendall(str.encode(make_pos(board)))
            else:
                start_row, start_col, end_row, end_col = map(int, data.split(','))
                if current_player == player:
                    valid_move, captured = is_valid_move((start_row, start_col), (end_row, end_col), player)
                    if valid_move:
                        board[start_row][start_col] = 0
                        board[end_row][end_col] = player
                        if not captured:
                            current_player = 3 - current_player  # Change turn only if no piece was captured
                        broadcast_board_state()
                        winner = check_for_winner()
                        if winner:
                            for conn in connections:
                                conn.sendall(str.encode(f"Game over: Player {winner} wins!"))
                            break
                    else:
                        conn.sendall(str.encode("Invalid move"))
                else:
                    conn.sendall(str.encode("Not your turn"))
        except Exception as e:
            print(f"Error during communication: {e}")
            break
    conn.close()
    print("Disconnected")

def check_for_winner():
    player1_pieces = 0
    player2_pieces = 0
    for row in board:
        for cell in row:
            if cell == 1 or cell == 3:  # Zakładając, że 1 i 3 to pionki gracza 1
                player1_pieces += 1
            elif cell == 2 or cell == 4:  # Zakładając, że 2 i 4 to pionki gracza 2
                player2_pieces += 1
    
    if player1_pieces == 0:
        return 2  # Gracz 2 wygrywa
    elif player2_pieces == 0:
        return 1  # Gracz 1 wygrywa
    return 0  # Gra toczy się dalej

def is_valid_move(start_pos, end_pos, player):
    start_row, start_col = start_pos
    end_row, end_col = end_pos
    piece = board[start_row][start_col]
    if piece == 0 or (piece != player and piece != player + 2):
        return False, False  # Brak pionka na początku lub błędny pionek gracza, brak zbicia
    if board[end_row][end_col] != 0:
        return False, False  # Miejsce docelowe nie jest puste, brak zbicia
    # Sprawdzenie czy ruch jest po przekątnej
    row_diff = abs(end_row - start_row)
    col_diff = abs(end_col - start_col)
    if row_diff != col_diff:
        return False, False  # Ruch musi być po przekątnej, brak zbicia
    # Sprawdzenie czy to prosty ruch lub zbiórka
    if row_diff == 1:
        return True, False  # Prosty ruch, brak zbicia
    elif row_diff == 2:
        middle_row = (start_row + end_row) // 2
        middle_col = (start_col + end_col) // 2
        middle_piece = board[middle_row][middle_col]
        if middle_piece == 0 or middle_piece == piece or middle_piece == piece + 2:
            return False, False  # Brak pionka przeciwnika do zbicia, brak zbicia
        # Usunięcie zbitego pionka
        board[middle_row][middle_col] = 0
        return True, True  # Zbicie pionka


def broadcast_board_state():
    global board, connections
    for conn in connections:
        conn.sendall(str.encode(make_pos(board)))

def initialize_board():
    # Tworzenie pustej planszy
    board = [[0 for _ in range(8)] for _ in range(8)]

    # Ustawianie pionków dla gracza 1 (niebieskie, identyfikator 1)
    for row in range(3):
        for col in range((row % 2) == 0, 8, 2):  # Pionki na czarnych polach
            board[row][col] = 1

    # Ustawianie pionków dla gracza 2 (czerwone, identyfikator 2)
    for row in range(5, 8):
        for col in range((row % 2) == 0, 8, 2):
            board[row][col] = 2

    return board


def update_board_from_data(data):
    """Zaktualizuj stan planszy na podstawie danych od klienta."""
    rows = data.split(';')
    for i, row in enumerate(rows):
        cells = row.split(',')
        for j, cell in enumerate(cells):
            board[i][j] = int(cell)


current_player = 1
board = initialize_board()
board_state = make_pos(board)
print("Generated board state:")
print(board_state)

while True:
    conn, addr = s.accept()
    print("Connected to:", addr)
    connections.append(conn)
    start_new_thread(thread_client, (conn, current_player))
    current_player = 2 if current_player == 1 else 1


