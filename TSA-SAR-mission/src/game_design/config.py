# config.py
import pyglet

# Window & grid
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 800
CELL_SIZE = 20
SIDEBAR_W = 360
PLAY_W_PX = WINDOW_WIDTH - SIDEBAR_W

GRID_W = WINDOW_WIDTH // CELL_SIZE
GRID_H = WINDOW_HEIGHT // CELL_SIZE
PLAY_W = PLAY_W_PX // CELL_SIZE
PLAY_H = GRID_H

# Time & zoom
TIME_LIMIT = 180
MIN_ZOOM = 0.25
MAX_ZOOM = 2.0
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

# Start pos
START = (1, 1)

# Difficulties
DIFFICULTIES = {
    "Easy": {"segments": 90, "seed": 42},
    "Medium": {"segments": 120, "seed": 42},
    "Hard": {"segments": 175, "seed": 42},
}

# Fonts
DEFAULT_FONT = "Arial"

# Convenience
def make_window():
    return pyglet.window.Window(WINDOW_WIDTH, WINDOW_HEIGHT, "SAR Mission")
