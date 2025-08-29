# hud.py
from pyglet import shapes, text
from config import (PLAY_W_PX, SIDEBAR_W, WINDOW_HEIGHT, COLOR_PANEL_RGB,
                    COLOR_PANEL_ALPHA, COLOR_PANEL_BORDER, COLOR_TEXT, DEFAULT_FONT)

def build_hud(ui_batch):
    panel_bg = shapes.Rectangle(PLAY_W_PX, 0, SIDEBAR_W, WINDOW_HEIGHT,
                                color=COLOR_PANEL_RGB, batch=ui_batch)
    panel_bg.opacity = COLOR_PANEL_ALPHA
    panel_border = shapes.BorderedRectangle(PLAY_W_PX+4, 4, SIDEBAR_W-8,
        WINDOW_HEIGHT-8, border=3, color=(20,20,28),
        border_color=COLOR_PANEL_BORDER, batch=ui_batch)

    title = text.Label("Mission HUD", x=PLAY_W_PX+SIDEBAR_W//2,
        y=WINDOW_HEIGHT-40, anchor_x='center',
        color=COLOR_TEXT, font_name=DEFAULT_FONT, font_size=18, bold=True,
        batch=ui_batch)
    status = text.Label("Press ENTER on Start screen to begin",
        x=PLAY_W_PX+20, y=WINDOW_HEIGHT-80, anchor_x='left',
        color=COLOR_TEXT, font_name=DEFAULT_FONT, font_size=12, batch=ui_batch)

    labels = {
        "difficulty": text.Label("", x=PLAY_W_PX+20, y=WINDOW_HEIGHT-100,
            anchor_x='left', color=COLOR_TEXT, font_size=12, batch=ui_batch),
        "time": text.Label("", x=PLAY_W_PX+20, y=WINDOW_HEIGHT-120,
            anchor_x='left', color=COLOR_TEXT, font_size=12, batch=ui_batch),
        "zoom": text.Label("", x=PLAY_W_PX+20, y=WINDOW_HEIGHT-140,
            anchor_x='left', color=COLOR_TEXT, font_size=12, batch=ui_batch),
        "view": text.Label("View: —", x=PLAY_W_PX+20, y=WINDOW_HEIGHT-160,
            anchor_x='left', color=COLOR_TEXT, font_size=12, batch=ui_batch),
        "victims": text.Label("", x=PLAY_W_PX+20, y=WINDOW_HEIGHT-180,
            anchor_x='left', color=COLOR_TEXT, font_size=12, batch=ui_batch),
        "player": text.Label("", x=PLAY_W_PX+20, y=WINDOW_HEIGHT-200,
            anchor_x='left', color=COLOR_TEXT, font_size=12, batch=ui_batch),
        "rescue": text.Label("", x=PLAY_W_PX+20, y=WINDOW_HEIGHT-220,
            anchor_x='left', color=COLOR_TEXT, font_size=12, batch=ui_batch),
        "carried": text.Label("Carrying: —", x=PLAY_W_PX+20, y=WINDOW_HEIGHT-240,
            anchor_x='left', color=COLOR_TEXT, font_size=12, batch=ui_batch),
        "help": text.Label(
            "Start: ←/→ diff • ↑/↓ view • 1/2/3 • L/G • ENTER | In-game: +/- zoom • G toggle • WASD/Arrows",
            x=PLAY_W_PX+20, y=WINDOW_HEIGHT-270, anchor_x='left',
            color=COLOR_TEXT, font_size=10, batch=ui_batch)
    }
    return {"panel_bg": panel_bg, "panel_border": panel_border,
            "title": title, "status": status, "labels": labels}
