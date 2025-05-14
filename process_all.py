import combine_inventory
import process_cm_inventory
import process_pms_inventory
from scraper import login_to_hospitality_suite

try:
    print("Running scraper...")
    import scraper
    scraper.login_to_hospitality_suite()
    print("Scraper completed")

    print("Processing CM inventory...")
    process_cm_inventory.process_cm_inventory()
    print("CM inventory processing complete")

    print("Processing PMS inventory...")
    process_pms_inventory.process_pms_inventory()
    print("PMS inventory processing complete")

    print("Combining inventory files...")
    combine_inventory.combine_inventory_files()
    print("Inventory files combined successfully")

except Exception as e:
    print(f"An error occurred: {str(e)}")