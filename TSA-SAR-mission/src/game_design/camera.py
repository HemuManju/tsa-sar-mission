# camera.py
import pyglet
from pyglet import gl
from config import (
    PLAY_W_PX, WINDOW_HEIGHT, WINDOW_WIDTH,
    MIN_ZOOM, MAX_ZOOM, CELL_SIZE, PLAY_W, PLAY_H
)

def set_play_projection(window, player, view_mode, zoom):
    """Set sub-viewport for playfield and an orthographic projection
       centered on the player. Returns the view_range (2 for local, 5 for global).
    """
    gl.glViewport(0, 0, PLAY_W_PX, WINDOW_HEIGHT)

    world_w = PLAY_W * CELL_SIZE
    world_h = PLAY_H * CELL_SIZE
    z = max(MIN_ZOOM, min(MAX_ZOOM, zoom))

    cx = (player[0] + 0.5) * CELL_SIZE
    cy = (player[1] + 0.5) * CELL_SIZE

    if view_mode == "global":
        w = min(world_w, world_w / z)
        h = min(world_h, world_h / z)
        view_range = 5
    else:
        base_w = 5 * CELL_SIZE
        base_h = 5 * CELL_SIZE
        w = min(base_w / z, world_w)
        h = min(base_h / z, world_h)
        view_range = 2

    left = max(0.0, min(cx - w / 2.0, world_w - w))
    bottom = max(0.0, min(cy - h / 2.0, world_h - h))
    right = left + w
    top = bottom + h

    # ✅ Use pyglet.math.Mat4, not window.math.Mat4
    window.projection = pyglet.math.Mat4.orthogonal_projection(
        left, right, bottom, top, -1.0, 1.0
    )
    return view_range

def reset_ui_projection(window):
    gl.glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    # ✅ Use pyglet.math.Mat4 here too
    window.projection = pyglet.math.Mat4.orthogonal_projection(
        0.0, float(WINDOW_WIDTH), 0.0, float(WINDOW_HEIGHT), -1.0, 1.0
    )
