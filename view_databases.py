import os
import sqlite3
import pandas as pd
from datetime import datetime

def get_table_info(conn, table_name):
    """Get column information for a table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()

def format_date(value):
    """Format date values to '11 June 2025' format"""
    try:
        # Try parsing the date
        if isinstance(value, str):
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
                try:
                    date_obj = datetime.strptime(value, fmt)
                    return date_obj.strftime('%d %B %Y')
                except ValueError:
                    continue
        elif isinstance(value, datetime):
            return value.strftime('%d %B %Y')
        return value
    except:
        return value

def get_table_data(conn, table_name, limit=100):
    """Get sample data from a table"""
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit}", conn)
        
        # Format date columns
        for col in df.columns:
            # Check if column name contains 'date' or 'Date'
            if 'date' in col.lower():
                df[col] = df[col].apply(format_date)
        
        return df
    except Exception as e:
        return pd.DataFrame({'Error': [str(e)]})

def generate_html():
    # Get all .db files in the data directory
    db_files = [f for f in os.listdir('data') if f.endswith('.db')]
    
    timestamp = datetime.now().strftime('%d %B %Y %H:%M:%S')
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Database Viewer</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .table-container {{
                position: relative;
                background: white;
                border-radius: 0.75rem;
                box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            }}
            .cell {{
                position: relative;
                transition: all 0.2s ease-in-out;
            }}
            .cell:hover {{
                background-color: rgb(219 234 254) !important;
            }}
            tr:hover td {{
                background-color: rgb(241 245 249);
            }}
            td:hover {{
                background-color: rgb(219 234 254) !important;
            }}
            td:hover ~ td {{
                background-color: rgb(241 245 249);
            }}
            tr:hover td:hover ~ td {{
                background-color: rgb(241 245 249);
            }}
            tr:hover td:hover {{
                background-color: rgb(219 234 254) !important;
            }}
            .table-header {{
                background: linear-gradient(to right, rgb(30 64 175), rgb(37 99 235));
                color: white;
            }}
            .table-header th {{
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
            .alternate-row {{
                background-color: rgb(248 250 252);
            }}
        </style>
    </head>
    <body class="bg-slate-50 p-8">
        <div class="max-w-7xl mx-auto">
            <div class="bg-white rounded-xl shadow-lg p-6 mb-8">
                <h1 class="text-3xl font-bold text-slate-800 mb-2">Database Viewer</h1>
                <p class="text-sm text-slate-500">Generated on: {timestamp}</p>
            </div>
    """

    for db_file in db_files:
        db_path = os.path.join('data', db_file)
        conn = sqlite3.connect(db_path)
        
        # Get all tables in the database
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        html_content += f"""
            <div class="mb-8">
                <div class="bg-white rounded-xl shadow-lg p-6">
                    <h2 class="text-2xl font-semibold text-slate-800 mb-4">Database: {db_file}</h2>
        """
        
        for table in tables:
            table_name = table[0]
            
            # Get table info
            columns = get_table_info(conn, table_name)
            column_names = [col[1] for col in columns]
            
            # Get sample data
            df = get_table_data(conn, table_name)
            
            html_content += f"""
                <div class="mb-6">
                    <h3 class="text-lg font-medium text-slate-700 mb-3">Table: {table_name}</h3>
                    <div class="overflow-x-auto rounded-lg table-container">
                        <table class="min-w-full divide-y divide-slate-200 text-sm">
                            <thead class="table-header">
                                <tr>
                                    {''.join(f'<th class="px-4 py-3 text-left text-xs tracking-wider">{col}</th>' for col in df.columns)}
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-200">
                                {''.join(
                                    f'<tr class="{"alternate-row" if i % 2 == 0 else ""}">{"".join(f"<td class=\"px-4 py-3 whitespace-nowrap text-slate-600 cell\">{str(val)}</td>" for val in row)}</tr>'
                                    for i, row in enumerate(df.values)
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            """
        
        conn.close()
        html_content += "</div></div>"
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    # Write the HTML file
    with open('data/database_viewer.html', 'w') as f:
        f.write(html_content)
    
    print(f"HTML file generated: data/database_viewer.html")

if __name__ == "__main__":
    generate_html() 