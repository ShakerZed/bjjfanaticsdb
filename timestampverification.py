import sqlite3
import pandas as pd

def inspect_timestamps(db_path="judo_mentions.db"):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT timestamp, throw_name FROM mentions ORDER BY timestamp LIMIT 50", conn)
    conn.close()
    
    print(df.head(50))  # Show first 50 entries

inspect_timestamps()
