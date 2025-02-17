import sqlite3

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

# Choose one of the two based on your needs:
remove_exact_duplicates("judo_mentions.db")  # Removes rows that are completely identical
# remove_soft_duplicates("judo_mentions.db")  # Removes all but one entry per post_id + throw_name
