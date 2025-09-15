# chatui.py
from pyglet import shapes
from pyglet.text.document import UnformattedDocument
from pyglet.text.layout import IncrementalTextLayout
from pyglet.text.caret import Caret
from config import (PLAY_W_PX, SIDEBAR_W, WINDOW_HEIGHT, COLOR_PANEL_BORDER,
                    COLOR_TEXT, DEFAULT_FONT)

def build_chat(ui_batch):
    hist_doc = UnformattedDocument("")
    hist_doc.set_style(0, 0, dict(color=COLOR_TEXT,
                                  font_name=DEFAULT_FONT, font_size=11))
    hist_layout = IncrementalTextLayout(hist_doc,
        width=SIDEBAR_W-30, height=WINDOW_HEIGHT-320,
        multiline=True, batch=ui_batch)
    hist_layout.x = PLAY_W_PX + 15
    hist_layout.y = WINDOW_HEIGHT - 300

    input_doc = UnformattedDocument("")
    input_doc.set_style(0, 0, dict(color=(240,240,255,255),
                                   font_name=DEFAULT_FONT, font_size=12))
    input_layout = IncrementalTextLayout(input_doc, width=SIDEBAR_W-40,
        height=26, multiline=False, batch=ui_batch)
    input_layout.x = PLAY_W_PX + 20
    input_layout.y = 40

    input_box = shapes.BorderedRectangle(PLAY_W_PX+15, 35, SIDEBAR_W-30, 34,
                                         border=2, color=(30,30,36),
                                         border_color=COLOR_PANEL_BORDER,
                                         batch=ui_batch)
    caret = Caret(input_layout, color=(255,255,255))
    caret.visible = True
    caret.on_activate()

    return {
        "hist_doc": hist_doc, "hist_layout": hist_layout,
        "input_doc": input_doc, "input_layout": input_layout,
        "input_box": input_box, "caret": caret, "lines": [], "focus": False
    }

def append_line(chat, line):
    chat["lines"].append(line)
    chat["hist_doc"].text = "\n".join(chat["lines"][-200:])
    chat["hist_doc"].set_style(
        0, len(chat["hist_doc"].text),
        dict(color=COLOR_TEXT, font_name="Arial", font_size=11)
    )
    chat["hist_layout"].view_y = max(
        0, chat["hist_layout"].content_height - chat["hist_layout"].height
    )





"...........collection......"

def chatui():
    return {
        "build_chat": build_chat,
        "append_line": append_line
    }
