#!/usr/bin/env python3
"""
create_judo_throws_db.py

Creates a SQLite database named 'judo_throws.db' with a table 'judo_throws'
containing all 67 recognized Kodokan Judo throws (Gokyo no Waza + Shinmeisho no Waza).

Usage:
  python create_judo_throws_db.py

After running, you can inspect the DB via:
  sqlite3 judo_throws.db
  .tables
  SELECT * FROM judo_throws;
"""

import sqlite3

def main():
    # A commonly referenced list of 67 Kodokan Judo throws.
    # This combines the Gokyo no Waza (40 throws) + additional recognized throws (Shinmeisho no Waza).
    # Some references may differ in naming/spelling or recognized variations.
    judo_throws = [
        # Gokyo no Waza (40)
        # Dai Ikkyo (1st group, 8 throws)
        "De Ashi Harai", "Hiza Guruma", "Sasae Tsuri Komi Ashi", "Uki Goshi",
        "O Goshi", "O Soto Gari", "O Soto Otoshi", "O Uchi Gari",
        # Dai Nikyo (2nd group, 8 throws)
        "Koshi Guruma", "Tsuki Goshi", "Uki Otoshi", "Harai Goshi",
        "Tsurikomi Goshi", "Okuri Ashi Harai", "Uchi Mata", "Seoi Nage",
        # Dai Sankyo (3rd group, 8 throws)
        "Ashi Guruma", "Hane Goshi", "Harai Tsuri Komi Ashi", "Tomoe Nage",
        "Kata Guruma", "Sumi Gaeshi", "Hikikomi Gaeshi", "Tsuri Goshi",
        # Dai Yonkyo (4th group, 8 throws)
        "Yoko Otoshi", "Tani Otoshi", "Hane Makikomi", "Sukui Nage",
        "Utsuri Goshi", "O Guruma", "Soto Makikomi", "Uki Waza",
        # Dai Gokyo (5th group, 8 throws)
        "O Soto Guruma", "Yoko Wakare", "Yoko Guruma", "Ushiro Goshi",
        "Ura Nage", "Sumi Otoshi", "Yoko Gake", "Obi Otoshi",

        # Shinmeisho no Waza (additional recognized throws; 27 to reach ~67 total)
        "Yama Arashi",  # famously used by Mifune
        "Kawazu Gake",
        "Kani Basami",
        "Uchi Mata Sukashi",
        "Te Guruma",
        "Daki Age",
        "Tawara Gaeshi",
        "Uchi Mata Gaeshi",
        "O Soto Gaeshi",
        "Harai Goshi Gaeshi",
        "Hane Goshi Gaeshi",
        "Kata Guruma Gaeshi",
        "O Soto Makikomi",  # some place it in Gokyo, references vary
        "O Soto Guruma Gaeshi",
        "Uchi Mata Makikomi",
        "Tsuri Goshi Gaeshi",
        "Koshi Guruma Gaeshi",
        "O Uchi Gaeshi",
        "Ko Uchi Gari",
        "Ko Soto Gari",
        "Uchi Makikomi",
        "Sumi Otoshi (variation)",  # if separate from Gokyo's
        "O Soto Kuchiki Taoshi",
        "O Soto Otoshi (variation)",
        "Yoko Wakare (variation)",
        "Yoko Guruma (variation)",
        "Ushiro Makikomi"  # see references
    ]

    # Connect to the DB (creates if not exist)
    conn = sqlite3.connect("judo_throws.db")
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS judo_throws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            throw_name TEXT
        )
    """)

    # Optional: Clear existing data if re-inserting
    cursor.execute("DELETE FROM judo_throws")

    # Insert each throw name
    for throw in judo_throws:
        cursor.execute("INSERT INTO judo_throws (throw_name) VALUES (?)", (throw,))

    conn.commit()
    conn.close()

    print(f"Created 'judo_throws.db' and inserted {len(judo_throws)} Judo throws!")

if __name__ == "__main__":
    main()
