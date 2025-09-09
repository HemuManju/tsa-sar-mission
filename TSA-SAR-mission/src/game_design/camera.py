# camera.py
import pyglet
from pyglet import gl
from config import (
    PLAY_W_PX, WINDOW_HEIGHT, WINDOW_WIDTH,
    MIN_ZOOM, MAX_ZOOM, CELL_SIZE, PLAY_W, PLAY_H
)

def set_play_projection(window, player, view_mode, zoom):
    """
    Edge-panning camera:
      - Global = same behavior as before (centered/zoomed on whole map)
      - Local  = viewport only moves when player crosses a margin near edges
    """
    gl.glViewport(0, 0, PLAY_W_PX, WINDOW_HEIGHT)

    world_w = PLAY_W * CELL_SIZE
    world_h = PLAY_H * CELL_SIZE
    z = max(MIN_ZOOM, min(MAX_ZOOM, zoom))

    # Player center in pixels
    cx = (player[0] + 0.5) * CELL_SIZE
    cy = (player[1] + 0.5) * CELL_SIZE

    # Viewport size
    if view_mode == "global":
        w = min(world_w, world_w / z)
        h = min(world_h, world_h / z)
        # Center-follow for global (unchanged)
        left   = max(0.0, min(cx - w / 2.0, world_w - w))
        bottom = max(0.0, min(cy - h / 2.0, world_h - h))

    else:
        # Local view window (same size rules as before)
        base_w = 5 * CELL_SIZE
        base_h = 5 * CELL_SIZE
        w = min(base_w / z, world_w)
        h = min(base_h / z, world_h)

        # Keep per-window camera state
        if not hasattr(window, "_cam_state"):
            window._cam_state = {}

        cam = window._cam_state
        # Re-init when switching mode or viewport size changes (e.g., zoom)
        if cam.get("mode") != "local" or cam.get("w") != w or cam.get("h") != h:
            cam["mode"], cam["w"], cam["h"] = "local", w, h
            cam["left"]   = max(0.0, min(cx - w / 2.0, world_w - w))
            cam["bottom"] = max(0.0, min(cy - h / 2.0, world_h - h))

        left, bottom = cam["left"], cam["bottom"]

        # How close to the edge before we pan (in cells)
        EDGE_MARGIN_CELLS = 1    # tweak to taste (e.g., 2 or 3)
        margin = EDGE_MARGIN_CELLS * CELL_SIZE

        # Horizontal edge-pan
        if cx < left + margin:
            left = max(0.0, cx - margin)
        elif cx > left + w - margin:
            left = min(world_w - w, cx - (w - margin))

        # Vertical edge-pan
        if cy < bottom + margin:
            bottom = max(0.0, cy - margin)
        elif cy > bottom + h - margin:
            bottom = min(world_h - h, cy - (h - margin))

        # Save updated camera rect
        cam["left"], cam["bottom"] = left, bottom

    right = left + w
    top   = bottom + h

    window.projection = pyglet.math.Mat4.orthogonal_projection(
        left, right, bottom, top, -1.0, 1.0
    )

    # Keep returning view_range like before (used by HUD/logic if any)
    return 2 if view_mode == "local" else 5


def reset_ui_projection(window):
    gl.glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    window.projection = pyglet.math.Mat4.orthogonal_projection(
        0.0, float(WINDOW_WIDTH), 0.0, float(WINDOW_HEIGHT), -1.0, 1.0
    )
