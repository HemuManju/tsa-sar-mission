# world.py
import random
from pyglet import shapes
from config import (PLAY_W, PLAY_H, CELL_SIZE, START, NUM_RED, NUM_PURPLE,
                    NUM_YELLOW, DIFFICULTIES, COLOR_WALL, COLOR_RED,
                    COLOR_PURPLE, COLOR_YELLOW, COLOR_RESCUE)
from helpers import line_h, line_v, clamp_grid

def victim_color(kind):
    return COLOR_YELLOW if kind == "yellow" else (COLOR_PURPLE if kind == "purple" else COLOR_RED)

def generate_walls(difficulty):
    cfg = DIFFICULTIES[difficulty]
    rng = random.Random(cfg["seed"])
    segments = cfg["segments"]
    walls = set()
    for x in range(PLAY_W):
        walls.add((x, 0)); walls.add((x, PLAY_H-1))
    for y in range(PLAY_H):
        walls.add((0, y)); walls.add((PLAY_W-1, y))

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

def place_victims(distmap, start):
    rng = random.Random(99)
    victims = {}
    mid_x, mid_y = PLAY_W // 2, PLAY_H // 2
    quads = {"top_right": [], "top_left": [], "bottom_right": [], "bottom_left": []}
    for pos, _d in distmap.items():
        if pos == start: continue
        qx = "left" if pos[0] < mid_x else "right"
        qy = "bottom" if pos[1] < mid_y else "top"
        quads[f"{qy}_{qx}"].append(pos)
    # bias reds to harder spots per quadrant
    red_to_place = NUM_RED
    for q in quads.values():
        q.sort(key=lambda p: distmap.get(p, 0), reverse=True)
        hard = q[:max(1, len(q)//3)]
        n = max(0, red_to_place // 4)
        for _ in range(n):
            if hard:
                p = rng.choice(hard)
                victims[p] = "red"
                hard.remove(p)
                distmap.pop(p, None)
    # remaining reds
    while sum(1 for k in victims.values() if k == "red") < NUM_RED and distmap:
        c = rng.choice(list(distmap.keys()))
        if c not in victims: victims[c] = "red"; distmap.pop(c, None)
    # purple/yellow
    rem = [p for p in distmap.keys() if p not in victims and p != start]
    rng.shuffle(rem)
    p2, y2 = NUM_PURPLE, NUM_YELLOW
    for p in rem:
        if p2 > 0: victims[p] = "purple"; p2 -= 1
        elif y2 > 0: victims[p] = "yellow"; y2 -= 1
        else: break
    return victims

def draw_world(play_batch, walls, victims):
    wall_shapes = []
    for (gx, gy) in walls:
        wall_shapes.append(shapes.Rectangle(
            gx*CELL_SIZE, gy*CELL_SIZE, CELL_SIZE, CELL_SIZE,
            color=COLOR_WALL, batch=play_batch))
    victim_shapes = {}
    for pos, kind in victims.items():
        gx, gy = pos
        victim_shapes[pos] = (shapes.Circle(
            gx*CELL_SIZE + CELL_SIZE/2, gy*CELL_SIZE + CELL_SIZE/2,
            CELL_SIZE/2 - 3, color=victim_color(kind), batch=play_batch), kind)
    return wall_shapes, victim_shapes

def make_rescue_triangle(play_batch, rescue_pos):
    if not rescue_pos: return None
    gx, gy = rescue_pos
    cx = gx*CELL_SIZE + CELL_SIZE/2
    cy = gy*CELL_SIZE + CELL_SIZE/2
    s = CELL_SIZE * 0.9; h = s * 0.5
    x1, y1 = cx, cy + h
    x2, y2 = cx - s/2, cy - h
    x3, y3 = cx + s/2, cy - h
    return shapes.Triangle(x1, y1, x2, y2, x3, y3,
                           color=COLOR_RESCUE, batch=play_batch)
