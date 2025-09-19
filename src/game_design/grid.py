# grid.py
from pyglet import shapes
from config import CELL_SIZE, PLAY_W, PLAY_H, COLOR_GRID

"""def build_grid_lines(batch):
    lines = []
    world_w = PLAY_W * CELL_SIZE
    world_h = PLAY_H * CELL_SIZE
    for gx in range(1, PLAY_W):
        x = gx * CELL_SIZE
        lines.append(shapes.Line(x, 0, x, world_h, width=1,
                                 color=COLOR_GRID, batch=batch))
    for gy in range(1, PLAY_H):
        y = gy * CELL_SIZE
        lines.append(shapes.Line(0, y, world_w, y, width=1,
                                 color=COLOR_GRID, batch=batch))
    return lines"""


def build_grid_lines(batch):
    lines = []
    world_w = PLAY_W * CELL_SIZE
    world_h = PLAY_H * CELL_SIZE
    for gx in range(1, PLAY_W):
        x = gx * CELL_SIZE
        lines.append(shapes.Line(x, 0, x, world_h, color=COLOR_GRID, batch=batch))
    for gy in range(1, PLAY_H):
        y = gy * CELL_SIZE
        lines.append(shapes.Line(0, y, world_w, y, color=COLOR_GRID, batch=batch))
    return lines
