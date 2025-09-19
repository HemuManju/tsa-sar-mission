HOST = "0.0.0.0"
PORT = 8765

import socket
import threading
import json

clients = []


def client_handler(conn, addr, game):
    print("Client connected:", addr)
    clients.append(conn)
    while True:
        # send game state as JSON
        state = {"player": game.player, "victims": list(game.victims.items())}
        conn.sendall(json.dumps(state).encode() + b"\n")


def start_server(game):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen()
    while True:
        conn, addr = s.accept()
        threading.Thread(target=client_handler, args=(conn, addr, game)).start()
