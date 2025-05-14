import pandas as pd
df = pd.read_csv('combined_inventory.csv')

# Filter to show only Deluxe and Premiere columns, keeping Date for reference
filtered_df = df[['Date', 'Deluxe Room', 'Premiere Room', 'Occupancy']]
df = filtered_df

# Filter rows where occupancy is less than 60%
df_deluxe_override = df[df['Occupancy'] < 60]
# Filter rows where Deluxe Room inventory is less than 0
df_deluxe_override = df_deluxe_override[(df_deluxe_override['Deluxe Room'] < 5) & (df_deluxe_override['Deluxe Room'] > -15)]
df_deluxe_override['alt_deluxe'] = 5


print(df_deluxe_override)

