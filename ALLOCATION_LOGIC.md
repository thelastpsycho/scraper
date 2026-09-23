# Allocation Logic (`backend/app/revenue/yield_engine.py`)

How the yield engine decides **how many rooms to open online** ("allocation") for each date and room type.

> This document describes existing business logic. The Phase 1 project-structure refactor only moved the implementation from `backend/app/scraper/yielder.py` to `backend/app/revenue/yield_engine.py`; it did not intentionally change the formulas below.

## 0. Preconditions per row

For each date row in `apply_yield_matrix`:

- Skip the row if `DemandLevel` is `NaN`.
- Pull Premiere and Deluxe remaining inventory from the combined dataset.
- `DemandLevel` is derived from occupancy using the configured demand bins and labels.

## 1. Base allotment rule — tiered buckets

`get_online_allotment(remaining, room_cap)` maps remaining inventory into controlled online-sale buckets:

| Remaining | Rooms opened online |
| --- | --- |
| ≤ 0 | 0 |
| 1–5 | `min(2, remaining, cap)` |
| 6–10 | `min(5, remaining, cap)` |
| 11–50 | `min(10, remaining, cap)` |
| > 50 | `min(30, remaining, cap)` |

The intent is to meter inventory rather than expose all remaining rooms online at once.

## 2. Premiere Room

Premiere uses the tiered rule against effective Premiere inventory. A negative Deluxe balance reduces the effective Premiere inventory because a Deluxe oversell may consume Premiere inventory through an upgrade. A positive Deluxe balance does not increase Premiere inventory.

## 3. Deluxe Room — override behavior

Deluxe normally uses the same tiered rule, but `should_override_deluxe` can force a small number of Deluxe rooms open when:

- Deluxe inventory is effectively sold out,
- Deluxe + Premiere combined inventory remains positive, and
- occupancy / Premiere-remaining conditions allow the override.

The combined-inventory guard prevents the override from selling when Deluxe + Premiere combined inventory has reached zero.

## 4. Other room types

The remaining room types use their existing per-room formulas, including tiered allocation, hold-one-back rules, full-remaining rules, Deluxe Suite fallback logic, and the near-full occupancy shutdown.

The implementation and configured room caps remain in `backend/app/revenue/yield_engine.py`.

## Design intent

1. Meter online releases instead of exposing all inventory.
2. Hold back scarce/premium categories where appropriate.
3. Use controlled override valves for Deluxe and near-full occupancy.
4. Allow specific cross-category fallbacks where existing business logic defines them.
