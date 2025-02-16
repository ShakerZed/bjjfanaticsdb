#!/usr/bin/env python3

"""
reddit_instructionals_match.py

1) Loads instructionals from bjjfanatics.db (the 'instructionals' table).
2) Checks newest posts and comments in /r/bjj for references to these instructionals.
3) Prints out matched instructionals (for now), and at the end prints a summary
   of total matches, including the type (submission/comment), ID, URL, and found instructional names.

Dependencies:
    - Python 3.7+
    - PRAW (pip install praw)
    - sqlite3 (standard library for DB)
    - (Optional) python-dotenv for loading .env files
    - A bjjfanatics.db containing a table named 'instructionals' with a 'name' column

Usage:
    1. Install PRAW: pip install praw
    2. Provide Reddit credentials as environment variables:
       - REDDIT_CLIENT_ID
       - REDDIT_CLIENT_SECRET
       - REDDIT_USER_AGENT
      Optionally use python-dotenv and a .env file.
    3. Run: python reddit_instructionals_match.py

Example environment variables:
    export REDDIT_CLIENT_ID="abc123"
    export REDDIT_CLIENT_SECRET="xyz789"
    export REDDIT_USER_AGENT="myGrapplingBot/0.1 by u/MyRedditUser"
"""

import os
import re  # for regex word-boundary matching
import sqlite3
import praw
import time

############### LOAD REDDIT CREDENTIALS FROM ENV ###############
reddit = praw.Reddit(
    client_id=os.environ.get("REDDIT_CLIENT_ID"),
    client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
    user_agent=os.environ.get("REDDIT_USER_AGENT")
)
###############################################################

# -------------------------
# load_instructionals
# -------------------------
def load_instructionals(db_path="bjjfanatics.db"):
    """
    Loads a list of instructional names from the 'instructionals' table
    in the given SQLite database.

    Returns: A list of strings representing the product names.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM instructionals")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

# -------------------------
# find_instructionals_in_text
# -------------------------
# Uses a regex approach with word boundaries to avoid partial matches.
# For each known instructional name, we build a case-insensitive pattern:
#    (?i)\b{escaped_name}\b
# so it only matches the phrase as a separate word.

def find_instructionals_in_text(text, instructionals):
    """
    Checks if any known instructionals appear as separate words in 'text'
    using regex word boundaries. Returns a list of matched names.
    """
    found = []
    text_lower = text.lower()
    for instr_name in instructionals:
        pattern = rf'(?i)\b{re.escape(instr_name)}\b'
        if re.search(pattern, text_lower):
            found.append(instr_name)
    return found

# -------------------------
# match_submissions
# -------------------------
def match_submissions(subreddit_name, instructionals, matches, limit=10):
    """
    Fetches newest submissions from the given subreddit and checks
    for any mention of your known instructionals.
    Prints matches to console for demonstration, also stores them in 'matches' list.
    """
    print(f"\n[DEBUG] Checking submissions in /r/{subreddit_name} (limit={limit})...")
    subreddit = reddit.subreddit(subreddit_name)
    for submission in subreddit.new(limit=limit):
        post_text = (submission.title or "") + " " + (submission.selftext or "")
        print(f"[DEBUG] Submission: {submission.id} | Title: {submission.title!r}")
        found = find_instructionals_in_text(post_text, instructionals)
        if found:
            print(f"Matched in Submission: {submission.id}")
            print(f"URL: {submission.url}")
            print(f"Instructionals Found: {found}")
            print("----------")
            # store match info
            matches.append({
                "type": "submission",
                "id": submission.id,
                "url": submission.url,
                "instructionals": found
            })
        else:
            print(f"[DEBUG] No matches in submission {submission.id}.")

# -------------------------
# match_comments
# -------------------------
def match_comments(subreddit_name, instructionals, matches, limit=20):
    """
    Fetches newest comments from the given subreddit and checks
    for any mention of your known instructionals.
    Prints matches to console for demonstration, also stores them in 'matches'.
    """
    print(f"\n[DEBUG] Checking comments in /r/{subreddit_name} (limit={limit})...")
    subreddit = reddit.subreddit(subreddit_name)
    for comment in subreddit.comments(limit=limit):
        text = comment.body or ""
        print(f"[DEBUG] Comment: {comment.id} | Author: {comment.author}")
        found = find_instructionals_in_text(text, instructionals)
        if found:
            permalink = f"https://www.reddit.com{comment.permalink}"
            print(f"Matched in Comment: {comment.id}")
            print(f"Permalink: {permalink}")
            print(f"Instructionals Found: {found}")
            print("----------")
            # store match info
            matches.append({
                "type": "comment",
                "id": comment.id,
                "url": permalink,
                "instructionals": found
            })
        else:
            print(f"[DEBUG] No matches in comment {comment.id}.")

# -------------------------
# main
# -------------------------

def main():
    # Load instructionals
    instructionals = load_instructionals("bjjfanatics.db")
    print(f"[INFO] Loaded {len(instructionals)} instructionals from bjjfanatics.db.")

    # We'll collect all matches here:
    matches = []

    # Check newest submissions in /r/bjj
    match_submissions(subreddit_name="bjj", instructionals=instructionals, matches=matches, limit=400)

    # Check newest comments in /r/bjj
    match_comments(subreddit_name="bjj", instructionals=instructionals, matches=matches, limit=10000)

    # Print summary at the end
    total_found = len(matches)
    print(f"\n[INFO] Summary of matches:")
    print(f"Total matches found: {total_found}")

    # If no matches, say so
    if total_found == 0:
        print("No instructional mentions were found.")
    else:
        # Otherwise, list them out
        for i, match in enumerate(matches, start=1):
            print(f"{i}. Type: {match['type']}, ID: {match['id']}, URL: {match['url']}, Instructionals: {match['instructionals']}")

if __name__ == "__main__":
    main()
