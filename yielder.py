import pandas as pd
from tabulate import tabulate
from datetime import datetime
import os
import sqlite3

# Demand level configuration
DEMAND_BINS = [0, 70, 85, 100]  # Bins for Low, Medium, High demand
DEMAND_LABELS = ['Low', 'Medium', 'High']

# Threshold configuration for inventory levels
VERY_LOW_THRESHOLD_PCT = 0.05  # 5% of capacity
LOW_THRESHOLD_PCT = 0.2       # 20% of capacity

# Room capacity configuration
ROOM_CAPS = {
    'Deluxe Room': 160,
    'Premiere Room': 260
}

# Override configuration
DELUXE_OVERRIDE_OCCUPANCY = 70  # Override threshold for occupancy
DELUXE_OVERRIDE_PREMIERE = 61   # Override threshold for Premiere inventory
DELUXE_OVERRIDE_AMOUNT = 2      # Amount of Deluxe rooms to open in override

def should_override_deluxe(occupancy, premiere_inventory, deluxe_inventory):
    """
    Determine if Deluxe inventory should be overridden based on conditions:
    1. Deluxe inventory is less than 1
    2. AND (Occupancy is lower than DELUXE_OVERRIDE_OCCUPANCY
        OR Premiere inventory is higher than DELUXE_OVERRIDE_PREMIERE)
    """
    return (deluxe_inventory < 1 and 
            (occupancy < DELUXE_OVERRIDE_OCCUPANCY or premiere_inventory > DELUXE_OVERRIDE_PREMIERE))

# Load and clean the dataset
def load_and_clean_data(db_path='data/combined_inventory.db', demand_bins=None, demand_labels=None):
    # Use default values if not provided
    demand_bins = demand_bins or DEMAND_BINS
    demand_labels = demand_labels or DEMAND_LABELS
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        
        # Read data from the combined_inventory table
        data = pd.read_sql_query("SELECT * FROM combined_inventory", conn)
        
        # Close the connection
        conn.close()
        
        # Print column names for debugging
        print("Available columns:", data.columns.tolist())
        
    except Exception as e:
        print(f"Error reading from database: {e}")
        return None
    
    # First, combine the _x and _y columns by adding them together
    for col in data.columns:
        if col.endswith('_x'):
            base_col = col[:-2]  # Remove _x suffix
            y_col = base_col + '_y'
            if y_col in data.columns:
                data[base_col] = data[col] + data[y_col]
                # Drop the original columns
                data = data.drop([col, y_col], axis=1)
    
    # Map the actual column names to our expected names
    column_mapping = {
        'Deluxe Room': 'Deluxe Room',
        'Premiere Room': 'Premiere Room'
    }
    
    # Rename columns if they exist
    for old_name, new_name in column_mapping.items():
        if old_name in data.columns:
            data = data.rename(columns={old_name: new_name})
    
    relevant_columns = ['Date', 'Deluxe Room', 'Premiere Room', 'Occupancy']
    missing_columns = [col for col in relevant_columns if col not in data.columns]
    if missing_columns:
        print(f"Error: Missing columns: {missing_columns}")
        return None
    
    data = data[relevant_columns]
    
    if data.isnull().any().any():
        print("Warning: Missing values detected. Filling with 0 for inventory and median for Occupancy.")
        data[['Deluxe Room', 'Premiere Room']] = data[['Deluxe Room', 'Premiere Room']].fillna(0)
        data['Occupancy'] = data['Occupancy'].fillna(data['Occupancy'].median())
    
    try:
        data['Date'] = pd.to_datetime(data['Date'])
    except Exception as e:
        print(f"Error: Invalid date format. {e}")
        return None
    
    def assign_season(date):
        year = date.year
        date_no_year = date.replace(year=2025)
        if (datetime(2025, 1, 1) <= date_no_year <= datetime(2025, 1, 5) or
            datetime(2025, 12, 27) <= date_no_year <= datetime(2025, 12, 31) or
            date >= datetime(2026, 1, 1) and date <= datetime(2026, 1, 3)):
            return 'Peak'
        elif (datetime(2025, 1, 6) <= date_no_year <= datetime(2025, 5, 31) or
              datetime(2025, 10, 1) <= date_no_year <= datetime(2025, 12, 22)):
            return 'Normal'
        elif (datetime(2025, 6, 1) <= date_no_year <= datetime(2025, 6, 30) or
              datetime(2025, 9, 1) <= date_no_year <= datetime(2025, 9, 30)):
            return 'Shoulder'
        elif (datetime(2025, 7, 1) <= date_no_year <= datetime(2025, 8, 31) or
              datetime(2025, 12, 23) <= date_no_year <= datetime(2025, 12, 26)):
            return 'High'
        else:
            print(f"Warning: Unassigned season for {date}. Defaulting to Normal.")
            return 'Normal'
    
    data['Season'] = data['Date'].apply(assign_season)
    
    try:
        data['DemandLevel'] = pd.cut(
            data['Occupancy'],
            bins=demand_bins,
            labels=demand_labels,
            include_lowest=True
        )
    except Exception as e:
        print(f"Error: Invalid Occupancy values. {e}")
        return None
    
    data['DayOfWeek'] = data['Date'].dt.day_name()
    
    if (data['Deluxe Room'] < 0).any() or (data['Premiere Room'] < 0).any():
        print("Warning: Negative inventory values detected.")
    
    return data

# Apply yield matrix with limited online allotment and BAR based on remaining inventory
def apply_yield_matrix(data, very_low_threshold_pct=None, low_threshold_pct=None, room_caps=None):
    # Use default values if not provided
    very_low_threshold_pct = very_low_threshold_pct or VERY_LOW_THRESHOLD_PCT
    low_threshold_pct = low_threshold_pct or LOW_THRESHOLD_PCT
    room_caps = room_caps or ROOM_CAPS
    
    yield_matrix = {
        'Deluxe Room': {
            'Normal': {
                'High': {'bar': 'BAR4'},
                'Medium': {'bar': 'BAR5'},
                'Low': {'bar': 'BAR6'}
            },
            'Shoulder': {
                'High': {'bar': 'BAR3'},
                'Medium': {'bar': 'BAR4'},
                'Low': {'bar': 'BAR5'}
            },
            'High': {
                'High': {'bar': 'BAR2'},
                'Medium': {'bar': 'BAR3'},
                'Low': {'bar': 'BAR4'}
            },
            'Peak': {
                'High': {'bar': 'BAR2'},
                'Medium': {'bar': 'BAR3'},
                'Low': {'bar': 'BAR3'}
            }
        },
        'Premiere Room': {
            'Normal': {
                'High': {'bar': 'BAR4'},
                'Medium': {'bar': 'BAR5'},
                'Low': {'bar': 'BAR6'}
            },
            'Shoulder': {
                'High': {'bar': 'BAR3'},
                'Medium': {'bar': 'BAR4'},
                'Low': {'bar': 'BAR5'}
            },
            'High': {
                'High': {'bar': 'BAR2'},
                'Medium': {'bar': 'BAR3'},
                'Low': {'bar': 'BAR4'}
            },
            'Peak': {
                'High': {'bar': 'BAR2'},
                'Medium': {'bar': 'BAR3'},
                'Low': {'bar': 'BAR3'}
            }
        }
    }
    
    valid_bar_rates = {'BAR2', 'BAR3', 'BAR4', 'BAR5', 'BAR6'}
    bar_rate_order = {'BAR6': 5, 'BAR5': 4, 'BAR4': 3, 'BAR3': 2, 'BAR2': 1}  # Lower number = more expensive
    bar_rate_reverse = {1: 'BAR2', 2: 'BAR3', 3: 'BAR4', 4: 'BAR5', 5: 'BAR6'}
    
    data['Deluxe Online Inventory'] = 0
    data['Deluxe BAR Rate'] = ''
    data['Premiere Online Inventory'] = 0
    data['Premiere BAR Rate'] = ''
    
    for idx, row in data.iterrows():
        season = row['Season']
        demand = row['DemandLevel']
        if pd.isna(demand):
            print(f"Warning: Skipping row {idx} due to invalid DemandLevel for {row['Date'].strftime('%Y-%m-%d')}.")
            continue
        
        premiere_remaining = row['Premiere Room']
        deluxe_remaining = row['Deluxe Room']
        
        # Function to determine online allotment based on remaining inventory
        def get_online_allotment(remaining, room_cap):
            if remaining <= 0:
                return 0
            elif 1 <= remaining <= 5:
                return min(2, remaining, room_cap)
            elif 6 <= remaining <= 10:
                return min(5, remaining, room_cap)
            elif 11 <= remaining <= 50:
                return min(10, remaining, room_cap)
            else:  # remaining > 50
                return min(30, remaining, room_cap)
        
        # Function to adjust BAR rate based on remaining inventory
        def adjust_bar_rate(base_bar, remaining_inventory, room_type, demand, season):
            
            capacity = room_caps[room_type]
            very_low_threshold = capacity * very_low_threshold_pct
            low_threshold = capacity * low_threshold_pct
            
            base_rank = bar_rate_order.get(base_bar, 4)  # Default to BAR5 if invalid
            if remaining_inventory <= very_low_threshold:
                new_rank = max(1, base_rank - 2)  # Shift up 2 levels, cap at BAR2
                print(f"{row['Date'].strftime('%Y-%m-%d')} {room_type}: Remaining {remaining_inventory} (Very Low) → {base_bar} to {bar_rate_reverse[new_rank]}")
            elif remaining_inventory <= low_threshold:
                new_rank = max(1, base_rank - 1)  # Shift up 1 level
                print(f"{row['Date'].strftime('%Y-%m-%d')} {room_type}: Remaining {remaining_inventory} (Low) → {base_bar} to {bar_rate_reverse[new_rank]}")
            else:
                new_rank = base_rank  # No change
                print(f"{row['Date'].strftime('%Y-%m-%d')} {room_type}: Remaining {remaining_inventory} (Moderate/High) → {base_bar}")
            return bar_rate_reverse.get(new_rank, 'BAR5')
        
        # Premiere Room
        room = 'Premiere Room'
        remaining = premiere_remaining
        online_inventory = get_online_allotment(remaining, room_caps[room])
        base_bar = yield_matrix[room][season][demand]['bar']
        if base_bar not in valid_bar_rates:
            print(f"Warning: Invalid Premiere BAR Rate '{base_bar}' for {row['Date'].strftime('%Y-%m-%d')}. Using BAR5.")
            base_bar = 'BAR5'
        bar_rate = adjust_bar_rate(base_bar, remaining, room, demand, season)
        
        data.at[idx, 'Premiere Online Inventory'] = online_inventory
        data.at[idx, 'Premiere BAR Rate'] = bar_rate
        
        # Deluxe Room
        room = 'Deluxe Room'
        remaining = deluxe_remaining
        
        # Check for override conditions
        if should_override_deluxe(row['Occupancy'], premiere_remaining, remaining):
            online_inventory = DELUXE_OVERRIDE_AMOUNT
            print(f"{row['Date'].strftime('%Y-%m-%d')} Deluxe Room: Override applied - Opening {online_inventory} rooms (Occupancy: {row['Occupancy']:.2f}%, Premiere: {premiere_remaining}, Deluxe: {remaining})")
        else:
            online_inventory = get_online_allotment(remaining, room_caps[room])
        
        base_bar = yield_matrix[room][season][demand]['bar']
        if base_bar not in valid_bar_rates:
            print(f"Warning: Invalid Deluxe BAR Rate '{base_bar}' for {row['Date'].strftime('%Y-%m-%d')}. Using BAR5.")
            base_bar = 'BAR5'
        bar_rate = adjust_bar_rate(base_bar, remaining, room, demand, season)
        
        data.at[idx, 'Deluxe Online Inventory'] = online_inventory
        data.at[idx, 'Deluxe BAR Rate'] = bar_rate
    
    return data

# Main execution
def main():
    data = load_and_clean_data()
    if data is None:
        return
    
    data = apply_yield_matrix(data)
    
    output = data[[
        'Date', 'DayOfWeek', 'Season', 'Occupancy', 'DemandLevel',
        'Deluxe Room', 'Deluxe Online Inventory', 'Deluxe BAR Rate',
        'Premiere Room', 'Premiere Online Inventory', 'Premiere BAR Rate'
    ]].copy()
    output['Date'] = output['Date'].dt.strftime('%Y-%m-%d')
    output['Occupancy'] = output['Occupancy'].round(2)
    output = output.rename(columns={
        'Deluxe Room': 'Deluxe Remaining Inventory',
        'Premiere Room': 'Premiere Remaining Inventory'
    })
    
    print("\n=== Day-by-Day Inventory Allocation ===")
    print(tabulate(output, headers='keys', tablefmt='grid', showindex=False))
    
    try:
        # Save to CSV
        output.to_csv('daily_inventory_allocation_seasonal.csv', index=False)
        print("\nOutput saved to 'daily_inventory_allocation_seasonal.csv'")
        
        # Save to SQLite
        import sqlite3
        import os
        
        # Define database path
        db_path = 'data/inventory_allocation.db'
        
        # Remove existing database file if it exists
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing database file: {db_path}")
        
        # Create db directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        
        # Enable date handling in SQLite
        conn.execute('PRAGMA foreign_keys = ON')
        
        # Define SQLite data types for each column
        dtype = {
            'Date': 'DATE',
            'DayOfWeek': 'TEXT',
            'Season': 'TEXT',
            'Occupancy': 'REAL',
            'DemandLevel': 'TEXT',
            'Deluxe Remaining Inventory': 'INTEGER',
            'Deluxe Online Inventory': 'INTEGER',
            'Deluxe BAR Rate': 'TEXT',
            'Premiere Remaining Inventory': 'INTEGER',
            'Premiere Online Inventory': 'INTEGER',
            'Premiere BAR Rate': 'TEXT'
        }
        
        # Ensure date is in YYYY-MM-DD format before saving
        output['Date'] = pd.to_datetime(output['Date']).dt.strftime('%Y-%m-%d')
        
        # Save to database with correct table name and data types
        output.to_sql('daily_inventory_allocation', conn, if_exists='replace', index=False, dtype=dtype)
        conn.close()
        print(f"Created new database file: {db_path}")
    except Exception as e:
        print(f"Error saving data: {e}")
        if 'conn' in locals():
            conn.close()
    
    # print("\n=== Key Observations ===")
    # print("- Demand levels based on hotel occupancy: Low (≤70%), Medium (>70% to ≤85%), High (>85%).")
    # print("- Yield matrix: Lowest BAR6 (Normal), BAR5 (Shoulder), BAR4 (High), BAR3 (Peak).")
    # print("- BAR adjustments: For High demand or Medium demand in Normal/High/Peak seasons, Very Low (≤8 Deluxe, ≤13 Premiere) → +2 levels, Low (9-32 Deluxe, 14-52 Premiere) → +1 level.")
    # print("- No BAR adjustments for Low demand or Medium demand in Shoulder season, ensuring base matrix rate (e.g., BAR4 for Medium in Shoulder).")
    # print("- Online allotment: 1-5 → 2, 6-10 → 5, 11-50 → 10, >50 → 30 rooms.")
    # print("- June 11, 2025 (59.63% Medium, Shoulder): Deluxe Online = 0, BAR4; Premiere Online = 30, BAR4.")
    # print("- July 21, 2025 (24.34% Low, High): Deluxe Online = 10, BAR4; Premiere Online = 30, BAR4.")
    # print("- July 14, 2025 (50.10% Medium, High): Deluxe Online = 10, BAR3 → BAR2; Premiere Online = 30, BAR3.")
    # print("- May 17, 2025 (68.58% Medium, Normal): Deluxe Online = 30, BAR5 → BAR4; Premiere Online = 10, BAR5 → BAR3.")
    # print("\n=== Implementation Notes ===")
    # print("- Seasons: Normal (Jan 6-May 31, Oct 1-Dec 22), Shoulder (Jun, Sep), High (Jul-Aug, Dec 23-26), Peak (Jan 1-5, Dec 27-Jan 3).")
    # print("- Negative inventory retained; online inventory ≥ 0.")
    # print("- BAR rates: BAR2-BAR6, BAR2 most expensive.")
    # print(f"- Room Capacities: Deluxe {ROOM_CAPS['Deluxe Room']}, Premiere {ROOM_CAPS['Premiere Room']}.")
    # print(f"- Deluxe Override: Opens {DELUXE_OVERRIDE_AMOUNT} rooms when Deluxe < 1 AND (occupancy < {DELUXE_OVERRIDE_OCCUPANCY}% or Premiere inventory > {DELUXE_OVERRIDE_PREMIERE}).")

if __name__ == "__main__":
    main()