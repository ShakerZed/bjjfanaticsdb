#!/usr/bin/env python3

"""
kano_judoscraper_implementation.py

1) Loads Judo throws from judo_throws.db (the 'judo_throws' table).
2) Checks newest posts and comments in /r/judo for references to these throws.
3) Stores matched throws in a new database (judo_mentions.db) with timestamps.
4) Prints out any matched throws, plus a final summary of total matches and a tally of throw mentions.
5) (NEW) Provides data visualization using Matplotlib and Seaborn, including:
   - A line chart showing top throws over time (now grouped by month).
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

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

################## LOAD REDDIT CREDENTIALS FROM ENV ##################
reddit = praw.Reddit(
    client_id="71rkosnFXt2NZBvyOz9N7A",
    client_secret="4E2h1YhnGLcoYobQlMY6gtmJcQ4qKg",
    user_agent="trends_danaher_bot/0.1 by Classic_Visual4481"
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
    text_lower = text.lower()
    for throw in judo_throws:
        pattern = rf'(?i)\b{re.escape(throw)}\b'
        if re.search(pattern, text_lower):
            found.append(throw)
    return found


def store_mention(db_path, mention_type, post_id, url, throw_name):
    """
    Inserts a record into the 'mentions' table for each mention of a Judo throw.
    The stored data includes a timestamp, the mention type (submission/comment),
    the Reddit post/comment ID, a URL to that post/comment, and the throw name.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())  # UTC time
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO mentions (timestamp, type, post_id, url, throw_name)
        VALUES (?, ?, ?, ?, ?)
    """, (timestamp, mention_type, post_id, url, throw_name))
    conn.commit()
    conn.close()


def match_submissions(subreddit_name, judo_throws, matches, db_path, limit=10):
    """
    Scans newest submissions in /r/<subreddit_name>, searching for Judo throw mentions.
    Saves each mention via store_mention().
    """
    print(f"\n[DEBUG] Checking submissions in /r/{subreddit_name} (limit={limit})...")
    subreddit = reddit.subreddit(subreddit_name)
    for submission in subreddit.new(limit=limit):
        post_text = (submission.title or "") + " " + (submission.selftext or "")
        found = find_throws_in_text(post_text, judo_throws)
        if found:
            print(f"Matched in Submission: {submission.id}")
            print(f"URL: {submission.url}")
            print(f"Judo Throws Found: {found}")
            print("----------")
            for throw in found:
                store_mention(db_path, "submission", submission.id, submission.url, throw)


def match_comments(subreddit_name, judo_throws, matches, db_path, limit=20):
    """
    Scans newest comments in /r/<subreddit_name>, searching for Judo throw mentions.
    Saves each mention via store_mention().
    """
    print(f"\n[DEBUG] Checking comments in /r/{subreddit_name} (limit={limit})...")
    subreddit = reddit.subreddit(subreddit_name)
    for comment in subreddit.comments(limit=limit):
        text = comment.body or ""
        found = find_throws_in_text(text, judo_throws)
        if found:
            permalink = f"https://www.reddit.com{comment.permalink}"
            print(f"Matched in Comment: {comment.id}")
            print(f"Permalink: {permalink}")
            print(f"Judo Throws Found: {found}")
            print("----------")
            for throw in found:
                store_mention(db_path, "comment", comment.id, permalink, throw)


def remove_exact_duplicates(db_path="judo_mentions.db"):
    """
    Removes exact duplicates where (timestamp, post_id, throw_name) are identical.
    Keeps only the first occurrence of each.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM mentions
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM mentions
            GROUP BY timestamp, post_id, throw_name
        )
    """)

    conn.commit()
    conn.close()
    print("Exact duplicates removed.")


def remove_soft_duplicates(db_path="judo_mentions.db"):
    """
    Removes duplicates where (post_id, throw_name) are identical, ignoring timestamp differences.
    Keeps only the first occurrence of each.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM mentions
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM mentions
            GROUP BY post_id, throw_name
        )
    """)

    conn.commit()
    conn.close()
    print("Soft duplicates removed (ignoring timestamp differences).")


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
    df = pd.read_sql_query("SELECT throw_name FROM mentions", conn)
    conn.close()

    # Count throw mentions
    throw_counts = df["throw_name"].value_counts().head(top_n)

    plt.figure(figsize=(10, 6))
    sns.barplot(x=throw_counts.values, y=throw_counts.index, palette="viridis")
    plt.title(f"Top {top_n} Judo Throws Mentioned")
    plt.xlabel("Number of Mentions")
    plt.ylabel("Throw Name")
    plt.tight_layout()
    plt.show()


def plot_mentions_over_time(db_path="judo_mentions.db", top_n=5):
    """
    Plots a line chart of the most popular throws over time, grouped by month.
    
    Steps:
    1) Get top N throws overall.
    2) Convert timestamps to monthly periods.
    3) Group by (month, throw_name) and count mentions.
    4) Pivot so each throw is a column, months are rows.
    5) Fill any missing months with zero.
    6) Plot a line chart with months on the X-axis.
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

    # Group by MONTH (via a monthly period, then take the period start time)
    df_top["month"] = df_top["timestamp"].dt.to_period("M").apply(lambda r: r.start_time)

    # Group by (month, throw_name)
    grouped = df_top.groupby(["month", "throw_name"]).size().reset_index(name="count")

    # Pivot so each throw_name is a column, rows are months
    pivot_df = grouped.pivot(index="month", columns="throw_name", values="count").fillna(0)

    # Sort by month
    pivot_df = pivot_df.sort_index()

    # Fill missing months so the timeline is continuous
    if not pivot_df.empty:
        full_month_range = pd.date_range(
            start=pivot_df.index.min(),
            end=pivot_df.index.max(),
            freq='MS'  # 'Month Start'
        )
        pivot_df = pivot_df.reindex(full_month_range, fill_value=0)
        pivot_df.index.name = "month"

    # Plot line chart
    plt.figure(figsize=(12, 6))
    # --- Outlier Truncation Logic (per throw) ---
    for throw in pivot_df.columns:
        col = pivot_df[throw]
        mean_val = col.mean()
        std_val = col.std()
        if std_val > 0:  # avoid dividing by zero or if everything is same
            cap = mean_val + 1 * std_val
            # Cap values above mean+4std
            pivot_df.loc[col > cap, throw] = cap

    # Plot line chart
    plt.figure(figsize=(12, 6))
    for throw in pivot_df.columns:
        plt.plot(pivot_df.index, pivot_df[throw], "o-", label=throw)

    plt.title(f"Monthly Mentions for Top {top_n} Throws (Outliers Capped)")
    plt.xlabel("Month") 
    plt.ylabel("Mentions")
    plt.xticks(rotation=45)
    plt.legend()
    plt.yscale("log")


    # Add a note about capping outliers
    plt.text(
        0.01, 0.95,
        "Note: Values above mean+4std are truncated.",
        transform=plt.gca().transAxes,
        fontsize=10,
        color='red'
    )



def main():
    """
    Main execution function.
    - Loads Judo throws from the database.
    - Ensures the mentions database table exists.
    - Scrapes submissions and comments for mentions.
    - Removes duplicates.
    - Summarizes the results.
    - Generates visualizations (bar chart & monthly line chart).
    """
    judo_throws = load_judo_throws("judo_throws.db")
    print(f"[INFO] Loaded {len(judo_throws)} Judo throws from judo_throws.db.")

    db_path = "judo_mentions.db"
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
    conn.commit()
    conn.close()

    # Scrape and store mentions
    match_submissions("judo", judo_throws, [], db_path, limit=10000000)
    match_comments("judo", judo_throws, [], db_path, limit=10000000)

    # Remove duplicate entries before summarizing and visualizing
    remove_exact_duplicates(db_path)
    remove_soft_duplicates(db_path)

    # Summarize and display the tally of mentions
    summarize_mentions(db_path)

    # Generate data visualizations
    print("\n[INFO] Generating bar chart of top throws...")
    plot_top_throws(db_path)

    print("\n[INFO] Generating line chart of top throws over time (monthly)...")
    plot_mentions_over_time(db_path)


if __name__ == "__main__":
    main()
