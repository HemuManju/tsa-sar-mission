# update.py
from config import CELL_SIZE
from chatui import append_line

def tick(game, dt):
    """Per-frame update (60 Hz). Handles pickups, rescue detection, HUD, and sprites."""
    if game.state != "playing":
        return

    pos = tuple(game.player)

    # Pick up victim (replace any currently carried) 
    if pos in game.victims:
        new_kind = game.victims[pos]
        # remove ground victim sprite
        if pos in game.victim_shapes:
            game.victim_shapes[pos][0].delete()
            del game.victim_shapes[pos]
        # remove from dict and set carried
        del game.victims[pos]
        game.set_carried(new_kind)

    #  Rescue detection: end mission immediately on reaching triangle)
    if game.rescue_pos and pos == game.rescue_pos and not game.rescue_reached:
        game.rescue_reached = True
        game.game_over = True                          # ✅ stop the game
        game.hud["status"].text = " Mission complete!"
        append_line(game.chat, "[SYSTEM] Rescue point reached! 🎯 Mission complete.")
        return  # stop further updates this frame

    # --- HUD stats ---
    reds = sum(1 for k in game.victims.values() if k == "red")
    purp = sum(1 for k in game.victims.values() if k == "purple")
    yell = sum(1 for k in game.victims.values() if k == "yellow")
    rtxt = f"{game.rescue_pos[0]},{game.rescue_pos[1]}" if game.rescue_pos else "—"

    L = game.hud["labels"]
    L["time"].text = f"Time: {game.time_remaining:>3d}s"
    L["zoom"].text = f"Zoom: {game.zoom:.2f}×"
    L["victims"].text = f"Victims left (R/P/Y): {reds}/{purp}/{yell}"
    L["player"].text = f"Player: {game.player[0]},{game.player[1]}"
    L["rescue"].text = f"Rescue: {rtxt}"
    L["carried"].text = f"Carrying: {game.carried if game.carried else '—'}"

    # --- Time up -> game over ---
    if game.time_remaining <= 0 and not game.game_over:
        game.game_over = True
        game.hud["status"].text = "⏱️ Time up! Mission ended."
        append_line(game.chat, "[SYSTEM] Time up! Mission ended.")
        return

    # --- Keep player & carried visuals in sync with grid position ---
    game.player_shape.x = game.player[0] * CELL_SIZE
    game.player_shape.y = game.player[1] * CELL_SIZE
    game.player_shape.width = CELL_SIZE
    game.player_shape.height = CELL_SIZE
    game.update_carried_position()

def second(game, dt):
    """Once per second: drain the timer (supports optional difficulty-based drain)."""
    if game.state == "playing" and not game.game_over:
        drain = getattr(game, "time_drain", 1)  # default 1s/sec; can be 2 on Hard, etc.
        game.time_remaining -= drain
