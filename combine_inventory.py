import pandas as pd

def combine_inventory_files():
    # Read the CSV files
    cm_df = pd.read_csv('cm_inventory.csv')
    pms_df = pd.read_csv('pms_inventory_processed.csv')

    # Standardize column names (strip, lower, replace common typos)
    def standardize_cols(df):
        df = df.rename(columns=lambda x: x.strip().replace('with Whirpool', 'Whirpool').replace('With Pool', 'With Pool'))
        return df
    cm_df = standardize_cols(cm_df)
    pms_df = standardize_cols(pms_df)

    # Find all columns except Date
    all_cols = set(cm_df.columns).union(set(pms_df.columns))
    all_cols.discard('Date')

    # Ensure both dataframes have all columns, fill missing with 0
    for col in all_cols:
        if col not in cm_df:
            cm_df[col] = 0
        if col not in pms_df:
            pms_df[col] = 0

    # Convert all numeric columns to float, keeping Date as string
    numeric_columns = [col for col in all_cols]
    cm_df[numeric_columns] = cm_df[numeric_columns].apply(pd.to_numeric, errors='coerce').fillna(0)
    pms_df[numeric_columns] = pms_df[numeric_columns].apply(pd.to_numeric, errors='coerce').fillna(0)

    # Merge on Date
    combined_df = cm_df[['Date'] + numeric_columns].copy()
    for col in numeric_columns:
        combined_df[col] = cm_df[col] + pms_df[col]

    # Add Occupancy column from pms_df if present
    if 'Occupancy' in pms_df.columns:
        combined_df['Occupancy'] = pms_df['Occupancy']

    # Reorder columns to put Occupancy last if present
    cols = [col for col in combined_df.columns if col != 'Occupancy']
    if 'Occupancy' in combined_df.columns:
        cols.append('Occupancy')
    combined_df = combined_df[cols]

    # Save the combined dataframe to a new CSV file
    combined_df.to_csv('combined_inventory.csv', index=False)

    print("Files have been combined successfully into combined_inventory.csv")

if __name__ == "__main__":
    combine_inventory_files()