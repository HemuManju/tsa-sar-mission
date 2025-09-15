
import yaml
from utils import skip_run
from game_design.controls import controllers
from game_design.update import update
from game_design.game import Game
from game_design.config import *
from game_design.camera import camera
from game_design.grid import build_grid_lines
from game_design.helpers import helpers
from game_design.chatui import chatui
from game_design.hud import build_hud
from game_design.world import world
from contextlib import contextmanager

# Load config
config_path = "TSA-SAR-mission/configs/config.yml"
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# Access skip flag
skip_flag = config.get("skip", False)

# Collect all modules/functions
def all_modules():
    return {
        "controllers": controllers,
        "update": update,
        "Game": Game,
        "camera": camera,
        "grid": build_grid_lines,
        "helpers": helpers,
        "chatui": chatui,
        "hud": build_hud,
        "world": world
    }

# ---- Conditional execution using skip_run ----
modules = all_modules()



@contextmanager
def skip_run(mode, name):
    def check():
        return mode == "run"   # Only run if explicitly set to "run"
    if mode == "skip":
        print(f" Skipping {name}...")
    elif mode == "run":
        print(f" Running {name}...")
    else:
        print(f" Unknown mode '{mode}' for {name}, skipping by default.")
    yield check
