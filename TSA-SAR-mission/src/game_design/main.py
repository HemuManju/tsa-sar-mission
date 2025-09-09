# main.py
import pyglet, argparse
from game import Game
from net import NetLink


def run_sar_mission_game():
    game = Game()
    pyglet.app.run()

if __name__ == "__main__":
    run_sar_mission_game()






def run():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bind", default="0.0.0.0:8765")  # WebSocket for browser viewers
    ap.add_argument("--view", choices=["local","global"], default=None)
    args = ap.parse_args()

    game = Game()
    game.net = NetLink()

    if args.view:
        game.view_mode = args.view  # e.g., local on host

    # Start WS server for browser clients
    host, port = args.bind.split(":"); port = int(port)
    game.net.start_host(game, bind_host=host, port=port)

    # Stream lightweight updates ~10/s
    pyglet.clock.schedule_interval(lambda dt: game.net.broadcast_update(game), 0.1)

    pyglet.app.run()

if __name__ == "__main__":
    run()