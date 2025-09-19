# hud.py
from pyglet import shapes, text
from config import (
    PLAY_W_PX,
    SIDEBAR_W,
    WINDOW_HEIGHT,
    COLOR_PANEL_RGB,
    COLOR_PANEL_ALPHA,
    COLOR_PANEL_BORDER,
    COLOR_TEXT,
    DEFAULT_FONT,
)


def build_hud(ui_batch):
    # Background panel on the right
    panel = shapes.BorderedRectangle(
        PLAY_W_PX,
        0,
        SIDEBAR_W,
        WINDOW_HEIGHT,
        border=2,
        color=COLOR_PANEL_RGB,
        border_color=COLOR_PANEL_BORDER,
        batch=ui_batch,
    )
    panel.opacity = COLOR_PANEL_ALPHA

    # Status line at top
    status = text.Label(
        "",
        x=PLAY_W_PX + SIDEBAR_W // 2,
        y=WINDOW_HEIGHT - 40,
        anchor_x="center",
        color=COLOR_TEXT,
        font_name=DEFAULT_FONT,
        font_size=14,
        batch=ui_batch,
    )

    # Labels dictionary
    labels = {
        "time": text.Label(
            "Time: —",
            x=PLAY_W_PX + 20,
            y=WINDOW_HEIGHT - 80,
            anchor_x="left",
            color=COLOR_TEXT,
            font_name=DEFAULT_FONT,
            font_size=12,
            batch=ui_batch,
        ),
        "zoom": text.Label(
            "Zoom: —",
            x=PLAY_W_PX + 20,
            y=WINDOW_HEIGHT - 105,
            anchor_x="left",
            color=COLOR_TEXT,
            font_name=DEFAULT_FONT,
            font_size=12,
            batch=ui_batch,
        ),
        "victims": text.Label(
            "Victims left: —",
            x=PLAY_W_PX + 20,
            y=WINDOW_HEIGHT - 130,
            anchor_x="left",
            color=COLOR_TEXT,
            font_name=DEFAULT_FONT,
            font_size=12,
            batch=ui_batch,
        ),
        "player": text.Label(
            "Player: —",
            x=PLAY_W_PX + 20,
            y=WINDOW_HEIGHT - 155,
            anchor_x="left",
            color=COLOR_TEXT,
            font_name=DEFAULT_FONT,
            font_size=12,
            batch=ui_batch,
        ),
        # "rescue": text.Label("Rescue: —", x=PLAY_W_PX + 20, y=WINDOW_HEIGHT - 180,
        # anchor_x="left", color=COLOR_TEXT,
        # font_name=DEFAULT_FONT, font_size=12, batch=ui_batch),
        "carried": text.Label(
            "Carrying: —",
            x=PLAY_W_PX + 20,
            y=WINDOW_HEIGHT - 205,
            anchor_x="left",
            color=COLOR_TEXT,
            font_name=DEFAULT_FONT,
            font_size=12,
            batch=ui_batch,
        ),
        "difficulty": text.Label(
            "",
            x=PLAY_W_PX + 20,
            y=WINDOW_HEIGHT - 230,
            anchor_x="left",
            color=COLOR_TEXT,
            font_name=DEFAULT_FONT,
            font_size=12,
            batch=ui_batch,
        ),
        # "view": text.Label("", x=PLAY_W_PX + 20, y=WINDOW_HEIGHT - 255,
        # anchor_x="left", color=COLOR_TEXT,
        # font_name=DEFAULT_FONT, font_size=12, batch=ui_batch),
    }

    return {"panel": panel, "status": status, "labels": labels}
