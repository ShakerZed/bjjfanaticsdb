#!/usr/bin/env python3
"""
fanatics_scraper_verbose_updated.py

An updated, verbose script to scrape BJJFanatics with the new 
HTML structure (product-card, product-card__item-title, product-card__price).
Stores data in a local SQLite database named bjjfanatics.db.
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
    
    cwd = os.getcwd()
    print(f"[DEBUG] Current working directory: {cwd}")
    
    try:
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

    Now updated to look for:
      <div class="product-card">
        <a class="product-card__item-title" href="...">Some Title</a>
        <span class="product-card__price">$47.00</span>
        ...
      </div>
    """
    print(f"[DEBUG] scrape_bjjfanatics_collections(): Starting to scrape {pages} pages.")
    
    base_url = "https://bjjfanatics.com"
    headers = {
        # Use a more realistic UA string to reduce blocking
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
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
            
            # Updated selector: look for divs with class="product-card"
            products = soup.find_all("div", class_="product-card")
            print(f"[DEBUG] Found {len(products)} products on page {page_num}.")

            if len(products) == 0:
                print("[WARN] 0 products found. Possibly HTML structure changed or we're blocked?")
            
            for product in products:
                # Title anchor with class "product-card__item-title"
                title_tag = product.find("a", class_="product-card__item-title")
                if title_tag:
                    product_name = title_tag.get_text(strip=True)
                    product_url = base_url + title_tag.get("href", "")
                else:
                    product_name = None
                    product_url = None
                
                # Price element with class "product-card__price"
                price_tag = product.find("span", class_="product-card__price")
                if price_tag:
                    price = price_tag.get_text(strip=True)
                else:
                    price = "N/A"
                
                # If you still want to parse out a "creator" from the name (e.g., "Gordon Ryan - System"),
                # you could do something naive like:
                creator = None
                if product_name and " - " in product_name:
                    parts = product_name.split(" - ", 1)
                    if len(parts) == 2:
                        creator = parts[0].strip()
                        product_name = parts[1].strip()
                
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
