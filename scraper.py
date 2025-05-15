from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import pandas as pd
from process_pms_inventory import process_pms_inventory
import os
import sqlite3
import platform

def setup_driver():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Add specific options for Mac ARM64
    if platform.system() == 'Darwin' and platform.machine() == 'arm64':
        chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    
    # Initialize the Chrome driver
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_pms_inventory():
    """
    Scrape PMS inventory data from the website
    """
    driver = setup_driver()
    try:
        # Navigate to the website
        driver.get("https://fo.hospitality.mykg.id/")
        print("Navigating to Hospitality Suite website...")
        
        # Wait for the page to load
        time.sleep(5)
        
        # Wait for the username field to be present
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "txtUsername"))
        )
        
        # Enter credentials
        username_field.send_keys("krisnatha")
        password_field = driver.find_element(By.ID, "txtPassword")
        password_field.send_keys("Nasibungkus13")
        
        # Click the login button
        login_button = driver.find_element(By.ID, "btnLogin")
        login_button.click()
        
        # Wait for login to complete and any popups to appear
        time.sleep(5)
        
        # Handle any popups or notifications that might appear
        try:
            # Wait for and close any toast notifications
            toast = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "toast-close-button"))
            )
            toast.click()
        except:
            pass  # No toast notification found, continue
        
        # Wait for the brand dropdown and select "The ANVAYA"
        brand_select_elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "className"))
        )
        brand_select = Select(brand_select_elem)
        brand_select.select_by_visible_text("The ANVAYA")
        
        # Wait for the hotel dropdown to be populated
        def hotel_option_loaded(driver):
            hotel_select_elem = driver.find_element(By.ID, "hotelName")
            options = [o.text for o in hotel_select_elem.find_elements(By.TAG_NAME, "option")]
            return "The ANVAYA Beach Resort Bali" in options
        WebDriverWait(driver, 10).until(hotel_option_loaded)
        
        hotel_select_elem = driver.find_element(By.ID, "hotelName")
        hotel_select = Select(hotel_select_elem)
        hotel_select.select_by_visible_text("The ANVAYA Beach Resort Bali")
        
        # Wait for selection to take effect
        time.sleep(2)
        
        print("Successfully logged in and selected hotel!")
        
        # Click the Front Office System menu
        front_office_menu = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.select-app[data-appid="1"]'))
        )
        front_office_menu.click()
        print("Clicked Front Office System menu!")
        
        # Wait for the page to load after clicking Front Office
        time.sleep(5)
        
        # Find and click the Utilities menu
        utilities_menu = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Utilities')]/parent::a"))
        )
        utilities_menu.click()
        print("Clicked Utilities menu!")
        
        # Wait for the Room Availability option and click it
        room_availability = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Room Availability')]/parent::a"))
        )
        room_availability.click()
        print("Clicked Room Availability!")
        
        # Wait for the page to load
        time.sleep(5)
        
        # Change days to 100
        days_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='number']"))
        )
        days_input.clear()
        days_input.send_keys("100")
        print("Changed days to 100")
        
        # Click search button
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnSearchRsv"))
        )
        search_button.click()
        print("Clicked search button")
        
        # Wait for table to load
        time.sleep(5)
        
        # Scrape the table data
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "tableRoomAvaibility"))
        )
        
        # Get all rows
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        # Extract headers
        headers = [th.text for th in rows[0].find_elements(By.TAG_NAME, "th")]
        
        # Extract data
        data = []
        for row in rows[1:]:  # Skip header row
            cols = row.find_elements(By.TAG_NAME, "td")
            row_data = [col.text for col in cols]
            data.append(row_data)
        
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
        
        # First save the raw scraped data to CSV
        df.to_csv('pms_inventory.csv', index=False)
        print("Raw data saved to pms_inventory.csv")
        
        # Save raw data to SQLite database
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Connect to SQLite database (this will create it if it doesn't exist)
        conn = sqlite3.connect('data/pms_inventory_raw.db')
        
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
        
        # Save DataFrame to SQLite with explicit data types
        df.to_sql('pms_inventory', conn, if_exists='replace', index=False, dtype=dtype_dict)
        
        # Close the connection
        conn.close()
        print("Raw data saved to data/pms_inventory_raw.db")
        
        # Then process the inventory data using the same function as process_pms_inventory.py
        print("\nStarting inventory data processing...")
        processed_df = process_pms_inventory(df)
        print("Inventory data processing completed!")
        
        return processed_df
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
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