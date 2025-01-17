#!/usr/bin/env python3
"""
bjj_scraper.py
--------------
A simple script to scrape BJJFanatics for BJJ instructionals (name, creator, price)
and store them in a local SQLite database.
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import time

DB_NAME = "bjjfanatics.db"

def create_database():
    """
    Create a local SQLite database (if it doesn't exist) 
    with a table called 'instructionals'.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS instructionals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            creator TEXT,
            price TEXT,
            product_url TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_instructional(name, creator, price, product_url):
    """
    Insert a single row into the 'instructionals' table.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO instructionals (name, creator, price, product_url)
        VALUES (?, ?, ?, ?)
    """, (name, creator, price, product_url))
    conn.commit()
    conn.close()

def scrape_bjjfanatics_collections(pages=2):
    """
    Scrape BJJFanatics' /collections/all page(s).
    By default, it scrapes 'pages' number of pages (2).
    Adjust 'pages' if you want to go deeper.
    """
    base_url = "https://bjjfanatics.com"
    headers = {
        # Use a decent User-Agent to avoid being blocked as a bot
        "User-Agent": "mybjjbot/1.0 (+https://example.com)"
    }

    for page_num in range(1, pages + 1):
        url = f"{base_url}/collections/all?page={page_num}"
        print(f"Scraping page {page_num}: {url}")

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve page {page_num}. Status code: {response.status_code}")
            break  # Stop if we hit an error

        soup = BeautifulSoup(response.text, "html.parser")
        
        # In Shopify themes, products might be in elements like "div.product-grid-item"
        products = soup.find_all("div", class_="product-grid-item")

        for product in products:
            link_tag = product.find("a", class_="product-link")
            if not link_tag:
                continue

            product_url = base_url + link_tag.get("href", "")
            raw_title = link_tag.get("title", "").strip()

            # Price might be in a span.price
            price_tag = product.find("span", class_="price")
            price = price_tag.get_text(strip=True) if price_tag else "N/A"

            # Attempt to parse "Creator - Title" from raw_title if present
            # This is site-specific and naive. Adjust logic as needed.
            creator = None
            product_name = raw_title
            if " - " in raw_title:
                parts = raw_title.split(" - ", 1)
                if len(parts) == 2:
                    creator = parts[0].strip()
                    product_name = parts[1].strip()

            insert_instructional(product_name, creator, price, product_url)

        # Be polite; don't hammer the server
        time.sleep(1)

    print("Scraping complete!")

def main():
    # 1) Ensure the database and table exist
    create_database()

    # 2) Scrape the first 2 pages (you can increase or decrease as desired)
    scrape_bjjfanatics_collections(pages=2)

    print(f"Done! Check {DB_NAME} for the 'instructionals' table.")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
bjj_scraper.py
--------------
A simple script to scrape BJJFanatics for BJJ instructionals (name, creator, price)
and store them in a local SQLite database.
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import time

DB_NAME = "bjjfanatics.db"

def create_database():
    """
    Create a local SQLite database (if it doesn't exist) 
    with a table called 'instructionals'.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS instructionals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            creator TEXT,
            price TEXT,
            product_url TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_instructional(name, creator, price, product_url):
    """
    Insert a single row into the 'instructionals' table.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO instructionals (name, creator, price, product_url)
        VALUES (?, ?, ?, ?)
    """, (name, creator, price, product_url))
    conn.commit()
    conn.close()

def scrape_bjjfanatics_collections(pages=2):
    """
    Scrape BJJFanatics' /collections/all page(s).
    By default, it scrapes 'pages' number of pages (2).
    Adjust 'pages' if you want to go deeper.
    """
    base_url = "https://bjjfanatics.com"
    headers = {
        # Use a decent User-Agent to avoid being blocked as a bot
        "User-Agent": "mybjjbot/1.0 (+https://example.com)"
    }

    for page_num in range(1, pages + 1):
        url = f"{base_url}/collections/all?page={page_num}"
        print(f"Scraping page {page_num}: {url}")

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve page {page_num}. Status code: {response.status_code}")
            break  # Stop if we hit an error

        soup = BeautifulSoup(response.text, "html.parser")
        
        # In Shopify themes, products might be in elements like "div.product-grid-item"
        products = soup.find_all("div", class_="product-grid-item")

        for product in products:
            link_tag = product.find("a", class_="product-link")
            if not link_tag:
                continue

            product_url = base_url + link_tag.get("href", "")
            raw_title = link_tag.get("title", "").strip()

            # Price might be in a span.price
            price_tag = product.find("span", class_="price")
            price = price_tag.get_text(strip=True) if price_tag else "N/A"

            # Attempt to parse "Creator - Title" from raw_title if present
            # This is site-specific and naive. Adjust logic as needed.
            creator = None
            product_name = raw_title
            if " - " in raw_title:
                parts = raw_title.split(" - ", 1)
                if len(parts) == 2:
                    creator = parts[0].strip()
                    product_name = parts[1].strip()

            insert_instructional(product_name, creator, price, product_url)

        # Be polite; don't hammer the server
        time.sleep(1)

    print("Scraping complete!")

def main():
    # 1) Ensure the database and table exist
    create_database()

    # 2) Scrape the first 2 pages (you can increase or decrease as desired)
    scrape_bjjfanatics_collections(pages=2)

    print(f"Done! Check {DB_NAME} for the 'instructionals' table.")

if __name__ == "__main__":
    main()
