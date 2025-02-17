#!/usr/bin/env python3

"""
kano_judoscraper_implementation.py

1) Loads Judo throws from judo_throws.db (the 'judo_throws' table).
2) Checks newest posts and comments in /r/judo for references to these throws.
3) Stores matched throws in a new database (judo_mentions.db) with timestamps.
4) Prints out any matched throws, plus a final summary of total matches and a tally of throw mentions.

This script is useful for tracking mentions of Judo techniques across Reddit, allowing for
insights into which techniques are being discussed the most over time.

Dependencies:
    - Python 3.7+
    - PRAW (pip install praw)
    - sqlite3 (standard library for DB operations)
    - (Optional) python-dotenv for environment-based secrets
    - A judo_throws.db containing a table named 'judo_throws' with a 'throw_name' column

Usage:
    1. Install dependencies: `pip install praw`
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

def summarize_mentions(db_path):
    """
    Summarizes the total number of mentions and counts how often each throw was mentioned.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT throw_name FROM mentions")
    rows = cursor.fetchall()
    conn.close()

    throw_counts = Counter(row[0] for row in rows)
    total_mentions = sum(throw_counts.values())

    print(f"\n[INFO] Summary of matches in /r/judo:")
    print(f"Total mention-events found: {total_mentions}")

    if total_mentions == 0:
        print("No Judo throw mentions found.")
    else:
        print("\n[INFO] Throw mentions tally:")
        for throw_name, count in throw_counts.most_common():
            print(f"{throw_name}: {count} times")

def main():
    """
    Main execution function.
    - Loads Judo throws from the database.
    - Ensures the mentions database table exists.
    - Scrapes submissions and comments for mentions.
    - Summarizes the results.
    """
    judo_throws = load_judo_throws("judo_throws.db")
    print(f"[INFO] Loaded {len(judo_throws)} Judo throws from judo_throws.db.")

    db_path = "judo_mentions.db"

    # Ensure the 'mentions' table exists
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
    match_submissions("judo", judo_throws, [], db_path, limit=100000)
    match_comments("judo", judo_throws, [], db_path, limit=200000)

    # Summarize and display the tally of mentions
    summarize_mentions(db_path)

if __name__ == "__main__":
    main()
