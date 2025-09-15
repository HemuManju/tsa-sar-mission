 
import pyglet
from pyglet import gl
from config import (
    PLAY_W_PX, WINDOW_HEIGHT, WINDOW_WIDTH,
    MIN_ZOOM, MAX_ZOOM, CELL_SIZE, PLAY_W, PLAY_H
)
 
 
def set_play_projection(window, player, view_mode, zoom):
    """
    Camera projection:
      - Global = full map, center-follow with zoom
      - Local  = zone-based snapping: when player touches the edge,
                 move to next zone with 2-cell overlap
    """
    gl.glViewport(0, 0, PLAY_W_PX, WINDOW_HEIGHT)
 
    world_w = PLAY_W * CELL_SIZE
    world_h = PLAY_H * CELL_SIZE
    z = max(MIN_ZOOM, min(MAX_ZOOM, zoom))
 
    # Player center in pixels
    cx = (player[0] + 0.5) * CELL_SIZE
    cy = (player[1] + 0.5) * CELL_SIZE
 
    if view_mode == "global":
        # --- Global: same as before (center-follow with zoom) ---
        w = min(world_w, world_w / z)
        h = min(world_h, world_h / z)
        left   = max(0.0, min(cx - w / 2.0, world_w - w))
        bottom = max(0.0, min(cy - h / 2.0, world_h - h))
 
    else:
        # --- Local: zone jumps with overlap ---
        ZONE_W_CELLS = 5
        ZONE_H_CELLS = 5
        OVERLAP = 2
 
        stride_x = (ZONE_W_CELLS - OVERLAP) * CELL_SIZE
        stride_y = (ZONE_H_CELLS - OVERLAP) * CELL_SIZE
        zone_w   = ZONE_W_CELLS * CELL_SIZE
        zone_h   = ZONE_H_CELLS * CELL_SIZE
 
        # Keep per-window camera state
        if not hasattr(window, "_cam_state"):
            window._cam_state = {}
 
        cam = window._cam_state
        if cam.get("mode") != "local":
            cam["mode"] = "local"
            # Initialize zone around player
            cam["left"] = max(0, min(cx - zone_w // 2, world_w - zone_w))
            cam["bottom"] = max(0, min(cy - zone_h // 2, world_h - zone_h))
 
        left, bottom = cam["left"], cam["bottom"]
 
        # --- Trigger shift if player touches edges ---
        if cx <= left:   # hit left edge
            left = max(0, left - stride_x)
        elif cx >= left + zone_w:  # hit right edge
            left = min(world_w - zone_w, left + stride_x)
 
        if cy <= bottom:  # hit bottom edge
            bottom = max(0, bottom - stride_y)
        elif cy >= bottom + zone_h:  # hit top edge
            bottom = min(world_h - zone_h, bottom + stride_y)
 
        # Save updated rect
        cam["left"], cam["bottom"] = left, bottom
 
        # Apply zoom
        w = zone_w / z
        h = zone_h / z
 
    right = left + w
    top   = bottom + h
 
    window.projection = pyglet.math.Mat4.orthogonal_projection(
        left, right, bottom, top, -1.0, 1.0
    )
 
    # Keep returning view_range like before (used by HUD/logic if any)
    return 2 if view_mode == "local" else 5
 
 
def reset_ui_projection(window):
    """Reset projection for HUD/UI drawing (screen-space coords)."""
    gl.glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    window.projection = pyglet.math.Mat4.orthogonal_projection(
        0.0, float(WINDOW_WIDTH), 0.0, float(WINDOW_HEIGHT), -1.0, 1.0
    )
 




"""-------------collect-------"""

def camera():
    return {
        "set_play_projection": set_play_projection,
        "reset_ui_projection": reset_ui_projection
    }

