import socket, threading, json, pyglet
from game import Game
from update import tick as orig_tick

HOST = "127.0.0.1"   # listen on all network interfaces
PORT = 8765
clients = []       # list of connected clients (sockets)

# ---- Networking ----
def client_handler(conn, addr):
    print("Client connected:", addr)
    clients.append(conn)
    try:
        while True:
            # We don’t need to receive messages from the client yet
            data = conn.recv(1024)
            if not data:
                break
    except Exception as e:
        print("Client error:", e)
    finally:
        if conn in clients:
            clients.remove(conn)
        conn.close()
        print("Client disconnected:", addr)

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server listening on {HOST}:{PORT}")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=client_handler, args=(conn, addr), daemon=True).start()

def send_state(game):
    """Send current game state to all clients as JSON"""
    state = {
        "player": game.player,
        "victims": list(game.victims.items()),
        "carried": game.carried,
    }
    msg = json.dumps(state).encode() + b"\n"
    for c in clients[:]:
        try:
            c.sendall(msg)
        except:
            clients.remove(c)

# ---- Monkey-patch tick ----
def patched_tick(game, dt):
    orig_tick(game, dt)   # normal update
    send_state(game)      # also broadcast state

import update
update.tick = patched_tick

# ---- Run Host Game ----
if __name__ == "__main__":
    threading.Thread(target=start_server, daemon=True).start()
    game = Game()
    pyglet.app.run()
