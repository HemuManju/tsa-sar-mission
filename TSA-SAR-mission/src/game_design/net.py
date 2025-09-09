# net.py
import asyncio, json, threading
import websockets
from config import CELL_SIZE  # for geometry in snapshots

class NetLink:
    def __init__(self):
        self.role = "solo"
        self.clients = set()
        self.loop = None
        self.thread = None

    @staticmethod
    def snapshot_from_game(game):
        # Send geometry so the browser can size its canvas
        return {
            "type": "snapshot",
            "PLAY_W": game.PLAY_W, "PLAY_H": game.PLAY_H, "CELL_SIZE": CELL_SIZE,
            "walls": list(map(list, getattr(game, "walls", set()))),
            "victims": {f"{x},{y}": k for (x, y), k in getattr(game, "victims", {}).items()},
            "rescue_positions": [list(p) for p in getattr(game, "rescue_positions", [])],
            "player": list(getattr(game, "player", (0, 0))),
            "time_remaining": getattr(game, "time_remaining", 0),
        }

    @staticmethod
    def update_from_game(game):
        return {
            "type": "update",
            "player": list(game.player),
            "time_remaining": game.time_remaining,
            "victims": {f"{x},{y}": k for (x, y), k in game.victims.items()},
        }

    # ---------- host ----------
    def start_host(self, game, bind_host="0.0.0.0", port=8765):
        self.role = "host"

        async def handler(ws):
            self.clients.add(ws)
            try:
                await ws.send(json.dumps(self.snapshot_from_game(game)))
                async for _ in ws:  # ignore incoming client messages
                    pass
            finally:
                self.clients.discard(ws)

        async def run():
            # origins=None → allow browser connections from any origin
            async with websockets.serve(handler, bind_host, port, max_size=5_000_000, origins=None):
                await asyncio.Future()

        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(
            target=self.loop.run_until_complete, args=(run(),), daemon=True
        )
        self.thread.start()

    def broadcast_snapshot(self, game):
        if self.role != "host" or not self.clients: return
        msg = json.dumps(self.snapshot_from_game(game))
        asyncio.run_coroutine_threadsafe(self._broadcast(msg), self.loop)

    def broadcast_update(self, game):
        if self.role != "host" or not self.clients: return
        msg = json.dumps(self.update_from_game(game))
        asyncio.run_coroutine_threadsafe(self._broadcast(msg), self.loop)

    async def _broadcast(self, msg):
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.clients.discard(ws)
