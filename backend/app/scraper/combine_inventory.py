import pandas as pd
import os
import sqlite3

def combine_inventory_files():
    try:
        # Get the absolute path to the data directory within the scraper folder
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(current_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Print paths for debugging
        print(f"Current directory: {current_dir}")
        print(f"Data directory: {data_dir}")
        
        # Define database paths
        pms_db_path = os.path.join(data_dir, 'pms_inventory_processed.db')
        cm_db_path = os.path.join(data_dir, 'cm_inventory_processed.db')
        
        # Check if input databases exist
        if not os.path.exists(pms_db_path):
            print(f"Error: PMS database not found at {pms_db_path}")
            return None
        if not os.path.exists(cm_db_path):
            print(f"Error: CM database not found at {cm_db_path}")
            return None
            
        print(f"Reading PMS data from: {pms_db_path}")
        print(f"Reading CM data from: {cm_db_path}")
        
        # Read the processed files from SQLite databases
        pms_conn = sqlite3.connect(pms_db_path)
        cm_conn = sqlite3.connect(cm_db_path)
        
        try:
            pms_df = pd.read_sql_query("SELECT * FROM pms_inventory_processed", pms_conn)
            print(f"Successfully read {len(pms_df)} rows from PMS database")
            print("PMS columns:", pms_df.columns.tolist())
            
            cm_df = pd.read_sql_query("SELECT * FROM cm_inventory_processed", cm_conn)
            print(f"Successfully read {len(cm_df)} rows from CM database")
            print("CM columns:", cm_df.columns.tolist())
        except sqlite3.OperationalError as e:
            print(f"Database error: {e}")
            if "no such table" in str(e):
                print("Error: Required table not found in database")
            return None
        finally:
            # Close the connections
            pms_conn.close()
            cm_conn.close()
        
        # Check if dataframes are empty
        if pms_df.empty:
            print("Error: No data found in PMS database")
            return None
        if cm_df.empty:
            print("Error: No data found in CM database")
            return None

        # Ensure Date columns are in datetime format
        try:
            pms_df['Date'] = pd.to_datetime(pms_df['Date'])
            cm_df['Date'] = pd.to_datetime(cm_df['Date'])
        except Exception as e:
            print(f"Error converting dates: {e}")
            return None

        # Merge the dataframes on Date
        try:
            combined_df = pd.merge(pms_df, cm_df, on='Date', how='outer')
            print(f"Successfully merged data. Combined dataframe has {len(combined_df)} rows")
        except Exception as e:
            print(f"Error merging dataframes: {e}")
            return None

        # Sort by Date
        combined_df = combined_df.sort_values('Date')

        # sum two values in the same column
        for col in combined_df.columns:
            if col.endswith('_x'):
                base_col = col[:-2]
                y_col = base_col + '_y'
                if y_col in combined_df.columns:
                    combined_df[base_col] = combined_df[col] + combined_df[y_col]
                    combined_df = combined_df.drop([col, y_col], axis=1)

        # Convert date back to string format for consistency
        combined_df['Date'] = combined_df['Date'].dt.strftime('%Y-%m-%d')

        # Save the combined data to CSV in data directory
        csv_path = os.path.join(data_dir, 'combined_inventory.csv')
        combined_df.to_csv(csv_path, index=False)
        print(f'Combined inventory saved to CSV: {csv_path}')

        # Save to SQLite database
        db_path = os.path.join(data_dir, 'combined_inventory.db')
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        
        try:
            # Create dtype dictionary for all columns except Date
            dtype_dict = {'Date': 'DATE'}
            for col in combined_df.columns:
                if col != 'Date':
                    dtype_dict[col] = 'INTEGER'
            
            # Save DataFrame to SQLite with explicit data types
            combined_df.to_sql('combined_inventory', conn, if_exists='replace', index=False, dtype=dtype_dict)
            
            # Verify the data was written
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM combined_inventory")
            count = cursor.fetchone()[0]
            print(f"Verified {count} rows written to combined_inventory table")
            
            if count == 0:
                print("Error: No data was written to the database")
                return None
                
        except Exception as e:
            print(f"Error writing to database: {e}")
            return None
        finally:
            # Close the connection
            conn.close()
            
        print(f'Combined inventory saved to database: {db_path}')
        return combined_df
        
    except Exception as e:
        print(f"Error during inventory combination: {e}")
        return None

if __name__ == "__main__":
    combine_inventory_files()