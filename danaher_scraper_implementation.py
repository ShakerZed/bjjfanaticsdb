#!/usr/bin/env python3

"""
reddit_instructionals_match.py

1) Loads instructionals from bjjfanatics.db (the 'instructionals' table).
2) Checks newest posts and comments in /r/bjj for references to these instructionals.
3) Prints out matched instructionals (for now).

Dependencies:
    - Python 3.7+
    - PRAW (pip install praw)
    - sqlite3 (standard library for DB)
    - A bjjfanatics.db containing a table named 'instructionals' with a 'name' column
    - (Optional) python-dotenv for loading .env files

Usage:
    1. Install PRAW: pip install praw
    2. Provide Reddit credentials as environment variables:
       - REDDIT_CLIENT_ID
       - REDDIT_CLIENT_SECRET
       - REDDIT_USER_AGENT
      (Optionally use python-dotenv and a .env file.)
    3. Run: python reddit_instructionals_match.py

Example environment variables:
    export REDDIT_CLIENT_ID="abc123"
    export REDDIT_CLIENT_SECRET="xyz789"
    export REDDIT_USER_AGENT="myGrapplingBot/0.1 by u/MyRedditUser"
"""

import os
import sqlite3
import praw
import time

############### LOAD REDDIT CREDENTIALS FROM ENV ###############
# Instead of hardcoding credentials, we load them from environment variables.
# E.g., on Windows PowerShell:
#   $env:REDDIT_CLIENT_ID="abc123"
#   $env:REDDIT_CLIENT_SECRET="xyz789"
#   $env:REDDIT_USER_AGENT="myGrapplingBot/0.1 by u/MyRedditUser"
# On Linux/macOS:
#   export REDDIT_CLIENT_ID="abc123"
#   export REDDIT_CLIENT_SECRET="xyz789"
#   export REDDIT_USER_AGENT="myGrapplingBot/0.1 by u/MyRedditUser"

reddit = praw.Reddit(
    client_id=os.environ.get("REDDIT_CLIENT_ID"),
    client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
    user_agent=os.environ.get("REDDIT_USER_AGENT")
)
###############################################################

# -------------------------
# load_instructionals
# -------------------------
# This function connects to your local SQLite database (bjjfanatics.db)
# and retrieves all names from the 'instructionals' table.
# The result is returned as a simple list of strings.
# Each string corresponds to an instructional title/product name.
# This list is then used to detect mentions in Reddit posts/comments.
def load_instructionals(db_path="bjjfanatics.db"):
    """
    Loads a list of instructional names from the 'instructionals' table
    in the given SQLite database.

    Returns: A list of strings representing the product names.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # We assume a table 'instructionals' with a 'name' column
    cursor.execute("SELECT name FROM instructionals")
    rows = cursor.fetchall()
    conn.close()
    # Return just the name as a list of strings
    return [row[0] for row in rows]

# -------------------------
# find_instructionals_in_text
# -------------------------
# This function takes a block of text (from a submission title/selftext or a comment)
# and checks whether any known instructionals (loaded from the DB) appear.
# It uses a simple case-insensitive substring check.
# If a match is found, the corresponding instructional name is appended
# to a 'found' list. The function returns this list of matched names.
def find_instructionals_in_text(text, instructionals):
    """
    Checks if any known instructionals appear as substrings in 'text'.
    Returns a list of matched instructional names.
    """
    text_lower = text.lower()
    found = []
    for instr_name in instructionals:
        # naive substring check
        if instr_name.lower() in text_lower:
            found.append(instr_name)
    return found

# -------------------------
# match_submissions
# -------------------------
# This function fetches the newest submissions (posts) in a given subreddit.
# For each post, it constructs the text by combining the title and selftext.
# Then it calls find_instructionals_in_text() to see if any known instructionals
# appear. If matches are found, it prints the results.
# The 'limit' parameter controls how many newest posts are fetched.
def match_submissions(subreddit_name, instructionals, limit=10):
    """
    Fetches newest submissions from the given subreddit and checks
    for any mention of your known instructionals.
    Prints matches to console for demonstration.
    """
    print(f"\n[DEBUG] Checking submissions in /r/{subreddit_name} (limit={limit})...")
    subreddit = reddit.subreddit(subreddit_name)
    for submission in subreddit.new(limit=limit):
        # Combine the title + selftext
        post_text = (submission.title or "") + " " + (submission.selftext or "")
        
        print(f"[DEBUG] Submission: {submission.id} | Title: {submission.title!r}")
        found = find_instructionals_in_text(post_text, instructionals)
        
        if found:
            print(f"Matched in Submission: {submission.id}")
            print(f"URL: {submission.url}")
            print(f"Instructionals Found: {found}")
            print("----------")
        else:
            print(f"[DEBUG] No matches in submission {submission.id}.")

# -------------------------
# match_comments
# -------------------------
# Similar to match_submissions, but fetches newest comments in the subreddit.
# For each comment body, we check if any known instructional names appear.
# If found, we print the comment ID, author, permalink, and the matched instructionals.
# The 'limit' parameter controls how many newest comments are fetched.
def match_comments(subreddit_name, instructionals, limit=20):
    """
    Fetches newest comments from the given subreddit and checks
    for any mention of your known instructionals.
    Prints matches to console for demonstration.
    """
    print(f"\n[DEBUG] Checking comments in /r/{subreddit_name} (limit={limit})...")
    subreddit = reddit.subreddit(subreddit_name)
    for comment in subreddit.comments(limit=limit):
        text = comment.body or ""
        
        print(f"[DEBUG] Comment: {comment.id} | Author: {comment.author}")
        found = find_instructionals_in_text(text, instructionals)
        
        if found:
            print(f"Matched in Comment: {comment.id}")
            print(f"Permalink: https://www.reddit.com{comment.permalink}")
            print(f"Instructionals Found: {found}")
            print("----------")
        else:
            print(f"[DEBUG] No matches in comment {comment.id}.")

# -------------------------
# main
# -------------------------
# The entry point. Loads the instructionals from the local DB,
# prints how many were loaded, then scans the /r/bjj subreddit
# for references in both submissions and comments.
# You can expand to other subreddits or loop, if desired.
def main():
    # 1) Load instructionals
    instructionals = load_instructionals("bjjfanatics.db")
    print(f"[INFO] Loaded {len(instructionals)} instructionals from bjjfanatics.db.")
    
    # 2) Check newest submissions in /r/bjj
    match_submissions(subreddit_name="bjj", instructionals=instructionals, limit=10)
    
    # 3) Check newest comments in /r/bjj
    match_comments(subreddit_name="bjj", instructionals=instructionals, limit=20)

if __name__ == "__main__":
    main()
