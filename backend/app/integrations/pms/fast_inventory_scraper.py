"""Selenium-free room-availability fetch, for verifying the API-based
approach against the existing Selenium scraper (integrations/pms/inventory_scraper.py)
without touching it. Read-only: this module never writes to any database.
"""

import time

from .api_client import PMSApiClient

# Maps the PMS API's JSON field names to the column names the existing
# Selenium scraper produces from the HTML table, so results from both paths
# can be compared directly.
FIELD_MAP = {
    "TrxDate": "Date",
    "AVR": "AVR",
    "AVS": "AVS",
    "ASP": "ASP",
    "ASW": "ASW",
    "AVP": "AVP",
    "BFS": "BFS",
    "DLK": "DLK",
    "DLT": "DLT",
    "DLKP": "DLKP",
    "DLTP": "DLTP",
    "DLS": "DLS",
    "FAM": "FAM",
    "PRKG": "PRKG",
    "PRKP": "PRKP",
    "PRTG": "PRTG",
    "PRTP": "PRTP",
    "PRKL": "PRKL",
    "PRTL": "PRTL",
    "PSU": "PSU",
    "ExtraBed": "Extra Bed",
    "TotalRoom": "Total Room",
    "RoomAvailable": "Available",
    "Tentatif": "Tentative",
    "Definite": "Definite",
    "RoomWaitingList": "Waiting List",
    "Allotment": "Allotment",
    "OutOfOrder": "Out of Order",
    # The Room Availability page's Vue table binds its "Occupancy" header to
    # a field literally named "Occupancy2" (confirmed from the rendered
    # page's id="_Occupancy2" / class="vuetable-th-_occupancy2" markup) -
    # not "Occupancy". The Selenium scraper never had to know this since it
    # just reads whatever column header text the table renders.
    "Occupancy2": "Occupancy",
}


def fetch_room_inventory(start_date, days, username=None, password=None):
    """Login and fetch `days` days of room-availability data starting at
    `start_date` (YYYY-MM-DD), via the PMS's JSON API instead of Selenium.

    Returns (rows, elapsed_seconds) where rows is a list of dicts using the
    same column names as the existing HTML-table scraper.
    """
    started = time.monotonic()
    client = PMSApiClient(username=username, password=password)
    client.login()
    raw_rows = client.get_available_room_inventory(start_date, days)

    rows = []
    for raw in raw_rows:
        row = {}
        for api_key, column_name in FIELD_MAP.items():
            value = raw.get(api_key)
            if column_name == "Date" and isinstance(value, str):
                value = value.split("T")[0]
            row[column_name] = value
        rows.append(row)

    elapsed = time.monotonic() - started
    return rows, elapsed
