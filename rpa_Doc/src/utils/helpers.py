import json
import os

def ensure_dir(path: str):
    """Ensures that the directory for a given path exists."""
    os.makedirs(os.path.dirname(path), exist_ok=True)

def load_json(path: str):
    """Loads a JSON file with utf-8 encoding."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, path: str, indent: int = 2):
    """Saves data to a JSON file with utf-8 encoding."""
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
