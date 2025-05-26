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
    """Wait for toast notifications to disappear"""
    try:
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CLASS_NAME, "toast-message"))
        )
    except:
        pass  # No toast found or already disappeared

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
    chrome_options.add_argument('--headless=new')
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
        
        # Click Add Allotment Room button to open modal
        log(driver, "Clicking Add Allotment Room button...")
        if not wait_and_click(driver, By.ID, "btnAddRoom", description="Add Allotment Room button"):
            raise Exception("Failed to click Add Allotment Room button")
            
        # Wait for modal to appear
        log(driver, "Waiting for modal to appear...")
        modal = wait_for_element_presence(driver, By.ID, "modalAddRoom", timeout=15, description="Add Room modal")
        if not modal:
            log(driver, "Modal did not appear after clicking Add Allotment Room button")
            raise Exception("Modal did not appear after clicking Add Allotment Room button")
        log(driver, "Successfully opened Add Room modal")
        # Add a short sleep to allow modal animation to finish
        time.sleep(1)
        # Wait for modal to be fully loaded and visible
        log(driver, "Waiting for modal to be fully loaded (visible)...")
        try:
            # Increase timeout to 30 seconds
            WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.ID, "txtStartDate"))
            )
            log(driver, "Modal is fully loaded and visible")
        except TimeoutException:
            log(driver, "Modal did not become visible within timeout period, trying to refresh page...")
            # Try to refresh the page and wait for it to load
            driver.refresh()
            wait_for_page_load(driver)
            time.sleep(2)  # Add a small delay after refresh
            
            # Try clicking the Add Allotment Room button again
            log(driver, "Retrying to click Add Allotment Room button...")
            add_button = wait_for_element_presence(driver, By.ID, "btnAddRoom", description="Add Allotment Room button")
            if add_button:
                try:
                    add_button.click()
                except:
                    driver.execute_script("arguments[0].click();", add_button)
                
                # Wait again for modal with increased timeout
                try:
                    WebDriverWait(driver, 30).until(
                        EC.visibility_of_element_located((By.ID, "txtStartDate"))
                    )
                    log(driver, "Modal is now visible after retry")
                except TimeoutException:
                    log(driver, "Modal still not visible after retry")
                    raise Exception("Modal did not become visible after retry")
            else:
                raise Exception("Could not find Add Allotment Room button after refresh")
        
        # Scroll modal into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", modal)
        time.sleep(1)  # Increased wait time for scroll to complete
        
        # Read and process CSV data
        log(driver, "Reading CSV data...")
        # Store dates and their inventory values
        date_inventory = []
        try:
            # Use the correct path to the CSV file
            csv_path = os.path.join(os.path.dirname(__file__), 'data/daily_inventory_allocation_seasonal.csv')
            log(driver, f"Attempting to open CSV file at: {csv_path}")
            
            with open(csv_path, 'r') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    # Convert date from YYYY-MM-DD to MM/DD/YYYY
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
            
        # Process each group
        for group_index, group in enumerate(groups):
            # Before starting the next group, ensure no lingering sweet alert
            try:
                WebDriverWait(driver, 3).until(
                    EC.invisibility_of_element_located((By.CLASS_NAME, "sweet-alert"))
                )
                log(driver, "No lingering sweet alert before starting next group")
            except TimeoutException:
                log(driver, "Lingering sweet alert detected, trying to close it")
                try:
                    ok_button = wait_for_element_presence(driver, By.CLASS_NAME, "confirm", description="sweet alert OK button")
                    if ok_button:
                        ok_button.click()
                        log(driver, "Clicked lingering OK on sweet alert")
                        WebDriverWait(driver, 5).until(
                            EC.invisibility_of_element_located((By.CLASS_NAME, "sweet-alert"))
                        )
                except Exception as e:
                    log(driver, f"Failed to close lingering sweet alert: {e}")
            
            log(driver, f"\nProcessing group {group_index + 1} of {len(groups)}")
            log(driver, f"Date range: {group[0]['date']} to {group[-1]['date']}")
            
            # Set start date
            log(driver, "Setting start date...")
            start_date_input = wait_for_element_presence(driver, By.ID, "txtStartDate", description="start date input")
            if not start_date_input:
                log(driver, "Could not find start date input field")
                raise Exception("Could not find start date input field")
            log(driver, f"Start date input found. Displayed: {start_date_input.is_displayed()}, Enabled: {start_date_input.is_enabled()}")
            
            # Scroll the modal into view first
            modal = driver.find_element(By.ID, "modalAddRoom")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", modal)
            time.sleep(0.5)  # Wait for scroll to complete
            
            # Try to make the input visible and interactable
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", start_date_input)
            time.sleep(0.5)  # Wait for scroll to complete
            
            # Try to click the input first to ensure it's focused
            try:
                start_date_input.click()
            except:
                log(driver, "Could not click start date input, trying JavaScript click")
                driver.execute_script("arguments[0].click();", start_date_input)
            
            time.sleep(0.5)  # Wait for click to register
            
            # Clear and set the date
            start_date_input.clear()
            start_date_input.send_keys(group[0]['date'])
            start_date_input.send_keys(Keys.TAB)  # Close datepicker
            log(driver, f"Set start date to {group[0]['date']}")
            
            # Set end date
            log(driver, "Setting end date...")
            end_date_input = wait_for_element_presence(driver, By.ID, "txtEndDate", description="end date input")
            if not end_date_input:
                log(driver, "Could not find end date input field")
                raise Exception("Could not find end date input field")
            log(driver, f"End date input found. Displayed: {end_date_input.is_displayed()}, Enabled: {end_date_input.is_enabled()}")
            
            # Try to make the input visible and interactable
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", end_date_input)
            time.sleep(0.5)  # Wait for scroll to complete
            
            # Try to click the input first to ensure it's focused
            try:
                end_date_input.click()
            except:
                log(driver, "Could not click end date input, trying JavaScript click")
                driver.execute_script("arguments[0].click();", end_date_input)
            
            time.sleep(0.5)  # Wait for click to register
            
            # Clear and set the date
            end_date_input.clear()
            # If single date, use same as start date
            if len(group) == 1:
                end_date_input.send_keys(group[0]['date'])
                end_date_input.send_keys(Keys.TAB)  # Close datepicker
                log(driver, f"Set end date to {group[0]['date']} (single date)")
            else:
                end_date_input.send_keys(group[-1]['date'])
                end_date_input.send_keys(Keys.TAB)  # Close datepicker
                log(driver, f"Set end date to {group[-1]['date']}")
                
            # Select Deluxe room type (value='DLT')
            log(driver, "Selecting Deluxe room type...")
            deluxe_checkbox = wait_for_element_presence(driver, By.XPATH, "//input[@type='checkbox' and @id='lstRoomType' and @value='DLT']", description="Deluxe room type checkbox")
            if not deluxe_checkbox:
                log(driver, "Could not find Deluxe room type checkbox (DLT)")
                raise Exception("Could not find Deluxe room type checkbox (DLT)")
            log(driver, f"Deluxe checkbox found. Displayed: {deluxe_checkbox.is_displayed()}, Enabled: {deluxe_checkbox.is_enabled()}")
            try:
                WebDriverWait(driver, 10).until(EC.visibility_of(deluxe_checkbox))
                log(driver, "Deluxe checkbox is now visible")
            except TimeoutException:
                log(driver, "Deluxe checkbox did not become visible, trying JavaScript click")
            driver.execute_script("arguments[0].scrollIntoView(true);", deluxe_checkbox)
            time.sleep(0.5)
            try:
                if not deluxe_checkbox.is_selected():
                    deluxe_checkbox.click()
                    log(driver, "Clicked Deluxe checkbox using normal click")
            except Exception as e:
                log(driver, f"Normal click failed: {str(e)}, trying JavaScript click")
                try:
                    driver.execute_script("arguments[0].click();", deluxe_checkbox)
                    log(driver, "Clicked Deluxe checkbox using JavaScript")
                except Exception as e:
                    log(driver, f"JavaScript click failed: {str(e)}, trying to set checked property")
                    try:
                        driver.execute_script("arguments[0].checked = true;", deluxe_checkbox)
                        log(driver, "Set Deluxe checkbox checked property")
                    except Exception as e:
                        log(driver, f"All click attempts failed: {str(e)}")
                        raise Exception("Could not interact with Deluxe checkbox")
            if deluxe_checkbox.is_selected():
                log(driver, "Successfully selected Deluxe room type")
            else:
                log(driver, "Warning: Deluxe checkbox may not be selected")
            
            # Fast tick for Deluxe Twin room type (value='DLT')
            log(driver, "Ticking Deluxe Twin room type (fast)...")
            deluxe_twin_checkbox = wait_for_element_presence(
                driver, By.XPATH, "//input[@type='checkbox' and @id='lstRoomType' and @value='DLT']",
                description="Deluxe Twin room type checkbox"
            )
            if not deluxe_twin_checkbox:
                log(driver, "Could not find Deluxe Twin room type checkbox (DLT)")
                raise Exception("Could not find Deluxe Twin room type checkbox (DLT)")
            if not deluxe_twin_checkbox.is_selected():
                driver.execute_script("arguments[0].checked = true;", deluxe_twin_checkbox)
                log(driver, "Deluxe Twin checkbox ticked via JS")
            else:
                log(driver, "Deluxe Twin checkbox already ticked")
            
            # Set number of rooms from inventory
            log(driver, "Setting number of rooms...")
            number_of_rooms = wait_for_element_presence(driver, By.ID, "txtNumberOfRoom", description="number of rooms input")
            if not number_of_rooms:
                log(driver, "Could not find number of rooms input field")
                raise Exception("Could not find number of rooms input field")
            log(driver, f"Number of rooms input found. Displayed: {number_of_rooms.is_displayed()}, Enabled: {number_of_rooms.is_enabled()}")
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
            log(driver, f"Remark textarea found. Displayed: {remark_textarea.is_displayed()}, Enabled: {remark_textarea.is_enabled()}")
            driver.execute_script("arguments[0].scrollIntoView(true);", remark_textarea)
            time.sleep(0.2)
            remark_textarea.clear()
            if len(group) == 1:
                remark_textarea.send_keys(f"Updated from CSV data - Deluxe Online Inventory for {group[0]['date']}")
            else:
                remark_textarea.send_keys(f"Updated from CSV data - Deluxe Online Inventory for {group[0]['date']} to {group[-1]['date']}")
            log(driver, "Added remark")
                
            log(driver, f"Filled form for dates {group[0]['date']} to {group[-1]['date']} with inventory {group[0]['inventory']}")
            
            # Click Save button
            log(driver, "Clicking Save button...")
            save_button = wait_for_element_presence(driver, By.ID, "btnSaveRoomAllotment", description="save button")
            if not save_button:
                log(driver, "Could not find save button")
                raise Exception("Could not find save button")
            log(driver, f"Save button found. Displayed: {save_button.is_displayed()}, Enabled: {save_button.is_enabled()}")
            driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
            time.sleep(0.2)
            save_button.click()
            log(driver, "Clicked Save button")
            time.sleep(1)  # Increased wait time for sweet alert
            
            # Wait for sweet alert to appear and click OK
            log(driver, "Waiting for sweet alert...")
            try:
                # Wait for sweet alert to be visible
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "sweet-alert"))
                )
                log(driver, "Sweet alert appeared")
                
                # Wait for OK button to be clickable
                ok_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "confirm"))
                )
                log(driver, "Found OK button in sweet alert")
                
                # Try to click OK button
                try:
                    ok_button.click()
                except:
                    log(driver, "Could not click OK button normally, trying JavaScript click")
                    driver.execute_script("arguments[0].click();", ok_button)
                
                log(driver, "Clicked OK on sweet alert")
                
                # Wait for sweet alert to disappear
                WebDriverWait(driver, 10).until(
                    EC.invisibility_of_element_located((By.CLASS_NAME, "sweet-alert"))
                )
                log(driver, "Sweet alert disappeared")
                
                # Wait for the modal to close
                try:
                    WebDriverWait(driver, 10).until(
                        EC.invisibility_of_element_located((By.ID, "modalAddRoom"))
                    )
                    log(driver, "Modal closed automatically")
                except TimeoutException:
                    log(driver, "Modal did not close automatically, trying to close it manually")
                    try:
                        # Try to find and click the close button
                        close_btn = driver.find_element(By.CSS_SELECTOR, '#modalAddRoom .close')
                        driver.execute_script("arguments[0].click();", close_btn)
                        log(driver, "Clicked modal close button")
                        
                        # Wait for modal to close
                        WebDriverWait(driver, 5).until(
                            EC.invisibility_of_element_located((By.ID, "modalAddRoom"))
                        )
                        log(driver, "Modal closed after manual close attempt")
                    except Exception as e:
                        log(driver, f"Failed to close modal manually: {str(e)}")
                        # Try ESC key as last resort
                        try:
                            driver.switch_to.active_element.send_keys(Keys.ESCAPE)
                            log(driver, "Sent ESCAPE to close modal")
                            time.sleep(1)
                        except Exception as e:
                            log(driver, f"Failed to close modal with ESC: {str(e)}")
                
                # Wait for save to complete (toast)
                log(driver, "Waiting for save confirmation...")
                wait_for_toast_disappear(driver)
                log(driver, "Successfully saved allotment room data")
                
                # Wait for the Add Allotment Room button to be clickable again
                try:
                    WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.ID, "btnAddRoom"))
                    )
                    log(driver, "Add Allotment Room button is clickable again")
                except TimeoutException:
                    log(driver, "Add Allotment Room button did not become clickable, continuing anyway")
                
                # Wait a bit before next save
                log(driver, "Waiting before next save...")
                time.sleep(2)  # Increased wait time
                
                # Click Add Allotment Room button again for next group
                log(driver, "Clicking Add Allotment Room button for next group...")
                add_button = wait_for_element_presence(driver, By.ID, "btnAddRoom", description="Add Allotment Room button")
                if not add_button:
                    log(driver, "Could not find Add Allotment Room button")
                    raise Exception("Could not find Add Allotment Room button")
                
                # Ensure button is clickable
                try:
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "btnAddRoom"))
                    )
                except TimeoutException:
                    log(driver, "Add Allotment Room button not clickable, trying JavaScript click")
                
                # Try to click the button
                try:
                    add_button.click()
                except:
                    log(driver, "Could not click Add Allotment Room button normally, trying JavaScript click")
                    driver.execute_script("arguments[0].click();", add_button)
                
                # Wait for modal to appear
                log(driver, "Waiting for modal to appear...")
                modal = wait_for_element_presence(driver, By.ID, "modalAddRoom", timeout=15, description="Add Room modal")
                if not modal:
                    log(driver, "Modal did not appear after clicking Add Allotment Room button")
                    raise Exception("Modal did not appear after clicking Add Allotment Room button")
                log(driver, "Successfully opened Add Room modal")
                
                # Add a short sleep to allow modal animation to finish
                time.sleep(1)
                
                # Wait for modal to be fully loaded and visible
                log(driver, "Waiting for modal to be fully loaded (visible)...")
                try:
                    # Increase timeout to 30 seconds
                    WebDriverWait(driver, 30).until(
                        EC.visibility_of_element_located((By.ID, "txtStartDate"))
                    )
                    log(driver, "Modal is fully loaded and visible")
                except TimeoutException:
                    log(driver, "Modal did not become visible within timeout period, trying to refresh page...")
                    # Try to refresh the page and wait for it to load
                    driver.refresh()
                    wait_for_page_load(driver)
                    time.sleep(2)  # Add a small delay after refresh
                    
                    # Try clicking the Add Allotment Room button again
                    log(driver, "Retrying to click Add Allotment Room button...")
                    add_button = wait_for_element_presence(driver, By.ID, "btnAddRoom", description="Add Allotment Room button")
                    if add_button:
                        try:
                            add_button.click()
                        except:
                            driver.execute_script("arguments[0].click();", add_button)
                        
                        # Wait again for modal with increased timeout
                        try:
                            WebDriverWait(driver, 30).until(
                                EC.visibility_of_element_located((By.ID, "txtStartDate"))
                            )
                            log(driver, "Modal is now visible after retry")
                        except TimeoutException:
                            log(driver, "Modal still not visible after retry")
                            raise Exception("Modal did not become visible after retry")
                    else:
                        raise Exception("Could not find Add Allotment Room button after refresh")
                
                # Scroll modal into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", modal)
                time.sleep(1)  # Increased wait time for scroll to complete
                
            except Exception as e:
                log(driver, f"Error handling sweet alert: {str(e)}")
                raise Exception(f"Failed to handle sweet alert: {str(e)}")
        
        log(driver, "Successfully processed all dates from CSV")
        
        log(driver, "Successfully logged in and selected hotel!")
        return True
        
    except Exception as e:
        log(driver, f"An error occurred during login and hotel selection: {str(e)}")
        return False
        
    finally:
        if should_quit_driver and driver:
            # driver.quit()  # Commented out to keep browser open
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