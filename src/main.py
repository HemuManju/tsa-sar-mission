import pyglet
import yaml

from game.gui import MainGUI
from utils import skip_run

# Load config
config_path = "configs/config.yml"
with open(config_path, "r") as file:
    config = yaml.safe_load(file)


with skip_run("run", "torch_eeg_dataset") as check, check():
    # Initialize the game and run with dynamic window size
    window_width, window_height = 800, 800  # Example window size
    game = MainGUI(window_width, window_height, config)  # Pass dynamic window size
    pyglet.clock.schedule_interval(game.update, 1 / 15)
    pyglet.app.run()
