from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
import time
import pandas as pd
from .process_pms_inventory import process_pms_inventory
import os
import sqlite3
import platform
from datetime import datetime

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

def wait_for_table_load(driver, timeout=20):
    """Wait for table to be loaded with data"""
    try:
        print("Waiting for table to load...")
        
        # Wait for table presence
        table = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "tableRoomAvaibility"))
        )
        print("Table element found")
        
        # Wait for loading indicator to disappear (if present)
        try:
            WebDriverWait(driver, 5).until_not(
                EC.presence_of_element_located((By.CLASS_NAME, "loading-indicator"))
            )
        except:
            pass  # No loading indicator found
        
        # Wait for table to have data rows
        def table_has_data(driver):
            rows = driver.find_elements(By.CSS_SELECTOR, "#tableRoomAvaibility tbody tr")
            return len(rows) > 1 and any(cell.text.strip() for cell in rows[1].find_elements(By.TAG_NAME, "td"))
        
        WebDriverWait(driver, timeout).until(table_has_data)
        print("Table has data rows")
        
        # Additional wait to ensure all cells are populated
        def cells_are_populated(driver):
            cells = driver.find_elements(By.CSS_SELECTOR, "#tableRoomAvaibility td")
            return len(cells) > 0 and all(cell.text.strip() for cell in cells[:10])  # Check first 10 cells
        
        WebDriverWait(driver, timeout).until(cells_are_populated)
        print("Table cells are populated")
        
        # Small delay to ensure any animations or final updates are complete
        time.sleep(1)
        
        return table
    except Exception as e:
        print(f"Error waiting for table load: {e}")
        return None

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

def scrape_pms_inventory(start_date=None):
    """
    Scrape PMS inventory data from the website
    """
    # Get the absolute path to the data directory within the scraper folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    driver = setup_driver()
    try:
        # Navigate to the website
        driver.get("https://fo.hospitality.mykg.id/")
        print("Navigating to Hospitality Suite website...")
        
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
        username_field.send_keys("krisnatha")
        
        password_field = driver.find_element(By.ID, "txtPassword")
        password_field.clear()
        password_field.send_keys("Nasibungkus13")
        
        # Click the login button
        if not wait_and_click(driver, By.ID, "btnLogin", description="login button"):
            raise Exception("Failed to click login button")
        
        print("Login credentials entered...")
        
        # Wait for login to complete
        wait_for_page_load(driver)
        wait_for_toast_disappear(driver)
        
        print("Successfully logged in!")
        
        # Navigate directly to Room Availability page
        print("Navigating to Room Availability page...")
        driver.get("https://fo.hospitality.mykg.id/RoomAvailable/index")
        wait_for_page_load(driver)
        
        # Wait for and click the date picker to open it
        date_picker = wait_for_element_presence(driver, By.CSS_SELECTOR, "input[type='text'][readonly]", 
                                              timeout=15, description="date picker input")
        if not date_picker:
            raise Exception("Date picker input not found")
        
        # Wait for navbar to be fully loaded
        navbar = wait_for_element_presence(driver, By.CLASS_NAME, "navbar-fixed-top", 
                                         timeout=10, description="navbar")
        if navbar:
            # Get navbar height
            navbar_height = navbar.size['height']
            print(f"Navbar height: {navbar_height}")
            
            # Scroll the page to ensure date picker is below navbar
            driver.execute_script(f"window.scrollTo(0, {navbar_height + 50});")
            time.sleep(1)  # Wait for scroll to complete
        
        # Try to set the date by interacting with the calendar UI
        try:
            if start_date:
                target_date = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                target_date = datetime.now()
            formatted_date = target_date.strftime('%d-%b-%Y')
            day = target_date.day
            month = target_date.strftime('%b')
            year = target_date.year

            # 1. Click the calendar button to open the date picker
            calendar_btn = date_picker.find_element(By.XPATH, "../div[@class='input-group-btn']/button")
            calendar_btn.click()
            print("Clicked calendar button to open date picker")
            time.sleep(1)

            # 2. Wait for the calendar dropdown to appear
            calendar_dropdown = wait_for_element_presence(
                driver, By.CSS_SELECTOR, "ul.dropdown-menu .uiv-datepicker", timeout=10, description="calendar dropdown")
            if not calendar_dropdown:
                raise Exception("Calendar dropdown not found")

            # 2.1. Navigate to the correct month and year
            month_names = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ]
            target_month = month_names[target_date.month - 1]
            target_year = str(target_date.year)
            max_nav_attempts = 24  # Prevent infinite loops
            for _ in range(max_nav_attempts):
                # Read the current month/year from the header
                header_btn = calendar_dropdown.find_element(By.CSS_SELECTOR, ".uiv-datepicker-title")
                header_text = header_btn.text.strip()
                # Example: '2024 February' or '2025 May'
                if ' ' in header_text:
                    current_year, current_month = header_text.split(' ', 1)
                else:
                    current_year, current_month = '', ''
                current_month = current_month.strip()
                current_year = current_year.strip()
                if current_month == target_month and current_year == target_year:
                    break  # We're at the right month/year
                # Find next/prev buttons (first and last <td> in the header row)
                header_row = calendar_dropdown.find_element(By.TAG_NAME, "thead").find_elements(By.TAG_NAME, "tr")[0]
                tds = header_row.find_elements(By.TAG_NAME, "td")
                prev_btn = tds[0].find_element(By.TAG_NAME, "button")
                next_btn = tds[-1].find_element(By.TAG_NAME, "button")
                # Decide which direction to go
                target_dt = int(target_year) * 12 + month_names.index(target_month)
                current_dt = int(current_year) * 12 + month_names.index(current_month)
                if target_dt > current_dt:
                    next_btn.click()
                else:
                    prev_btn.click()
                time.sleep(0.5)
            else:
                raise Exception("Could not navigate to the correct month/year in the calendar")

            # 3. Find and click the correct day button (skip text-muted)
            day_found = False
            day_buttons = calendar_dropdown.find_elements(By.CSS_SELECTOR, "button[data-action='select']")
            for btn in day_buttons:
                try:
                    span = btn.find_element(By.TAG_NAME, "span")
                    # Skip if span or button has 'text-muted' class
                    if 'text-muted' in span.get_attribute('class') or 'text-muted' in btn.get_attribute('class'):
                        continue
                    if span.text == str(day):
                        btn.click()
                        print(f"Selected day {day} in calendar (not muted)")
                        day_found = True
                        break
                except Exception:
                    continue
            if not day_found:
                raise Exception(f"Could not find day {day} in calendar (non-muted)")

            # Wait for Vue to update the input
            time.sleep(2)

            # Change days to 100 with retry mechanism (moved here to prevent reset)
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    days_input = wait_for_element_presence(driver, By.CSS_SELECTOR, "input[type='number']", 
                                                         timeout=15, description="days input")
                    if not days_input:
                        raise Exception("Days input field not found")
                    
                    # Clear and set the value using JavaScript
                    driver.execute_script("""
                        const input = arguments[0];
                        const value = arguments[1];
                        
                        // Clear the input
                        input.value = '';
                        
                        // Set the new value
                        input.value = value;
                        
                        // Create and dispatch input event
                        const inputEvent = new Event('input', { bubbles: true });
                        input.dispatchEvent(inputEvent);
                        
                        // Create and dispatch change event
                        const changeEvent = new Event('change', { bubbles: true });
                        input.dispatchEvent(changeEvent);
                        
                        // Trigger Vue's reactivity if available
                        if (input.__vue__) {
                            input.__vue__.$emit('input', value);
                            input.__vue__.$emit('change', value);
                        }
                    """, days_input, "100")
                    
                    # Verify the value was set correctly
                    time.sleep(1)
                    actual_value = days_input.get_attribute('value')
                    if actual_value == "100":
                        print("Successfully set days to 100")
                        break
                    else:
                        print(f"Days value not set correctly. Expected 100, got {actual_value}")
                        if attempt < max_attempts - 1:
                            print("Retrying...")
                            time.sleep(1)
                        else:
                            raise Exception("Failed to set days value after multiple attempts")
                            
                except Exception as e:
                    if attempt < max_attempts - 1:
                        print(f"Attempt {attempt + 1} failed: {str(e)}")
                        time.sleep(1)
                    else:
                        raise Exception(f"Failed to set days value: {str(e)}")

        except Exception as e:
            print(f"Error setting date via calendar: {str(e)}")
            raise Exception(f"Failed to set date via calendar: {str(e)}")
        
        # Click search button and wait for results
        if not wait_and_click(driver, By.ID, "btnSearchRsv", timeout=15, description="search button"):
            raise Exception("Failed to click search button")
        print("Clicked search button")
        
        # Add longer wait time for table to fully load
        print("Waiting for table to fully load...")
        time.sleep(20)  # Wait 20 seconds for full table load
        
        # Wait for table to load with more detailed status updates
        table = wait_for_table_load(driver)
        if not table:
            raise Exception("Failed to load table data")
        
        print("Table loaded successfully, extracting data...")
        
        # Get all rows
        rows = table.find_elements(By.TAG_NAME, "tr")
        if len(rows) <= 1:
            raise Exception("Table has no data rows")
        
        # Extract headers
        headers = [th.text for th in rows[0].find_elements(By.TAG_NAME, "th")]
        if not headers:
            raise Exception("No headers found in table")
        
        # Extract data
        data = []
        for row in rows[1:]:  # Skip header row
            cols = row.find_elements(By.TAG_NAME, "td")
            row_data = [col.text for col in cols]
            if row_data:  # Only add non-empty rows
                data.append(row_data)
        
        if not data:
            raise Exception("No data rows found in table")
        
        # Create DataFrame
        df = pd.DataFrame(data, columns=headers)
        
        # Convert numeric columns to appropriate types
        numeric_columns = ['DLK', 'DLT', 'DLKP', 'DLTP', 'PRKG', 'PRKP', 'PRTG', 'PRTP', 'PRKL', 'PRTL',
                         'Extra Bed', 'Total Room', 'Available', 'Tentative', 'Definite', 'Waiting List', 
                         'Allotment', 'Out of Order']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        print("\nScraping completed successfully!")
        
        # Save raw data to CSV
        csv_path = os.path.join(data_dir, 'pms_inventory.csv')
        df.to_csv(csv_path, index=False)
        print(f"Raw data saved to {csv_path}")
        
        # Save to SQLite database
        db_path = os.path.join(data_dir, 'pms_inventory_raw.db')
        conn = sqlite3.connect(db_path)
        
        # Define data types for each column
        dtype_dict = {
            'Date': 'DATE',
            'AVR': 'INTEGER',
            'AVS': 'INTEGER',
            'ASP': 'INTEGER',
            'ASW': 'INTEGER',
            'AVP': 'INTEGER',
            'BFS': 'INTEGER',
            'DLK': 'INTEGER',
            'DLT': 'INTEGER',
            'DLKP': 'INTEGER',
            'DLTP': 'INTEGER',
            'DLS': 'INTEGER',
            'FAM': 'INTEGER',
            'PRKG': 'INTEGER',
            'PRKP': 'INTEGER',
            'PRTG': 'INTEGER',
            'PRTP': 'INTEGER',
            'PRKL': 'INTEGER',
            'PRTL': 'INTEGER',
            'PSU': 'INTEGER',
            'Extra Bed': 'INTEGER',
            'Total Room': 'INTEGER',
            'Available': 'INTEGER',
            'Tentative': 'INTEGER',
            'Definite': 'INTEGER',
            'Waiting List': 'INTEGER',
            'Allotment': 'INTEGER',
            'Out of Order': 'INTEGER'
        }
        
        # Save DataFrame to SQLite
        df.to_sql('pms_inventory', conn, if_exists='replace', index=False, dtype=dtype_dict)
        conn.close()
        print(f"Raw data saved to {db_path}")
        
        # Process the inventory data
        print("\nStarting inventory data processing...")
        processed_df = process_pms_inventory(df)
        print("Processed data saved to CSV and database")
        
        return processed_df
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # Take screenshot on error
        try:
            screenshot_path = os.path.join(data_dir, 'error_screenshot.png')
            driver.save_screenshot(screenshot_path)
            print(f"Error screenshot saved to {screenshot_path}")
        except:
            pass
        return None
    finally:
        driver.quit()
        print("Browser closed")

def main():
    """
    Main function to run the scraping and processing sequence
    """
    print("=== Starting PMS Inventory Scraping and Processing ===")
    print("Step 1: Scraping data from Hospitality Suite...")
    processed_data = scrape_pms_inventory()
    
    if processed_data is not None:
        print("\n=== Process Completed Successfully ===")
        print("1. Data scraped from Hospitality Suite")
        print("2. Raw data saved to pms_inventory.csv")
        print("3. Data processed and saved to pms_inventory_processed.csv")
    else:
        print("\n=== Process Failed ===")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main() 