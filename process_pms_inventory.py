import pandas as pd
import os
import sqlite3

def process_pms_inventory(df=None):
    # If no DataFrame is provided, read from CSV (for backward compatibility)
    if df is None:
        df = pd.read_csv('pms_inventory.csv')
        
        # Convert numeric columns to appropriate types
        numeric_columns = ['DLK', 'DLT', 'DLKP', 'DLTP', 'PRKG', 'PRKP', 'PRTG', 'PRTP', 'PRKL', 'PRTL',
                         'Extra Bed', 'Total Room', 'Available', 'Tentative', 'Definite', 'Waiting List', 
                         'Allotment', 'Out of Order']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Convert date format if it's a string
        if isinstance(df['Date'].iloc[0], str):
            df['Date'] = pd.to_datetime(df['Date'], format='%A, %d-%b-%Y')

    # AVR	= The Anvaya Residence
    # AVS	= The Anvaya Suite No Pool
    # ASP	= The Anvaya Suite With Pool
    # ASW	= The Anvaya Suite Whirpool
    # AVP	= The Anvaya Villa
    # BFS	= Beach Front Private Suite Room
    # DLK + DLT	= Deluxe Room
    # DLKP + DLTP	= Deluxe Pool Access
    # DLS	= Deluxe Suite Room
    # FAM	= Family Premiere Room
    # PRKG + PRKP + PRTG + PRTP	= Premiere Room
    # PRKL + PRTL	= Premiere Room Lagoon Access
    # PSU	= Premiere Suite Room

    # Create new columns by combining existing ones
    df['Deluxe Room'] = df['DLK'] + df['DLT'] 
    df['Deluxe Pool Access'] = df['DLKP'] + df['DLTP']
    df['Premiere Room'] = df['PRKG'] + df['PRKP'] + df['PRTG'] + df['PRTP']
    df['Premiere Room Lagoon Access'] = df['PRKL'] + df['PRTL']

    # Rename columns to match desired names
    df = df.rename(columns={
        'AVR': 'The Anvaya Residence',
        'AVS': 'The Anvaya Suite No Pool', 
        'ASP': 'The Anvaya Suite With Pool',
        'ASW': 'The Anvaya Suite Whirpool',
        'AVP': 'The Anvaya Villa',
        'BFS': 'Beach Front Private Suite Room',
        'DLS': 'Deluxe Suite Room',
        'FAM': 'Family Premiere Room',
        'PSU': 'Premiere Suite Room'
    })

    # Drop original columns that were combined
    df = df.drop(['DLK', 'DLT', 'DLKP', 'DLTP', 'PRKG', 'PRKP', 'PRTG', 'PRTP', 'PRKL', 'PRTL'], axis=1)
    # Drop additional columns
    df = df.drop(['Extra Bed', 'Total Room', 'Available', 'Tentative', 'Definite', 'Waiting List', 'Allotment', 'Out of Order'], axis=1)

    # Ensure date is in datetime format
    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'], format='%A, %d-%b-%Y')

    # Save to CSV
    df.to_csv('pms_inventory_processed.csv', index=False)
    
    # Save to SQLite database
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Connect to SQLite database
    conn = sqlite3.connect('data/pms_inventory_processed.db')
    
    # Define data types for each column
    dtype_dict = {
        'Date': 'DATE',
        'The Anvaya Residence': 'INTEGER',
        'The Anvaya Suite No Pool': 'INTEGER',
        'The Anvaya Suite With Pool': 'INTEGER',
        'The Anvaya Suite Whirpool': 'INTEGER',
        'The Anvaya Villa': 'INTEGER',
        'Beach Front Private Suite Room': 'INTEGER',
        'Deluxe Suite Room': 'INTEGER',
        'Family Premiere Room': 'INTEGER',
        'Premiere Suite Room': 'INTEGER',
        'Deluxe Room': 'INTEGER',
        'Deluxe Pool Access': 'INTEGER',
        'Premiere Room': 'INTEGER',
        'Premiere Room Lagoon Access': 'INTEGER'
    }
    
    # Save DataFrame to SQLite with explicit data types
    df.to_sql('pms_inventory_processed', conn, if_exists='replace', index=False, dtype=dtype_dict)
    
    # Close the connection
    conn.close()
    
    return df

if __name__ == "__main__":
    process_pms_inventory()