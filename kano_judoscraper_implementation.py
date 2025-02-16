#!/usr/bin/env python3
"""
kano_judoscraper_implementation.py

1) Loads Judo throws from judo_throws.db (the 'judo_throws' table).
2) Checks newest posts and comments in /r/judo for references to these throws.
3) Prints out any matched throws, plus a final summary of total matches.

Dependencies:
    - Python 3.7+
    - PRAW (pip install praw)
    - sqlite3 (standard library for DB)
    - (Optional) python-dotenv for environment-based secrets
    - A judo_throws.db containing a table named 'judo_throws' with a 'throw_name' column

Usage:
    1. Install PRAW: pip install praw
    2. Provide Reddit credentials as environment variables:
       - REDDIT_CLIENT_ID
       - REDDIT_CLIENT_SECRET
       - REDDIT_USER_AGENT
      (Optionally use python-dotenv and a .env file.)
    3. Run: python kano_judoscraper_implementation.py

Example environment variables:
    export REDDIT_CLIENT_ID="abc123"
    export REDDIT_CLIENT_SECRET="xyz789"
    export REDDIT_USER_AGENT="myJudoBot/0.1 by u/MyRedditUser"
"""

import os
import re
import sqlite3
import praw
import time

################## LOAD REDDIT CREDENTIALS FROM ENV ##################
# If you prefer a .env approach:
# from dotenv import load_dotenv
# load_dotenv()
# and ensure .env has the relevant variables.
reddit = praw.Reddit(
    client_id=os.environ.get("REDDIT_CLIENT_ID"),
    client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
    user_agent=os.environ.get("REDDIT_USER_AGENT")
)
######################################################################

def load_judo_throws(db_path="judo_throws.db"):
    """
    Loads Judo throw names from the 'judo_throws' table in judo_throws.db.
    Returns a list of strings representing each throw name.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # We assume a table 'judo_throws' with a 'throw_name' column
    cursor.execute("SELECT throw_name FROM judo_throws")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def find_throws_in_text(text, judo_throws):
    """
    Uses a case-insensitive regex with word boundaries to match throw names
    as separate words. Returns a list of matched throw names.
    """
    found = []
    text_lower = text.lower()
    for throw in judo_throws:
        pattern = rf'(?i)\b{re.escape(throw)}\b'  # \b ensures whole-word match
        if re.search(pattern, text_lower):
            found.append(throw)
    return found

def match_submissions(subreddit_name, judo_throws, matches, limit=10):
    """
    Scans newest submissions in 'subreddit_name', searching for Judo throw mentions.
    Prints them and stores in 'matches' list for final summary.
    """
    print(f"\n[DEBUG] Checking submissions in /r/{subreddit_name} (limit={limit})...")
    subreddit = reddit.subreddit(subreddit_name)
    for submission in subreddit.new(limit=limit):
        post_text = (submission.title or "") + " " + (submission.selftext or "")
        print(f"[DEBUG] Submission: {submission.id} | Title: {submission.title!r}")
        found = find_throws_in_text(post_text, judo_throws)
        if found:
            print(f"Matched in Submission: {submission.id}")
            print(f"URL: {submission.url}")
            print(f"Judo Throws Found: {found}")
            print("----------")
            matches.append({
                "type": "submission",
                "id": submission.id,
                "url": submission.url,
                "throws": found
            })
        else:
            print(f"[DEBUG] No matches in submission {submission.id}.")

def match_comments(subreddit_name, judo_throws, matches, limit=20):
    """
    Scans newest comments in 'subreddit_name', searching for Judo throw mentions.
    Prints them and stores in 'matches' list for final summary.
    """
    print(f"\n[DEBUG] Checking comments in /r/{subreddit_name} (limit={limit})...")
    subreddit = reddit.subreddit(subreddit_name)
    for comment in subreddit.comments(limit=limit):
        text = comment.body or ""
        print(f"[DEBUG] Comment: {comment.id} | Author: {comment.author}")
        found = find_throws_in_text(text, judo_throws)
        if found:
            permalink = f"https://www.reddit.com{comment.permalink}"
            print(f"Matched in Comment: {comment.id}")
            print(f"Permalink: {permalink}")
            print(f"Judo Throws Found: {found}")
            print("----------")
            matches.append({
                "type": "comment",
                "id": comment.id,
                "url": permalink,
                "throws": found
            })
        else:
            print(f"[DEBUG] No matches in comment {comment.id}.")

def main():
    # 1) Load Judo throws
    judo_throws = load_judo_throws("judo_throws.db")
    print(f"[INFO] Loaded {len(judo_throws)} Judo throws from judo_throws.db.")

    # 2) We'll accumulate all matches here for a final summary
    matches = []

    # 3) Check newest submissions in /r/judo
    match_submissions("judo", judo_throws, matches, limit=10)

    # 4) Check newest comments in /r/judo
    match_comments("judo", judo_throws, matches, limit=20)

    # 5) Summarize all found mentions
    total_found = len(matches)
    print(f"\n[INFO] Summary of matches in /r/judo:")
    print(f"Total matches found: {total_found}")

    if total_found == 0:
        print("No Judo throw mentions found.")
    else:
        for i, match in enumerate(matches, start=1):
            print(f"{i}. Type: {match['type']}, ID: {match['id']}, URL: {match['url']}, Throws: {match['throws']}")

if __name__ == "__main__":
    main()
