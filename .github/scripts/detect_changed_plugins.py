#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

PLUGINS_DIR = Path("plugins")


def get_changed_files():
    base_sha = os.environ.get("GITHUB_BASE_SHA")
    head_sha = os.environ.get("GITHUB_SHA")

    if not base_sha or not head_sha:
        return []

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_sha}...{head_sha}"],
            capture_output=True,
            text=True,
            check=True,
        )

        return [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]

    except subprocess.CalledProcessError as e:
        print(f"Error detecting changed files: {e}", file=os.sys.stderr)
        return []


def detect_changed_plugins():
    changed_files = get_changed_files()
    changed_plugins = set()

    for file_path in changed_files:
        path = Path(file_path)

        if len(path.parts) < 2:
            continue

        if path.parts[0] != "plugins":
            continue

        plugin_name = path.parts[1]
        plugin_path = PLUGINS_DIR / plugin_name

        if plugin_path.is_dir():
            changed_plugins.add(plugin_name)

    return sorted(changed_plugins)


if __name__ == "__main__":
    plugins = detect_changed_plugins()

    if plugins:
        print(",".join(plugins))
    else:
        print("")
