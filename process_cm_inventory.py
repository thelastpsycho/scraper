import pandas as pd
import os
import sqlite3

def process_cm_inventory():
    df = pd.read_excel('xxx.xlsx')
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

    # Save to CSV
    df.to_csv('cm_inventory.csv', index=False, mode='w')
    print('cm_inventory.csv saved')

    # Save to SQLite database
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Connect to SQLite database
    conn = sqlite3.connect('data/cm_inventory_processed.db')
    
    # Create dtype dictionary for all columns except Date
    dtype_dict = {'Date': 'DATE'}
    for col in df.columns:
        if col != 'Date':
            dtype_dict[col] = 'INTEGER'
    
    # Save DataFrame to SQLite with explicit data types
    df.to_sql('cm_inventory_processed', conn, if_exists='replace', index=False, dtype=dtype_dict)
    
    # Close the connection
    conn.close()
    print('data/cm_inventory_processed.db saved')

if __name__ == "__main__":
    process_cm_inventory()
