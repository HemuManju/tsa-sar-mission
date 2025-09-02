# world.py
import random
from pyglet import shapes
from config import (
    PLAY_W, PLAY_H, CELL_SIZE, START,
    NUM_RED, NUM_PURPLE, NUM_YELLOW, DIFFICULTIES,
    COLOR_WALL, COLOR_RED, COLOR_PURPLE, COLOR_YELLOW, COLOR_RESCUE,
)

# Optional knobs/colors (fallbacks if missing)
try:    from config import COLOR_WALL_ORANGE
except: COLOR_WALL_ORANGE = (255, 165, 0)
try:    from config import WALL_CLEARANCE
except: WALL_CLEARANCE = 2                    # int
try:    from config import WALL_ORANGE_PCT
except: WALL_ORANGE_PCT = 0.20                # float 0..1
try:    from config import MULTI_WALL_PCT
except: MULTI_WALL_PCT = 0.30                 # float 0..1
try:    from config import MULTI_WALL_LAYERS
except: MULTI_WALL_LAYERS = (1, 3)            # (min_layers, max_layers)

# --- Type sanitizers so bad config values won't crash ---
def _as_float01(v, default):
    try:
        if isinstance(v, (tuple, list)): v = v[0]
        return max(0.0, min(1.0, float(v)))
    except Exception:
        return default
def _as_pair(v, default):
    try:
        if isinstance(v, int): return (max(0, v), max(0, v))
        if isinstance(v, (tuple, list)) and len(v) == 2:
            a, b = int(v[0]), int(v[1])
            if a > b: a, b = b, a
            return (max(0, a), max(0, b))
    except Exception:
        pass
    return default
WALL_ORANGE_PCT   = _as_float01(WALL_ORANGE_PCT, 0.20)
MULTI_WALL_PCT    = _as_float01(MULTI_WALL_PCT, 0.30)
MULTI_WALL_LAYERS = _as_pair(MULTI_WALL_LAYERS, (1, 3))

def victim_color(k): return COLOR_YELLOW if k=="yellow" else (COLOR_PURPLE if k=="purple" else COLOR_RED)
def _in(x,y): return 0<=x<PLAY_W and 0<=y<PLAY_H
def _buf(cells, r=WALL_CLEARANCE):
    out=set()
    for x,y in cells:
        for dx in range(-r,r+1):
            for dy in range(-r,r+1):
                nx,ny=x+dx,y+dy
                if _in(nx,ny): out.add((nx,ny))
    return out
def _comps(wset):
    vis, res = set(), []
    for c in wset:
        if c in vis: continue
        st=[c]; comp=set()
        while st:
            x,y=st.pop()
            if (x,y) in vis or (x,y) not in wset: continue
            vis.add((x,y)); comp.add((x,y))
            for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if (nx,ny) in wset and (nx,ny) not in vis: st.append((nx,ny))
        res.append(comp)
    return res

def generate_walls(diff: str):
    """Borders + random segments with clearance, then thicken ~MULTI_WALL_PCT components by MULTI_WALL_LAYERS."""
    cfg = DIFFICULTIES[diff]; rng = random.Random(cfg.get("seed", None))
    walls, reserved = set(), set()

    # 1) Borders (keep distance from edges)
    border={(x,0) for x in range(PLAY_W)}|{(x,PLAY_H-1) for x in range(PLAY_W)}|{(0,y) for y in range(PLAY_H)}|{(PLAY_W-1,y) for y in range(PLAY_H)}
    walls |= border; reserved |= _buf(border); reserved |= _buf({START}, max(2, WALL_CLEARANCE))

    # 2) Random segments honoring clearance
    segs=int(cfg.get("segments",120)); tries=segs*30; placed=0; dirs=[(1,0),(-1,0),(0,1),(0,-1)]
    while placed<segs and tries>0:
        tries-=1
        sx,sy=rng.randrange(1,PLAY_W-1),rng.randrange(1,PLAY_H-1)
        if (sx,sy) in reserved or (sx,sy)==START: continue
        dx,dy=rng.choice(dirs); length=rng.randint(3,8); prop=[]; x,y=sx,sy; ok=True
        for _ in range(length):
            if not _in(x,y) or (x,y)==START or (x,y) in reserved or (x,y) in walls: ok=False; break
            prop.append((x,y)); x+=dx; y+=dy
        if not ok or not prop or any(p in walls for p in _buf(prop)): continue
        walls.update(prop); reserved |= _buf(prop); placed += 1

    # 3) Thicken/connect a subset of components (2–4 cells thick)
    comps = _comps(walls)
    if comps:
        k = max(1, int(len(comps) * MULTI_WALL_PCT))
        targets = rng.sample(comps, k) if k <= len(comps) else comps
        for comp in targets:
            layers = rng.randint(MULTI_WALL_LAYERS[0], MULTI_WALL_LAYERS[1])
            for _ in range(layers):
                comp_buf = _buf(comp)         # allow growth inside own buffer
                ring=set()
                for x,y in comp:
                    for dx in (-1,0,1):
                        for dy in (-1,0,1):
                            if dx==dy==0: continue
                            nx,ny=x+dx,y+dy
                            if _in(nx,ny): ring.add((nx,ny))
                add={c for c in ring if c not in walls and c not in (reserved - comp_buf)}
                if not add: break
                walls.update(add); reserved |= _buf(add); comp.update(add)

    return walls

def place_victims(distmap, start):
    """Spread victims; bias some reds to harder/farther spots per quadrant."""
    rng=random.Random(99); victims={}
    midx,midy=PLAY_W//2,PLAY_H//2
    quad={"top_right":[], "top_left":[], "bottom_right":[], "bottom_left":[]}
    for p,_ in list(distmap.items()):
        if p==start: continue
        quad[("top_" if p[1]>=midy else "bottom_")+("left" if p[0]<midx else "right")].append(p)
    red=NUM_RED
    for q in quad.values():
        q.sort(key=lambda p: distmap.get(p,0), reverse=True)
        hard=q[:max(1,len(q)//3)]; n=max(0, red//4)
        for _ in range(n):
            if not hard: break
            p=rng.choice(hard); victims[p]="red"; hard.remove(p); distmap.pop(p,None)
    while sum(1 for v in victims.values() if v=="red")<NUM_RED and distmap:
        c=rng.choice(list(distmap.keys()))
        if c not in victims: victims[c]="red"; distmap.pop(c,None)
    rem=[p for p in list(distmap.keys()) if p not in victims and p!=start]; rng.shuffle(rem)
    p2,y2=NUM_PURPLE,NUM_YELLOW
    for p in rem:
        if p2>0: victims[p]="purple"; p2-=1
        elif y2>0: victims[p]="yellow"; y2-=1
        else: break
    return victims

def draw_world(play_batch, walls, victims):
    """Draw walls (whole-component orange) and victim circles."""
    comps = _comps(walls)
    orange=set()
    if comps:
        k=int(len(comps) * WALL_ORANGE_PCT)
        if k>0:
            for i in random.sample(range(len(comps)), k):
                orange.update(comps[i])
    wall_shapes=[shapes.Rectangle(x*CELL_SIZE,y*CELL_SIZE,CELL_SIZE,CELL_SIZE,
                                  color=(COLOR_WALL_ORANGE if (x,y) in orange else COLOR_WALL),
                                  batch=play_batch) for (x,y) in walls]
    victim_shapes={p:(shapes.Circle(p[0]*CELL_SIZE+CELL_SIZE/2,
                                    p[1]*CELL_SIZE+CELL_SIZE/2,
                                    CELL_SIZE/2-3,
                                    color=victim_color(t), batch=play_batch), t)
                   for p,t in victims.items()}
    return wall_shapes, victim_shapes

def make_rescue_triangle(play_batch, rescue_pos):
    if not rescue_pos: return None
    gx,gy = rescue_pos
    cx,cy = gx*CELL_SIZE+CELL_SIZE/2, gy*CELL_SIZE+CELL_SIZE/2
    s=CELL_SIZE*0.9; h=s*0.5
    return shapes.Triangle(cx,cy+h, cx-s/2,cy-h, cx+s/2,cy-h, color=COLOR_RESCUE, batch=play_batch)
