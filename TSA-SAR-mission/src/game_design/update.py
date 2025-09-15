# update.py
from config import CELL_SIZE
from chatui import append_line


def _format_rescue_text(game):
    """HUD-friendly rescue text: supports multiple or single rescue points."""
    if hasattr(game, "rescue_positions") and game.rescue_positions:
        return " | ".join(f"{x},{y}" for (x, y) in game.rescue_positions[:3])
    if getattr(game, "rescue_pos", None):
        x, y = game.rescue_pos
        return f"{x},{y}"
    return "—"


def _format_carried_text(game):
    """HUD-friendly carried text for new (list) or legacy (single) models."""
    if hasattr(game, "carried") and isinstance(game.carried, list):
        return f"{len(game.carried)}/3"
    return f"{game.carried}" if getattr(game, "carried", None) else "—"


def _pickup_if_present(game, pos):
    """
    If there's a victim on the current tile:
      - Only pick up if capacity allows (len(carried) < 3).
      - Do NOT remove from the map unless actually picked up.
      - Stay silent when full (no system message).
    """
    if pos not in game.victims:
        return

    # New carry-stack model
    if hasattr(game, "add_carried") and isinstance(game.carried, list):
        if len(game.carried) >= 3:
            # capacity full: do nothing (keep victim on the ground, no message)
            return

        # capacity available -> remove ground victim and add to carried
        new_kind = game.victims[pos]
        if pos in game.victim_shapes:
            game.victim_shapes[pos][0].delete()
            del game.victim_shapes[pos]
        del game.victims[pos]
        game.add_carried(new_kind)
        # Optional: uncomment if you want a pickup toast
        # append_line(game.chat, f"[SYSTEM] Picked up a victim. Carrying {len(game.carried)}/3.")

    else:
        # Legacy single-carry fallback
        new_kind = game.victims[pos]
        if pos in game.victim_shapes:
            game.victim_shapes[pos][0].delete()
            del game.victim_shapes[pos]
        del game.victims[pos]
        game.set_carried(new_kind)
        # Optional: toast
        # append_line(game.chat, f"[SYSTEM] Picked up a victim: {new_kind}.")


def _handle_rescue(game, pos):
    """
    Drop logic when on a rescue point:
      - New model: drop all carried victims at ANY rescue point.
      - End mission only when no ground victims remain AND nothing is carried.
      - Legacy model: end mission on the single rescue tile.
    """
    # New multi-rescue system
    if hasattr(game, "rescue_positions") and game.rescue_positions:
        if pos in game.rescue_positions:
            if hasattr(game, "carried") and isinstance(game.carried, list) and game.carried:
                saved_n = len(game.carried)
                game.drop_all_carried()
                # Optional: toast; comment out if you want silence here too
                append_line(game.chat, f"[SYSTEM] Dropped {saved_n} victim(s) at rescue point.")
            # Mission auto-complete when everything is handled
            if not game.victims and not getattr(game, "carried", []):
                if not game.game_over:
                    game.game_over = True
                    game.hud["status"].text = " Mission complete! All victims handled."
                    append_line(game.chat, "[SYSTEM] Mission complete! All victims handled.")
            return

    # Legacy single-rescue behavior (kept for compatibility)
    if getattr(game, "rescue_pos", None) and pos == game.rescue_pos and not game.rescue_reached:
        game.rescue_reached = True
        game.game_over = True
        game.hud["status"].text = " Mission complete!"
        append_line(game.chat, "[SYSTEM] Rescue point reached! Mission complete.")

def _update_hud(game):
    """Refresh HUD labels for time, zoom, victims, player, carried."""
    reds = sum(1 for k in game.victims.values() if k == "red")
    purp = sum(1 for k in game.victims.values() if k == "purple")
    yell = sum(1 for k in game.victims.values() if k == "yellow")

    L = game.hud["labels"]
    L["time"].text = f"Time: {game.time_remaining:>3d}s"
    # L["zoom"].text = f"Zoom: {game.zoom:.2f}×"   
    L["victims"].text = f"Victims left (R/P/Y): {reds}/{purp}/{yell}"
    L["player"].text = f"Player: {game.player[0]},{game.player[1]}"
    # L["rescue"].text = f"Rescue: {rtxt}"         
    L["carried"].text = f"Carrying: {_format_carried_text(game)}"


def tick(game, dt):
    """Per-frame update (60 Hz). Handles pickups, rescue detection, HUD, and sprites."""
    if game.state != "playing":
        return

    pos = tuple(game.player)

    # 1) Try pickup on current tile (capacity-aware & silent when full)
    _pickup_if_present(game, pos)

    # 2) Rescue handling (drop at any rescue point, optional mission complete)
    _handle_rescue(game, pos)

    # 3) Time up -> game over
    if game.time_remaining <= 0 and not game.game_over:
        game.game_over = True
        game.hud["status"].text = " Time up! Mission ended."
        append_line(game.chat, "[SYSTEM] Time up! Mission ended.")
        return

    # 4) Sync visuals
    game.player_shape.x = game.player[0] * CELL_SIZE
    game.player_shape.y = game.player[1] * CELL_SIZE
    game.player_shape.width = CELL_SIZE
    game.player_shape.height = CELL_SIZE
    game.update_carried_position()

    # 5) HUD update
    _update_hud(game)


def second(game, dt):
    """Once per second: drain the timer (supports optional difficulty-based drain)."""
    if game.state == "playing" and not game.game_over:
        drain = getattr(game, "time_drain", 1)  # default 1s/sec; can be 2 on Hard, etc.
        game.time_remaining -= drain





"..........collection...."

def update():
    return {
        "_format_rescue_text": _format_rescue_text,
        "_format_carried_text": _format_carried_text,
        "_pickup_if_present": _pickup_if_present,
        "_handle_rescue": _handle_rescue,
        "_update_hud": _update_hud,
        "tick": tick,
        "second": second
    }
