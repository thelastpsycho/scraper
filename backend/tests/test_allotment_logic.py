"""Skip-unchanged date-range collapsing tests for the PMS allotment updaters."""
from app.integrations.pms.allotment_updater import _build_date_ranges
from app.integrations.pms.other_room_allotment_updater import build_batches, REST_ROOM_TYPE_CONFIG


def days(*items):
    """items: (date, inventory, skip) tuples -> the dict shape _build_date_ranges expects."""
    return [{'date': date, 'inventory': inventory, 'skip': skip} for date, inventory, skip in items]


def test_unchanged_run_in_the_middle_splits_and_is_dropped():
    source = days(
        ('01/01/2026', 5, False),
        ('01/02/2026', 5, False),
        ('01/03/2026', 5, True),   # already matches CM - should be skipped
        ('01/04/2026', 5, False),
        ('01/05/2026', 5, False),
    )
    runs, skipped_count = _build_date_ranges(source)
    assert skipped_count == 1
    assert runs == [
        {'start': '01/01/2026', 'end': '01/02/2026', 'inventory': 5, 'skip': False},
        {'start': '01/04/2026', 'end': '01/05/2026', 'inventory': 5, 'skip': False},
    ]


def test_no_skips_reproduces_a_single_contiguous_run():
    source = days(('01/01/2026', 3, False), ('01/02/2026', 3, False), ('01/03/2026', 3, False))
    runs, skipped_count = _build_date_ranges(source)
    assert skipped_count == 0
    assert runs == [{'start': '01/01/2026', 'end': '01/03/2026', 'inventory': 3, 'skip': False}]


def test_all_skipped_yields_no_runs():
    source = days(('01/01/2026', 3, True), ('01/02/2026', 3, True))
    runs, skipped_count = _build_date_ranges(source)
    assert runs == []
    assert skipped_count == 1


def _rows(*day_values, config=REST_ROOM_TYPE_CONFIG):
    """day_values: (date, {room_type: value}) -> allocation_rows shape build_batches expects."""
    rows = []
    for date, values in day_values:
        row = {'Date': date}
        for room_type, room_config in config.items():
            row[room_config['csv_column']] = values.get(room_type, 0)
        rows.append(row)
    return rows


def test_build_batches_skips_room_type_matching_current_cm_value(monkeypatch, tmp_path):
    import sqlite3
    from app.integrations.pms import other_room_allotment_updater as mod

    db_path = tmp_path / "cm_inventory_processed.db"
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE cm_inventory_processed ("Date" DATE, "Deluxe Suite Room" INTEGER)')
    conn.execute("INSERT INTO cm_inventory_processed VALUES ('2026-01-01', 2)")
    conn.execute("INSERT INTO cm_inventory_processed VALUES ('2026-01-02', 2)")
    conn.commit()
    conn.close()

    from app.inventory.cm_repository import load_cm_current_values as _load_cm_current_values
    monkeypatch.setattr(mod, "load_cm_current_values", lambda: _load_cm_current_values(str(db_path)))

    rows = _rows(
        ('2026-01-01', {'Deluxe Suite Room': 2}),  # matches CM -> skip
        ('2026-01-02', {'Deluxe Suite Room': 4}),  # differs from CM -> keep
    )
    batches, skipped_count = build_batches(rows, skip_unchanged=True)
    assert skipped_count == 1
    dates_pushed = {d for b in batches for d in b['date_ranges']}
    assert ('01/02/2026', '01/02/2026') in dates_pushed
    assert ('01/01/2026', '01/01/2026') not in dates_pushed


def test_build_batches_never_skips_room_type_with_no_cm_column(monkeypatch, tmp_path):
    # Every current REST_ROOM_TYPE_CONFIG entry has a real cm_column (as of the
    # 2026-09-24 D-EDGE "Rooms to show" filter fix that surfaced Deluxe Pool
    # Access in the export). cm_column=None still needs to degrade safely to
    # "always push" for whatever room type hits this in the future, so exercise
    # that path with a synthetic config rather than relying on a real one.
    from app.integrations.pms import other_room_allotment_updater as mod

    synthetic_config = {
        'Synthetic Room': {'csv_column': 'Synthetic Room Online Inventory', 'checkbox_value': 'SYN', 'cm_column': None},
    }
    monkeypatch.setattr(mod, "REST_ROOM_TYPE_CONFIG", synthetic_config)
    # No cm_inventory_processed.db at all - load_cm_current_values() degrades to {}.
    monkeypatch.setattr(mod, "load_cm_current_values", lambda: {})

    rows = _rows(
        ('2026-01-01', {'Synthetic Room': 1}),
        ('2026-01-02', {'Synthetic Room': 1}),
        config=synthetic_config,
    )
    batches, skipped_count = build_batches(rows, skip_unchanged=True)
    assert skipped_count == 0
    dates_pushed = {d for b in batches for d in b['date_ranges']}
    assert ('01/01/2026', '01/02/2026') in dates_pushed


def test_deluxe_pool_access_now_has_a_cm_column_and_can_be_skipped(monkeypatch, tmp_path):
    import sqlite3
    from app.integrations.pms import other_room_allotment_updater as mod

    assert REST_ROOM_TYPE_CONFIG['Deluxe Pool Access']['cm_column'] == 'Deluxe Pool Access'

    db_path = tmp_path / "cm_inventory_processed.db"
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE cm_inventory_processed ("Date" DATE, "Deluxe Pool Access" INTEGER)')
    conn.execute("INSERT INTO cm_inventory_processed VALUES ('2026-01-01', 3)")
    conn.commit()
    conn.close()

    from app.inventory.cm_repository import load_cm_current_values as _load_cm_current_values
    monkeypatch.setattr(mod, "load_cm_current_values", lambda: _load_cm_current_values(str(db_path)))

    rows = _rows(('2026-01-01', {'Deluxe Pool Access': 3}))
    batches, skipped_count = build_batches(rows, skip_unchanged=True)
    assert skipped_count == 1
    assert all('Deluxe Pool Access' not in b['room_types'] for b in batches)


def test_skip_unchanged_false_reproduces_default_behavior(monkeypatch, tmp_path):
    import sqlite3
    from app.integrations.pms import other_room_allotment_updater as mod

    db_path = tmp_path / "cm_inventory_processed.db"
    conn = sqlite3.connect(db_path)
    conn.execute('CREATE TABLE cm_inventory_processed ("Date" DATE, "Deluxe Suite Room" INTEGER)')
    conn.execute("INSERT INTO cm_inventory_processed VALUES ('2026-01-01', 2)")
    conn.commit()
    conn.close()
    from app.inventory.cm_repository import load_cm_current_values as _load_cm_current_values
    monkeypatch.setattr(mod, "load_cm_current_values", lambda: _load_cm_current_values(str(db_path)))

    rows = _rows(('2026-01-01', {'Deluxe Suite Room': 2}))
    batches, skipped_count = build_batches(rows, skip_unchanged=False)
    assert skipped_count == 0
    dates_pushed = {d for b in batches for d in b['date_ranges']}
    assert ('01/01/2026', '01/01/2026') in dates_pushed
