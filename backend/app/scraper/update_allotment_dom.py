import csv
import os
import time
import platform
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

def wait_for_element(driver, by, value, timeout=15):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )

def wait_for_clickable(driver, by, value, timeout=15):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )

def wait_for_page_load(driver, timeout=15):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )

def wait_for_toast_disappear(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "toast-message"))
        )
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CLASS_NAME, "toast-message"))
        )
        return True
    except:
        return False

def handle_sweet_alert_dom(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "swal2-container"))
        )
        # Click the confirm button via DOM
        driver.execute_script("document.querySelector('.swal2-container .swal2-confirm').click();")
        time.sleep(1)
        return True
    except Exception as e:
        print(f"No sweet alert found or error: {e}")
        return False

def login_and_navigate(driver, username, password):
    print("Navigating to login page...")
    driver.get("https://fo.hospitality.mykg.id/")
    wait_for_page_load(driver)
    print("Waiting for login fields...")
    wait_for_element(driver, By.ID, "txtUsername")
    # Set username and password via DOM
    driver.execute_script("document.getElementById('txtUsername').value = arguments[0];", username)
    driver.execute_script("document.getElementById('txtPassword').value = arguments[0];", password)
    time.sleep(0.2)
    # Click login
    driver.execute_script("document.getElementById('btnLogin').click();")
    print("Clicked login button.")
    wait_for_page_load(driver)
    wait_for_toast_disappear(driver)
    print("Logged in. Waiting for brand dropdown...")
    wait_for_element(driver, By.ID, "className")
    time.sleep(1)
    # Select brand (try several variations)
    brand_names = ["The ANVAYA", "THE ANVAYA", "The Anvaya", "THE ANVAYA BEACH RESORT BALI"]
    for brand in brand_names:
        try:
            driver.execute_script(f"var sel=document.getElementById('className'); for(var i=0;i<sel.options.length;i++){{if(sel.options[i].text=='{brand}'){{sel.selectedIndex=i;sel.dispatchEvent(new Event('change',{{bubbles:true}}));break;}}}}")
            time.sleep(1)
            # Wait for hotel dropdown to update
            wait_for_element(driver, By.ID, "hotelName")
            options = driver.execute_script("return Array.from(document.getElementById('hotelName').options).map(o=>o.text);")
            if any("ANVAYA" in o for o in options):
                print(f"Selected brand: {brand}")
                break
        except Exception as e:
            continue
    # Select hotel
    print("Selecting hotel...")
    driver.execute_script("var sel=document.getElementById('hotelName'); for(var i=0;i<sel.options.length;i++){if(sel.options[i].text.includes('ANVAYA')){sel.selectedIndex=i;sel.dispatchEvent(new Event('change',{bubbles:true}));break;}}")
    time.sleep(1)
    wait_for_page_load(driver)
    # Click Rate Management menu
    print("Navigating to Rate Management...")
    driver.execute_script("document.querySelector('a[data-appid=\'4\']').click();")
    wait_for_page_load(driver)
    # Click Allotment in the navigation
    print("Navigating to Allotment menu...")
    driver.execute_script("var el = Array.from(document.querySelectorAll('span')).find(e => e.textContent.includes('Allotment')); if(el){el.parentElement.click();}")
    wait_for_page_load(driver)
    # Go to the allotment detail page
    print("Navigating to allotment detail page...")
    driver.get("https://fo.hospitality.mykg.id/allotment/detail?companyid=1001")
    wait_for_page_load(driver)
    print("Ready to process allotment.")

def read_and_group_csv(csv_path):
    date_inventory = []
    with open(csv_path, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            date_obj = datetime.strptime(row['Date'], '%Y-%m-%d')
            formatted_date = date_obj.strftime('%m/%d/%Y')
            date_inventory.append({
                'date': formatted_date,
                'inventory': int(row['Deluxe Online Inventory'])
            })
    # Group consecutive dates with the same inventory
    groups = []
    current_group = []
    for item in date_inventory:
        if not current_group:
            current_group.append(item)
        elif item['inventory'] == current_group[0]['inventory']:
            current_group.append(item)
        else:
            groups.append(current_group)
            current_group = [item]
    if current_group:
        groups.append(current_group)
    return groups

def add_date_range_dom(driver, start_date, end_date):
    driver.execute_script("document.getElementById('txtStartDate').value = arguments[0];", start_date)
    driver.execute_script("document.getElementById('txtStartDate').dispatchEvent(new Event('change', {bubbles:true}));")
    time.sleep(0.2)
    driver.execute_script("document.getElementById('txtEndDate').value = arguments[0];", end_date)
    driver.execute_script("document.getElementById('txtEndDate').dispatchEvent(new Event('change', {bubbles:true}));")
    time.sleep(0.2)
    driver.execute_script("document.getElementById('ModalAddRoomAddDateButton').click();")
    time.sleep(0.5)

def select_deluxe_room_type_dom(driver):
    driver.execute_script("var cb=document.querySelector(\"input#lstRoomType[value='DLT']\"); if(cb && !cb.checked){cb.checked=true;cb.dispatchEvent(new Event('change', {bubbles:true}));}")
    time.sleep(0.2)

def set_number_of_rooms_dom(driver, number_of_rooms):
    driver.execute_script("document.getElementById('txtNumberOfRoom').value = arguments[0];", number_of_rooms)
    driver.execute_script("document.getElementById('txtNumberOfRoom').dispatchEvent(new Event('input', {bubbles:true}));")
    time.sleep(0.2)

def set_remark_dom(driver, remark):
    driver.execute_script("document.getElementById('txtRemarkAllotment').value = arguments[0];", remark)
    driver.execute_script("document.getElementById('txtRemarkAllotment').dispatchEvent(new Event('input', {bubbles:true}));")
    time.sleep(0.2)

def click_save_dom(driver):
    driver.execute_script("document.getElementById('btnSaveRoomAllotment').click();")
    print('Clicked Save button')
    time.sleep(1)

def process_allotment_dom(driver, groups):
    for group_index, group in enumerate(groups):
        inventory = group[0]['inventory']
        for batch_start in range(0, len(group), 5):
            batch = group[batch_start:batch_start+5]
            print(f"Processing group {group_index+1}, batch {batch_start//5+1} (inventory: {inventory})")
            driver.execute_script("document.getElementById('btnAddRoom').click();")
            time.sleep(1.5)
            for date_range in batch:
                add_date_range_dom(driver, date_range['date'], date_range['date'])
            select_deluxe_room_type_dom(driver)
            set_number_of_rooms_dom(driver, inventory)
            set_remark_dom(driver, f"Automated update via DOM, inventory {inventory}, batch {batch_start//5+1}")
            click_save_dom(driver)
            handle_sweet_alert_dom(driver)
            wait_for_toast_disappear(driver)
            print(f"Successfully processed batch {batch_start//5+1} in group {group_index+1}")
            time.sleep(2)

def main(username="krisnatha", password="Nasibungkus13"):
    driver = setup_driver()
    try:
        login_and_navigate(driver, username, password)
        csv_path = os.path.join(os.path.dirname(__file__), 'data/daily_inventory_allocation_seasonal.csv')
        groups = read_and_group_csv(csv_path)
        print(f"Read and grouped CSV into {len(groups)} groups.")
        process_allotment_dom(driver, groups)
        print('Allotment update via DOM completed.')
    finally:
        # driver.quit()  # Uncomment to close browser after running
        pass

if __name__ == '__main__':
    main() 