import pytest
import json
import os
import sys
from pathlib import Path
PLUGIN_DIR = Path(__file__).parent.parent / 'plugins'
sys.path.insert(0, str(Path(__file__).parent.parent / '.github'))
from verified_plugins import MAINTAINER_VERIFIED_PLUGINS

@pytest.fixture
def plugin_dir():
    return PLUGIN_DIR

@pytest.fixture
def valid_permissions():
    return ['db.read', 'db.write', 'inventory.read', 'inventory.write', 'inventory.delete', 'users.read', 'users.write', 'system.settings', 'system.files.read', 'system.files.write', 'system.network', 'notifications.send', 'api.public', 'api.admin']

@pytest.fixture
def plugin_public_key():
    return 'lLEUuDnXSAZGt2P5CHYEg86PHgx6DGl2rGaVsznIU+c='