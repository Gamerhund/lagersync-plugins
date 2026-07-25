#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

PLUGINS_DIR = Path("plugins")


def _git_diff_name_only(base_sha, head_sha):
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_sha}...{head_sha}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            f"::error::git diff {base_sha}...{head_sha} failed: "
            f"{result.stderr.strip()}",
            file=sys.stderr,
        )
        return None
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def get_changed_files():
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")

    if event_name == "workflow_dispatch":
        return None

    base_sha = os.environ.get("BASE_SHA")
    head_sha = os.environ.get("HEAD_SHA")

    if not base_sha or not head_sha:
        print(
            "::error::BASE_SHA/HEAD_SHA not set (event=" + event_name + "). "
            "Check the env: block for this step in runtime-tests.yml.",
            file=sys.stderr,
        )
        sys.exit(2)

    changed_files = _git_diff_name_only(base_sha, head_sha)
    if changed_files is None:
        print(
            "::error::Could not compute the diff - checkout probably needs fetch-depth: 0.",
            file=sys.stderr,
        )
        sys.exit(2)

    return changed_files


def detect_changed_plugins():
    changed_files = get_changed_files()

    if changed_files is None:
        return sorted(p.name for p in PLUGINS_DIR.iterdir() if p.is_dir())

    changed_plugins = set()
    for file_path in changed_files:
        path = Path(file_path)
        if len(path.parts) < 2 or path.parts[0] != "plugins":
            continue
        plugin_name = path.parts[1]
        if (PLUGINS_DIR / plugin_name).is_dir():
            changed_plugins.add(plugin_name)

    return sorted(changed_plugins)


if __name__ == "__main__":
    plugins = detect_changed_plugins()
    print(",".join(plugins))
