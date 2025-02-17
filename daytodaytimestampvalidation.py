import sqlite3
import pandas as pd

def inspect_daily_counts(db_path="judo_mentions.db"):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT timestamp, throw_name FROM mentions", conn)
    conn.close()
    
    # Convert timestamps to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"] = df["timestamp"].dt.date
    
    # Count how many mentions occur each day
    daily_counts = df.groupby("date").size().reset_index(name="mention_count")
    
    print("Day-by-day mention counts:")
    print(daily_counts.sort_values("date"))  # sort by date ascending

inspect_daily_counts()
