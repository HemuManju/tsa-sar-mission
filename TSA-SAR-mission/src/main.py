

import yaml
from utils import skip_run
from data.mission import run_sar_mission_game

# Load config
config_path = "TSA-SAR-mission/configs/config.yml"
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

# Access skip flag
skip_flag = config.get("skip", False)

# Conditional execution using skip_run
with skip_run(skip_flag, "Data") as check:
    if check():
        run_sar_mission_game()
