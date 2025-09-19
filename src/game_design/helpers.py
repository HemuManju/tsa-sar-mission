# helpers.py
from collections import deque
from config import PLAY_W, PLAY_H


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


def bfs_distances(start, passable):
    q = deque([start])
    dist = {start: 0}
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (
                0 <= nx < PLAY_W
                and 0 <= ny < PLAY_H
                and (nx, ny) in passable
                and (nx, ny) not in dist
            ):
                dist[(nx, ny)] = dist[(x, y)] + 1
                q.append((nx, ny))
    return dist


"......collection...."


def helpers():
    return {
        "line_h": line_h,
        "line_v": line_v,
        "clamp_grid": clamp_grid,
        "bfs_distances": bfs_distances,
    }
