import pandas as pd

def process_pms_inventory():
    df = pd.read_csv('pms_inventory.csv')

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

    # change dat einto date format
    df['Date'] = pd.to_datetime(df['Date'], format='%A, %d-%b-%Y')

    df.to_csv('pms_inventory_processed.csv', index=False)

if __name__ == "__main__":
    process_pms_inventory()