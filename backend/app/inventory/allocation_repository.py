"""Single source of truth for the yield engine -> allotment-updater handoff.

The yield engine writes the daily allocation matrix to ``inventory_allocation.db``
(table ``daily_inventory_allocation``). The allotment-updater flows read it back
through :func:`load_allocation_rows`, which returns the same list-of-dicts shape
the old ``daily_inventory_allocation_seasonal.csv`` produced so callers keep
strptime-ing ``row['Date']`` and ``int(row[<column>])`` exactly as before.
"""

import os
import sqlite3
from ..infrastructure.paths import get_data_dir

DATA_DIR = get_data_dir()
ALLOCATION_DB_PATH = os.path.join(DATA_DIR, 'inventory_allocation.db')
ALLOCATION_TABLE = 'daily_inventory_allocation'


def load_allocation_rows(db_path=ALLOCATION_DB_PATH):
    """Load the daily allocation table as a list of dicts keyed by column name.

    The ``Date`` column is normalised to a ``YYYY-MM-DD`` string so callers can
    parse it the same way they did when this data came from a CSV.
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        rows = [dict(row) for row in conn.execute(f"SELECT * FROM {ALLOCATION_TABLE}")]
    finally:
        conn.close()

    for row in rows:
        row['Date'] = str(row['Date'])[:10]
    return rows
