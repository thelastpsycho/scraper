import sqlite3

import pandas as pd

from app.inventory import channel_manager_processor as processor


def test_cm_processor_preserves_dates_for_pms_alignment(monkeypatch, tmp_path):
    # This mirrors the transposed D-EDGE export: the first column is the
    # worksheet title, followed by the type marker and date columns.
    source = pd.DataFrame({
        'D-EDGE export': ['Deluxe Room', 'Deluxe Room'],
        'Unnamed: 1': [None, None],
        'Unnamed: 2': ['Left for sale', 'Price (IDR)'],
        '2026-09-26 00:00:00': ['5', '3450000'],
        '2026-09-27 00:00:00': ['0', '3450000'],
    })
    monkeypatch.setattr(processor.pd, 'read_excel', lambda _: source.copy())
    monkeypatch.setattr(processor, 'get_data_dir', lambda: str(tmp_path))
    (tmp_path / 'cm_upload.xlsx').touch()

    assert processor.process_cm_inventory().endswith('successfully')
    with sqlite3.connect(tmp_path / 'cm_inventory_processed.db') as conn:
        result = pd.read_sql_query('SELECT * FROM cm_inventory_processed', conn)

    assert result['Date'].tolist() == ['2026-09-26', '2026-09-27']
    assert result['Deluxe Room'].tolist() == [5, 0]
