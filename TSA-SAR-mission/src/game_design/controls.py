# controls.py
from pyglet.window import key
from chatui import append_line
from config import MIN_ZOOM, MAX_ZOOM, ZOOM_STEP, PLAY_W_PX, SIDEBAR_W

def move(game, dx, dy):
    if game.state != "playing" or game.game_over: return
    nx, ny = game.player[0] + dx, game.player[1] + dy
    if (0 <= nx < game.PLAY_W and 0 <= ny < game.PLAY_H
        and (nx, ny) not in game.walls):
        game.player[0], game.player[1] = nx, ny

def key_press(game, symbol, modifiers):
    if game.state == "start":
        if symbol == key.LEFT:
            game.start_diff_idx = (game.start_diff_idx - 1) % len(game.start_diffs)
            game.refresh_start_labels(); return
        if symbol == key.RIGHT:
            game.start_diff_idx = (game.start_diff_idx + 1) % len(game.start_diffs)
            game.refresh_start_labels(); return
        if symbol in (key._1, key.NUM_1):
            game.start_diff_idx = 0; game.refresh_start_labels(); return
        if symbol in (key._2, key.NUM_2):
            game.start_diff_idx = 1; game.refresh_start_labels(); return
        if symbol in (key._3, key.NUM_3):
            game.start_diff_idx = 2; game.refresh_start_labels(); return
        if symbol in (key.UP, key.DOWN, key.L, key.G):
            game.start_view = "Global" if game.start_view == "Local" else "Local"
            if symbol == key.L: game.start_view = "Local"
            if symbol == key.G: game.start_view = "Global"
            game.refresh_start_labels(); return
        if symbol in (key.ENTER, key.RETURN):
            game.apply_start_and_begin(); return
        if symbol in (key.EQUAL, key.NUM_ADD):
            game.zoom = min(MAX_ZOOM, game.zoom + ZOOM_STEP); return
        if symbol in (key.MINUS, key.NUM_SUBTRACT):
            game.zoom = max(MIN_ZOOM, game.zoom - ZOOM_STEP); return
        return

    if symbol in (key.EQUAL, key.NUM_ADD):
        game.zoom = min(MAX_ZOOM, game.zoom + ZOOM_STEP); return
    if symbol in (key.MINUS, key.NUM_SUBTRACT):
        game.zoom = max(MIN_ZOOM, game.zoom - ZOOM_STEP); return
    if symbol == key.G:
        game.view_mode = "global" if game.view_mode == "local" else "local"
        game.hud["labels"]["view"].text = f"View: {game.view_mode.capitalize()}"; return

    if symbol in (key.LEFT, key.A): move(game, -1, 0); return
    if symbol in (key.RIGHT, key.D): move(game,  1, 0); return
    if symbol in (key.UP, key.W): move(game, 0, 1); return
    if symbol in (key.DOWN, key.S): move(game, 0,-1); return

    if symbol in (key.ENTER, key.RETURN) and game.chat["focus"]:
        msg = game.chat["input_doc"].text.strip()
        if msg:
            append_line(game.chat, f"[YOU] {msg}")
        game.chat["input_doc"].text = ""
        if game.chat["caret"]: game.chat["caret"].position = 0

    if symbol == key.ESCAPE:
        game.chat["focus"] = False
        if game.chat["caret"]: game.chat["caret"].visible = False

def mouse_press(game, x, y, button, modifiers):
    from pyglet.window import mouse
    if button == mouse.LEFT:
        x1 = PLAY_W_PX+15; x2 = x1 + SIDEBAR_W-30
        y1 = 35; y2 = 35+34
        if x1 <= x <= x2 and y1 <= y <= y2:
            game.chat["focus"] = True
            if game.chat["caret"]:
                game.chat["caret"].visible = True
                game.chat["caret"].on_mouse_press(x, y, button, modifiers)
        else:
            game.chat["focus"] = False
            if game.chat["caret"]: game.chat["caret"].visible = False




"...........collection......"

def controllers():
    return {
        "move": move,
        "key_press": key_press,
        "mouse_press": mouse_press
    }
