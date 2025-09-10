# host_server.py
import socket, threading, json, pyglet

# IMPORTANT: avoid clashing with a pip package named "game"
# If your file is game.py in the same folder, this is fine.
# Otherwise consider renaming to sar_game.py and importing from there.
from game import Game
from update import tick as orig_tick

HOST = "0.0.0.0"   # listen on all interfaces
PORT = 8765
clients = []       # connected client sockets

def client_handler(conn, addr):
    print("Client connected:", addr)
    clients.append(conn)
    try:
        while True:
            # We don't receive anything yet; just keep the connection open
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
    """Send current game state to all clients as JSON."""
    # IMPORTANT: JSON can't have tuple keys; encode victims as list of [ [x,y], kind ]
    victims_serializable = [ [list(pos), kind] for pos, kind in game.victims.items() ]
    state = {
        "player": list(game.player),  # ensure JSON-friendly
        "victims": victims_serializable,
        "carried": list(game.carried),
    }
    msg = (json.dumps(state) + "\n").encode("utf-8")
    for c in clients[:]:
        try:
            c.sendall(msg)
        except Exception:
            try:
                clients.remove(c)
            except ValueError:
                pass

# ---- Monkey-patch tick ----
def patched_tick(game, dt):
    orig_tick(game, dt)   # run the normal update
    send_state(game)      # broadcast state every frame/update

import update
update.tick = patched_tick

if __name__ == "__main__":
    threading.Thread(target=start_server, daemon=True).start()
    game = Game()        # make sure this triggers update.tick internally
    pyglet.app.run()
