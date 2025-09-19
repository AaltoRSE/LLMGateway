import json
import os

# Get the directory of the current file
current_file_directory = os.path.dirname(os.path.abspath(__file__))

# Load the configuration file
config_file_path = os.path.join(current_file_directory, "config.json")
with open(config_file_path, "r", encoding="utf-8") as config_file:
    config: dict[any, any] = json.load(config_file)

base_quota = float(config.get("baseQuota", "30"))
