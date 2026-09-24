"""Push BAR price levels into the D-EDGE / Availpro extranet.

This is the pricing counterpart to ``allotment_updater.py``. Where that
flow pushes *allotment* (room counts) into the hospitality PMS, this flow reads
the yield engine's ``inventory_allocation.db`` (table ``daily_inventory_allocation``,
columns ``Deluxe BAR Rate`` / ``Premiere BAR Rate`` with values ``BAR2``..``BAR7``)
and applies the matching price level to the BAR - Best Flexible Rate for the
Deluxe Room and Premiere Room via the extranet's "Apply a price level" screen.

The extranet screen (https://extranet.availpro.com/Plannings/en/22255/pricinggrid/apply)
works in four steps, all rebuilt fresh each time the page is (re)loaded:

  1. "Define period and level" - a react-calendar range picker (add one or more
     date ranges via the "Add" button) plus a native <select> price level.
  2. "Select rates"           - checkbox list; we keep only "BAR - Best Flexible Rate".
  3. "Select rooms"           - checkbox list; we keep only the target room.
  4. "Apply price level"      - commits; a "...applied successfully" banner appears.

To avoid the per-run "new device" email code, Chrome is launched against a
persistent ``--user-data-dir`` profile: authorise the device once by hand and the
trust cookie survives into every later run. Login/device creds are read from the
request args or the DEDGE_USERNAME / DEDGE_PASSWORD env vars.

Batching: for each room we collapse consecutive same-level days into contiguous
date ranges, group those ranges by price level, and do ONE "apply" per level
(stacking every range for that level into a single period definition). That turns
~50 daily runs into ~10 applies.
"""

import os
import time
import platform
import traceback
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException

from .bar_checkpoint import BarCheckpoint

from ...shared import log_queue
from ...inventory.allocation_repository import load_allocation_rows
from ...infrastructure.paths import get_dedge_profile_dir, get_data_dir

# --- Site / account configuration -------------------------------------------

HOTEL_ID = "22255"
START_URL = f"https://extranet.availpro.com/Planning/Monthly?hotelId={HOTEL_ID}&language=en"
APPLY_URL = f"https://extranet.availpro.com/Plannings/en/{HOTEL_ID}/pricinggrid/apply"

RATE_LABEL = "BAR - Best Flexible Rate"

# Years that actually have a BAR price-level structure created on the D-EDGE
# extranet. dedge_price_level() builds labels like "BAR 4 2027" from whatever
# year a date falls in, but selecting one that doesn't exist yet fails loudly
# (see define_period's NoSuchElementException handling) - so any allocation
# row outside this set is skipped before it gets that far. Add a year here
# once its price levels have been created on the extranet.
DEDGE_CONFIGURED_BAR_YEARS = {2026}

# Which allocation column drives each room, and the exact extranet room label.
ROOM_CONFIG = {
    "deluxe": {"column": "Deluxe BAR Rate", "room_label": "DELUXE-ROOM - Deluxe Room"},
    "premiere": {"column": "Premiere BAR Rate", "room_label": "PREMIERE-ROOM-KING - Premiere Room"},
}

# Persistent Chrome profile so the D-EDGE "trusted device" cookie survives runs.
DEFAULT_PROFILE_DIR = get_dedge_profile_dir()


def dedge_price_level(bar_rate, year):
    """Map a yield engine BAR code ('BAR3') to an extranet price-level label ('BAR 3 2026')."""
    n = int(str(bar_rate).upper().replace("BAR", "").strip())
    return f"BAR {n} {year}"


# --- Logging (mirrors update_pms_cm_allotment.log) --------------------------

def log(driver, message, type="info"):
    print(message)
    if driver is not None:
        try:
            driver.execute_script(f"console.log({message!r})")
        except Exception:
            pass
    try:
        log_queue.put({"type": type, "message": message})
    except Exception:
        pass


# --- Driver setup -----------------------------------------------------------

def setup_driver(user_data_dir=DEFAULT_PROFILE_DIR, headless=None):
    chrome_options = Options()
    # Headless when the caller asks for it, else fall back to the SELENIUM_HEADLESS
    # env var. Note: the *first* run needs to be visible so the D-EDGE device code
    # can be entered by hand - only go headless once the profile is trusted.
    if headless is None:
        headless = os.environ.get("SELENIUM_HEADLESS", "").lower() in ("1", "true", "yes")
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")

    # Persistent profile => the "new device" email code is only needed once.
    if user_data_dir:
        os.makedirs(user_data_dir, exist_ok=True)
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument("--profile-directory=Default")

    if platform.system() == "Darwin" and platform.machine() == "arm64":
        chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    return webdriver.Chrome(options=chrome_options)


def wait_for_page_load(driver, timeout=20):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


# --- Login / device authorisation -------------------------------------------

def _find_first(driver, selectors):
    for by, value in selectors:
        els = driver.find_elements(by, value)
        for el in els:
            if el.is_displayed():
                return el
    return None


def _wait_for_device_authorization(driver, timeout=300):
    """Pause here while a human enters the emailed device-verification code.

    Only useful when the browser is actually visible (headless=False) - there is
    no one to read the email or click otherwise. Once this passes, the trust
    cookie is written into the persistent Chrome profile and every later run
    (headless or not) skips this step entirely.
    """
    log(driver,
        "New device detected - D-EDGE emailed a verification code to authorize this "
        f"browser. Enter it in the open Chrome window within {timeout // 60} minutes...")
    WebDriverWait(driver, timeout).until(
        lambda d: "/Device" not in d.current_url and "extranet.availpro.com" in d.current_url
    )
    log(driver, "Device verified - trust is now stored in this Chrome profile for future runs")


def ensure_logged_in(driver, username, password, timeout=30):
    """Make sure we land on the extranet, logging in through D-EDGE if required.

    Returns True when the extranet is reachable. If a one-time device
    authorisation code is required (emailed, cannot be automated), this blocks
    until a human enters it in the visible browser window (see
    _wait_for_device_authorization) - only works with headless=False.
    """
    driver.get(APPLY_URL)
    wait_for_page_load(driver)
    time.sleep(1)
    url = driver.current_url

    if "extranet.availpro.com" in url and "/Device" not in url:
        log(driver, "Existing D-EDGE session is valid - skipping login")
        return True

    if "/Device" in url:
        _wait_for_device_authorization(driver)
        driver.get(APPLY_URL)
        wait_for_page_load(driver)
        if "extranet.availpro.com" not in driver.current_url:
            raise RuntimeError(f"Login did not reach the extranet (at {driver.current_url})")
        log(driver, "Logged in to D-EDGE successfully")
        return True

    # We are on the login domain. Step 1: username.
    log(driver, "Logging in to D-EDGE...")
    user_field = _find_first(driver, [
        (By.ID, "Username"), (By.NAME, "Username"),
        (By.CSS_SELECTOR, "input[type='text']:not([type='hidden'])"),
    ])
    if not user_field:
        raise RuntimeError("Could not find the D-EDGE username field")
    user_field.clear()
    user_field.send_keys(username)

    # Password may already be on this page, or behind a "Login" click.
    pwd_field = _find_first(driver, [(By.CSS_SELECTOR, "input[type='password']")])
    if not pwd_field:
        _click_login_button(driver)
        WebDriverWait(driver, timeout).until(
            lambda d: _find_first(d, [(By.CSS_SELECTOR, "input[type='password']")]) is not None
        )
        pwd_field = _find_first(driver, [(By.CSS_SELECTOR, "input[type='password']")])

    pwd_field.clear()
    pwd_field.send_keys(password)
    _click_login_button(driver)
    wait_for_page_load(driver)
    time.sleep(2)

    if "/Device" in driver.current_url:
        _wait_for_device_authorization(driver)

    # Re-navigate to the apply screen now that we are authenticated.
    driver.get(APPLY_URL)
    wait_for_page_load(driver)
    if "extranet.availpro.com" not in driver.current_url:
        raise RuntimeError(f"Login did not reach the extranet (at {driver.current_url})")
    log(driver, "Logged in to D-EDGE successfully")
    return True


def _click_login_button(driver):
    btn = _find_first(driver, [
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.XPATH, "//button[normalize-space()='Login']"),
        (By.CSS_SELECTOR, "input[type='submit']"),
    ])
    if not btn:
        raise RuntimeError("Could not find the D-EDGE login button")
    btn.click()


# --- "Apply a price level" building blocks ----------------------------------

def _js_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    driver.execute_script("arguments[0].click();", element)


def _open_apply_form(driver, timeout=30):
    """Load a fresh apply form (resets rates->all, rooms->all, no period)."""
    driver.get(APPLY_URL)
    wait_for_page_load(driver)
    WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Define period and level']"))
    )


def _click_calendar_day(driver, day, max_month_advances=24):
    """Click a react-calendar day tile, advancing months until it is visible."""
    label = f"{day.strftime('%B')} {day.day}, {day.year}"
    xpath = ("//button[contains(@class,'react-calendar__tile')]"
             f"[.//abbr[@aria-label='{label}']]")
    for _ in range(max_month_advances):
        tiles = driver.find_elements(By.XPATH, xpath)
        if tiles:
            tile = tiles[0]
            if tile.get_attribute("disabled"):
                raise RuntimeError(f"Calendar day {label} is disabled (in the past?)")
            _js_click(driver, tile)
            return
        nxt = driver.find_element(By.CSS_SELECTOR, "button.react-calendar__navigation__next-button")
        if nxt.get_attribute("disabled"):
            break
        _js_click(driver, nxt)
        time.sleep(0.2)
    raise RuntimeError(f"Could not locate calendar day {label}")


def _add_date_range(driver, start_day, end_day):
    """Fill the currently-active (last, empty) period row with a start/end range."""
    active_from = driver.find_elements(By.CSS_SELECTOR, "input[name='From']")[-1]
    # The react-calendar popup only opens on a *real* pointer click - a scripted
    # (execute_script) click does not activate it, so its day tiles never register.
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", active_from)
    active_from.click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".react-calendar"))
    )
    _click_calendar_day(driver, start_day)
    _click_calendar_day(driver, end_day)
    # Wait until this row's To value is populated (calendar closes on range complete).
    WebDriverWait(driver, 10).until(
        lambda d: d.find_elements(By.CSS_SELECTOR, "input[name='To']")[-1].get_attribute("value")
    )


def _dump_add_button_diagnostics(driver):
    """On a genuine (non-transient) Add-button timeout, save a screenshot and
    the outerHTML of every 'Add'-labelled button so the failure can be
    diagnosed from the artifacts instead of needing to reproduce it live."""
    try:
        data_dir = get_data_dir()
        screenshot_path = os.path.join(data_dir, 'bar_add_button_error.png')
        driver.save_screenshot(screenshot_path)
        buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Add']")
        html_path = os.path.join(data_dir, 'bar_add_button_error.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(f"Matched {len(buttons)} button[aria-label='Add'] element(s)\n\n")
            for i, btn in enumerate(buttons):
                f.write(f"--- button {i} ---\n")
                f.write(f"disabled attr: {btn.get_attribute('disabled')!r}\n")
                f.write(f"outerHTML: {btn.get_attribute('outerHTML')}\n\n")
        log(driver, f"Add-button diagnostics saved: {screenshot_path}, {html_path}")
    except Exception as diag_err:
        log(driver, f"Failed to save Add-button diagnostics: {diag_err}")


def _wait_add_button_enabled(driver, timeout=20):
    """Wait for the 'Add' button to become enabled, re-finding it once on a
    timeout. Under a longer chained session (scrape_cm -> allotment -> BAR
    back to back) the site can be slower to clear the disabled state than a
    standalone BAR run, and a cached element reference can also go stale if
    the row re-renders - so retry with a fresh lookup before giving up."""
    def enabled_add_button(d):
        try:
            button = d.find_element(By.CSS_SELECTOR, "button[aria-label='Add']")
            if button.is_enabled() and not button.get_attribute("disabled"):
                return button
        except (StaleElementReferenceException, NoSuchElementException):
            pass
        return False

    last_err = None
    for _attempt in range(2):
        try:
            return WebDriverWait(driver, timeout).until(enabled_add_button)
        except TimeoutException as e:
            last_err = e
    _dump_add_button_diagnostics(driver)
    raise last_err


def define_period(driver, ranges, price_level_label):
    """Open the period panel, stack every range, pick the level, and save."""
    _js_click(driver, driver.find_element(
        By.XPATH, "//button[normalize-space()='Define period and level']"))
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='From']"))
    )

    for i, (start_day, end_day) in enumerate(ranges):
        _add_date_range(driver, start_day, end_day)
        if i < len(ranges) - 1:
            # More ranges to come: commit this row and spawn a fresh empty one.
            # (Never leave a trailing empty row - it disables Save.)
            add_btn = _wait_add_button_enabled(driver)
            row_count = len(driver.find_elements(By.CSS_SELECTOR, "input[name='From']"))
            _js_click(driver, add_btn)
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.CSS_SELECTOR, "input[name='From']")) > row_count
            )

    level_select = Select(driver.find_element(By.CSS_SELECTOR, "select.avp-custom-select"))
    try:
        level_select.select_by_visible_text(price_level_label)
    except NoSuchElementException:
        available = [o.text for o in level_select.options if o.text.strip()]
        raise RuntimeError(
            f"Price level '{price_level_label}' does not exist on D-EDGE yet (available: {available}). "
            "This usually means next year's price-level structure hasn't been created on the "
            "extranet yet - create it there, then rerun (already-applied chunks are checkpointed "
            "and will be skipped)."
        )
    _click_panel_save(driver)
    # Panel collapses to a summary containing the chosen level.
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located(
            (By.XPATH, f"//*[contains(normalize-space(),'{price_level_label}')]"))
    )


def _select_only(driver, panel_button_text, item_label):
    """In a "Select rates"/"Select rooms" panel, keep only ``item_label`` checked."""
    _js_click(driver, driver.find_element(
        By.XPATH, f"//button[normalize-space()='{panel_button_text}']"))
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.ID, "selectTable-all"))
    )
    all_cb = driver.find_element(By.ID, "selectTable-all")
    if all_cb.is_selected():
        _js_click(driver, driver.find_element(By.CSS_SELECTOR, "label[for='selectTable-all']"))
        WebDriverWait(driver, 10).until(lambda d: not all_cb.is_selected())
    target = driver.find_element(
        By.XPATH, f"//label[contains(normalize-space(),\"{item_label}\")]")
    _js_click(driver, target)
    time.sleep(0.3)
    _click_panel_save(driver)
    time.sleep(0.5)


def _click_panel_save(driver):
    save = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Save']"))
    )
    _js_click(driver, save)


def _apply_price_level(driver, timeout=30):
    apply_btn = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Apply price level']"))
    )
    _js_click(driver, apply_btn)
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located(
            (By.XPATH, "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
                       "'abcdefghijklmnopqrstuvwxyz'),'applied successfully')]"))
    )


# --- Run building -----------------------------------------------------------

# D-EDGE's "Define period and level" panel permanently disables its "Add" button
# once a period holds this many date-range rows (confirmed live: the 11th row's
# Add button stayed disabled=true indefinitely - not a load/timing issue). A price
# level needing more ranges than this must be split across multiple applies.
MAX_RANGES_PER_APPLY = 10


def _chunk_ranges(ranges, size=MAX_RANGES_PER_APPLY):
    if size < 1:
        raise ValueError("Chunk size must be positive")
    return [ranges[i:i + size] for i in range(0, len(ranges), size)]


def build_level_groups(rows, column):
    """Collapse consecutive same-level days into ranges, grouped by price level.

    Returns a dict keyed by (year, bar_rate) -> list of (start_date, end_date)
    datetime pairs. Rows must be date-sorted; a gap in the calendar (or a change
    of bar value) starts a new range.
    """
    dated = []
    for row in rows:
        bar = row.get(column)
        if not bar:
            continue
        dated.append((datetime.strptime(row["Date"], "%Y-%m-%d"), str(bar)))
    dated.sort(key=lambda x: x[0])

    runs = []  # (start, end, bar)
    cur = None
    for day, bar in dated:
        if cur and bar == cur[2] and day.year == cur[0].year and day == cur[1] + timedelta(days=1):
            cur = (cur[0], day, cur[2])
        else:
            if cur:
                runs.append(cur)
            cur = (day, day, bar)
    if cur:
        runs.append(cur)

    groups = {}
    for start, end, bar in runs:
        groups.setdefault((start.year, bar), []).append((start, end))
    return groups


def _planned_chunks(rows, rooms, max_levels_per_room):
    """Canonical fingerprint input for safe resumption after partial failures."""
    plan = []
    for room in rooms:
        if room not in ROOM_CONFIG:
            continue
        groups = build_level_groups(rows, ROOM_CONFIG[room]["column"])
        for idx, ((year, bar_rate), ranges) in enumerate(sorted(groups.items())):
            if max_levels_per_room and idx >= max_levels_per_room:
                break
            for chunk in _chunk_ranges(ranges):
                plan.append(_chunk_identity(room, dedge_price_level(bar_rate, year), chunk))
    return plan


def _chunk_identity(room, level_label, chunk):
    return [room, level_label, [[start.isoformat(), end.isoformat()] for start, end in chunk]]


# --- Main entry point -------------------------------------------------------

def update_bar(driver=None, username=None, password=None,
               rooms=("deluxe", "premiere"), user_data_dir=DEFAULT_PROFILE_DIR,
               dry_run=False, max_levels_per_room=None, headless=None,
               reset_checkpoint=False):
    """Apply yield engine BAR levels to the extranet for the given rooms.

    dry_run: build and log every apply plan but stop before clicking the final
             "Apply price level" (safe rehearsal against the live site).
    max_levels_per_room: cap the number of price-level groups per room (testing).
    reset_checkpoint: explicitly discard a checkpoint if starting a new run
                      after a partial failure or after intentional external edits.
    headless: run Chrome headless (None -> honour the SELENIUM_HEADLESS env var).
              Only use headless once the profile's device is trusted.
    Credentials fall back to the DEDGE_USERNAME / DEDGE_PASSWORD env vars.
    """
    username = username or os.environ.get("DEDGE_USERNAME", "")
    password = password or os.environ.get("DEDGE_PASSWORD", "")

    owns_driver = driver is None
    try:
        if driver is None:
            driver = setup_driver(user_data_dir, headless=headless)

        ensure_logged_in(driver, username, password)

        rows = load_allocation_rows()
        log(driver, f"Loaded {len(rows)} allocation rows from inventory_allocation.db")

        in_scope = [r for r in rows if int(r["Date"][:4]) in DEDGE_CONFIGURED_BAR_YEARS]
        skipped = len(rows) - len(in_scope)
        if skipped:
            skipped_years = sorted({r["Date"][:4] for r in rows if int(r["Date"][:4]) not in DEDGE_CONFIGURED_BAR_YEARS})
            log(driver, f"Skipping {skipped} row(s) in {', '.join(skipped_years)} - no price-level structure "
                        f"created on D-EDGE yet for that year (only {sorted(DEDGE_CONFIGURED_BAR_YEARS)} configured)")
        rows = in_scope

        checkpoint = BarCheckpoint(
            _planned_chunks(rows, rooms, max_levels_per_room),
            reset=reset_checkpoint, dry_run=dry_run,
        )
        if checkpoint.resumed:
            log(driver, f"Resuming BAR run: {len(checkpoint.completed)} previously confirmed chunk(s) will be skipped")

        total_applied = 0
        for room_key in rooms:
            if room_key not in ROOM_CONFIG:
                log(driver, f"Skipping unknown room '{room_key}'", type="error")
                continue
            cfg = ROOM_CONFIG[room_key]
            groups = build_level_groups(rows, cfg["column"])
            log(driver, f"\n=== {cfg['room_label']} : {len(groups)} price levels to apply ===")

            processed = 0
            for (year, bar_rate), ranges in sorted(groups.items()):
                if max_levels_per_room and processed >= max_levels_per_room:
                    log(driver, f"Reached max_levels_per_room={max_levels_per_room}, stopping this room")
                    break
                level_label = dedge_price_level(bar_rate, year)
                pretty = ", ".join(f"{s.strftime('%Y-%m-%d')}->{e.strftime('%Y-%m-%d')}"
                                   for s, e in ranges)
                log(driver, f"\n[{cfg['room_label']}] {level_label}  ({len(ranges)} ranges: {pretty})")

                chunks = _chunk_ranges(ranges)
                if len(chunks) > 1:
                    log(driver, f"  {len(ranges)} ranges exceeds the {MAX_RANGES_PER_APPLY}-row D-EDGE limit per apply - "
                                f"splitting into {len(chunks)} applies")

                for chunk_idx, chunk in enumerate(chunks, start=1):
                    chunk_id = _chunk_identity(room_key, level_label, chunk)
                    if checkpoint.contains(chunk_id):
                        log(driver, f"  Already applied chunk {chunk_idx}/{len(chunks)} in the previous run; skipping")
                        continue
                    if len(chunks) > 1:
                        log(driver, f"  -- chunk {chunk_idx}/{len(chunks)}: {len(chunk)} ranges --")
                    _open_apply_form(driver)
                    define_period(driver, chunk, level_label)
                    _select_only(driver, "Select rates", RATE_LABEL)
                    _select_only(driver, "Select rooms", cfg["room_label"])

                    if dry_run:
                        log(driver, "  [dry-run] configured everything, NOT clicking 'Apply price level'")
                    else:
                        _apply_price_level(driver)
                        checkpoint.mark(chunk_id)
                        log(driver, f"  Applied {level_label} to {cfg['room_label']} successfully")
                        total_applied += 1
                processed += 1

        if not dry_run:
            checkpoint.finish()
        log(driver, f"\nDone. {total_applied} price-level applies committed"
                    f"{' (dry-run: 0 committed)' if dry_run else ''}.")
        return True

    except Exception as e:
        tb = traceback.format_exc()
        # First line of the traceback's final frame tells us exactly where it broke.
        summary = str(e).splitlines()[0] if str(e).strip() else e.__class__.__name__
        log(driver, f"An error occurred ({e.__class__.__name__}): {summary}", type="error")
        for line in tb.strip().splitlines()[-6:]:
            log(driver, f"  {line}", type="error")
        return False
    finally:
        if owns_driver and driver:
            # Leave the browser open for inspection, matching the PMS flow's habit.
            pass


if __name__ == "__main__":
    drv = setup_driver()
    try:
        # Rehearse safely first: dry_run leaves the site unchanged.
        update_bar(drv, rooms=("deluxe", "premiere"), dry_run=True, max_levels_per_room=1)
    finally:
        pass
