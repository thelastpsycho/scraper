# Hospitality Suite Scraper

This is a Python-based web scraper for the Hospitality Suite website using Selenium and Chrome WebDriver.

## Prerequisites

- Python 3.7 or higher
- Chrome browser installed
- pip (Python package installer)

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have Chrome browser installed on your system.

## Usage

Run the scraper:
```bash
python scraper.py
```

The script will:
1. Open Chrome browser
2. Navigate to the login page
3. Enter the credentials
4. Click the login button
5. Wait for the login process to complete
6. Keep the browser open for inspection (press Enter to close)

## Notes

- The script currently includes basic login functionality
- You can modify the `scraper.py` file to add additional scraping logic after successful login
- To run the browser in headless mode, uncomment the `--headless` option in the `setup_driver()` function 