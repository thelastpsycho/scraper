from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import time
import pandas as pd

def setup_driver():
    # Set up Chrome options
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Uncomment to run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # Initialize the Chrome driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login_to_hospitality_suite():
    driver = setup_driver()
    try:
        # Navigate to the login page
        driver.get('https://fo.hospitality.mykg.id/')
        
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
        
        # Save to CSV, replacing if file exists
        df.to_csv('pms_inventory.csv', index=False, mode='w')
        print("Data saved to pms_inventory.csv (replaced existing file if any)")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Keep the browser open for inspection
        # input("Press Enter to close the browser...")
        # driver.quit()
        driver.quit()
        print("Browser closed")

if __name__ == "__main__":
    login_to_hospitality_suite() 