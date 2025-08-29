import random
from collections import deque
import pyglet
from pyglet import shapes, text
from pyglet.window import key, mouse

# =========================
# Config
# =========================
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 800
CELL_SIZE = 20

GRID_W = WINDOW_WIDTH // CELL_SIZE
GRID_H = WINDOW_HEIGHT // CELL_SIZE

SIDEBAR_W = 360
PLAY_W_PX = WINDOW_WIDTH - SIDEBAR_W
PLAY_W = PLAY_W_PX // CELL_SIZE
PLAY_H = GRID_H

TIME_LIMIT = 300
MIN_ZOOM = 0.25
MAX_ZOOM = 1.50
ZOOM_STEP = 0.10

# Colors
COLOR_BG = (22, 24, 28)
COLOR_GRID = (55, 60, 70)
COLOR_WALL = (90, 100, 115)
COLOR_PLAYER = (60, 200, 255)

COLOR_PANEL_RGB = (10, 10, 14)
COLOR_PANEL_ALPHA = 220
COLOR_PANEL_BORDER = (140, 100, 220)

COLOR_TEXT = (230, 230, 240, 255)
COLOR_PURPLE = (190, 140, 255)
COLOR_YELLOW = (255, 227, 102)
COLOR_RED = (230, 70, 70)
COLOR_RESCUE = (255, 220, 60)

# Victims
NUM_RED = 15
NUM_PURPLE = 30
NUM_YELLOW = 45

START = (1, 1)

# Difficulty presets
DIFFICULTIES = {
    "Easy": {"segments": 90, "seed": 42},
    "Medium": {"segments": 120, "seed": 42},
    "Hard": {"segments": 150, "seed": 42},
}

# =========================
# Helpers
# =========================
def line_h(x, y, w):
    return [(x + i, y) for i in range(max(1, w))]

def line_v(x, y, h):
    return [(x, y + i) for i in range(max(1, h))]

def clamp_grid(points):
    out = []
    for x, y in points:
        if 0 <= x < PLAY_W and 0 <= y < PLAY_H:
            out.append((x, y))
    return set(out)

def grid_to_px(gx, gy):
    return gx * CELL_SIZE, gy * CELL_SIZE

def bfs_distances(start, passable):
    q = deque([start])
    dist = {start: 0}
    while q:
        x, y = q.popleft()
        for nx, ny in ((x+1,y), (x-1,y), (x,y+1), (x,y-1)):
            if 0 <= nx < PLAY_W and 0 <= ny < PLAY_H and (nx, ny) in passable and (nx, ny) not in dist:
                dist[(nx, ny)] = dist[(x, y)] + 1
                q.append((nx, ny))
    return dist

# =========================
# Game
# =========================
class Game:
    def __init__(self):
        self.window = pyglet.window.Window(WINDOW_WIDTH, WINDOW_HEIGHT, "SAR Mission")
        self.window.push_handlers(self)

        # batches
        self.play_batch = pyglet.graphics.Batch()
        self.ui_batch = pyglet.graphics.Batch()

        # ----- STATE -----
        self.game_state = "start"  # "start" -> "playing"
        self.zoom = 1.0

        # Selections made on the start page (defaults)
        self._start_diffs = ["Easy", "Medium", "Hard"]
        self._start_diff_idx = 0
        self._start_view = "Local"  # or "Global"

        # Active (applied once Enter is pressed)
        self.difficulty = None
        self.view_mode = "local"   # "local" or "global"

        self.time_remaining = TIME_LIMIT
        self.game_over = False
        self.player = list(START)
        self.rescue_pos = None
        self.rescue_reached = False

        # grid lines
        self.grid_v = [(shapes.Line(0,0,0,0,width=1,color=COLOR_GRID,batch=self.play_batch), gx)
                         for gx in range(1, PLAY_W)]
        self.grid_h = [(shapes.Line(0,0,0,0,width=1,color=COLOR_GRID,batch=self.play_batch), gy)
                         for gy in range(1, PLAY_H)]

        # dynamic world drawables (built after difficulty chosen)
        self.wall_shapes = []
        self.victim_shapes = {}
        self.player_shape = shapes.Rectangle(0, 0, 0, 0, color=COLOR_PLAYER, batch=self.play_batch)

        # rescue marker (triangle)
        self.rescue_triangle = None
        self._rescue_cache = {"pos": None, "z": None}

        # ----- Sidebar panel -----
        self.panel_bg = shapes.Rectangle(PLAY_W_PX, 0, SIDEBAR_W, WINDOW_HEIGHT,
                                         color=COLOR_PANEL_RGB, batch=self.ui_batch)
        self.panel_bg.opacity = COLOR_PANEL_ALPHA
        self.panel_border = shapes.BorderedRectangle(PLAY_W_PX+4, 4, SIDEBAR_W-8, WINDOW_HEIGHT-8,
                                                     border=3, color=(20,20,28),
                                                     border_color=COLOR_PANEL_BORDER, batch=self.ui_batch)

        self.title_label = text.Label("Mission HUD", x=PLAY_W_PX+SIDEBAR_W//2, y=WINDOW_HEIGHT-40,
                                      anchor_x='center', color=COLOR_TEXT, font_size=18, bold=True, batch=self.ui_batch)
        self.status_label = text.Label("Press ENTER on Start screen to begin",
                                       x=PLAY_W_PX+20, y=WINDOW_HEIGHT-80, anchor_x='left',
                                       color=COLOR_TEXT, font_size=12, batch=self.ui_batch)

        # Vertically stacked HUD stats
        self.difficulty_label = text.Label("", x=PLAY_W_PX+20, y=WINDOW_HEIGHT-100, anchor_x='left', color=COLOR_TEXT, font_size=12, batch=self.ui_batch)
        self.time_label = text.Label("", x=PLAY_W_PX+20, y=WINDOW_HEIGHT-120, anchor_x='left', color=COLOR_TEXT, font_size=12, batch=self.ui_batch)
        self.zoom_label = text.Label("", x=PLAY_W_PX+20, y=WINDOW_HEIGHT-140, anchor_x='left', color=COLOR_TEXT, font_size=12, batch=self.ui_batch)
        self.view_label = text.Label("View: —", x=PLAY_W_PX+20, y=WINDOW_HEIGHT-160, anchor_x='left', color=COLOR_TEXT, font_size=12, batch=self.ui_batch)
        self.victims_label = text.Label("", x=PLAY_W_PX+20, y=WINDOW_HEIGHT-180, anchor_x='left', color=COLOR_TEXT, font_size=12, batch=self.ui_batch)
        self.player_label = text.Label("", x=PLAY_W_PX+20, y=WINDOW_HEIGHT-200, anchor_x='left', color=COLOR_TEXT, font_size=12, batch=self.ui_batch)
        self.rescue_label = text.Label("", x=PLAY_W_PX+20, y=WINDOW_HEIGHT-220, anchor_x='left', color=COLOR_TEXT, font_size=12, batch=self.ui_batch)

        self.help_label = text.Label(
            "Start: ←/→ diff • ↑/↓ view • 1/2/3 • L/G • ENTER start | In-game: +/- zoom • G toggle • WASD/Arrows move",
            x=PLAY_W_PX+20, y=WINDOW_HEIGHT-250, anchor_x='left',
            color=COLOR_TEXT, font_size=10, batch=self.ui_batch)

        # ----- Start screen overlay (not in any batch so it can disappear) -----
        self.start_title = text.Label("Mission Setup",
                                      x=PLAY_W_PX//2, y=WINDOW_HEIGHT//2 + 80,
                                      anchor_x='center', color=COLOR_TEXT, font_size=28, bold=True)
        self.start_diff_label = text.Label("", x=PLAY_W_PX//2, y=WINDOW_HEIGHT//2 + 30,
                                           anchor_x='center', color=COLOR_TEXT, font_size=18)
        self.start_view_label = text.Label("", x=PLAY_W_PX//2, y=WINDOW_HEIGHT//2 - 10,
                                           anchor_x='center', color=COLOR_TEXT, font_size=18)
        self.start_hint = text.Label("Use arrows / 1-2-3 / L-G • Press ENTER to start",
                                     x=PLAY_W_PX//2, y=WINDOW_HEIGHT//2 - 60,
                                     anchor_x='center', color=COLOR_TEXT, font_size=12)
        self._refresh_start_labels()

        # ----- Chat UI -----
        from pyglet.text.document import UnformattedDocument
        from pyglet.text.layout import IncrementalTextLayout
        from pyglet.text.caret import Caret

        self.chat_history_doc = UnformattedDocument("")
        self.chat_history_doc.set_style(0, 0, dict(color=COLOR_TEXT, font_name="Arial", font_size=11))
        self.chat_history_layout = IncrementalTextLayout(self.chat_history_doc,
                                                         width=SIDEBAR_W-30, height=WINDOW_HEIGHT-320,
                                                         multiline=True, batch=self.ui_batch)
        self.chat_history_layout.x = PLAY_W_PX + 15
        self.chat_history_layout.y = WINDOW_HEIGHT - 280

        self.input_doc = UnformattedDocument("")
        self.input_doc.set_style(0, 0, dict(color=(240,240,255,255), font_name="Arial", font_size=12))
        self.input_layout = IncrementalTextLayout(self.input_doc, width=SIDEBAR_W-40, height=26,
                                                  multiline=False, batch=self.ui_batch)
        self.input_layout.x = PLAY_W_PX + 20
        self.input_layout.y = 40

        self.input_box = shapes.BorderedRectangle(PLAY_W_PX+15, 35, SIDEBAR_W-30, 34,
                                                  border=2, color=(30,30,36),
                                                  border_color=COLOR_PANEL_BORDER, batch=self.ui_batch)

        self.caret = Caret(self.input_layout, color=(255,255,255))
        self.caret.visible = True
        self.caret.on_activate()
        self.input_focus = False
        self.chat_lines = []

        # timers
        pyglet.clock.schedule_interval(self._tick, 1/60.0)
        pyglet.clock.schedule_interval(self._second, 1.0)

    # ---------- start screen helpers ----------
    def _refresh_start_labels(self):
        diff = self._start_diffs[self._start_diff_idx]
        self.start_diff_label.text = f"Difficulty:  {diff}"
        self.start_view_label.text = f"View:        {self._start_view}"

    def _apply_start_selection_and_begin(self):
        # Apply selected options
        self.difficulty = self._start_diffs[self._start_diff_idx]
        self.view_mode = self._start_view.lower()
        self.view_label.text = f"View: {self._start_view}"
        # Build world and switch state
        self._rebuild_world()
        self.game_state = "playing"
        self.status_label.text = ""       # clear hint
        self.difficulty_label.text = ""   # keep difficulty hidden if you prefer

    # ---------- world (depends on difficulty) ----------
    def _rebuild_world(self):
        # clear old shapes
        for r, *_ in self.wall_shapes:
            r.delete()
        for (c, _kind) in self.victim_shapes.values():
            c.delete()
        self.wall_shapes = []
        self.victim_shapes = {}
        if self.rescue_triangle:
            self.rescue_triangle.delete()
            self.rescue_triangle = None
        self._rescue_cache = {"pos": None, "z": None}

        # walls
        self.walls = self._generate_walls()
        self.passable = {(x, y) for x in range(PLAY_W) for y in range(PLAY_H)} - self.walls
        if START in self.walls:
            self.walls.discard(START)
            self.passable.add(START)

        # distances from START
        distmap = bfs_distances(START, self.passable)

        # victims
        self.victims = self._place_victims(distmap)

        # rescue = farthest reachable from START (avoid victim tile if possible)
        if distmap:
            far_sorted = sorted(distmap.items(), key=lambda kv: kv[1], reverse=True)
            chosen = None
            for pos, _d in far_sorted:
                if pos not in self.victims and pos != START:
                    chosen = pos; break
            self.rescue_pos = chosen or far_sorted[0][0]
        else:
            self.rescue_pos = START
        self.rescue_reached = False

        # create drawables
        for (gx, gy) in self.walls:
            r = shapes.Rectangle(0, 0, 0, 0, color=COLOR_WALL, batch=self.play_batch)
            self.wall_shapes.append((r, gx, gy))
        for pos, kind in self.victims.items():
            c = shapes.Circle(0, 0, 1, color=self._victim_color(kind), batch=self.play_batch)
            self.victim_shapes[pos] = (c, kind)

        # reset timers/player
        self.time_remaining = TIME_LIMIT
        self.player = list(START)

    def _generate_walls(self):
        cfg = DIFFICULTIES[self.difficulty]
        rng = random.Random(cfg["seed"])
        segments = cfg["segments"]
        walls = set()
        # border
        for x in range(PLAY_W):
            walls.add((x, 0))
            walls.add((x, PLAY_H-1))
        for y in range(PLAY_H):
            walls.add((0, y))
            walls.add((PLAY_W-1, y))

        # random segments; keep spawn zone clear
        for _ in range(segments):
            length = rng.randint(3, 10)
            if rng.random() < 0.5:
                x = rng.randint(1, PLAY_W-2-length)
                y = rng.randint(2, PLAY_H-3)
                pts = line_h(x, y, length)
            else:
                x = rng.randint(2, PLAY_W-3)
                y = rng.randint(1, PLAY_H-2-length)
                pts = line_v(x, y, length)
            if any(0 <= sx <= 7 and 0 <= sy <= 7 for sx, sy in pts):
                continue
            walls.update(pts)
        walls.discard(START)
        return clamp_grid(walls)

    def _place_victims(self, distmap):
        rng = random.Random(99)
        victims = {}

        # Partition grid into quadrants
        mid_x = PLAY_W // 2
        mid_y = PLAY_H // 2
        quadrants = {
            "top_right":  [], "top_left":   [],
            "bottom_right": [], "bottom_left":  []
        }

        for pos, _dist in distmap.items():
            if pos == START: continue
            qx = "left" if pos[0] < mid_x else "right"
            qy = "bottom" if pos[1] < mid_y else "top"
            quadrants[f"{qy}_{qx}"].append(pos)

        # Select some reds from harder (farther) cells in each quadrant
        red_to_place = NUM_RED
        for q_cells in quadrants.values():
            q_cells.sort(key=lambda p: distmap.get(p, 0), reverse=True)
            hard_cells = q_cells[:max(1, len(q_cells)//3)]
            num_in_quadrant = max(0, red_to_place // 4)
            for _ in range(num_in_quadrant):
                if hard_cells:
                    p = rng.choice(hard_cells)
                    victims[p] = "red"
                    hard_cells.remove(p)
                    distmap.pop(p, None)

        while sum(1 for k in victims.values() if k == "red") < NUM_RED and distmap:
            candidate = rng.choice(list(distmap.keys()))
            if candidate not in victims:
                victims[candidate] = "red"
                distmap.pop(candidate, None)

        remaining_candidates = [p for p in distmap.keys() if p not in victims and p != START]
        rng.shuffle(remaining_candidates)

        purple_to_place = NUM_PURPLE
        yellow_to_place = NUM_YELLOW

        for p in remaining_candidates:
            if purple_to_place > 0:
                victims[p] = "purple"
                purple_to_place -= 1
            elif yellow_to_place > 0:
                victims[p] = "yellow"
                yellow_to_place -= 1
            else:
                break

        return victims

    def _victim_color(self, kind):
        return COLOR_YELLOW if kind == "yellow" else (COLOR_PURPLE if kind == "purple" else COLOR_RED)

    # ---------- runtime ----------
    def _tick(self, dt):
        if self.game_state != "playing":
            return
        # pick up victims
        pos = tuple(self.player)
        if pos in self.victims:
            if pos in self.victim_shapes:
                self.victim_shapes[pos][0].delete()
                del self.victim_shapes[pos]
            del self.victims[pos]
        # rescue detection
        if self.rescue_pos and tuple(self.player) == self.rescue_pos and not self.rescue_reached:
            self.rescue_reached = True
            self._append_chat_line("[SYSTEM] Rescue point reached! 🎯")
        # stats
        reds = sum(1 for k in self.victims.values() if k == "red")
        purples = sum(1 for k in self.victims.values() if k == "purple")
        yellows = sum(1 for k in self.victims.values() if k == "yellow")
        rescue_txt = f"{self.rescue_pos[0]},{self.rescue_pos[1]}" if self.rescue_pos else "—"
        self.time_label.text = f"Time: {self.time_remaining:>3d}s"
        self.zoom_label.text = f"Zoom: {self.zoom:.2f}×"
        self.victims_label.text = f"Victims left (R/P/Y): {reds}/{purples}/{yellows}"
        self.player_label.text = f"Player: {self.player[0]},{self.player[1]}"
        self.rescue_label.text = f"Rescue: {rescue_txt}"

        if self.time_remaining <= 0 and not self.game_over:
            self.game_over = True
            self._append_chat_line("[SYSTEM] Time up! Mission ended.")

    def _second(self, dt):
        if self.game_state == "playing" and not self.game_over:
            self.time_remaining -= 1

    # ---------- movement & chat ----------
    def _move(self, dx, dy):
        if self.game_state != "playing" or self.game_over:
            return
        nx, ny = self.player[0] + dx, self.player[1] + dy
        if 0 <= nx < PLAY_W and 0 <= ny < PLAY_H and (nx, ny) not in self.walls:
            self.player[0], self.player[1] = nx, ny

    def _append_chat_line(self, line):
        self.chat_lines.append(line)
        text_blob = "\n".join(self.chat_lines[-200:])
        self.chat_history_doc.text = text_blob
        self.chat_history_doc.set_style(0, len(self.chat_history_doc.text),
                                        dict(color=COLOR_TEXT, font_name="Arial", font_size=11))
        self.chat_history_layout.view_y = max(
            0,
            self.chat_history_layout.content_height - self.chat_history_layout.height
        )

    # ---------- draw helpers (CPU-side zoom) ----------
    def _apply_zoom_positions(self):
        z = self.zoom
        if self.view_mode == "global":
            play_aspect = PLAY_W_PX / WINDOW_HEIGHT
            grid_aspect = PLAY_W / PLAY_H
            if grid_aspect > play_aspect:
                z = PLAY_W_PX / (PLAY_W * CELL_SIZE)
            else:
                z = WINDOW_HEIGHT / (PLAY_H * CELL_SIZE)

        W0 = PLAY_W * CELL_SIZE
        H0 = PLAY_H * CELL_SIZE
        dx = (W0 - W0 * z) / 2.0
        dy = (H0 - H0 * z) / 2.0

        # grid lines
        for ln, gx in self.grid_v:
            x = (gx * CELL_SIZE) * z + dx
            ln.x, ln.y = x, 0 * z + dy
            ln.x2, ln.y2 = x, H0 * z + dy
            ln.width = max(1, int(z))
        for ln, gy in self.grid_h:
            y = (gy * CELL_SIZE) * z + dy
            ln.x, ln.y = 0 * z + dx, y
            ln.x2, ln.y2 = W0 * z + dx, y
            ln.width = max(1, int(z))

        # walls
        for r, gx, gy in self.wall_shapes:
            r.x = (gx * CELL_SIZE) * z + dx
            r.y = (gy * CELL_SIZE) * z + dy
            r.width = CELL_SIZE * z
            r.height = CELL_SIZE * z

        # player
        self.player_shape.x = (self.player[0] * CELL_SIZE) * z + dx
        self.player_shape.y = (self.player[1] * CELL_SIZE) * z + dy
        self.player_shape.width = CELL_SIZE * z
        self.player_shape.height = CELL_SIZE * z

        # victims
        for (gx, gy), (c, kind) in self.victim_shapes.items():
            c.x = (gx * CELL_SIZE + CELL_SIZE/2) * z + dx
            c.y = (gy * CELL_SIZE + CELL_SIZE/2) * z + dy
            c.radius = max(2.0, (CELL_SIZE/2 - 3) * z)
            c.color = self._victim_color(kind)

        # rescue triangle (fixed orientation)
        if self.rescue_pos:
            if (self._rescue_cache["pos"] != self.rescue_pos) or (self._rescue_cache["z"] != z):
                if self.rescue_triangle:
                    self.rescue_triangle.delete()
                    self.rescue_triangle = None
                gx, gy = self.rescue_pos
                cx = (gx * CELL_SIZE + CELL_SIZE/2) * z + dx
                cy = (gy * CELL_SIZE + CELL_SIZE/2) * z + dy
                s = CELL_SIZE * z * 0.9
                h = s * 0.5
                x1, y1 = cx, cy + h
                x2, y2 = cx - s/2, cy - h
                x3, y3 = cx + s/2, cy - h
                self.rescue_triangle = shapes.Triangle(x1, y1, x2, y2, x3, y3,
                                                       color=COLOR_RESCUE, batch=self.play_batch)
                self._rescue_cache["pos"] = self.rescue_pos
                self._rescue_cache["z"] = z

    # ---------- events ----------
    def on_draw(self):
        self.window.clear()
        pyglet.gl.glClearColor(COLOR_BG[0]/255.0, COLOR_BG[1]/255.0, COLOR_BG[2]/255.0, 1.0)
        self._apply_zoom_positions()
        self.play_batch.draw()
        self.ui_batch.draw()

        # draw start overlay only while in "start"
        if self.game_state == "start":
            self.start_title.draw()
            self.start_diff_label.draw()
            self.start_view_label.draw()
            self.start_hint.draw()

    def on_key_press(self, symbol, modifiers):
        # ----- START SCREEN -----
        if self.game_state == "start":
            if symbol == key.LEFT:
                self._start_diff_idx = (self._start_diff_idx - 1) % len(self._start_diffs)
                self._refresh_start_labels(); return
            if symbol == key.RIGHT:
                self._start_diff_idx = (self._start_diff_idx + 1) % len(self._start_diffs)
                self._refresh_start_labels(); return
            if symbol in (key._1, key.NUM_1):
                self._start_diff_idx = 0; self._refresh_start_labels(); return
            if symbol in (key._2, key.NUM_2):
                self._start_diff_idx = 1; self._refresh_start_labels(); return
            if symbol in (key._3, key.NUM_3):
                self._start_diff_idx = 2; self._refresh_start_labels(); return

            if symbol in (key.UP, key.DOWN):
                self._start_view = "Global" if self._start_view == "Local" else "Local"
                self._refresh_start_labels(); return
            if symbol == key.L:
                self._start_view = "Local"; self._refresh_start_labels(); return
            if symbol == key.G:
                self._start_view = "Global"; self._refresh_start_labels(); return

            if symbol in (key.ENTER, key.RETURN):
                self._apply_start_selection_and_begin()
                return

            # allow preview zoom on start for fun (local only)
            if symbol in (key.EQUAL, key.NUM_ADD):
                self.zoom = min(MAX_ZOOM, self.zoom + ZOOM_STEP); return
            if symbol in (key.MINUS, key.NUM_SUBTRACT):
                self.zoom = max(MIN_ZOOM, self.zoom - ZOOM_STEP); return
            return

        # ----- IN-GAME CONTROLS -----
        if symbol in (key.EQUAL, key.NUM_ADD):
            if self.view_mode == "local":
                self.zoom = min(MAX_ZOOM, self.zoom + ZOOM_STEP)
            return
        if symbol in (key.MINUS, key.NUM_SUBTRACT):
            if self.view_mode == "local":
                self.zoom = max(MIN_ZOOM, self.zoom - ZOOM_STEP)
            return

        # Toggle view mode
        if symbol == key.G:
            self.view_mode = "global" if self.view_mode == "local" else "local"
            self.view_label.text = f"View: {self.view_mode.capitalize()}"
            return

        if symbol in (key.LEFT, key.A): self._move(-1, 0); return
        if symbol in (key.RIGHT, key.D): self._move( 1, 0); return
        if symbol in (key.UP, key.W): self._move( 0, 1); return
        if symbol in (key.DOWN, key.S): self._move( 0,-1); return

        # chat submit
        if symbol in (key.ENTER, key.RETURN):
            if getattr(self, "input_focus", False):
                msg = self.input_doc.text.strip()
                if msg:
                    self._append_chat_line(f"[YOU] {msg}")
                self.input_doc.text = ""
                if self.caret: self.caret.position = 0
            return

        # defocus chat
        if symbol == key.ESCAPE:
            self.input_focus = False
            if self.caret: self.caret.visible = False
            return

    def on_text(self, text_input):
        if getattr(self, "input_focus", False) and self.caret:
            self.caret.on_text(text_input)

    def on_text_motion(self, motion):
        if getattr(self, "input_focus", False) and self.caret:
            self.caret.on_text_motion(motion)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            if PLAY_W_PX+15 <= x <= PLAY_W_PX+15+SIDEBAR_W-30 and 35 <= y <= 35+34:
                self.input_focus = True
                if self.caret:
                    self.caret.visible = True
                    self.caret.on_mouse_press(x, y, button, modifiers)
            else:
                self.input_focus = False
                if self.caret: self.caret.visible = False

# =========================
# Run
# =========================
if __name__ == "__main__":
    game = Game()
    pyglet.app.run()
