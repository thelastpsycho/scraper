import pandas as pd
import os
import sqlite3
from ..infrastructure.paths import get_data_dir

def process_cm_inventory():
    # Get the absolute path to the data directory within the scraper folder
    data_dir = get_data_dir()
    
    # Use path for the Excel file in data directory
    upload_path = os.path.join(data_dir, 'cm_upload.xlsx')
    
    if not os.path.exists(upload_path):
        raise FileNotFoundError(f"The CM Excel file was not found at: {upload_path}")
    
    df = pd.read_excel(upload_path)

    # Keep an unfiltered copy of exactly what was scraped/uploaded (before the
    # 'Left for sale' filter + transpose below) so it can be inspected as-is.
    raw_db_path = os.path.join(data_dir, 'cm_inventory_raw.db')
    raw_conn = sqlite3.connect(raw_db_path)
    df.to_sql('cm_inventory_raw', raw_conn, if_exists='replace', index=False)
    raw_conn.close()

    df = df.drop('Unnamed: 1', axis=1)
    df = df.rename(columns={'Unnamed: 2': 'Type'})
    df = df[df['Type'] == 'Left for sale']
    df = df.drop('Type', axis=1)
    # Transpose the DataFrame
    df = df.transpose()

    # Make the first row the column headers
    df.columns = df.iloc[0]
    df = df.iloc[1:]

    # Reset the index to make the dates into a column
    df = df.reset_index()
    df = df.rename(columns={'index': 'Date'})

    # Preserve Date before coercing the inventory values. Converting the whole
    # frame first turns ISO date strings into NaN/0 (1970-01-01), which then
    # prevents the CM rows from aligning with PMS dates during combination.
    dates = pd.to_datetime(df['Date'], errors='raise')
    values = df.drop(columns=['Date']).apply(pd.to_numeric, errors='coerce').fillna(0)
    df = pd.concat([dates.rename('Date'), values], axis=1)

    # Convert date to YYYY-MM-DD format for consistency
    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

    # Save to SQLite database (single source of truth for downstream stages)
    db_path = os.path.join(data_dir, 'cm_inventory_processed.db')
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    
    # Create dtype dictionary for all columns except Date
    dtype_dict = {'Date': 'DATE'}
    for col in df.columns:
        if col != 'Date':
            dtype_dict[col] = 'INTEGER'
    
    # Save DataFrame to SQLite with explicit data types
    df.to_sql('cm_inventory_processed', conn, if_exists='replace', index=False, dtype=dtype_dict)
    
    # Close the connection
    conn.close()
    print(f'Processed data saved to {db_path}')
    
    return "CM Inventory processing completed successfully"

if __name__ == "__main__":
    process_cm_inventory()
