from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException, ElementNotInteractableException
import time
import platform
from datetime import datetime
import os
from selenium.webdriver.common.keys import Keys
from ..shared import log_queue
from .allocation_store import load_allocation_rows

# Room types not covered by update_pms_cm_allotment.py (Deluxe Room / Premiere Room).
# Each maps to exactly one PMS checkbox value, verified live in the "Add Room" modal
# at https://fo.hospitality.mykg.id/allotment/detail?companyid=1001. Deluxe Pool Access
# and Premiere Room Lagoon Access are each a sum of two PMS codes for reading purposes
# (see process_pms_inventory.py), but - matching the existing Deluxe/Premiere precedent
# of writing to only one representative code - are written to a single checkbox only
# (DLTP / PRKL respectively), not both.
REST_ROOM_TYPE_CONFIG = {
    'Deluxe Suite Room': {'csv_column': 'Deluxe Suite Room Online Inventory', 'checkbox_value': 'DLS'},
    'Family Premiere Room': {'csv_column': 'Family Premiere Room Online Inventory', 'checkbox_value': 'FAM'},
    'Premiere Suite Room': {'csv_column': 'Premiere Suite Room Online Inventory', 'checkbox_value': 'PSU'},
    'Beach Front Private Suite Room': {'csv_column': 'Beach Front Private Suite Room Online Inventory', 'checkbox_value': 'BFS'},
    'The Anvaya Suite Whirpool': {'csv_column': 'The Anvaya Suite Whirpool Online Inventory', 'checkbox_value': 'ASW'},
    'The Anvaya Suite No Pool': {'csv_column': 'The Anvaya Suite No Pool Online Inventory', 'checkbox_value': 'AVS'},
    'The Anvaya Suite With Pool': {'csv_column': 'The Anvaya Suite With Pool Online Inventory', 'checkbox_value': 'ASP'},
    'The Anvaya Residence': {'csv_column': 'The Anvaya Residence Online Inventory', 'checkbox_value': 'AVR'},
    'The Anvaya Villa': {'csv_column': 'The Anvaya Villa Online Inventory', 'checkbox_value': 'AVP'},
    'Deluxe Pool Access': {'csv_column': 'Deluxe Pool Access Online Inventory', 'checkbox_value': 'DLTP'},
    'Premiere Room Lagoon Access': {'csv_column': 'Premiere Room Lagoon Access Online Inventory', 'checkbox_value': 'PRKL'},
}

MAX_DATE_RANGES_PER_SAVE = 5


def wait_for_toast_disappear(driver, timeout=10):
    """Wait for toast message to disappear"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "toast-message"))
        )
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CLASS_NAME, "toast-message"))
        )
        return True
    except TimeoutException:
        return False


def wait_for_page_load(driver, timeout=10):
    """Wait for page to finish loading"""
    return WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )


def wait_for_element_presence(driver, by, value, timeout=10, description="element"):
    """Helper function to wait for element presence with better error handling"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        print(f"Timeout waiting for {description} to be present")
        return None
    except Exception as e:
        print(f"Error finding {description}: {e}")
        return None


def wait_and_click(driver, by, value, timeout=10, description="element"):
    """Helper function to wait for and click an element with better error handling"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        WebDriverWait(driver, 2).until(
            lambda d: element.is_displayed() and element.is_enabled()
        )
        element.click()
        return True
    except TimeoutException:
        print(f"Timeout waiting for {description} to be clickable")
        return False
    except ElementClickInterceptedException:
        print(f"Click intercepted on {description}, trying JavaScript click")
        try:
            driver.execute_script("arguments[0].click();", element)
            return True
        except Exception as e:
            print(f"JavaScript click failed: {e}")
            return False
    except Exception as e:
        print(f"Error clicking {description}: {e}")
        return False


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')

    if platform.system() == 'Darwin' and platform.machine() == 'arm64':
        chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def log(driver, message, type='info'):
    """Log message to both console and browser, and send to queue for streaming"""
    print(message)
    try:
        driver.execute_script(f"console.log({repr(message)})")
    except Exception as e:
        print(f"Could not log to browser console: {e}")

    try:
        log_queue.put({
            'type': type,
            'message': message
        })
    except Exception as e:
        print(f"Could not send log to queue: {e}")


def add_date_range(driver, start_date, end_date):
    """Add a date range to the form"""
    log(driver, f"Adding date range: {start_date} to {end_date}")

    start_date_input = wait_for_element_presence(driver, By.ID, "txtStartDate", description="start date input")
    if not start_date_input:
        raise Exception("Could not find start date input field")

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", start_date_input)
    time.sleep(0.5)

    driver.execute_script("arguments[0].value = '';", start_date_input)
    time.sleep(0.5)

    log(driver, f"Setting start date value to: {start_date}")
    driver.execute_script(f"arguments[0].value = '{start_date}';", start_date_input)
    time.sleep(0.5)

    start_date_value = start_date_input.get_attribute('value')
    log(driver, f"Start date value after setting: {start_date_value}")

    end_date_input = wait_for_element_presence(driver, By.ID, "txtEndDate", description="end date input")
    if not end_date_input:
        raise Exception("Could not find end date input field")

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", end_date_input)
    time.sleep(0.5)

    driver.execute_script("arguments[0].value = '';", end_date_input)
    time.sleep(0.5)

    log(driver, f"Setting end date value to: {end_date}")
    driver.execute_script(f"arguments[0].value = '{end_date}';", end_date_input)
    time.sleep(0.5)

    end_date_value = end_date_input.get_attribute('value')
    log(driver, f"End date value after setting: {end_date_value}")

    time.sleep(1)

    final_start_date = start_date_input.get_attribute('value')
    final_end_date = end_date_input.get_attribute('value')

    log(driver, f"Final start date: {final_start_date}")
    log(driver, f"Final end date: {final_end_date}")

    if not final_start_date or not final_end_date:
        if not final_start_date:
            driver.execute_script(f"arguments[0].value = '{start_date}';", start_date_input)
            time.sleep(0.5)
        if not final_end_date:
            driver.execute_script(f"arguments[0].value = '{end_date}';", end_date_input)
            time.sleep(0.5)

        final_start_date = start_date_input.get_attribute('value')
        final_end_date = end_date_input.get_attribute('value')

        if not final_start_date or not final_end_date:
            raise Exception(f"Failed to set dates correctly. Start: {final_start_date} (expected {start_date}), End: {final_end_date} (expected {end_date})")

    add_date_button = wait_for_element_presence(driver, By.ID, "ModalAddRoomAddDateButton", description="Add Date button")
    if not add_date_button:
        raise Exception("Could not find Add Date button")

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_date_button)
    time.sleep(0.5)

    try:
        add_date_button.click()
    except:
        driver.execute_script("arguments[0].click();", add_date_button)

    time.sleep(1)
    log(driver, "Successfully added date range")


def handle_sweet_alert(driver, timeout=10):
    """Handle sweet alert dialog (this site uses SweetAlert v1, not SweetAlert2)"""
    try:
        alert = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".sweet-alert.visible"))
        )

        try:
            message_element = alert.find_element(By.TAG_NAME, "p")
            message = message_element.text if message_element else "No message found"
        except NoSuchElementException:
            message = "No message found"
        log(driver, f"Sweet alert message: {message}")

        confirm_button = alert.find_element(By.CSS_SELECTOR, ".sa-button-container .confirm")
        if confirm_button:
            confirm_button.click()
            time.sleep(1)
            return True

        return False
    except TimeoutException:
        log(driver, "No sweet alert found within timeout period")
        return False
    except Exception as e:
        log(driver, f"Error handling sweet alert: {str(e)}")
        return False


def build_batches(allocation_rows):
    """
    Read the daily allocation rows and produce a flat list of batch jobs
    that push all 11 REST_ROOM_TYPE_CONFIG room types to the PMS with as few
    "Add Room" modal submissions as possible.

    Each batch job is a dict: {'date_ranges': [(start, end), ...], 'checkbox_values': [...], 'number_of_rooms': int}

    Algorithm:
    1. Per room type, collapse consecutive equal-value days into contiguous (start, end, value) runs.
    2. Group runs that share the exact same (start, end, value) across room types -
       these can be checked together in a single Save (this is what fires whenever the
       Occupancy >= 95 override in yielder.py zeroes all 11 room types on the same days).
    3. Re-key by (frozenset(room_types), value) so separate date windows sharing the same
       room-type set and value can be packed as multiple ranges in one modal too.
    4. Chunk each group's date ranges into batches of up to MAX_DATE_RANGES_PER_SAVE.
    """
    rows = []
    for row in allocation_rows:
        date_obj = datetime.strptime(row['Date'], '%Y-%m-%d')
        rows.append({
            'date': date_obj.strftime('%m/%d/%Y'),
            **{room_type: int(row[config['csv_column']]) for room_type, config in REST_ROOM_TYPE_CONFIG.items()}
        })

    # Step 1: per-room-type contiguous runs
    runs_by_room_type = {}
    for room_type in REST_ROOM_TYPE_CONFIG:
        runs = []
        current_run = None
        for row in rows:
            value = row[room_type]
            if current_run is None:
                current_run = {'start': row['date'], 'end': row['date'], 'value': value}
            elif value == current_run['value']:
                current_run['end'] = row['date']
            else:
                runs.append(current_run)
                current_run = {'start': row['date'], 'end': row['date'], 'value': value}
        if current_run is not None:
            runs.append(current_run)
        runs_by_room_type[room_type] = runs

    # Step 2: group by exact (start, end, value) across room types
    exact_groups = {}
    for room_type, runs in runs_by_room_type.items():
        for run in runs:
            key = (run['start'], run['end'], run['value'])
            exact_groups.setdefault(key, []).append(room_type)

    # Step 3: re-key by (frozenset(room_types), value) -> list of (start, end)
    set_groups = {}
    for (start, end, value), room_types in exact_groups.items():
        key = (frozenset(room_types), value)
        set_groups.setdefault(key, []).append((start, end))

    # Step 4: chunk into batches of up to MAX_DATE_RANGES_PER_SAVE date ranges
    batches = []
    for (room_type_set, value), date_ranges in set_groups.items():
        checkbox_values = [REST_ROOM_TYPE_CONFIG[rt]['checkbox_value'] for rt in room_type_set]
        for i in range(0, len(date_ranges), MAX_DATE_RANGES_PER_SAVE):
            chunk = date_ranges[i:i + MAX_DATE_RANGES_PER_SAVE]
            batches.append({
                'room_types': sorted(room_type_set),
                'checkbox_values': checkbox_values,
                'number_of_rooms': value,
                'date_ranges': chunk,
            })

    return batches


def update_rest_allotment(driver=None, username=None, password=None, max_dates=None):
    """
    Login to the website, select the hotel brand, and push online-inventory allotment
    for all 11 REST_ROOM_TYPE_CONFIG room types (everything except Deluxe/Premiere,
    which are handled separately by update_pms_cm_allotment.py).

    max_dates: if set, only process the first N dates worth of batches (for testing).
    Credentials fall back to the PMS_USERNAME / PMS_PASSWORD env vars when not passed.
    """
    username = username or os.environ.get("PMS_USERNAME", "")
    password = password or os.environ.get("PMS_PASSWORD", "")
    try:
        if driver is None:
            driver = setup_driver()

        driver.get("https://fo.hospitality.mykg.id/")
        log(driver, "Navigating to Hospitality Suite website...")

        wait_for_page_load(driver)

        username_field = wait_for_element_presence(driver, By.ID, "txtUsername", timeout=15, description="username field")
        if not username_field:
            raise Exception("Username field not found")

        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "txtUsername"))
        )
        username_field.clear()
        username_field.send_keys(username)

        password_field = driver.find_element(By.ID, "txtPassword")
        password_field.clear()
        password_field.send_keys(password)

        if not wait_and_click(driver, By.ID, "btnLogin", description="login button"):
            raise Exception("Failed to click login button")

        log(driver, "Login credentials entered...")

        wait_for_page_load(driver)
        wait_for_toast_disappear(driver)

        log(driver, "Waiting for brand dropdown to be ready...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "className"))
        )
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "className"))
        )

        brand_select_elem = driver.find_element(By.ID, "className")
        if not brand_select_elem:
            raise Exception("Brand dropdown not found")

        def brand_options_loaded(driver):
            try:
                brand_select = Select(driver.find_element(By.ID, "className"))
                options = [o.text for o in brand_select.options]
                log(driver, f"Current brand options: {options}")
                return len(options) > 1
            except:
                return False

        log(driver, "Waiting for brand options to load...")
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                WebDriverWait(driver, 15).until(brand_options_loaded)
                break
            except TimeoutException:
                if attempt < max_attempts - 1:
                    log(driver, f"Attempt {attempt + 1} failed, brand options never populated - reloading page and retrying...")
                    driver.get(driver.current_url)
                    wait_for_page_load(driver)
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.ID, "className"))
                    )
                else:
                    raise Exception("Brand options failed to load after multiple attempts")

        brand_select = Select(brand_select_elem)
        available_options = [option.text for option in brand_select.options]
        log(driver, f"Available brand options: {available_options}")

        brand_name_variations = ["The ANVAYA", "THE ANVAYA", "The Anvaya", "THE ANVAYA BEACH RESORT BALI"]
        selected = False

        for brand_name in brand_name_variations:
            try:
                log(driver, f"Attempting to select brand: {brand_name}")
                brand_select.select_by_visible_text(brand_name)
                selected = True
                log(driver, f"Successfully selected brand: {brand_name}")
                break
            except NoSuchElementException:
                log(driver, f"Brand name '{brand_name}' not found in dropdown")
                continue

        if not selected:
            raise Exception(f"Could not find any matching brand name. Available options: {available_options}")

        def hotel_option_loaded(driver):
            try:
                hotel_select_elem = driver.find_element(By.ID, "hotelName")
                options = [o.text for o in hotel_select_elem.find_elements(By.TAG_NAME, "option")]
                log(driver, f"Available hotel options: {options}")
                return len(options) > 1
            except Exception as e:
                log(driver, f"Error checking hotel options: {str(e)}")
                return False

        log(driver, "Waiting for hotel options to load...")
        WebDriverWait(driver, 15).until(hotel_option_loaded)

        hotel_select_elem = driver.find_element(By.ID, "hotelName")
        hotel_select = Select(hotel_select_elem)
        log(driver, "Attempting to select hotel: The ANVAYA Beach Resort Bali")
        hotel_select.select_by_visible_text("The ANVAYA Beach Resort Bali")
        log(driver, "Hotel selected successfully")

        wait_for_page_load(driver)

        rate_management_link = wait_for_element_presence(
            driver,
            By.CSS_SELECTOR,
            'a[data-appid="4"]',
            timeout=15,
            description="Rate Management menu"
        )
        if not rate_management_link:
            raise Exception("Rate Management menu not found")

        if not wait_and_click(driver, By.CSS_SELECTOR, 'a[data-appid="4"]', description="Rate Management menu"):
            raise Exception("Failed to click Rate Management menu")

        wait_for_page_load(driver)

        log(driver, "Looking for Allotment menu...")
        allotment_link = wait_for_element_presence(
            driver,
            By.XPATH,
            "//span[contains(text(), 'Allotment')]/parent::a",
            timeout=15,
            description="Allotment menu"
        )
        if not allotment_link:
            raise Exception("Allotment menu not found")

        if not wait_and_click(driver, By.XPATH, "//span[contains(text(), 'Allotment')]/parent::a", description="Allotment menu"):
            raise Exception("Failed to click Allotment menu")

        wait_for_page_load(driver)
        log(driver, "Successfully clicked Allotment menu")

        log(driver, "Navigating to allotment detail page...")
        driver.get("https://fo.hospitality.mykg.id/allotment/detail?companyid=1001")

        wait_for_page_load(driver)
        log(driver, "Successfully navigated to allotment detail page")

        log(driver, "Reading allocation data and building batches...")
        try:
            batches = build_batches(load_allocation_rows())
        except Exception as e:
            log(driver, f"Error reading allocation data: {str(e)}")
            raise

        if max_dates:
            batches = batches[:max_dates]
            log(driver, f"Limiting test run to first {len(batches)} batches")

        log(driver, f"Built {len(batches)} batches covering {len(REST_ROOM_TYPE_CONFIG)} room types")

        for batch_index, batch in enumerate(batches):
            log(driver, f"\nProcessing batch {batch_index + 1} of {len(batches)}: "
                         f"room types {batch['room_types']}, inventory {batch['number_of_rooms']}")

            if not wait_and_click(driver, By.ID, "btnAddRoom", description="Add Allotment Room button"):
                raise Exception("Failed to click Add Allotment Room button")

            modal = wait_for_element_presence(driver, By.ID, "modalAddRoom", timeout=15, description="Add Room modal")
            if not modal:
                raise Exception("Modal did not appear after clicking Add Allotment Room button")

            WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.ID, "txtStartDate"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", modal)
            time.sleep(1)

            for start, end in batch['date_ranges']:
                log(driver, f"    Adding range: {start} to {end} (inventory: {batch['number_of_rooms']})")
                add_date_range(driver, start, end)

            for checkbox_value in batch['checkbox_values']:
                log(driver, f"Selecting room type checkbox '{checkbox_value}'...")
                room_type_checkbox = wait_for_element_presence(
                    driver, By.XPATH,
                    f"//input[@type='checkbox' and @id='lstRoomType' and @value='{checkbox_value}']",
                    description=f"'{checkbox_value}' room type checkbox"
                )
                if not room_type_checkbox:
                    raise Exception(f"Could not find room type checkbox ({checkbox_value})")
                driver.execute_script("arguments[0].scrollIntoView(true);", room_type_checkbox)
                time.sleep(0.3)
                if not room_type_checkbox.is_selected():
                    try:
                        room_type_checkbox.click()
                    except:
                        driver.execute_script("arguments[0].click();", room_type_checkbox)

            log(driver, "Setting number of rooms...")
            number_of_rooms = wait_for_element_presence(driver, By.ID, "txtNumberOfRoom", description="number of rooms input")
            if not number_of_rooms:
                raise Exception("Could not find number of rooms input field")
            driver.execute_script("arguments[0].scrollIntoView(true);", number_of_rooms)
            time.sleep(0.5)
            try:
                number_of_rooms.clear()
                number_of_rooms.send_keys(str(batch['number_of_rooms']))
            except ElementNotInteractableException:
                driver.execute_script(
                    "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
                    number_of_rooms, str(batch['number_of_rooms'])
                )
            log(driver, f"Set number of rooms to {batch['number_of_rooms']}")

            log(driver, "Adding remark...")
            remark_textarea = wait_for_element_presence(driver, By.ID, "txtRemarkAllotment", description="remark textarea")
            if not remark_textarea:
                raise Exception("Could not find remark textarea")
            driver.execute_script("arguments[0].scrollIntoView(true);", remark_textarea)
            time.sleep(0.2)
            remark_text = (f"Updated from CSV data - {', '.join(batch['room_types'])} "
                            f"Online Inventory {batch['number_of_rooms']}, batch {batch_index + 1} of {len(batches)}")
            try:
                remark_textarea.clear()
                remark_textarea.send_keys(remark_text)
            except ElementNotInteractableException:
                driver.execute_script(
                    "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
                    remark_textarea, remark_text
                )
            log(driver, "Added remark")

            log(driver, "Clicking Save button...")
            save_button = wait_for_element_presence(driver, By.ID, "btnSaveRoomAllotment", description="save button")
            if not save_button:
                raise Exception("Could not find save button")
            driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
            time.sleep(0.2)
            try:
                save_button.click()
            except (ElementNotInteractableException, ElementClickInterceptedException):
                driver.execute_script("arguments[0].click();", save_button)
            log(driver, "Clicked Save button")
            time.sleep(1)

            if not handle_sweet_alert(driver):
                log(driver, "Failed to handle sweet alert")
                raise Exception("Failed to handle sweet alert")
            wait_for_toast_disappear(driver)
            log(driver, f"Successfully processed batch {batch_index + 1} of {len(batches)}")
            time.sleep(2)

        log(driver, "Successfully processed all room types from CSV")
        return True

    except Exception as e:
        log(driver, f"An error occurred: {str(e)}")
        return False


if __name__ == "__main__":
    driver = setup_driver()
    try:
        if update_rest_allotment(driver):
            print("Successfully updated the rest of the room types")
        else:
            print("Failed to update the rest of the room types")
    finally:
        pass
