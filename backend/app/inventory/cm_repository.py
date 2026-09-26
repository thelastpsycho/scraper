"""Read access to the channel manager's current ("old") allotment values.

The PMS allotment updaters compare a newly calculated value (from
``inventory_allocation.db``, see ``allocation_repository.py``) against what's
already live in the channel manager before deciding whether a PMS update is
needed at all. ``cm_inventory_processed.db`` (written by
``channel_manager_processor.py``) is the source of truth for that current
value - one row per date, one column per room type.
"""

import os
import sqlite3
from ..infrastructure.paths import get_data_dir

CM_PROCESSED_DB_PATH = os.path.join(get_data_dir(), 'cm_inventory_processed.db')
CM_PROCESSED_TABLE = 'cm_inventory_processed'


def load_cm_current_values(db_path=CM_PROCESSED_DB_PATH):
    """Load the current CM snapshot as ``{date_str: {column_name: int}}``.

    ``date_str`` is ``YYYY-MM-DD``, matching ``load_allocation_rows()``'s
    normalized ``Date`` values. Returns an empty dict (not an error) when the
    db or table doesn't exist yet, so callers can treat "no CM data" the same
    as "no match found" rather than needing a separate error path.
    """
    if not os.path.exists(db_path):
        return {}

    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(f"SELECT * FROM {CM_PROCESSED_TABLE}").fetchall()
        except sqlite3.OperationalError:
            return {}
    finally:
        conn.close()

    values = {}
    for row in rows:
        row = dict(row)
        date_str = str(row.pop('Date'))[:10]
        values[date_str] = row
    return values
