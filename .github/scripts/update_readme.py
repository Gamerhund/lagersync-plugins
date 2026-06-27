#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
README Generator - Plugin Marketplace
Automatically updates README.md and README_EN.md based on plugin.json files.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse

# Root directory
ROOT_DIR = Path(__file__).parent.parent.parent
PLUGIN_DIR = ROOT_DIR / "plugins"
README_DE = ROOT_DIR / "README.md"
README_EN = ROOT_DIR / "README_EN.md"

# Einzige Quelle fuer die verified-Liste: .github/verified_plugins.py.
# Wer hier nichts importieren, sondern lieber eine eigene Liste pflegen wuerde,
# baut sich genau die Inkonsistenz ein, die diese Zeile verhindern soll.
sys.path.insert(0, str(Path(__file__).parent.parent))
from verified_plugins import MAINTAINER_VERIFIED_PLUGINS  # noqa: E402

# English descriptions for already-signed/verified plugins.
#
# IMPORTANT: verified plugins have an Ed25519 signature (plugin.sig) computed
# over their exact plugin.json content. Adding a "description_en" field to
# plugin.json would change that content and invalidate the signature, which
# only the maintainer can re-create with the private key. So for these
# plugins we keep the translation here instead of in plugin.json.
#
# New, not-yet-verified community plugins don't have this problem (they have
# no signature yet) - they can simply add "description_en" to their own
# plugin.json, which takes priority below.
VERIFIED_PLUGIN_DESCRIPTIONS_EN = {
    "ki-assistent": "AI chat with Ollama/OpenAI integration. Can query inventory levels and perform stock changes.",
    "low_stock_notifications": "Notifications via Telegram, Discord, Webhook, or Email.",
    "pro-design": "Professional design options and themes for your inventory management system.",
    "sso": "Single sign-on via OpenID Connect with configurable username claim, nonce, logout, and scope, plus improved security. Works with any OIDC provider.",
}


def load_plugin_metadata(plugin_dir: Path) -> Dict[str, dict]:
    """Load all plugin.json files from plugins/ directory."""
    plugins = {}
    for plugin_path in plugin_dir.iterdir():
        if plugin_path.is_dir():
            json_file = plugin_path / "plugin.json"
            if json_file.exists():
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        plugins[plugin_path.name] = data
                except Exception as e:
                    print(f"Error loading {json_file}: {e}")
    return plugins


def is_verified(plugin_name: str) -> bool:
    """Check if plugin is in maintainer verified list."""
    return plugin_name in MAINTAINER_VERIFIED_PLUGINS


def generate_plugin_table(plugins: Dict[str, dict], lang: str = "de") -> str:
    """Generate plugin table markdown."""
    if lang == "de":
        headers = "| Plugin | Beschreibung | Typ |\n|--------|-------------|-----|"
        verified_label = "✅ Verifiziert"
        community_label = "👤 Community"
    else:
        headers = "| Plugin | Description | Type |\n|----------|-------------|------|"
        verified_label = "✅ Verified"
        community_label = "👤 Community"

    rows = []
    for plugin_name in sorted(plugins.keys()):
        metadata = plugins[plugin_name]
        name = metadata.get("name", plugin_name)

        if lang == "en":
            # Priority: explicit description_en in plugin.json (safe for new,
            # not-yet-signed plugins) > known translation table (for already
            # signed plugins, see VERIFIED_PLUGIN_DESCRIPTIONS_EN above) >
            # German description as last-resort fallback.
            description = (
                metadata.get("description_en")
                or VERIFIED_PLUGIN_DESCRIPTIONS_EN.get(plugin_name)
                or metadata.get("description", "")
            )
        else:
            description = metadata.get("description", "")

        status = verified_label if is_verified(plugin_name) else community_label
        
        row = f"| [**{plugin_name}**](plugins/{plugin_name}/) | {description} | {status} |"
        rows.append(row)
    
    return f"{headers}\n" + "\n".join(rows)


def generate_badge(count: int, lang: str = "de") -> str:
    """Generate plugin count badge."""
    if lang == "de":
        return f"[![Plugins](https://img.shields.io/badge/Plugins-{count}%20verfügbar-blue.svg)](plugins/)"
    else:
        return f"[![Plugins](https://img.shields.io/badge/Plugins-{count}%20Available-blue.svg)](plugins/)"


def update_readme(readme_path: Path, plugins: Dict[str, dict], lang: str = "de"):
    """Update README file with new plugin table and badge."""
    if not readme_path.exists():
        print(f"README file not found: {readme_path}")
        return
    
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Generate new content
    count = len(plugins)
    new_badge = generate_badge(count, lang)
    new_table = generate_plugin_table(plugins, lang)
    
    # Update badge (find by pattern, not fixed line number)
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "Plugins" in line:
            # Extract badge image URL from markdown pattern [![...](URL)](...)
            image_url = None
            if "](" in line:
                url_start = line.find("](") + 2
                url_end = line.find(")", url_start)
                if url_end != -1:
                    image_url = line[url_start:url_end]
            if image_url:
                parsed = urlparse(image_url)
                if parsed.hostname == "img.shields.io":
                    lines[i] = new_badge
                    break
    
    # Update plugin table (between "## 📦 Verfügbare Plugins" and "---")
    # or "## 📦 Available Plugins" for English
    table_start_marker = "## 📦 Verfügbare Plugins" if lang == "de" else "## 📦 Available Plugins"
    
    new_lines = []
    in_table_section = False
    table_section_added = False
    
    for line in lines:
        if table_start_marker in line:
            new_lines.append(line)
            new_lines.append("")
            new_lines.append(new_table)
            new_lines.append("")
            in_table_section = True
            table_section_added = True
        elif in_table_section and line.strip() == "---":
            new_lines.append(line)
            in_table_section = False
        elif not in_table_section:
            new_lines.append(line)
        # Skip all lines while in_table_section is True (old table content)
    
    new_content = "\n".join(new_lines)
    
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"Updated {readme_path.name} with {count} plugins")


def main():
    print("Starting README update...")
    
    # Load plugin metadata
    plugins = load_plugin_metadata(PLUGIN_DIR)
    print(f"Found {len(plugins)} plugins")
    
    # Update German README
    update_readme(README_DE, plugins, lang="de")
    
    # Update English README
    update_readme(README_EN, plugins, lang="en")
    
    print("README update complete!")


if __name__ == "__main__":
    main()
