import socket

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = '127.0.0.1'
        self.port = 2137
        self.addr = (self.server, self.port)
         # Ustawienie timeoutu na 5 sekund
        self.pos = self.connect()
    
    def getPos(self):
        return self.pos

    def get_player_number(self):
        # Zakładając, że serwer najpierw wysyła numer gracza
        return int(self.client.recv(2048).decode())

    def send(self, data):
        try:
            self.client.send(str.encode(data))
            return self.client.recv(2048).decode()
        except Exception as e:
            print(e)
            return None

    def connect(self):
        try:
            self.client.connect(self.addr)
            return self.client.recv(2048).decode()
        except Exception as e:
            print(f"Connection error: {e}")
            return None

    def send(self, data):
        try:
            data_str = str(data)
            self.client.send(data_str.encode())
            # Timeout dla odbioru danych może być także tutaj zarządzany.
            self.client.settimeout(2)  # Oczekuj na odpowiedź max 2 sekundy
            return self.client.recv(2048).decode()
        except socket.timeout:
            print("Timeout while waiting for server response.")
            return None
        except socket.error as e:
            print(f"Socket error: {e}")
            return None