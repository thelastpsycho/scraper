import pandas as pd
import os
import sqlite3

def process_cm_inventory():
    # Get the absolute path to the data directory within the scraper folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, 'data')
    
    # Use path for the Excel file in data directory
    upload_path = os.path.join(data_dir, 'cm_upload.xlsx')
    
    if not os.path.exists(upload_path):
        raise FileNotFoundError(f"The CM Excel file was not found at: {upload_path}")
    
    df = pd.read_excel(upload_path)
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

    # Replace any non-numeric values with 0 except the ones in column Date
    df = df.apply(pd.to_numeric, errors='coerce').fillna(0)
    df['Date'] = pd.to_datetime(df['Date'])

    # Convert date to YYYY-MM-DD format for consistency
    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

    # Save processed data to CSV in data directory
    csv_path = os.path.join(data_dir, 'cm_inventory_processed.csv')
    df.to_csv(csv_path, index=False)
    print(f'Processed data saved to {csv_path}')

    # Save to SQLite database in data directory
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
