# game.py
import pyglet
from pyglet import shapes, text
from config import *
from camera import set_play_projection, reset_ui_projection
from grid import build_grid_lines
from hud import build_hud
from chatui import build_chat
from helpers import bfs_distances
from world import generate_walls, place_victims, draw_world, make_rescue_triangle, victim_color
from update import tick, second
from controls import key_press, mouse_press
import random


class Game:
    def __init__(self):
        self.window = make_window(); self.window.push_handlers(self)
        self.PLAY_W, self.PLAY_H = PLAY_W, PLAY_H
        self.play_batch = pyglet.graphics.Batch(); self.ui_batch = pyglet.graphics.Batch()
        self.state, self.zoom, self.view_mode = "start", 1.0, "local"
        self.time_remaining, self.game_over = TIME_LIMIT, False
        self.player = [*START]
        self.rescue_positions, self.rescue_shapes = [], []
        self.rescue_reached = False
        self.carried, self.carried_shapes = [], []
        self.grid_lines = build_grid_lines(self.play_batch)
        self.wall_shapes, self.victim_shapes = [], {}
        self.player_shape = shapes.Rectangle(
            0, 0, CELL_SIZE, CELL_SIZE,
            color=COLOR_PLAYER, batch=self.play_batch
        )
        self.hud = build_hud(self.ui_batch)
        self.hud["status"].text = "Press ENTER on Start screen to begin"
        self.start_diffs, self.start_diff_idx, self.start_view = ["Easy","Medium","Hard"], 0, "Local"
        self.start_title = text.Label(
            "Mission Setup", x=PLAY_W_PX//2, y=WINDOW_HEIGHT//2+80,
            anchor_x="center", color=COLOR_TEXT, font_size=28, bold=True
        )
        self.start_diff_label = text.Label(
            "", x=PLAY_W_PX//2, y=WINDOW_HEIGHT//2+30,
            anchor_x="center", color=COLOR_TEXT, font_size=18
        )
        self.start_view_label = text.Label(
            "", x=PLAY_W_PX//2, y=WINDOW_HEIGHT//2-10,
            anchor_x="center", color=COLOR_TEXT, font_size=18
        )
        self.start_hint = text.Label(
            "Use arrows / 1-2-3 / L-G • Press ENTER to start",
            x=PLAY_W_PX//2, y=WINDOW_HEIGHT//2-60,
            anchor_x="center", color=COLOR_TEXT, font_size=12
        )
        self.refresh_start_labels()
        self.chat = build_chat(self.ui_batch)
        pyglet.clock.schedule_interval(lambda dt: tick(self,dt), 1/60.0)
        pyglet.clock.schedule_interval(lambda dt: second(self,dt), 1.0)

    def get_matrix(self):
        # Start with all free cells = 1
        matrix = [[1 for _ in range(self.PLAY_W)] for _ in range(self.PLAY_H)]

        # Walls = 0
        for (x, y) in self.walls:
            matrix[y][x] = 0

        # Victims
        for (x, y), kind in self.victims.items():
            if kind == "red":
                matrix[y][x] = 2
            elif kind == "purple":
                matrix[y][x] = 3
            elif kind == "yellow":
                matrix[y][x] = 4

        # Player start (optional marker = 9)
        px, py = START
        matrix[py][px] = 9

        return matrix


    def refresh_start_labels(self):
        d = self.start_diffs[self.start_diff_idx]
        self.start_diff_label.text = f"Difficulty:  {d}"
        self.start_view_label.text = f"View:        {self.start_view}"

    def apply_start_and_begin(self):
        self.difficulty = self.start_diffs[self.start_diff_idx]
        self.view_mode = self.start_view.lower()
        self.hud["labels"]["view"].text = f"View: {self.start_view}"
        self.rebuild_world(); self.state = "playing"
        self.hud["status"].text = ""; self.hud["labels"]["difficulty"].text = ""

    def _clear_rescue_visuals(self):
        for t in self.rescue_shapes:
            try: t.delete()
            except: pass
        self.rescue_shapes = []

    def _clear_carried_visuals(self):
        for c in self.carried_shapes:
            try: c.delete()
            except: pass
        self.carried_shapes = []

    def rebuild_world(self):
        for r,*_ in self.wall_shapes: r.delete()
        for (c,_k) in self.victim_shapes.values(): c.delete()
        self.wall_shapes.clear(); self.victim_shapes.clear()
        self._clear_rescue_visuals(); self._clear_carried_visuals()
        self.carried = []; self.hud["labels"]["carried"].text = "Carrying: 0/2"

        self.walls = generate_walls(self.difficulty)
        self.passable = {(x,y) for x in range(PLAY_W) for y in range(PLAY_H)} - self.walls
        self.passable.add(START)
        distmap = bfs_distances(START, self.passable)  # still used by place_victims
        self.victims = place_victims(distmap, START, self.passable)

        # --- fixed-region rescue points: up-left, middle, down-left ---
        def nearest_valid(anchor, forbidden):
            ax, ay = anchor; best=None; bestd=10**9
            for (x,y) in self.passable:
                if (x,y) in forbidden: continue
                d = abs(x-ax)+abs(y-ay)
                if d < bestd: bestd, best = d, (x,y)
            return best or START
        
        # anchors = [(1, PLAY_H-2), (PLAY_W//2, PLAY_H//2), (PLAY_W-2, 1)]

        num_rescue_points = 3
        anchors = random.sample(list(self.passable - {START}), num_rescue_points)

        forbidden = set(self.victims.keys()) | {START}
        picks = []
        for a in anchors:
            p = nearest_valid(a, forbidden | set(picks)); picks.append(p)
        self.rescue_positions, self.rescue_reached = picks, False

        self.wall_shapes, self.victim_shapes = draw_world(self.play_batch, self.walls, self.victims)
        self.player = [*START]; self.player_shape.x = self.player[0]*CELL_SIZE; self.player_shape.y = self.player[1]*CELL_SIZE
        for rp in self.rescue_positions:
            tri = make_rescue_triangle(self.play_batch, rp)
            if tri: self.rescue_shapes.append(tri)
        try:
            self.hud["labels"]["rescue"].text = "Rescue: " + " | ".join(f"{x},{y}" for x,y in self.rescue_positions[:3])
        except: pass
        self.time_remaining = TIME_LIMIT

    def add_carried(self, kind):
        if len(self.carried)>=3: return False
        self.carried.append(kind); self._sync_carried_sprites()
        self.hud["labels"]["carried"].text = f"Carrying: {len(self.carried)}/3"
        return True

    def drop_all_carried(self):
        self.carried.clear(); self._sync_carried_sprites()
        self.hud["labels"]["carried"].text = "Carrying: 0/3"

    def _sync_carried_sprites(self):
        while len(self.carried_shapes)>len(self.carried):
            s=self.carried_shapes.pop()
            try: s.delete()
            except: pass
        while len(self.carried_shapes)<len(self.carried):
            self.carried_shapes.append(shapes.Circle(0,0,CELL_SIZE*0.22,color=(255,255,255),batch=self.play_batch))
        offs=[(-5,6),(5,6),(0,-6)]
        for i,s in enumerate(self.carried_shapes):
            s.color = victim_color(self.carried[i])
            s.x = self.player_shape.x + CELL_SIZE/2 + offs[i][0]
            s.y = self.player_shape.y + CELL_SIZE/2 + offs[i][1]

    def update_carried_position(self):
        offs=[(-5,6),(5,6),(0,-6)]
        for i,s in enumerate(self.carried_shapes):
            s.x = self.player_shape.x + CELL_SIZE/2 + offs[i][0]
            s.y = self.player_shape.y + CELL_SIZE/2 + offs[i][1]

    def on_draw(self):
        self.window.clear()
        pyglet.gl.glClearColor(COLOR_BG[0]/255.0, COLOR_BG[1]/255.0, COLOR_BG[2]/255.0, 1.0)
        self.view_range = set_play_projection(self.window, self.player, self.view_mode, self.zoom)
        self.play_batch.draw(); reset_ui_projection(self.window); self.ui_batch.draw()
        if self.state=="start":
            self.start_title.draw(); self.start_diff_label.draw(); self.start_view_label.draw(); self.start_hint.draw()



    def on_key_press(self, symbol, modifiers): key_press(self, symbol, modifiers)
    def on_mouse_press(self, x, y, button, modifiers): mouse_press(self, x, y, button, modifiers)
    def on_text(self, s):
        if self.chat["focus"] and self.chat["caret"]: self.chat["caret"].on_text(s)
    def on_text_motion(self, m):
        if self.chat["focus"] and self.chat["caret"]: self.chat["caret"].on_text_motion(m)
