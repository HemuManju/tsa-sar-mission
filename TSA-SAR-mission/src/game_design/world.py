# world.py
import random
from pyglet import shapes
from config import (
    PLAY_W, PLAY_H, CELL_SIZE, START,
    NUM_RED, NUM_PURPLE, NUM_YELLOW, DIFFICULTIES,
    COLOR_WALL, COLOR_RED, COLOR_PURPLE, COLOR_YELLOW, COLOR_RESCUE,
)

# Optional knobs/colors with safe fallbacks
try:    from config import COLOR_WALL_ORANGE
except: COLOR_WALL_ORANGE = (255, 165, 0)
try:    from config import WALL_CLEARANCE
except: WALL_CLEARANCE = 2
try:    from config import WALL_ORANGE_PCT
except: WALL_ORANGE_PCT = 0.20
try:    from config import MULTI_WALL_PCT
except: MULTI_WALL_PCT = 0.15
try:    from config import MULTI_WALL_LAYERS
except: MULTI_WALL_LAYERS = (1, 2)
try:    from config import MULTI_WALL_GROW_PCT
except: MULTI_WALL_GROW_PCT = 0.25
try:    from config import MIN_PASSABLE_RATIO
except: MIN_PASSABLE_RATIO = 0.50

# --- helpers / sanitizers ---
def _f01(v, d):
    try:
        if isinstance(v, (tuple, list)): v = v[0]
        return max(0.0, min(1.0, float(v)))
    except: return d
def _pair(v, d):
    try:
        if isinstance(v, int): return (max(0, v), max(0, v))
        if isinstance(v, (tuple, list)) and len(v) == 2:
            a, b = int(v[0]), int(v[1])
            return (min(a, b), max(a, b))
    except: pass
    return d

WALL_ORANGE_PCT     = _f01(WALL_ORANGE_PCT, 0.20)
MULTI_WALL_PCT      = _f01(MULTI_WALL_PCT, 0.15)
MULTI_WALL_GROW_PCT = _f01(MULTI_WALL_GROW_PCT, 0.25)
MULTI_WALL_LAYERS   = _pair(MULTI_WALL_LAYERS, (1, 2))

def victim_color(k): return COLOR_YELLOW if k == "yellow" else (COLOR_PURPLE if k == "purple" else COLOR_RED)
def _in(x, y): return 0 <= x < PLAY_W and 0 <= y < PLAY_H
def _buf(cells, r=WALL_CLEARANCE):
    out = set()
    for x, y in cells:
        for dx in range(-r, r+1):
            for dy in range(-r, r+1):
                nx, ny = x+dx, y+dy
                if _in(nx, ny): out.add((nx, ny))
    return out
def _comps(wset):
    vis, res = set(), []
    for c in wset:
        if c in vis: continue
        st = [c]; comp = set()
        while st:
            x, y = st.pop()
            if (x, y) in vis or (x, y) not in wset: continue
            vis.add((x, y)); comp.add((x, y))
            for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if (nx, ny) in wset and (nx, ny) not in vis: st.append((nx, ny))
        res.append(comp)
    return res
def _border():
    return {(x,0) for x in range(PLAY_W)} | {(x,PLAY_H-1) for x in range(PLAY_W)} | \
           {(0,y) for y in range(PLAY_H)} | {(PLAY_W-1,y) for y in range(PLAY_H)}

def generate_walls(difficulty: str):
    """Borders + random segments (clearance), slim thickening; per-difficulty overrides applied."""
    cfg = DIFFICULTIES[difficulty]
    rng = random.Random(cfg.get("seed", None))

    # per-difficulty overrides (fallback to global defaults)
    min_passable = float(cfg.get("min_passable_ratio", MIN_PASSABLE_RATIO))
    multi_pct    = _f01(cfg.get("multi_wall_pct", MULTI_WALL_PCT), MULTI_WALL_PCT)
    layers_cfg   = _pair(cfg.get("layers", MULTI_WALL_LAYERS), MULTI_WALL_LAYERS)
    layers_min, layers_max = layers_cfg

    total = PLAY_W * PLAY_H
    max_walls = int(total * (1.0 - min_passable))
    def can_add(n): return (len(walls) + n) <= max_walls

    walls, reserved = set(), set()

    # 1) Borders (kept gray; also reserve clearance)
    border = _border()
    walls |= border
    reserved |= _buf(border)
    reserved |= _buf({START}, max(2, WALL_CLEARANCE))

    # 2) Random segments with clearance & coverage cap
    segs = int(cfg.get("segments", 120))
    tries, placed = segs * 30, 0
    dirs = [(1,0), (-1,0), (0,1), (0,-1)]
    while placed < segs and tries > 0 and len(walls) < max_walls:
        tries -= 1
        sx, sy = rng.randrange(1, PLAY_W-1), rng.randrange(1, PLAY_H-1)
        if (sx, sy) in reserved or (sx, sy) == START: continue
        dx, dy = rng.choice(dirs); length = rng.randint(3, 8)
        prop = []; x, y = sx, sy; ok = True
        for _ in range(length):
            if not _in(x, y) or (x, y) == START or (x, y) in reserved or (x, y) in walls:
                ok = False; break
            prop.append((x, y)); x += dx; y += dy
        if not ok or not prop or any(p in walls for p in _buf(prop)): continue
        if not can_add(len(prop)):
            need = max(0, max_walls - len(walls))
            if need == 0: break
            prop = prop[:need]
        walls.update(prop); reserved |= _buf(prop); placed += 1

    # 3) Slim thickening: pick ~multi_pct components, grow by layers (4-neighbor rim, sampled)
    comps = _comps(walls)
    if comps:
        k = max(1, int(len(comps) * multi_pct))
        targets = rng.sample(comps, min(k, len(comps)))
        for comp in targets:
            layers = rng.randint(layers_min, layers_max)
            for _ in range(layers):
                if len(walls) >= max_walls: break
                comp_buf = _buf(comp)  # allow growth inside own buffer
                rim = set()
                for x, y in comp:
                    for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):  # 4-neighbor => slimmer
                        if _in(nx, ny): rim.add((nx, ny))
                elig = [c for c in rim if c not in walls and c not in (reserved - comp_buf)]
                if not elig: break
                take = max(1, int(len(elig) * MULTI_WALL_GROW_PCT))
                rng.shuffle(elig)
                add = set(elig[:take])
                if not can_add(len(add)):
                    need = max(0, max_walls - len(walls))
                    if need <= 0: break
                    add = set(list(add)[:need])
                if not add: break
                walls.update(add); reserved |= _buf(add); comp.update(add)

    return walls

def place_victims(distmap, start, all_passable=None):
    """
    Place victims using BFS distances when available; if the reachable set is
    too small, fall back to all passable cells so victims always appear.
    """
    rng = random.Random(99)
    victims = {}

    pool = [p for p in distmap.keys() if p != start]
    if all_passable is not None:
        extras = list((all_passable - set(pool)) - {start})
        rng.shuffle(extras); pool += extras
    if not pool: return victims

    mid_x, mid_y = PLAY_W // 2, PLAY_H // 2
    quads = {"top_right": [], "top_left": [], "bottom_right": [], "bottom_left": []}
    for p in pool:
        qx = "left" if p[0] < mid_x else "right"
        qy = "bottom" if p[1] < mid_y else "top"
        quads[f"{qy}_{qx}"].append(p)

    keydist = lambda p: distmap.get(p, 0)
    for q in quads.values(): q.sort(key=keydist, reverse=True)

    reds_left = NUM_RED; per_q = max(0, NUM_RED // 4)
    for q in quads.values():
        take = min(per_q, len(q), reds_left)
        for _ in range(take):
            victims[q.pop(0)] = "red"; reds_left -= 1
    if reds_left > 0:
        rest = sorted([p for p in pool if p not in victims], key=keydist, reverse=True)
        for p in rest[:reds_left]: victims[p] = "red"

    remaining = [p for p in pool if p not in victims]; rng.shuffle(remaining)
    p2, y2 = NUM_PURPLE, NUM_YELLOW
    for p in remaining:
        if p2 > 0: victims[p] = "purple"; p2 -= 1
        elif y2 > 0: victims[p] = "yellow"; y2 -= 1
        if p2 == 0 and y2 == 0: break
    return victims

def draw_world(play_batch, walls, victims):
    """Draw walls (whole-component orange except border) and victim circles."""
    comps = _comps(walls)
    orange = set()
    if comps:
        k = int(len(comps) * WALL_ORANGE_PCT)
        if k > 0:
            for i in random.sample(range(len(comps)), k):
                orange.update(comps[i])
    # keep border gray
    orange -= _border()

    wall_shapes = [
        shapes.Rectangle(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE,
                         color=(COLOR_WALL_ORANGE if (x,y) in orange else COLOR_WALL),
                         batch=play_batch)
        for (x, y) in walls
    ]
    victim_shapes = {
        p: (shapes.Circle(p[0]*CELL_SIZE + CELL_SIZE/2,
                          p[1]*CELL_SIZE + CELL_SIZE/2,
                          CELL_SIZE/2 - 3, color=victim_color(t), batch=play_batch), t)
        for p, t in victims.items()
    }
    return wall_shapes, victim_shapes

def make_rescue_triangle(play_batch, rescue_pos):
    if not rescue_pos: return None
    gx, gy = rescue_pos
    cx, cy = gx*CELL_SIZE + CELL_SIZE/2, gy*CELL_SIZE + CELL_SIZE/2
    s = CELL_SIZE * 0.9; h = s * 0.5
    return shapes.Triangle(cx, cy+h, cx - s/2, cy - h, cx + s/2, cy - h,
                           color=COLOR_RESCUE, batch=play_batch)
