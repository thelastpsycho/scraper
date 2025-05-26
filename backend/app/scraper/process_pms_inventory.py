import pandas as pd
import os
import sqlite3

def process_pms_inventory(df=None):
    # Get the absolute path to the data directory within the scraper folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, 'data')
    
    # Print the paths for debugging
    print(f"Current directory: {current_dir}")
    print(f"Data directory: {data_dir}")
    
    os.makedirs(data_dir, exist_ok=True)
    
    # If no DataFrame is provided, read from the raw database in data directory
    if df is None:
        try:
            # Connect to SQLite database
            db_path = os.path.join(data_dir, 'pms_inventory_raw.db')
            if not os.path.exists(db_path):
                print(f"Error: Raw database not found at {db_path}")
                return None
                
            conn = sqlite3.connect(db_path)
            
            # Read data from the pms_inventory table
            df = pd.read_sql_query("SELECT * FROM pms_inventory", conn)
            
            # Close the connection
            conn.close()
            
            if df.empty:
                print("Error: No data found in the raw database")
                return None
            
            print(f"Successfully read raw data from {db_path}")
            
            # Convert numeric columns to appropriate types
            numeric_columns = ['DLK', 'DLT', 'DLKP', 'DLTP', 'PRKG', 'PRKP', 'PRTG', 'PRTP', 'PRKL', 'PRTL',
                             'Extra Bed', 'Total Room', 'Available', 'Tentative', 'Definite', 'Waiting List', 
                             'Allotment', 'Out of Order']
            
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Convert date format if it's a string
            if isinstance(df['Date'].iloc[0], str):
                try:
                    df['Date'] = pd.to_datetime(df['Date'], format='%A, %d-%b-%Y')
                except ValueError:
                    df['Date'] = pd.to_datetime(df['Date'], format='%A, %d-%B-%Y')
        except Exception as e:
            print(f"Error reading from database: {e}")
            return None

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

    try:
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
            try:
                # First try with abbreviated month names (e.g., Jun)
                df['Date'] = pd.to_datetime(df['Date'], format='%A, %d-%b-%Y')
            except ValueError:
                try:
                    # Then try with full month names (e.g., June)
                    df['Date'] = pd.to_datetime(df['Date'], format='%A, %d-%B-%Y')
                except ValueError:
                    try:
                        # Try parsing without specifying format
                        df['Date'] = pd.to_datetime(df['Date'])
                    except ValueError as e:
                        print(f"Error parsing dates: {str(e)}")
                        print("Sample date value:", df['Date'].iloc[0])
                        raise

        # Convert date to YYYY-MM-DD format for consistency
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

        # Save processed data to CSV in data directory
        csv_path = os.path.join(data_dir, 'pms_inventory_processed.csv')
        df.to_csv(csv_path, index=False)
        print(f"Processed data saved to CSV: {csv_path}")
        
        # Save to SQLite database
        db_path = os.path.join(data_dir, 'pms_inventory_processed.db')
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        
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
        print(f"Processed data saved to database: {db_path}")
        
        return df
        
    except Exception as e:
        print(f"Error during data processing: {e}")
        return None

if __name__ == "__main__":
    process_pms_inventory()