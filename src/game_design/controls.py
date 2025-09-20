from chatui import append_line
from config import MAX_ZOOM, MIN_ZOOM, PLAY_W_PX, SIDEBAR_W, ZOOM_STEP
from pyglet.window import key, mouse


def move(game, dx, dy):
    if game.state != "playing" or game.game_over:
        return
    nx, ny = game.player[0] + dx, game.player[1] + dy
    if 0 <= nx < game.PLAY_W and 0 <= ny < game.PLAY_H and (nx, ny) not in game.walls:
        game.player[0], game.player[1] = nx, ny


# Helper functions for each action
def handle_difficulty_selection(game, symbol):
    difficulty_map = {
        key._1: 0,
        key._2: 1,
        key._3: 2,
    }

    if symbol in difficulty_map:
        game.start_diff_idx = difficulty_map[symbol]
        game.refresh_start_labels()


def handle_view_toggle(game, symbol):
    if symbol == key.L or symbol == key.G:
        # Toggle between "Local" and "Global" view
        game.start_view = "Local" if game.start_view == "Global" else "Global"
        game.refresh_start_labels()


def handle_zoom(game, symbol):
    if symbol in (key.EQUAL, key.NUM_ADD):
        game.zoom = min(MAX_ZOOM, game.zoom + ZOOM_STEP)
    elif symbol in (key.MINUS, key.NUM_SUBTRACT):
        game.zoom = max(MIN_ZOOM, game.zoom - ZOOM_STEP)


def handle_movement(game, symbol):
    # Unified movement map for both arrow keys and WASD
    direction_map = {
        key.LEFT: (-1, 0),
        key.RIGHT: (1, 0),
        key.UP: (0, 1),
        key.DOWN: (0, -1),
    }

    if symbol in direction_map:
        move(game, *direction_map[symbol])


def handle_chat_input(game, symbol):
    if symbol in (key.ENTER, key.RETURN) and game.chat["focus"]:
        msg = game.chat["input_doc"].text.strip()
        if msg:
            append_line(game.chat, f"[YOU] {msg}")
        game.chat["input_doc"].text = ""
        if game.chat["caret"]:
            game.chat["caret"].position = 0


def handle_escape(game, symbol):
    if symbol == key.ESCAPE:
        game.chat["focus"] = False
        if game.chat["caret"]:
            game.chat["caret"].visible = False


# Main key press handler
def key_press(game, symbol, modifiers):
    if game.state == "start":
        handle_difficulty_selection(game, symbol)
        handle_view_toggle(game, symbol)
        handle_zoom(game, symbol)
        if symbol in (key.ENTER, key.RETURN):
            game.apply_start_and_begin()
        return  # Exit after handling start screen actions

    # Handle zoom and movement (shared logic between start and game states)
    handle_zoom(game, symbol)
    handle_movement(game, symbol)

    # Handle chat input if relevant
    handle_chat_input(game, symbol)

    # Handle escape
    handle_escape(game, symbol)


def mouse_press(game, x, y, button, modifiers):
    if button == mouse.LEFT:
        x1 = PLAY_W_PX + 15
        x2 = x1 + SIDEBAR_W - 30
        y1 = 35
        y2 = 35 + 34
        if x1 <= x <= x2 and y1 <= y <= y2:
            game.chat["focus"] = True
            if game.chat["caret"]:
                game.chat["caret"].visible = True
                game.chat["caret"].on_mouse_press(x, y, button, modifiers)
        else:
            game.chat["focus"] = False
            if game.chat["caret"]:
                game.chat["caret"].visible = False


def controllers():
    return {"move": move, "key_press": key_press, "mouse_press": mouse_press}
