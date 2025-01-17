#!/usr/bin/env python3
"""
fanatics_scraper_verbose.py

A verbose script to scrape BJJFanatics for BJJ instructionals
and store them in a local SQLite database, with debug prints
for troubleshooting.
"""

import os
import time
import sqlite3
import requests
from bs4 import BeautifulSoup

DB_NAME = "bjjfanatics.db"

def create_database():
    """
    Create (if not present) a local SQLite database named bjjfanatics.db
    and an 'instructionals' table to store the scraped data.
    """
    print("[DEBUG] create_database(): Starting database creation logic...")
    
    # Print the current working directory so you know where the .db file goes
    cwd = os.getcwd()
    print(f"[DEBUG] Current working directory: {cwd}")
    
    try:
        # Connect (creates bjjfanatics.db if it doesn't exist)
        conn = sqlite3.connect(DB_NAME)
        print(f"[DEBUG] Connected to '{DB_NAME}' database successfully.")
        
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
        print("[DEBUG] Executed CREATE TABLE IF NOT EXISTS for 'instructionals'.")
        
        conn.commit()
        conn.close()
        print("[DEBUG] Database setup complete. Table 'instructionals' is ready.")
        
    except Exception as e:
        print("[ERROR] create_database():", e)

def insert_instructional(name, creator, price, product_url):
    """
    Insert a single record into the 'instructionals' table.
    Provides verbose output for debugging.
    """
    print(f"[DEBUG] insert_instructional(): Attempting to insert:\n"
          f"        name={name}, creator={creator}, price={price}, url={product_url}")
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO instructionals (name, creator, price, product_url)
            VALUES (?, ?, ?, ?)
        """, (name, creator, price, product_url))
        conn.commit()
        conn.close()
        
        print("[DEBUG] Insert successful.")
    except Exception as e:
        print("[ERROR] insert_instructional():", e)

def scrape_bjjfanatics_collections(pages=2):
    """
    Scrape the BJJFanatics /collections/all pages.
    Defaults to 2 pages, but you can adjust. Includes extra debug prints.
    """
    print(f"[DEBUG] scrape_bjjfanatics_collections(): Starting to scrape {pages} pages.")
    
    base_url = "https://bjjfanatics.com"
    headers = {
        # A user-agent to reduce the chance of being blocked as a bot
        "User-Agent": "mybjjbot/1.0 (+https://example.com)"
    }

    for page_num in range(1, pages + 1):
        url = f"{base_url}/collections/all?page={page_num}"
        print(f"[DEBUG] Requesting page {page_num}: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            print(f"[DEBUG] Received HTTP status: {response.status_code}")
            
            if response.status_code != 200:
                print("[WARN] Non-200 status code. Stopping further scraping.")
                break
            
            # Print a snippet of the response to ensure we got real product HTML
            html_snippet = response.text[:300].replace("\n", " ")
            print(f"[DEBUG] HTML snippet (first 300 chars): {html_snippet}")
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Look for divs with class="product-grid-item"
            products = soup.find_all("div", class_="product-grid-item")
            print(f"[DEBUG] Found {len(products)} products on page {page_num}.")

            if len(products) == 0:
                print("[WARN] 0 products found. Possibly HTML structure changed or we're blocked?")
            
            for product in products:
                link_tag = product.find("a", class_="product-link")
                if not link_tag:
                    print("[DEBUG] No 'a.product-link' found in this product element.")
                    continue
                
                product_url = base_url + link_tag.get("href", "")
                raw_title = link_tag.get("title", "").strip()
                
                # Attempt to get price
                price_tag = product.find("span", class_="price")
                price = price_tag.get_text(strip=True) if price_tag else "N/A"
                
                # Try parsing "Creator - Title" if present
                creator = None
                product_name = raw_title
                if " - " in raw_title:
                    parts = raw_title.split(" - ", 1)
                    if len(parts) == 2:
                        creator = parts[0].strip()
                        product_name = parts[1].strip()
                
                # Insert record into the database
                insert_instructional(product_name, creator, price, product_url)
            
            # Sleep a bit to avoid hammering the server
            time.sleep(1)
        
        except requests.exceptions.RequestException as req_err:
            print(f"[ERROR] Network error on page {page_num}:", req_err)
            break
        except Exception as e:
            print("[ERROR] scrape_bjjfanatics_collections():", e)
            break

def main():
    print("[DEBUG] main(): Starting script execution...")
    
    # Create the DB and table if needed
    create_database()
    
    # Scrape some pages (default = 2)
    scrape_bjjfanatics_collections(pages=2)
    
    print("[DEBUG] main(): Script completed. Check for 'bjjfanatics.db' and confirm data.")

if __name__ == "__main__":
    main()
