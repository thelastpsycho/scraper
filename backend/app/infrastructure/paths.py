"""Central paths for runtime files.

Source modules were reorganized in the Phase 1 refactor, but runtime data and
the persistent D-EDGE Chrome profile intentionally remain under the historical
`backend/app/scraper/` directory so existing local databases, uploads, debug
artifacts, and trusted-device sessions continue to work unchanged.
"""

import os

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_DIR = os.path.join(APP_DIR, "scraper")
DATA_DIR = os.path.join(RUNTIME_DIR, "data")
DEDGE_PROFILE_DIR = os.path.join(RUNTIME_DIR, ".dedge_profile")


def get_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    return DATA_DIR


def get_data_path(filename):
    return os.path.join(get_data_dir(), filename)


def get_dedge_profile_dir():
    os.makedirs(DEDGE_PROFILE_DIR, exist_ok=True)
    return DEDGE_PROFILE_DIR
