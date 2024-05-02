import pygame
import threading
import time
from network import Network
import win32gui, win32con

# Initialize Pygame
pygame.init()

the_program_to_hide = win32gui.GetForegroundWindow()
win32gui.ShowWindow(the_program_to_hide , win32con.SW_HIDE)

# Constants for the game
BOARD_SIZE = 8
SQUARE_SIZE = 100
WINDOW_SIZE = BOARD_SIZE * SQUARE_SIZE
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
n = Network()

def show_waiting_message(screen, message):
    screen.fill(BLACK)  # Czyści ekran
    font = pygame.font.Font(None, 36)  # Ustawienie czcionki
    text = font.render(message, True, WHITE)  # Tworzy obiekt tekstu
    text_rect = text.get_rect(center=(WINDOW_SIZE / 2, WINDOW_SIZE / 2))
    screen.blit(text, text_rect)  # Umieszcza tekst na ekranie
    pygame.display.flip()  # Aktualizuje wyświetlane treści

# Set up the display
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("red")

# Board representation: 0 for empty, 1 for player 1, 2 for player 2, 3 for player 1 king, 4 for player 2 king
board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]

def draw_board():
    screen.fill(BLACK)
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            color = WHITE if (row + col) % 2 == 0 else BLACK
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
            piece = board[row][col]
            if piece != 0:
                piece_color = BLUE if piece == 1 else RED
                pygame.draw.circle(screen, piece_color, (col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2), SQUARE_SIZE // 2 - 10)
    pygame.display.flip()

def make_move(start_pos, end_pos):
    start_row, start_col = start_pos
    end_row, end_col = end_pos
    move_data = f"{start_row},{start_col},{end_row},{end_col}"
    response = n.send(move_data)
    if "Invalid" not in response:
        update_board_from_network(response)
    else:
        print("Invalid move, try again.")

def update_board_from_network(response):
    """ Update the board based on the server's response. """
    if response and "Invalid" not in response:
        try:
            rows = response.split(';')
            for i, row in enumerate(rows):
                cells = row.split(',')
                for j, cell in enumerate(cells):
                    board[i][j] = int(cell)
            draw_board()
            pygame.display.flip()
        except Exception as e:
            print(f"Failed to update board from network: {e}")
    else:
        print(f"Server response: {response}")

def poll_server_for_updates():
    """ Continuously request the current board state from the server. """
    while True:
        response = n.send("get_board_state")
        if response:
            update_board_from_network(response)
        else:
            print("Error retrieving board state from server.")
        time.sleep(0.16)  # Poll every second 60 fps 

def red_start():
    print("Initial board setup complete.")
    initial_state = n.send("get_board_state")
    if initial_state:
        update_board_from_network(initial_state)
    else:
        print("Failed to receive initial board state.")

    show_waiting_message(screen, "Oczekiwanie na drugiego gracza...")

    # Oczekiwanie na potwierdzenie dołączenia drugiego gracza
    while True:
        response = n.send("check_player")
        if response == "start":
            break
        time.sleep(1)  # Odczekaj sekundę przed kolejnym zapytaniem

    # Kontynuacja z normalną pętlą gry
    clock = pygame.time.Clock()
    running = True
    selected_piece = None
    current_player = 1
    threading.Thread(target=poll_server_for_updates, daemon=True).start()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                col = pos[0] // SQUARE_SIZE
                row = pos[1] // SQUARE_SIZE
                if selected_piece and (row, col) != selected_piece:
                    start_pos = selected_piece
                    end_pos = (row, col)
                    move_data = f"{start_pos[0]},{start_pos[1]},{end_pos[0]},{end_pos[1]}"
                    response = n.send(move_data)
                    update_board_from_network(response)
                    selected_piece = None
                    current_player = 3 - current_player  # Switch player
                elif board[row][col] in [2, 4]:  # Select only red pieces
                    selected_piece = (row, col)

        draw_board()
       
        clock.tick(60)

    pygame.quit()

red_start()