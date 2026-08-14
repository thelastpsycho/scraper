# Allocation Logic (`backend/app/scraper/yielder.py`)

How the yielder decides **how many rooms to open online** ("allocation") for each
date and each room type. Allocation is computed per-date, per-room-type from the
*remaining inventory*, plus contextual signals like occupancy and season.

## 0. Preconditions per row

For each date row (`apply_yield_matrix`, loop at `yielder.py:288`):

- Skip the row if `DemandLevel` is `NaN` (occupancy fell outside the demand bins).
- Pull `premiere_remaining` and `deluxe_remaining` from the combined inventory.

`DemandLevel` comes from `Occupancy` binned via `DEMAND_BINS = [0, 70, 85, 100]`
→ `Low / Medium / High` (`yielder.py:8`, `yielder.py:187`).

## 1. The base allotment rule — tiered buckets

`get_online_allotment(remaining, room_cap)` (`yielder.py:46`) is the workhorse.
It maps remaining inventory into fixed buckets, then clamps to both the remaining
count and the room cap:

| Remaining | Rooms opened online       |
|-----------|---------------------------|
| ≤ 0       | 0                         |
| 1–5       | `min(2, remaining, cap)`  |
| 6–10      | `min(5, remaining, cap)`  |
| 11–50     | `min(10, remaining, cap)` |
| > 50      | `min(30, remaining, cap)` |

Intent: never dump all remaining rooms online at once — release them in
controlled chunks that scale with how much is left.

## 2. Premiere Room

`allocation = get_online_allotment(effective_premiere_remaining, cap=260)` where
`effective_premiere_remaining = premiere_remaining + min(deluxe_remaining, 0)`
(`yielder.py:326`). A Deluxe oversell (negative remaining) will be upgraded into
Premiere and so consumes real Premiere availability; a Deluxe surplus (positive)
does *not* add to Premiere, because there is no Premiere→Deluxe downgrade. So
once Deluxe+Premiere combined drops to ≤ 0, Premiere's effective remaining is ≤ 0
and it opens 0 — instead of the old behavior of still opening 30 off a raw
`premiere_remaining > 50`. (A BAR rate is also computed off the raw
`premiere_remaining`, but that's pricing, not allocation.)

## 3. Deluxe Room — with an override

Deluxe normally uses `get_online_allotment(deluxe_remaining, cap=160)`, **but**
an override can force it open (`yielder.py:339`).

`should_override_deluxe` (`yielder.py:84`) returns true when:

- `deluxe_inventory < 1` (Deluxe is effectively sold out), **AND**
- `deluxe_inventory + premiere_remaining > 0` (Deluxe+Premiere combined still
  has rooms — a Deluxe oversell can be upgraded into Premiere, but only while
  the two categories together have slack), **AND**
- `occupancy < 70` **OR** `premiere_remaining > 61`

Meaning: if Deluxe is empty but either the hotel isn't full yet *or* there's
still lots of Premiere sitting unsold — *and* the combined Deluxe+Premiere
inventory hasn't hit zero — forcibly open up to **2** Deluxe rooms
(`DELUXE_OVERRIDE_AMOUNT`, clamped to `deluxe_remaining + premiere_remaining`)
anyway, to keep the cheaper category selling and capture demand rather than
showing zero availability. Otherwise it falls back to the normal tiered rule.

The combined-inventory guard is what stops the override from selling into a
hole: if Deluxe is oversold at `-100` while Premiere has `100` left, the sum is
`0`, so no override fires and Deluxe is written as `0`.

## 4. The 11 "simple" room types

These get an **online count only, no BAR pricing** (`yielder.py:356`).
`SIMPLE_ROOM_TYPES` is every room in `ROOM_CAPS` except Deluxe/Premiere
(`yielder.py:34`).

**Global gate first:** if `Occupancy >= 95` (`NEAR_FULL_OCCUPANCY_THRESHOLD`),
every simple room is closed (`allocation = 0`), regardless of its own rule.
Otherwise each room follows its own formula:

| Room type(s)                                                       | Rule                                            | Function                          |
|-------------------------------------------------------------------|-------------------------------------------------|-----------------------------------|
| Deluxe Pool Access, Premiere Room Lagoon Access, Premiere Suite Room | same tiered buckets as above                    | `get_online_allotment`            |
| Deluxe Suite Room                                                  | stepped ladder (see below), Premiere-Suite fallback | `allot_deluxe_suite` (`:72`)      |
| Beach Front Private Suite Room                                     | `remaining − 1`, but keep 1 open if only 1 left | `allot_minus_one_except_one` (`:62`) |
| Family Premiere, Anvaya Suite Whirpool, Anvaya Suite No Pool       | `max(0, remaining − 1)` (always hold one back)  | `allot_minus_one` (`:59`)         |
| Anvaya Suite With Pool, Anvaya Residence, Anvaya Villa             | open everything remaining                       | `allot_as_remaining` (`:69`)      |

**Deluxe Suite ladder** (`allot_deluxe_suite`, `yielder.py:72`):

- remaining ≥ 5 → 4
- remaining == 4 → 3
- remaining 2–3 → 2
- remaining == 1 → 1
- remaining ≤ 0 → 1 *only if* Premiere Suite has > 3 left, else 0
  (borrow-a-sale fallback when its sibling category has slack)

## Summary of the design intent

1. **Meter releases in buckets** — the more remaining, the bigger the chunk, but
   never all at once (`get_online_allotment`).
2. **Hold back the scarce/premium types** — the small-inventory suites/villas
   mostly do `remaining − 1` to avoid overselling a 1–4 room category.
3. **Two override valves:**
   - Deluxe: *force* rooms open when sold out but conditions say demand is
     capturable (`should_override_deluxe`).
   - Simple rooms: *force* everything shut once the hotel is ≥95% full.
4. **Cross-category fallbacks** — Deluxe Suite and Deluxe Room both peek at their
   Premiere sibling's remaining inventory to decide whether to open when they'd
   otherwise be zero.
