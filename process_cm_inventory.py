import pandas as pd

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

    df.to_csv('cm_inventory.csv', index=False, mode='w')
    print('cm_inventory.csv saved')

if __name__ == "__main__":
    process_cm_inventory()
