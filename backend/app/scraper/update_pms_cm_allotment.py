from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
import time
import platform
import csv
from datetime import datetime
import os
from selenium.webdriver.common.keys import Keys
from ..shared import log_queue

def wait_for_toast_disappear(driver, timeout=10):
    """Wait for toast message to disappear"""
    try:
        # Wait for toast to appear
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "toast-message"))
        )
        # Wait for toast to disappear
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
        # Add a small delay before clicking to ensure the element is truly ready
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
    # Set up Chrome options
    chrome_options = Options()
    # chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-gpu')  # Required for headless on some systems
    chrome_options.add_argument('--disable-software-rasterizer')  # Better performance in headless
    
    # Add specific options for Mac ARM64
    if platform.system() == 'Darwin' and platform.machine() == 'arm64':
        chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    
    # Initialize the Chrome driver
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def log(driver, message, type='info'):
    """Log message to both console and browser, and send to queue for streaming"""
    print(message)
    try:
        driver.execute_script(f"console.log({repr(message)})")
    except Exception as e:
        print(f"Could not log to browser console: {e}")
    
    # Send log to queue for streaming
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
    
    # Set start date
    start_date_input = wait_for_element_presence(driver, By.ID, "txtStartDate", description="start date input")
    if not start_date_input:
        raise Exception("Could not find start date input field")
    
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", start_date_input)
    time.sleep(0.5)
    
    # Clear and set start date value directly first
    driver.execute_script("arguments[0].value = '';", start_date_input)
    time.sleep(0.5)
    
    # Set the start date value
    log(driver, f"Setting start date value to: {start_date}")
    driver.execute_script(f"arguments[0].value = '{start_date}';", start_date_input)
    time.sleep(0.5)
    
    # Verify start date was set
    start_date_value = start_date_input.get_attribute('value')
    log(driver, f"Start date value after setting: {start_date_value}")
    
    # Parse the start date
    start_date_obj = datetime.strptime(start_date, '%m/%d/%Y')
    start_day = str(start_date_obj.day)
    
    # Set end date
    end_date_input = wait_for_element_presence(driver, By.ID, "txtEndDate", description="end date input")
    if not end_date_input:
        raise Exception("Could not find end date input field")
    
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", end_date_input)
    time.sleep(0.5)
    
    # Clear and set end date value directly first
    driver.execute_script("arguments[0].value = '';", end_date_input)
    time.sleep(0.5)
    
    # Set the end date value
    log(driver, f"Setting end date value to: {end_date}")
    driver.execute_script(f"arguments[0].value = '{end_date}';", end_date_input)
    time.sleep(0.5)
    
    # Verify end date was set
    end_date_value = end_date_input.get_attribute('value')
    log(driver, f"End date value after setting: {end_date_value}")
    
    # Parse the end date
    end_date_obj = datetime.strptime(end_date, '%m/%d/%Y')
    end_day = str(end_date_obj.day)
    
    # Wait a moment to ensure dates are properly set
    time.sleep(1)
    
    # Verify both dates are set correctly before proceeding
    final_start_date = start_date_input.get_attribute('value')
    final_end_date = end_date_input.get_attribute('value')
    
    log(driver, f"Final start date: {final_start_date}")
    log(driver, f"Final end date: {final_end_date}")
    
    if not final_start_date or not final_end_date:
        # Try setting the dates one more time if they were cleared
        if not final_start_date:
            driver.execute_script(f"arguments[0].value = '{start_date}';", start_date_input)
            time.sleep(0.5)
        if not final_end_date:
            driver.execute_script(f"arguments[0].value = '{end_date}';", end_date_input)
            time.sleep(0.5)
        
        # Check one final time
        final_start_date = start_date_input.get_attribute('value')
        final_end_date = end_date_input.get_attribute('value')
        
        if not final_start_date or not final_end_date:
            raise Exception(f"Failed to set dates correctly. Start: {final_start_date} (expected {start_date}), End: {final_end_date} (expected {end_date})")
    
    # Click Add Date button
    add_date_button = wait_for_element_presence(driver, By.ID, "ModalAddRoomAddDateButton", description="Add Date button")
    if not add_date_button:
        raise Exception("Could not find Add Date button")
    
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_date_button)
    time.sleep(0.5)
    
    try:
        add_date_button.click()
    except:
        driver.execute_script("arguments[0].click();", add_date_button)
    
    # Wait for the new date range to be added and verify it was added
    time.sleep(1)
    log(driver, "Successfully added date range")

def handle_sweet_alert(driver, timeout=10):
    """Handle sweet alert dialog"""
    try:
        # Wait for sweet alert to appear
        alert = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "swal2-container"))
        )
        
        # Get alert message
        message_element = alert.find_element(By.CLASS_NAME, "swal2-html-container")
        message = message_element.text if message_element else "No message found"
        log(driver, f"Sweet alert message: {message}")
        
        # Find and click the confirm button
        confirm_button = alert.find_element(By.CLASS_NAME, "swal2-confirm")
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

def update_allotmet(driver=None, username="krisnatha", password="Nasibungkus13"):
    """
    Login to the website and select the hotel brand
    Returns True if successful, False otherwise
    """
    try:
        # If no driver is provided, create a new one
        if driver is None:
            driver = setup_driver()
            should_quit_driver = False
        else:
            should_quit_driver = False

        # Navigate to the website
        driver.get("https://fo.hospitality.mykg.id/")
        log(driver, "Navigating to Hospitality Suite website...")
        
        # Wait for page to load completely
        wait_for_page_load(driver)
        
        # Wait for the username field to be present and interactable
        username_field = wait_for_element_presence(driver, By.ID, "txtUsername", timeout=15, description="username field")
        if not username_field:
            raise Exception("Username field not found")
        
        # Ensure the field is interactable
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "txtUsername"))
        )
        username_field.clear()
        username_field.send_keys(username)
        
        password_field = driver.find_element(By.ID, "txtPassword")
        password_field.clear()
        password_field.send_keys(password)
        
        # Click the login button
        if not wait_and_click(driver, By.ID, "btnLogin", description="login button"):
            raise Exception("Failed to click login button")
        
        log(driver, "Login credentials entered...")
        
        # Wait for login to complete
        wait_for_page_load(driver)
        wait_for_toast_disappear(driver)
        
        # Wait for the brand dropdown to be present and interactable
        log(driver, "Waiting for brand dropdown to be ready...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "className"))
        )
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, "className"))
        )
        
        # Wait for the brand dropdown and select "The ANVAYA"
        brand_select_elem = driver.find_element(By.ID, "className")
        if not brand_select_elem:
            raise Exception("Brand dropdown not found")
        
        # Wait for brand options to be populated
        def brand_options_loaded(driver):
            try:
                brand_select = Select(driver.find_element(By.ID, "className"))
                options = [o.text for o in brand_select.options]
                log(driver, f"Current brand options: {options}")
                return len(options) > 1  # More than just "Select Brand"
            except:
                return False
            
        log(driver, "Waiting for brand options to load...")
        # Try multiple times to wait for options
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                WebDriverWait(driver, 15).until(brand_options_loaded)
                break
            except TimeoutException:
                if attempt < max_attempts - 1:
                    log(driver, f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(2)  # Wait before retrying
                else:
                    raise Exception("Brand options failed to load after multiple attempts")
        
        # Print all available options for debugging
        brand_select = Select(brand_select_elem)
        available_options = [option.text for option in brand_select.options]
        log(driver, f"Available brand options: {available_options}")
        
        # Try different variations of the brand name
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
        
        # Wait for the hotel dropdown to be populated
        def hotel_option_loaded(driver):
            try:
                hotel_select_elem = driver.find_element(By.ID, "hotelName")
                options = [o.text for o in hotel_select_elem.find_elements(By.TAG_NAME, "option")]
                log(driver, f"Available hotel options: {options}")
                return len(options) > 1  # More than just "Select Hotel"
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
        
        # Wait for selection to take effect
        wait_for_page_load(driver)
        
        # Click Rate Management menu
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
            
        # Wait for page to load after clicking
        wait_for_page_load(driver)
        
        # Click Allotment in the navigation
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
            
        # Wait for page to load after clicking
        wait_for_page_load(driver)
        log(driver, "Successfully clicked Allotment menu")
        
        # Navigate directly to the allotment detail page
        log(driver, "Navigating to allotment detail page...")
        driver.get("https://fo.hospitality.mykg.id/allotment/detail?companyid=1001")
        
        # Wait for page to load
        wait_for_page_load(driver)
        log(driver, "Successfully navigated to allotment detail page")
        
        # Read and process CSV data
        log(driver, "Reading CSV data...")
        date_inventory = []
        try:
            csv_path = os.path.join(os.path.dirname(__file__), 'data/daily_inventory_allocation_seasonal.csv')
            log(driver, f"Attempting to open CSV file at: {csv_path}")
            
            with open(csv_path, 'r') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    date_obj = datetime.strptime(row['Date'], '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%m/%d/%Y')
                    date_inventory.append({
                        'date': formatted_date,
                        'inventory': int(row['Deluxe Online Inventory'])
                    })
                log(driver, f"Successfully read {len(date_inventory)} dates from CSV")
        except Exception as e:
            log(driver, f"Error reading CSV file: {str(e)}")
            raise
        
        # Group consecutive dates with same inventory
        log(driver, "Grouping consecutive dates...")
        current_group = []
        groups = []
        
        for i, item in enumerate(date_inventory):
            if not current_group:
                current_group.append(item)
            elif item['inventory'] == current_group[0]['inventory']:
                current_group.append(item)
            else:
                groups.append(current_group)
                current_group = [item]
        
        if current_group:
            groups.append(current_group)
        log(driver, f"Created {len(groups)} groups of consecutive dates")
        
        # Process each group with correct batching logic
        log(driver, "Processing date ranges in batches of 5 within each inventory group...")
        for group_index, group in enumerate(groups):
            log(driver, f"\nProcessing inventory group {group_index + 1} of {len(groups)} (inventory: {group[0]['inventory']})")
            # Split this group into batches of 5 date ranges
            for batch_start in range(0, len(group), 5):
                batch = group[batch_start:batch_start+5]
                log(driver, f"  Processing batch {batch_start//5 + 1} of {(len(group) + 4)//5} in this group")
                # Click Add Allotment Room button to open modal
                if not wait_and_click(driver, By.ID, "btnAddRoom", description="Add Allotment Room button"):
                    raise Exception("Failed to click Add Allotment Room button")
                # Wait for modal to appear
                modal = wait_for_element_presence(driver, By.ID, "modalAddRoom", timeout=15, description="Add Room modal")
                if not modal:
                    raise Exception("Modal did not appear after clicking Add Allotment Room button")
                # Wait for modal to be fully loaded
                WebDriverWait(driver, 30).until(
                    EC.visibility_of_element_located((By.ID, "txtStartDate"))
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", modal)
                time.sleep(1)
                # Add each date range in the batch
                for date_range in batch:
                    log(driver, f"    Adding date: {date_range['date']} (inventory: {date_range['inventory']})")
                    add_date_range(driver, date_range['date'], date_range['date'])
                # After adding all date ranges in the batch, select Deluxe room type
                log(driver, "Selecting Deluxe room type...")
                deluxe_checkbox = wait_for_element_presence(driver, By.XPATH, "//input[@type='checkbox' and @id='lstRoomType' and @value='DLT']", description="Deluxe room type checkbox")
                if not deluxe_checkbox:
                    log(driver, "Could not find Deluxe room type checkbox (DLT)")
                    raise Exception("Could not find Deluxe room type checkbox (DLT)")
                driver.execute_script("arguments[0].scrollIntoView(true);", deluxe_checkbox)
                time.sleep(0.5)
                if not deluxe_checkbox.is_selected():
                    try:
                        deluxe_checkbox.click()
                    except:
                        driver.execute_script("arguments[0].click();", deluxe_checkbox)
                # Set number of rooms from inventory (use the group's inventory)
                log(driver, "Setting number of rooms...")
                number_of_rooms = wait_for_element_presence(driver, By.ID, "txtNumberOfRoom", description="number of rooms input")
                if not number_of_rooms:
                    log(driver, "Could not find number of rooms input field")
                    raise Exception("Could not find number of rooms input field")
                driver.execute_script("arguments[0].scrollIntoView(true);", number_of_rooms)
                time.sleep(0.2)
                number_of_rooms.clear()
                number_of_rooms.send_keys(str(group[0]['inventory']))
                log(driver, f"Set number of rooms to {group[0]['inventory']}")
                # Add remark
                log(driver, "Adding remark...")
                remark_textarea = wait_for_element_presence(driver, By.ID, "txtRemarkAllotment", description="remark textarea")
                if not remark_textarea:
                    log(driver, "Could not find remark textarea")
                    raise Exception("Could not find remark textarea")
                driver.execute_script("arguments[0].scrollIntoView(true);", remark_textarea)
                time.sleep(0.2)
                remark_textarea.clear()
                remark_textarea.send_keys(f"Updated from CSV data - Deluxe Online Inventory for inventory {group[0]['inventory']}, batch {batch_start//5 + 1}")
                log(driver, "Added remark")
                # Click Save button
                log(driver, "Clicking Save button...")
                save_button = wait_for_element_presence(driver, By.ID, "btnSaveRoomAllotment", description="save button")
                if not save_button:
                    log(driver, "Could not find save button")
                    raise Exception("Could not find save button")
                driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
                time.sleep(0.2)
                save_button.click()
                log(driver, "Clicked Save button")
                time.sleep(1)
                # Wait for and handle sweet alert
                if not handle_sweet_alert(driver):
                    log(driver, "Failed to handle sweet alert")
                    raise Exception("Failed to handle sweet alert")
                # Wait for toast to disappear
                if not wait_for_toast_disappear(driver):
                    log(driver, "Failed to wait for toast to disappear")
                    raise Exception("Failed to wait for toast to disappear")
                log(driver, f"Successfully processed batch {batch_start//5 + 1} in group {group_index + 1}")
                # Wait a bit before processing next batch
                time.sleep(2)
        log(driver, "Successfully processed all dates from CSV")
        return True
        
    except Exception as e:
        log(driver, f"An error occurred: {str(e)}")
        return False
        
    finally:
        if should_quit_driver and driver:
            pass

def wait_for_datepicker(driver, timeout=10):
    """Wait for datepicker to be visible"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "datepicker"))
        )
        return True
    except TimeoutException:
        return False

def select_date_from_picker(driver, date_str):
    """Select date from datepicker"""
    # Convert MM/DD/YYYY to datetime
    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
    day = str(date_obj.day)
    
    # Find and click the day in the datepicker
    day_element = wait_for_element_presence(
        driver,
        By.XPATH,
        f"//div[contains(@class, 'datepicker')]//td[text()='{day}']",
        description="datepicker day"
    )
    if day_element:
        day_element.click()
        return True
    return False

if __name__ == "__main__":
    # Test the function
    driver = setup_driver()
    try:
        if update_allotmet(driver):
            print("Successfully logged in and selected hotel")
        else:
            print("Failed to login or select hotel")
    finally:
        # driver.quit()  # Commented out to keep browser open
        pass 