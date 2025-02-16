#!/usr/bin/env python3
"""
create_judo_db.py

Creates a SQLite database (judo_throws.db) with a table named 'judo_throws' 
and populates it with a list of common Judo throw names.

Usage:
  python create_judo_db.py
"""

import sqlite3

def main():
    # 1) A short list of Judo throws.
    #    Feel free to add or remove based on your preferences or references.
    judo_throws = [
        "De Ashi Harai",
        "Hiza Guruma",
        "Sasae Tsurikomi Ashi",
        "Uki Goshi",
        "O Goshi",
        "Koshi Guruma",
        "Ippon Seoi Nage",
        "Morote Seoi Nage",
        "Tai Otoshi",
        "Harai Goshi",
        "Uchi Mata",
        "O Soto Gari",
        "O Uchi Gari",
        "Kouchi Gari",
        "Tomoe Nage"
    ]

    # 2) Connect (or create) the SQLite database
    conn = sqlite3.connect("judo_throws.db")
    cursor = conn.cursor()

    # 3) Create a table named 'judo_throws' with an 'id' and 'throw_name'
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS judo_throws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            throw_name TEXT
        )
    """)

    # 4) Optionally clear existing data if you want to re-insert
    cursor.execute("DELETE FROM judo_throws")

    # 5) Insert the list of judo throw names
    for throw in judo_throws:
        cursor.execute("INSERT INTO judo_throws (throw_name) VALUES (?)", (throw,))
    
    conn.commit()
    conn.close()

    print(f"Created 'judo_throws.db' and inserted {len(judo_throws)} Judo throws!")

if __name__ == "__main__":
    main()
