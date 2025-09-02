# game.py
import pyglet
from pyglet import shapes, text
from config import *
from camera import set_play_projection, reset_ui_projection
from grid import build_grid_lines
from hud import build_hud
from chatui import build_chat
from helpers import bfs_distances
from world import (generate_walls, place_victims, draw_world,
                   make_rescue_triangle, victim_color)
from update import tick, second
from controls import key_press, mouse_press

class Game:
    def __init__(self):
        self.window = make_window()
        self.window.push_handlers(self)
        self.PLAY_W, self.PLAY_H = PLAY_W, PLAY_H

        self.play_batch = pyglet.graphics.Batch()
        self.ui_batch = pyglet.graphics.Batch()

        self.state = "start"
        self.zoom = 1.0
        self.view_mode = "local"
        self.time_remaining = TIME_LIMIT
        self.game_over = False
        self.player = [*START]
        self.rescue_pos = None
        self.rescue_reached = False

        self.carried = None
        self.carried_shape = None

        self.grid_lines = build_grid_lines(self.play_batch)
        self.wall_shapes = []
        self.victim_shapes = {}
        self.player_shape = shapes.Rectangle(0, 0, CELL_SIZE, CELL_SIZE,
                                             color=COLOR_PLAYER, batch=self.play_batch)
        self.rescue_triangle = None

        self.hud = build_hud(self.ui_batch)
        self.hud["status"].text = "Press ENTER on Start screen to begin"

        self.start_diffs = ["Easy", "Medium", "Hard"]
        self.start_diff_idx = 0
        self.start_view = "Local"
        self.start_title = text.Label("Mission Setup",
            x=PLAY_W_PX//2, y=WINDOW_HEIGHT//2 + 80,
            anchor_x='center', color=COLOR_TEXT, font_size=28, bold=True)
        self.start_diff_label = text.Label("", x=PLAY_W_PX//2,
            y=WINDOW_HEIGHT//2 + 30, anchor_x='center',
            color=COLOR_TEXT, font_size=18)
        self.start_view_label = text.Label("", x=PLAY_W_PX//2,
            y=WINDOW_HEIGHT//2 - 10, anchor_x='center',
            color=COLOR_TEXT, font_size=18)
        self.start_hint = text.Label("Use arrows / 1-2-3 / L-G • Press ENTER to start",
            x=PLAY_W_PX//2, y=WINDOW_HEIGHT//2 - 60, anchor_x='center',
            color=COLOR_TEXT, font_size=12)
        self.refresh_start_labels()

        self.chat = build_chat(self.ui_batch)

        pyglet.clock.schedule_interval(lambda dt: tick(self, dt), 1/60.0)
        pyglet.clock.schedule_interval(lambda dt: second(self, dt), 1.0)

    # ----- start helpers -----
    def refresh_start_labels(self):
        d = self.start_diffs[self.start_diff_idx]
        self.start_diff_label.text = f"Difficulty:  {d}"
        self.start_view_label.text = f"View:        {self.start_view}"

    def apply_start_and_begin(self):
        self.difficulty = self.start_diffs[self.start_diff_idx]
        self.view_mode = self.start_view.lower()
        self.hud["labels"]["view"].text = f"View: {self.start_view}"
        self.rebuild_world()
        self.state = "playing"
        self.hud["status"].text = ""
        self.hud["labels"]["difficulty"].text = ""

    # ----- world build -----
    def rebuild_world(self):
        for r, *_ in self.wall_shapes: r.delete()
        for (c, _k) in self.victim_shapes.values(): c.delete()
        self.wall_shapes.clear(); self.victim_shapes.clear()
        if self.rescue_triangle: self.rescue_triangle.delete(); self.rescue_triangle = None
        if self.carried_shape: self.carried_shape.delete(); self.carried_shape = None
        self.carried = None
        self.hud["labels"]["carried"].text = "Carrying: —"

        self.walls = generate_walls(self.difficulty)
        self.passable = {(x,y) for x in range(PLAY_W) for y in range(PLAY_H)} - self.walls
        self.passable.add(START)

        distmap = bfs_distances(START, self.passable)
        self.victims = place_victims(distmap, START)

        if distmap:
            far = sorted(distmap.items(), key=lambda kv: kv[1], reverse=True)
            chosen = next((p for p,_ in far if p not in self.victims and p != START), far[0][0])
            self.rescue_pos = chosen
        else:
            self.rescue_pos = START
        self.rescue_reached = False

        self.wall_shapes, self.victim_shapes = draw_world(self.play_batch, self.walls, self.victims)
        self.player = [*START]
        self.player_shape.x = self.player[0]*CELL_SIZE
        self.player_shape.y = self.player[1]*CELL_SIZE
        self.rescue_triangle = make_rescue_triangle(self.play_batch, self.rescue_pos)
        self.time_remaining = TIME_LIMIT

    # ----- carry helpers -----
    def set_carried(self, kind):
        self.carried = kind
        cx = self.player_shape.x + CELL_SIZE/2
        cy = self.player_shape.y + CELL_SIZE/2
        if self.carried_shape is None:
            from pyglet import shapes
            self.carried_shape = shapes.Circle(cx, cy, CELL_SIZE*0.35,
                                               color=victim_color(kind), batch=self.play_batch)
        else:
            self.carried_shape.color = victim_color(kind)
            self.carried_shape.x, self.carried_shape.y = cx, cy
            self.carried_shape.radius = CELL_SIZE*0.35
        self.hud["labels"]["carried"].text = f"Carrying: {kind}"

    def update_carried_position(self):
        if self.carried_shape:
            self.carried_shape.x = self.player_shape.x + CELL_SIZE/2
            self.carried_shape.y = self.player_shape.y + CELL_SIZE/2

    # ----- events -----
    def on_draw(self):
        self.window.clear()
        pyglet.gl.glClearColor(COLOR_BG[0]/255.0, COLOR_BG[1]/255.0, COLOR_BG[2]/255.0, 1.0)
        self.view_range = set_play_projection(self.window, self.player, self.view_mode, self.zoom)
        self.play_batch.draw()
        reset_ui_projection(self.window)
        self.ui_batch.draw()
        if self.state == "start":
            self.start_title.draw(); self.start_diff_label.draw()
            self.start_view_label.draw(); self.start_hint.draw()

    def on_key_press(self, symbol, modifiers): key_press(self, symbol, modifiers)
    def on_mouse_press(self, x, y, button, modifiers): mouse_press(self, x, y, button, modifiers)
    def on_text(self, s):
        if self.chat["focus"] and self.chat["caret"]: self.chat["caret"].on_text(s)
    def on_text_motion(self, m):
        if self.chat["focus"] and self.chat["caret"]: self.chat["caret"].on_text_motion(m)
