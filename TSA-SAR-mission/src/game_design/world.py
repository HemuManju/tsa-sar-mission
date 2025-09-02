# world.py
import random
from pyglet import shapes
from config import (
    # Grid & colors
    PLAY_W, PLAY_H, CELL_SIZE, START,
    COLOR_WALL, COLOR_RED, COLOR_PURPLE, COLOR_YELLOW, COLOR_RESCUE,
    COLOR_WALL_ORANGE,
    # Victims & difficulties
    NUM_RED, NUM_PURPLE, NUM_YELLOW, DIFFICULTIES,
    # Wall gen knobs (globals; can be overridden per difficulty)
    WALL_CLEARANCE, WALL_ORANGE_PCT, MULTI_WALL_PCT, MULTI_WALL_LAYERS,
    MULTI_WALL_GROW_PCT, MIN_PASSABLE_RATIO,
    # Red victim distribution knobs
    RED_SEP_CELLS, RED_FAR_QUANTILE, RED_SECTORS_X, RED_SECTORS_Y,
    # Segment controls
    WALL_SEGMENT_LEN, WALL_ATTEMPTS_PER_SEG,
)

# --- small helpers ---
def victim_color(k): return COLOR_YELLOW if k == "yellow" else (COLOR_PURPLE if k == "purple" else COLOR_RED)
def _in(x, y): return 0 <= x < PLAY_W and 0 <= y < PLAY_H
def _border_cells():
    return {(x, 0) for x in range(PLAY_W)} | {(x, PLAY_H-1) for x in range(PLAY_W)} | \
           {(0, y) for y in range(PLAY_H)} | {(PLAY_W-1, y) for y in range(PLAY_H)}
def _buf(cells, r=WALL_CLEARANCE):
    out = set()
    for x, y in cells:
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                nx, ny = x + dx, y + dy
                if _in(nx, ny): out.add((nx, ny))
    return out
def _comps(wset):
    vis, comps = set(), []
    for c in wset:
        if c in vis: continue
        st = [c]; comp = set()
        while st:
            x, y = st.pop()
            if (x, y) in vis or (x, y) not in wset: continue
            vis.add((x, y)); comp.add((x, y))
            for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if (nx, ny) in wset and (nx, ny) not in vis: st.append((nx, ny))
        comps.append(comp)
    return comps

# --- wall generation ---
def generate_walls(difficulty: str):
    """
    Borders (kept gray) + random segments with clearance; slim thickening (4-neighbor rim);
    coverage cap so each mode remains playable. Uses per-difficulty overrides if present.
    """
    cfg = DIFFICULTIES[difficulty]
    rng = random.Random(cfg.get("seed", None))

    # allow per-difficulty overrides (fallback to global config knobs)
    min_passable = float(cfg.get("min_passable_ratio", MIN_PASSABLE_RATIO))
    multi_pct    = float(cfg.get("multi_wall_pct",   MULTI_WALL_PCT))
    layers_min, layers_max = tuple(cfg.get("layers", MULTI_WALL_LAYERS))
    grow_pct     = float(cfg.get("grow_pct",         MULTI_WALL_GROW_PCT))

    walls, reserved = set(), set()
    total = PLAY_W * PLAY_H
    max_walls = int(total * (1.0 - min_passable))
    def can_add(n): return len(walls) + n <= max_walls

    # 1) perimeter (kept gray forever)
    border = _border_cells()
    walls |= border
    reserved |= _buf(border)
    reserved |= _buf({START}, max(2, WALL_CLEARANCE))

    # 2) random segments with clearance + budget
    segs = int(cfg.get("segments", 120))
    attempts = segs * int(WALL_ATTEMPTS_PER_SEG)
    placed = 0
    dirs = [(1,0), (-1,0), (0,1), (0,-1)]
    min_len, max_len = WALL_SEGMENT_LEN

    while placed < segs and attempts > 0 and len(walls) < max_walls:
        attempts -= 1
        sx, sy = rng.randrange(1, PLAY_W-1), rng.randrange(1, PLAY_H-1)
        if (sx, sy) in reserved or (sx, sy) == START: continue
        dx, dy = rng.choice(dirs)
        length = rng.randint(int(min_len), int(max_len))

        prop = []
        x, y = sx, sy
        ok = True
        for _ in range(length):
            if not _in(x, y) or (x, y) == START or (x, y) in reserved or (x, y) in walls:
                ok = False; break
            prop.append((x, y)); x += dx; y += dy
        if not ok or not prop or any(p in walls for p in _buf(prop)): continue

        if not can_add(len(prop)):
            need = max(0, max_walls - len(walls))
            if need == 0: break
            prop = prop[:need]

        walls.update(prop)
        reserved |= _buf(prop)
        placed += 1

    # 3) slim thickening: 4-neighbor rim, grow only a fraction each layer
    comps = _comps(walls)
    if comps:
        k = max(1, int(len(comps) * multi_pct))
        for comp in rng.sample(comps, min(k, len(comps))):
            layers = random.randint(int(layers_min), int(layers_max))
            for _ in range(layers):
                if len(walls) >= max_walls: break
                comp_buf = _buf(comp)  # allow growth inside own buffer
                rim = set()
                for x, y in comp:
                    for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                        if _in(nx,ny): rim.add((nx,ny))
                elig = [c for c in rim if c not in walls and c not in (reserved - comp_buf)]
                if not elig: break
                take = max(1, int(len(elig) * grow_pct))
                rng.shuffle(elig)
                add = set(elig[:take])
                if not can_add(len(add)):
                    need = max(0, max_walls - len(walls))
                    if need <= 0: break
                    add = set(list(add)[:need])
                if not add: break
                walls.update(add); reserved |= _buf(add); comp.update(add)

    return walls

# --- victim placement (reds: far, spaced, sector-balanced) ---
def place_victims(distmap, start, all_passable=None):
    """
    Reds come from farthest quantile, balanced across RED_SECTORS_X × RED_SECTORS_Y sectors,
    with Chebyshev spacing >= RED_SEP_CELLS (relaxes if map is tight).
    Purples/Yellows fill the remaining slots.
    """
    rng = random.Random(99)
    victims = {}

    # pool: reachable first, then any passable (for tight Hard maps)
    pool = [p for p in distmap.keys() if p != start]
    if all_passable is not None:
        extras = list((all_passable - set(pool)) - {start})
        rng.shuffle(extras); pool += extras
    if not pool: return victims

    # distance scores (unreachable -> 0)
    scored = [(p, distmap.get(p, 0)) for p in pool]
    scored.sort(key=lambda t: t[1])
    q_idx = int(len(scored) * float(RED_FAR_QUANTILE))
    cutoff = scored[q_idx][1] if 0 <= q_idx < len(scored) else 0
    far = [p for (p, d) in scored if d >= cutoff]
    far.sort(key=lambda p: distmap.get(p, 0), reverse=True)

    # sectoring
    SX, SY = int(RED_SECTORS_X), int(RED_SECTORS_Y)
    def sector_of(p):
        sx = min(SX-1, (p[0] * SX) // max(1, PLAY_W))
        sy = min(SY-1, (p[1] * SY) // max(1, PLAY_H))
        return (int(sx), int(sy))
    buckets = {}
    for p in far:
        buckets.setdefault(sector_of(p), []).append(p)
    for lst in buckets.values():
        lst.sort(key=lambda p: distmap.get(p, 0), reverse=True)

    # greedy round-robin with global spacing
    def cheby(a,b): return max(abs(a[0]-b[0]), abs(a[1]-b[1]))
    reds, sep = [], int(RED_SEP_CELLS)
    order = list(buckets.keys()) or [(0,0)]
    while len(reds) < NUM_RED and sep >= 2:
        placed = False
        for s in order:
            if len(reds) >= NUM_RED: break
            lst = buckets.get(s, [])
            while lst:
                p = lst[0]
                if all(cheby(p,q) >= sep for q in reds):
                    reds.append(p); lst.pop(0); placed = True; break
                else:
                    lst.pop(0)
        if not placed: sep -= 1  # relax if stuck

    # top up if still short
    if len(reds) < NUM_RED:
        remaining = [p for p in far if p not in reds] + [p for p,_ in scored if p not in reds]
        for p in remaining:
            if len(reds) >= NUM_RED: break
            if all(cheby(p,q) >= 2 for q in reds): reds.append(p)

    for p in reds[:NUM_RED]: victims[p] = "red"

    # others
    rest = [p for p in pool if p not in victims and p != start]
    rng.shuffle(rest)
    p2, y2 = NUM_PURPLE, NUM_YELLOW
    for p in rest:
        if p2 > 0: victims[p] = "purple"; p2 -= 1
        elif y2 > 0: victims[p] = "yellow"; y2 -= 1
        if p2 == 0 and y2 == 0: break

    return victims

# --- drawing ---
def draw_world(play_batch, walls, victims):
    """Walls (component-orange except perimeter) + victim circles."""
    comps = _comps(walls)
    orange = set()
    if comps:
        k = int(len(comps) * float(WALL_ORANGE_PCT))
        if k > 0:
            for i in random.sample(range(len(comps)), k):
                orange.update(comps[i])
    orange -= _border_cells()  # keep frame gray

    wall_shapes = [shapes.Rectangle(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE,
                                    color=(COLOR_WALL_ORANGE if (x,y) in orange else COLOR_WALL),
                                    batch=play_batch) for (x,y) in walls]
    victim_shapes = {
        p: (shapes.Circle(p[0]*CELL_SIZE + CELL_SIZE/2,
                          p[1]*CELL_SIZE + CELL_SIZE/2,
                          CELL_SIZE/2 - 3,
                          color=victim_color(t), batch=play_batch), t)
        for p, t in victims.items()
    }
    return wall_shapes, victim_shapes

def make_rescue_triangle(play_batch, rescue_pos):
    if not rescue_pos: return None
    gx, gy = rescue_pos
    cx, cy = gx*CELL_SIZE + CELL_SIZE/2, gy*CELL_SIZE + CELL_SIZE/2
    s = CELL_SIZE * 0.9; h = s * 0.5
    return shapes.Triangle(cx, cy + h, cx - s/2, cy - h, cx + s/2, cy - h,
                           color=COLOR_RESCUE, batch=play_batch)
