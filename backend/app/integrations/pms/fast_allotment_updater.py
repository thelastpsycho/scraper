"""Selenium-free allotment push, for verifying the API-based approach against
the existing Selenium updaters (allotment_updater.py, other_room_allotment_updater.py)
without touching them.

Two modes:
- push_allotment(): a single (date range, room type) call, for manually
  testing the request/response shape.
- build_full_plan() + push_jobs_concurrent(): reads the real
  inventory_allocation.db (the same source the production updaters read) and
  fires the resulting (date range, room type) jobs at the PMS concurrently,
  with a dry_run mode that builds every payload without sending any of them.

FULL_ROOM_TYPE_CONFIG mirrors ROOM_TYPE_CONFIG (allotment_updater.py) +
REST_ROOM_TYPE_CONFIG (other_room_allotment_updater.py) - duplicated rather
than imported so this module stays fully standalone from the Selenium code
path it's meant to validate.
"""

import concurrent.futures
import time
from datetime import datetime

from ...inventory.allocation_repository import load_allocation_rows
from ...inventory.cm_repository import load_cm_current_values
from .api_client import PMSApiClient, PMSApiError

FULL_ROOM_TYPE_CONFIG = {
    "deluxe": {"csv_column": "Deluxe Online Inventory", "checkbox_value": "DLT", "label": "Deluxe", "cm_column": "Deluxe Room"},
    "premiere": {"csv_column": "Premiere Online Inventory", "checkbox_value": "PRKG", "label": "Premiere", "cm_column": "Premiere Room"},
    "deluxe_suite": {"csv_column": "Deluxe Suite Room Online Inventory", "checkbox_value": "DLS", "label": "Deluxe Suite Room", "cm_column": "Deluxe Suite Room"},
    "family_premiere": {"csv_column": "Family Premiere Room Online Inventory", "checkbox_value": "FAM", "label": "Family Premiere Room", "cm_column": "Family Premiere Room"},
    "premiere_suite": {"csv_column": "Premiere Suite Room Online Inventory", "checkbox_value": "PSU", "label": "Premiere Suite Room", "cm_column": "Premiere Suite Room"},
    "beach_front_private_suite": {"csv_column": "Beach Front Private Suite Room Online Inventory", "checkbox_value": "BFS", "label": "Beach Front Private Suite Room", "cm_column": "Beach Front Private Suite Room"},
    "anvaya_suite_whirlpool": {"csv_column": "The Anvaya Suite Whirpool Online Inventory", "checkbox_value": "ASW", "label": "The Anvaya Suite Whirpool", "cm_column": "The Anvaya Suite with Whirpool"},
    "anvaya_suite_no_pool": {"csv_column": "The Anvaya Suite No Pool Online Inventory", "checkbox_value": "AVS", "label": "The Anvaya Suite No Pool", "cm_column": "The Anvaya Suite No Pool"},
    "anvaya_suite_with_pool": {"csv_column": "The Anvaya Suite With Pool Online Inventory", "checkbox_value": "ASP", "label": "The Anvaya Suite With Pool", "cm_column": "The Anvaya Suite With Pool"},
    "anvaya_residence": {"csv_column": "The Anvaya Residence Online Inventory", "checkbox_value": "AVR", "label": "The Anvaya Residence", "cm_column": "The Anvaya Residence"},
    "anvaya_villa": {"csv_column": "The Anvaya Villa Online Inventory", "checkbox_value": "AVP", "label": "The Anvaya Villa", "cm_column": "The Anvaya Villa"},
    "deluxe_pool_access": {"csv_column": "Deluxe Pool Access Online Inventory", "checkbox_value": "DLTP", "label": "Deluxe Pool Access", "cm_column": "Deluxe Pool Access"},
    "premiere_lagoon_access": {"csv_column": "Premiere Room Lagoon Access Online Inventory", "checkbox_value": "PRKL", "label": "Premiere Room Lagoon Access", "cm_column": "Premiere Room Lagoon Access"},
}

# For the single-row manual test endpoint's dropdown - sourced from the same
# config above so it can't drift from the room types the bulk planner knows about.
ROOM_TYPES = [
    {"label": config["label"], "value": config["checkbox_value"]}
    for config in FULL_ROOM_TYPE_CONFIG.values()
]

# checkbox value (e.g. "DLT") -> label (e.g. "Deluxe"), for building remarks
# that read the same way the production Selenium updaters' remarks do.
LABEL_BY_CHECKBOX_VALUE = {
    config["checkbox_value"]: config["label"] for config in FULL_ROOM_TYPE_CONFIG.values()
}


def _to_pms_date(iso_date):
    """'YYYY-MM-DD' -> 'YYYY/MM/DD', matching convertDateInputToDateDB() in
    the PMS's own front-end JS."""
    return iso_date.replace("-", "/")


def push_allotment(company_id, room_type, start_date, end_date, number_of_rooms, remark,
                    dry_run=True, username=None, password=None):
    """Build (and optionally send) one allotment save call, exactly matching
    the payload shape the PMS "Add Allotment Room" modal sends for a single
    date range + room type.

    start_date/end_date: 'YYYY-MM-DD'. dry_run=True (default) builds the
    payload and logs in, but never calls POST api/allotment.

    Returns a dict describing what happened, safe to return directly as a
    JSON API response.
    """
    started = time.monotonic()
    client = PMSApiClient(username=username, password=password)
    client.login()

    payload = {
        "CompanyId": company_id,
        "StartDate": _to_pms_date(start_date),
        "EndDate": _to_pms_date(end_date),
        "TypeId": room_type,
        "NoOfRoom": number_of_rooms,
        "Remark": remark,
        "IsClosed": False,
        "Closed": "0",
        "HotelId": client.hotel_id,
        "UserId": client.user_id,
    }

    result = {
        "dry_run": dry_run,
        "request_payload": payload,
        "response": None,
    }

    if not dry_run:
        result["response"] = client.save_allotment(
            company_id=company_id,
            start_date=payload["StartDate"],
            end_date=payload["EndDate"],
            type_id=room_type,
            no_of_rooms=number_of_rooms,
            remark=remark,
            is_closed=False,
        )

    result["elapsed_seconds"] = time.monotonic() - started
    return result


def _build_date_ranges(date_inventory):
    """Collapse a date-ordered list of {'date', 'inventory', 'skip'} dicts into
    contiguous (start, end, inventory) runs, dropping runs flagged 'skip'.

    Same algorithm as _build_date_ranges() in allotment_updater.py, duplicated
    here to keep this module standalone. A new run starts whenever either the
    inventory value or the skip status changes between consecutive days.

    Returns (kept_runs, skipped_run_count).
    """
    runs = []
    current_run = None
    for item in date_inventory:
        if current_run is None:
            current_run = {'start': item['date'], 'end': item['date'], 'inventory': item['inventory'], 'skip': item['skip']}
        elif item['inventory'] == current_run['inventory'] and item['skip'] == current_run['skip']:
            current_run['end'] = item['date']
        else:
            runs.append(current_run)
            current_run = {'start': item['date'], 'end': item['date'], 'inventory': item['inventory'], 'skip': item['skip']}
    if current_run is not None:
        runs.append(current_run)

    skipped_run_count = sum(1 for r in runs if r['skip'])
    kept_runs = [r for r in runs if not r['skip']]
    return kept_runs, skipped_run_count


def build_jobs_for_room_type(room_type_key, rows, cm_values, max_dates=None, skip_unchanged=True):
    """Build the flat list of (date range, room type) jobs for one room type
    from already-loaded allocation rows. Returns (jobs, skipped_run_count)."""
    config = FULL_ROOM_TYPE_CONFIG[room_type_key]
    cm_column = config.get('cm_column')

    date_inventory = []
    for row in rows:
        if config['csv_column'] not in row or row[config['csv_column']] is None:
            continue
        inventory = int(row[config['csv_column']])
        cm_current = cm_values.get(row['Date'], {}).get(cm_column) if cm_column else None
        is_unchanged = skip_unchanged and cm_current is not None and int(cm_current) == inventory
        date_obj = datetime.strptime(row['Date'], '%Y-%m-%d')
        date_inventory.append({
            'date': date_obj.strftime('%Y/%m/%d'),
            'inventory': inventory,
            'skip': is_unchanged,
        })
    if max_dates:
        date_inventory = date_inventory[:max_dates]

    runs, skipped_run_count = _build_date_ranges(date_inventory)
    jobs = [{
        'room_type': room_type_key,
        'label': config['label'],
        'checkbox_value': config['checkbox_value'],
        'start_date': r['start'],
        'end_date': r['end'],
        'number_of_rooms': r['inventory'],
    } for r in runs]
    return jobs, skipped_run_count


def build_full_plan(room_types=None, max_dates=None, skip_unchanged=True):
    """Read inventory_allocation.db (same source the production updaters use)
    and build the full flat list of (date range, room type) jobs that would
    need to be pushed. Purely local - no PMS login or network call.

    room_types: optional list of FULL_ROOM_TYPE_CONFIG keys to restrict to
    (defaults to all 13).
    """
    rows = load_allocation_rows()
    cm_values = load_cm_current_values() if skip_unchanged else {}

    keys = [k for k in (room_types or FULL_ROOM_TYPE_CONFIG.keys()) if k in FULL_ROOM_TYPE_CONFIG]

    plan = {'jobs': [], 'skipped_ranges': 0, 'by_room_type': {}}
    for key in keys:
        jobs, skipped = build_jobs_for_room_type(key, rows, cm_values, max_dates=max_dates, skip_unchanged=skip_unchanged)
        plan['jobs'].extend(jobs)
        plan['skipped_ranges'] += skipped
        plan['by_room_type'][key] = {'label': FULL_ROOM_TYPE_CONFIG[key]['label'], 'job_count': len(jobs)}
    return plan


def push_jobs_concurrent(jobs, company_id=1001, dry_run=True, max_workers=8, username=None, password=None):
    """Fire one PMS login, then push every job concurrently (bounded by
    max_workers). dry_run=True builds every payload without sending it.

    Returns a summary dict with per-job results, safe to return directly as a
    JSON API response.
    """
    started = time.monotonic()
    client = PMSApiClient(username=username, password=password)
    client.login()

    def run_one(job):
        remark = f"Updated from yield matrix - {job['label']} Online Inventory {job['number_of_rooms']}"
        payload_preview = {
            'CompanyId': company_id,
            'StartDate': job['start_date'],
            'EndDate': job['end_date'],
            'TypeId': job['checkbox_value'],
            'NoOfRoom': job['number_of_rooms'],
            'Remark': remark,
        }
        result = {'job': job, 'payload': payload_preview, 'success': None, 'response': None, 'error': None}
        if dry_run:
            result['success'] = True
            return result
        try:
            resp = client.save_allotment(
                company_id=company_id,
                start_date=job['start_date'],
                end_date=job['end_date'],
                type_id=job['checkbox_value'],
                no_of_rooms=job['number_of_rooms'],
                remark=remark,
            )
            result['response'] = resp
            result['success'] = bool(resp.get('IsSuccess'))
            if not result['success']:
                result['error'] = resp.get('Message') or resp.get('ReturnMessage')
        except PMSApiError as e:
            result['success'] = False
            result['error'] = str(e)
        return result

    results = []
    if jobs:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            results = list(pool.map(run_one, jobs))

    success_count = sum(1 for r in results if r['success'])
    return {
        'dry_run': dry_run,
        'total': len(results),
        'success_count': success_count,
        'failed_count': len(results) - success_count,
        'elapsed_seconds': time.monotonic() - started,
        'results': results,
    }
