"""BAR date grouping and D-EDGE row-limit regression tests."""
from datetime import datetime

import pytest

from app.integrations.dedge.bar_updater import (
    _chunk_ranges, _planned_chunks, build_level_groups, MAX_RANGES_PER_APPLY,
)


def rows(*items):
    return [{"Date": date, "Deluxe BAR Rate": rate, "Premiere BAR Rate": None}
            for date, rate in items]


def test_year_boundary_produces_separate_price_level_groups():
    source = rows(
        ("2026-12-30", "BAR3"), ("2026-12-31", "BAR3"),
        ("2027-01-01", "BAR3"), ("2027-01-02", "BAR3"),
    )
    result = build_level_groups(source, "Deluxe BAR Rate")
    assert result == {
        (2026, "BAR3"): [(datetime(2026, 12, 30), datetime(2026, 12, 31))],
        (2027, "BAR3"): [(datetime(2027, 1, 1), datetime(2027, 1, 2))],
    }
    plan = _planned_chunks(source, ("deluxe",), None)
    assert {part[1] for part in plan} == {"BAR 3 2026", "BAR 3 2027"}


def test_chunking_never_exceeds_dedge_limit():
    values = list(range(25))
    chunks = _chunk_ranges(values)
    assert [len(chunk) for chunk in chunks] == [10, 10, 5]
    assert [item for chunk in chunks for item in chunk] == values
    assert all(len(chunk) <= MAX_RANGES_PER_APPLY for chunk in chunks)


def test_chunking_preserves_small_and_empty_inputs():
    assert _chunk_ranges([]) == []
    assert _chunk_ranges([1, 2]) == [[1, 2]]
    with pytest.raises(ValueError):
        _chunk_ranges([1], size=0)


def test_nonconsecutive_dates_do_not_merge():
    source = rows(("2026-11-01", "BAR3"), ("2026-11-03", "BAR3"),
                  ("2026-11-04", "BAR4"))
    groups = build_level_groups(source, "Deluxe BAR Rate")
    assert len(groups[(2026, "BAR3")]) == 2
    assert len(groups[(2026, "BAR4")]) == 1
