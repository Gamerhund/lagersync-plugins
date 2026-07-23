#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def get_changed_files():
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        return []

def detect_changed_plugins():
    changed_files = get_changed_files()
    plugins_dir = Path("plugins")
    changed_plugins = set()
    
    for file_path in changed_files:
        if not file_path:
            continue
        
        path = Path(file_path)
        if path.parts and path.parts[0] == "plugins":
            plugin_name = path.parts[1] if len(path.parts) > 1 else None
            if plugin_name and (plugins_dir / plugin_name).exists():
                changed_plugins.add(plugin_name)
    
    return sorted(changed_plugins)

if __name__ == "__main__":
    plugins = detect_changed_plugins()
    if plugins:
        print(",".join(plugins))
    else:
        print("")
