#!/usr/bin/env python3
"""
grappling_reddit_bot.py

Monitors /r/bjj, /r/wrestling, /r/mma for references to instructionals from bjjfanatics.db,
logging each mention to a 'reddit_mentions' table in the same database.
"""

import os
import time
import sqlite3
import praw

DB_NAME = "bjjfanatics.db"

# 1) Set up PRAW (Reddit API client)
# Replace the placeholders with your actual credentials from https://www.reddit.com/prefs/apps
reddit = praw.Reddit(
    client_id="obfuscated",
    client_secret="secret",
    user_agent="trends_danaher_bot/0.1 by Classic_Visual4481",
    # If you need certain privileges, add username and password:
    # username="Classic_Visual4481",
    # password="YOUR_REDDIT_PASSWORD"
)

def create_mentions_table():
    """
    Ensure the reddit_mentions table exists in the DB.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reddit_mentions (
            mention_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subreddit TEXT,
            mention_type TEXT,        -- 'submission' or 'comment'
            post_id TEXT,
            comment_id TEXT,
            matched_instructional TEXT,
            mention_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def load_instructionals():
    """
    Loads known instructionals from the 'instructionals' table (scraped from BJJFanatics).
    Returns a list of strings (the 'name' column).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM instructionals")
    rows = cursor.fetchall()
    conn.close()
    instructionals = [row[0] for row in rows]
    return instructionals

def find_instructionals_in_text(text, instructionals):
    """
    Return a list of instructionals that appear as substrings in the text.
    Naive approach: just check if instr_name.lower() in text.lower().
    """
    text_lower = text.lower()
    found = []
    for instr_name in instructionals:
        if instr_name.lower() in text_lower:
            found.append(instr_name)
    return found

def log_mention(subreddit, mention_type, post_id, comment_id, matched_instructional):
    """
    Insert a row in 'reddit_mentions' for each mention found.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Ensure the table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reddit_mentions (
            mention_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subreddit TEXT,
            mention_type TEXT,
            post_id TEXT,
            comment_id TEXT,
            matched_instructional TEXT,
            mention_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        INSERT INTO reddit_mentions (subreddit, mention_type, post_id, comment_id, matched_instructional)
        VALUES (?, ?, ?, ?, ?)
    """, (subreddit, mention_type, post_id, comment_id, matched_instructional))
    conn.commit()
    conn.close()

def scan_subreddit_submissions(subreddit_name, instructionals):
    """
    Poll the newest submissions in a subreddit to find matches.
    """
    subreddit = reddit.subreddit(subreddit_name)
    # Fetch the newest 20 (adjust as needed)
    for submission in subreddit.new(limit=20):
        text = (submission.title or "") + " " + (submission.selftext or "")
        found_instr = find_instructionals_in_text(text, instructionals)
        for instr in found_instr:
            log_mention(subreddit_name, "submission", submission.id, None, instr)

def scan_subreddit_comments(subreddit_name, instructionals):
    """
    Poll the newest comments in a subreddit to find matches.
    """
    subreddit = reddit.subreddit(subreddit_name)
    # Fetch the newest 50 comments (adjust as needed)
    for comment in subreddit.comments(limit=50):
        text = comment.body
        found_instr = find_instructionals_in_text(text, instructionals)
        for instr in found_instr:
            log_mention(subreddit_name, "comment", None, comment.id, instr)

def main():
    # 1) Ensure the mention table exists
    create_mentions_table()

    # 2) Load known instructionals
    instructionals = load_instructionals()
    print(f"Loaded {len(instructionals)} instructionals from '{DB_NAME}'.")

    # 3) Define subreddits to monitor
    subreddits = ["bjj", "wrestling", "mma"]

    # 4) Continuous polling
    while True:
        for sub in subreddits:
            print(f"Checking subreddit: /r/{sub} ...")
            scan_subreddit_submissions(sub, instructionals)
            scan_subreddit_comments(sub, instructionals)

        # Sleep 5 minutes
        print("Sleeping for 300 seconds...")
        time.sleep(300)

if __name__ == "__main__":
    main()
