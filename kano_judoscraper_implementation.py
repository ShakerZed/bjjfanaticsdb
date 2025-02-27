#!/usr/bin/env python3

"""
kano_judoscraper_implementation.py

1) Loads Judo throws from judo_throws.db (the 'judo_throws' table).
2) Checks newest posts and comments in /r/judo for references to these throws.
3) Stores matched throws in a new database (judo_mentions.db) with timestamps.
4) Prints out any matched throws, plus a final summary of total matches and a tally of throw mentions.
5) (NEW) Provides data visualization using Matplotlib and Seaborn, including:
   - A line chart showing top throws over time.
   - A bar chart showing the most-mentioned throws.

This script is useful for tracking mentions of Judo techniques across Reddit, allowing for
insights into which techniques are being discussed the most over time.

Dependencies:
    - Python 3.7+
    - PRAW (pip install praw)
    - sqlite3 (standard library for DB operations)
    - (Optional) python-dotenv for environment-based secrets
    - A judo_throws.db containing a table named 'judo_throws' with a 'throw_name' column
    - pandas, matplotlib, seaborn for data visualization

Usage:
    1. Install dependencies: `pip install praw pandas matplotlib seaborn`
    2. Provide environment variables (or .env) for:
       - REDDIT_CLIENT_ID
       - REDDIT_CLIENT_SECRET
       - REDDIT_USER_AGENT
    3. Run the script: `python kano_judoscraper_implementation.py`
"""


import os
import re
import sqlite3
import praw
import time
from collections import Counter
from datetime import datetime, timedelta

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Optional: Add support for .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("dotenv not installed, using environment variables directly")

################## LOAD REDDIT CREDENTIALS FROM ENV ##################
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT")
)
######################################################################

def load_judo_throws(db_path="judo_throws.db"):
    """
    Loads Judo throw names from 'judo_throws' table in judo_throws.db.
    Returns a list of strings (the throw names).
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT throw_name FROM judo_throws")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def find_throws_in_text(text, judo_throws):
    """
    Uses a regex with word boundaries to find Judo throws in text.
    Returns a list of matched throw names.
    """
    found = []
    if not text or not isinstance(text, str):
        return found
        
    text_lower = text.lower()
    for throw in judo_throws:
        pattern = rf'(?i)\b{re.escape(throw)}\b'
        if re.search(pattern, text_lower):
            found.append(throw)
    return found

def store_mention(db_path, mention_type, post_id, url, throw_name, timestamp=None):
    """
    Stores a mention in the database with an accurate timestamp.
    
    Args:
        db_path: Path to SQLite database
        mention_type: Either 'submission' or 'comment'
        post_id: Reddit ID for the post/comment
        url: Link to the post/comment
        throw_name: Name of the Judo throw mentioned
        timestamp: If provided, use this timestamp. Otherwise use current UTC time.
    """
    # Use provided timestamp or current UTC time
    if timestamp is None:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO mentions (timestamp, type, post_id, url, throw_name)
        VALUES (?, ?, ?, ?, ?)
    """, (timestamp, mention_type, post_id, url, throw_name))
    conn.commit()
    conn.close()

def match_submissions(subreddit_name, judo_throws, db_path, limit=10000, time_filter=None):
    """
    Scans submissions in /r/<subreddit_name>, searching for Judo throw mentions.
    Saves each mention via store_mention() with the correct submission timestamp.
    
    Args:
        time_filter: Optional time filter for submissions ('all', 'year', 'month', etc.)
    """
    print(f"\n[INFO] Checking submissions in /r/{subreddit_name} (limit={limit})...")
    
    subreddit = reddit.subreddit(subreddit_name)
    count = 0
    matches = 0
    
    try:
        # Use different methods based on time_filter
        if time_filter:
            submissions = subreddit.top(time_filter=time_filter, limit=limit)
        else:
            submissions = subreddit.new(limit=limit)
        
        for submission in submissions:
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} submissions, found {matches} matches so far...")
            
            post_text = (submission.title or "") + " " + (submission.selftext or "")
            found = find_throws_in_text(post_text, judo_throws)
            
            if found:
                matches += len(found)
                # Get actual submission timestamp
                submission_time = datetime.fromtimestamp(submission.created_utc)
                formatted_time = submission_time.strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"Matched in Submission: {submission.id} from {formatted_time}")
                print(f"URL: {submission.url}")
                print(f"Judo Throws Found: {found}")
                print("----------")
                
                for throw in found:
                    store_mention(db_path, "submission", submission.id, 
                                  submission.url, throw, formatted_time)
    
    except Exception as e:
        print(f"[ERROR] Error processing submissions: {str(e)}")
    
    print(f"[INFO] Completed submission processing. Checked {count} submissions, found {matches} throw mentions.")
    return matches

def match_comments(subreddit_name, judo_throws, db_path, limit=20000):
    """
    Scans comments in /r/<subreddit_name>, searching for Judo throw mentions.
    Saves each mention via store_mention() with the correct comment timestamp.
    """
    print(f"\n[INFO] Checking comments in /r/{subreddit_name} (limit={limit})...")
    
    subreddit = reddit.subreddit(subreddit_name)
    count = 0
    matches = 0
    
    try:
        for comment in subreddit.comments(limit=limit):
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} comments, found {matches} matches so far...")
            
            text = comment.body or ""
            found = find_throws_in_text(text, judo_throws)
            
            if found:
                matches += len(found)
                # Get actual comment timestamp
                comment_time = datetime.fromtimestamp(comment.created_utc)
                formatted_time = comment_time.strftime("%Y-%m-%d %H:%M:%S")
                
                permalink = f"https://www.reddit.com{comment.permalink}"
                print(f"Matched in Comment: {comment.id} from {formatted_time}")
                print(f"Permalink: {permalink}")
                print(f"Judo Throws Found: {found}")
                print("----------")
                
                for throw in found:
                    store_mention(db_path, "comment", comment.id, 
                                  permalink, throw, formatted_time)
    
    except Exception as e:
        print(f"[ERROR] Error processing comments: {str(e)}")
    
    print(f"[INFO] Completed comment processing. Checked {count} comments, found {matches} throw mentions.")
    return matches

def scrape_by_time_periods(subreddit_name, judo_throws, db_path, periods=6):
    """
    Scrape Reddit using different time filters to get more balanced historical data.
    
    This function uses Reddit's built-in time filters to ensure we get data
    from different time periods, not just the most recent posts.
    
    Args:
        periods: Number of different time periods to use (approximate)
    """
    print(f"[INFO] Starting time-based scraping for /r/{subreddit_name}")
    
    # Use Reddit's time filters
    time_filters = ["hour", "day", "week", "month", "year", "all"]
    
    total_matches = 0
    for time_filter in time_filters:
        print(f"\n[INFO] Scraping posts with time filter: {time_filter}")
        matches = match_submissions(subreddit_name, judo_throws, db_path, 
                                   limit=5000, time_filter=time_filter)
        total_matches += matches
    
    print(f"[INFO] Completed time-based scraping with {total_matches} total matches")
    return total_matches

def remove_exact_duplicates(db_path="judo_mentions.db"):
    """
    Removes exact duplicates where (timestamp, post_id, throw_name) are identical.
    Keeps only the first occurrence of each.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Count duplicates before removal
    cursor.execute("""
        SELECT COUNT(*) as count FROM mentions
    """)
    before_count = cursor.fetchone()[0]

    cursor.execute("""
        DELETE FROM mentions
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM mentions
            GROUP BY timestamp, post_id, throw_name
        )
    """)
    
    # Count after removal
    cursor.execute("""
        SELECT COUNT(*) as count FROM mentions
    """)
    after_count = cursor.fetchone()[0]
    removed = before_count - after_count

    conn.commit()
    conn.close()
    print(f"Removed {removed} exact duplicates. {after_count} records remaining.")

def remove_soft_duplicates(db_path="judo_mentions.db"):
    """
    Removes duplicates where (post_id, throw_name) are identical, ignoring timestamp differences.
    Keeps only the first occurrence of each.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Count duplicates before removal
    cursor.execute("""
        SELECT COUNT(*) as count FROM mentions
    """)
    before_count = cursor.fetchone()[0]

    cursor.execute("""
        DELETE FROM mentions
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM mentions
            GROUP BY post_id, throw_name
        )
    """)
    
    # Count after removal
    cursor.execute("""
        SELECT COUNT(*) as count FROM mentions
    """)
    after_count = cursor.fetchone()[0]
    removed = before_count - after_count

    conn.commit()
    conn.close()
    print(f"Removed {removed} soft duplicates. {after_count} records remaining.")

def verify_timestamps(db_path="judo_mentions.db"):
    """
    Check for any suspicious timestamps in the database.
    Prints a report of timestamp ranges and any future dates.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get earliest and latest timestamps
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM mentions")
    earliest, latest = cursor.fetchone()
    
    # Check for future dates
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("SELECT COUNT(*) FROM mentions WHERE timestamp > ?", (now,))
    future_count = cursor.fetchone()[0]
    
    if future_count > 0:
        print(f"[WARNING] Found {future_count} records with future timestamps!")
        cursor.execute("SELECT timestamp, type, post_id, throw_name FROM mentions WHERE timestamp > ? LIMIT 10", (now,))
        future_records = cursor.fetchall()
        print("Sample future records:")
        for record in future_records:
            print(f"  {record}")
    
    # Count by year to see distribution
    cursor.execute("""
        SELECT strftime('%Y', timestamp) as year, COUNT(*) as count 
        FROM mentions 
        GROUP BY year
        ORDER BY year
    """)
    year_counts = cursor.fetchall()
    
    print("\nTimestamp Analysis:")
    print(f"Earliest timestamp: {earliest}")
    print(f"Latest timestamp: {latest}")
    print(f"Current time: {now}")
    print("\nMentions by year:")
    for year, count in year_counts:
        print(f"  {year}: {count} mentions")
    
    conn.close()

def fix_future_timestamps(db_path="judo_mentions.db"):
    """
    Fix any timestamps that are in the future by setting them to current time.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update future timestamps
    cursor.execute("""
        UPDATE mentions
        SET timestamp = ?
        WHERE timestamp > ?
    """, (now, now))
    
    updated_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    if updated_count > 0:
        print(f"[INFO] Fixed {updated_count} records with future timestamps")
    return updated_count

def summarize_mentions(db_path):
    """
    Summarizes the total number of mentions and counts how often each throw was mentioned.
    Also prints earliest and latest mention timestamps.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch all throw_name values
    cursor.execute("SELECT throw_name FROM mentions")
    rows = cursor.fetchall()

    # Earliest & latest timestamps
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM mentions")
    earliest, latest = cursor.fetchone()

    conn.close()

    throw_counts = Counter(row[0] for row in rows)
    total_mentions = sum(throw_counts.values())

    print(f"\n[INFO] Summary of matches in /r/judo:")
    print(f"Total mention-events found: {total_mentions}")

    if earliest and latest:
        print(f"Earliest mention timestamp: {earliest}")
        print(f"Latest mention timestamp:  {latest}")

    if total_mentions == 0:
        print("No Judo throw mentions found.")
        return

    print("\n[INFO] Throw mentions tally:")
    for throw_name, count in throw_counts.most_common():
        print(f"{throw_name}: {count} times")

def plot_top_throws(db_path="judo_mentions.db", top_n=10):
    """
    Generates a bar plot for the top N most mentioned Judo throws using Seaborn.
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT throw_name, type FROM mentions", conn)
    conn.close()

    # Count throw mentions
    throw_counts = df["throw_name"].value_counts().head(top_n)

    plt.figure(figsize=(12, 8))
    ax = sns.barplot(x=throw_counts.values, y=throw_counts.index, palette="viridis")
    
    # Add count labels to the bars
    for i, v in enumerate(throw_counts.values):
        ax.text(v + 0.5, i, str(v), color='black', va='center')
    
    plt.title(f"Top {top_n} Judo Throws Mentioned", fontsize=16)
    plt.xlabel("Number of Mentions", fontsize=12)
    plt.ylabel("Throw Name", fontsize=12)
    plt.tight_layout()
    plt.savefig("top_throws.png")
    plt.show()
    
    # Additional plot: Separate by mention type (submission vs comment)
    plt.figure(figsize=(12, 8))
    
    # Create a crosstab of throw_name vs type
    throws_by_type = pd.crosstab(df["throw_name"], df["type"])
    throws_by_type = throws_by_type.loc[throw_counts.index]
    
    throws_by_type.plot(kind="barh", stacked=True, figsize=(12, 8), 
                        colormap="viridis", width=0.8)
    
    plt.title(f"Top {top_n} Judo Throws by Mention Type", fontsize=16)
    plt.xlabel("Number of Mentions", fontsize=12)
    plt.ylabel("Throw Name", fontsize=12)
    plt.legend(title="Mention Type")
    plt.tight_layout()
    plt.savefig("top_throws_by_type.png")
    plt.show()

def plot_mentions_over_time(db_path="judo_mentions.db", top_n=5, normalize=False, 
                           moving_avg=True, window=3):
    """
    Plots a line chart of the most popular throws over time, grouped by month.
    
    Args:
        normalize: If True, normalize counts as percentage of total mentions that month
        moving_avg: If True, add a moving average trendline
        window: Window size for moving average
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT timestamp, throw_name FROM mentions", conn)
    conn.close()

    # Convert timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Count total mentions per throw, then filter to top_n
    throw_counts = df["throw_name"].value_counts()
    top_throws = throw_counts.head(top_n).index.tolist()  # list of throw names

    # Filter DataFrame to only include top throws
    df_top = df[df["throw_name"].isin(top_throws)].copy()

    # Group by MONTHLY intervals (better granularity than 6-months)
    df_top["month"] = df_top["timestamp"].dt.strftime("%Y-%m")

    # Group by (month, throw_name)
    grouped = df_top.groupby(["month", "throw_name"]).size().reset_index(name="count")
    
    # Get total mentions per month (for normalization)
    month_totals = grouped.groupby("month")["count"].sum().reset_index()
    month_totals.columns = ["month", "total"]
    
    # Merge totals back if normalization requested
    if normalize:
        grouped = pd.merge(grouped, month_totals, on="month")
        grouped["normalized"] = grouped["count"] / grouped["total"] * 100
        value_col = "normalized"
        y_label = "Percentage of Mentions (%)"
    else:
        value_col = "count"
        y_label = "Number of Mentions"

    # Pivot so each throw_name is a column, rows are months
    pivot_df = grouped.pivot(index="month", columns="throw_name", values=value_col).fillna(0)

    # Sort by month
    pivot_df = pivot_df.sort_index()

    # Plot line chart
    plt.figure(figsize=(14, 8))
    
    # Plot each throw as a line with markers
    for throw in pivot_df.columns:
        plt.plot(pivot_df.index, pivot_df[throw], "o-", label=throw, linewidth=2, markersize=6)
        
        # Add moving average if requested
        if moving_avg:
            ma = pivot_df[throw].rolling(window=window, min_periods=1).mean()
            plt.plot(pivot_df.index, ma, "--", color="gray", alpha=0.7, 
                    linewidth=1.5, label=f"{throw} ({window}-month avg)" if throw == pivot_df.columns[0] else "")

    title_prefix = "Normalized " if normalize else ""
    plt.title(f"{title_prefix}Monthly Mentions for Top {top_n} Judo Throws", fontsize=16)
    plt.xlabel("Month", fontsize=12)
    plt.ylabel(y_label, fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend(loc="best")
    
    # Add note about normalization if used
    if normalize:
        plt.text(
            0.01, 0.95,
            "Note: Values shown as percentage of all throw mentions that month.",
            transform=plt.gca().transAxes,
            fontsize=10,
            color='red'
        )

    plt.tight_layout()
    plt.savefig(f"{'normalized_' if normalize else ''}mentions_over_time.png")
    plt.show()

def initialize_database(db_path="judo_mentions.db"):
    """
    Initialize the database with appropriate schema.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mentions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            type TEXT NOT NULL,
            post_id TEXT NOT NULL,
            url TEXT NOT NULL,
            throw_name TEXT NOT NULL
        );
    """)
    
    # Add indices for better query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mentions_timestamp ON mentions(timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mentions_throw_name ON mentions(throw_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mentions_post_id ON mentions(post_id);")
    
    conn.commit()
    conn.close()
    print(f"[INFO] Database initialized at {db_path}")

def main():
    """
    Main execution function.
    - Loads Judo throws from the database.
    - Ensures the mentions database table exists.
    - Scrapes submissions and comments for mentions.
    - Removes duplicates.
    - Summarizes the results.
    - Generates visualizations.
    """
    print("[INFO] Starting Judo mentions scraper")
    print("[INFO] Current time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    judo_throws = load_judo_throws("judo_throws.db")
    print(f"[INFO] Loaded {len(judo_throws)} Judo throws from judo_throws.db.")

    db_path = "judo_mentions.db"
    initialize_database(db_path)

    # Scrape and store mentions using time-based approach for better historical coverage
    scrape_by_time_periods("judo", judo_throws, db_path, periods=6)
    
    # Also scrape recent comments
    match_comments("judo", judo_throws, db_path, limit=10000)

    # Verify and fix any timestamp issues
    verify_timestamps(db_path)
    fixed_count = fix_future_timestamps(db_path)
    if fixed_count > 0:
        print("[INFO] Re-verifying timestamps after fixes:")
        verify_timestamps(db_path)

    # Remove duplicate entries before summarizing and visualizing
    remove_exact_duplicates(db_path)
    remove_soft_duplicates(db_path)

    # Summarize and display the tally of mentions
    summarize_mentions(db_path)

    # Generate data visualizations
    print("\n[INFO] Generating bar chart of top throws...")
    plot_top_throws(db_path)

    print("\n[INFO] Generating regular timeline chart...")
    plot_mentions_over_time(db_path, normalize=False, moving_avg=True)
    
    print("\n[INFO] Generating normalized timeline chart...")
    plot_mentions_over_time(db_path, normalize=True, moving_avg=True)

    print("\n[INFO] Scraping and visualization complete!")

if __name__ == "__main__":
    main()