#!/usr/bin/env python3
"""
bjj_scraper_verbose.py

A verbose script to scrape BJJFanatics for BJJ instructionals
and store them in a local SQLite database. Includes extra print
statements to help debug issues (e.g. no .db file created).
"""

import os
import time
import sqlite3
import requests
from bs4 import BeautifulSoup

DB_NAME = "bjjfanatics.db"

def create_database():
    """
    Creates (if not present) a local SQLite database called 'bjjfanatics.db'
    and an 'instructionals' table to store the scraped data.
    Verbose prints help confirm each step.
    """
    print("[DEBUG] create_database(): Starting database creation logic...")
    
    # Print the current working directory to confirm where the .db file will be created
    cwd = os.getcwd()
    print(f"[DEBUG] Current working directory: {cwd}")
    
    try:
        # Connect (creates the file if it doesn't exist)
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
    Inserts a single record into the 'instructionals' table.
    Provides verbose output for debug.
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
    Scrapes the BJJFanatics /collections/all page(s).
    Defaults to 2 pages, but you can adjust.
    Prints verbose info for each step to help you see status codes,
    how many products were found, etc.
    """
    print(f"[DEBUG] scrape_bjjfanatics_collections(): Starting to scrape {pages} pages.")
    
    base_url = "https://bjjfanatics.com"
    headers = {
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
            
            # Check a snippet of the response to ensure we're getting the expected HTML
            print("[DEBUG] HTML snippet:", response.text[:200].replace("\n", " "))
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # This CSS class might change if BJJFanatics updates their site/theme
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
                
                # Price might be inside <span class="price"> 
                price_tag = product.find("span", class_="price")
                price = price_tag.get_text(strip=True) if price_tag else "N/A"
                
                # Attempt to parse "Creator - Title" if present in raw_title
                creator = None
                product_name = raw_title
                if " - " in raw_title:
                    parts = raw_title.split(" - ", 1)
                    if len(parts) == 2:
                        creator = parts[0].strip()
                        product_name = parts[1].strip()
                
                # Insert record into DB
                insert_instructional(product_name, creator, price, product_url)
            
            # Sleep to avoid hammering the server
            time.sleep(1)
        
        except requests.exceptions.RequestException as req_err:
            print(f"[ERROR] Network error on page {page_num}:", req_err)
            break  # Stop scraping if a major network error occurred
        except Exception as e:
            print("[ERROR] scrape_bjjfanatics_collections():", e)
            break  # For any unforeseen errors, stop

def main():
    print("[DEBUG] main(): Starting script execution...")
    
    # 1) Create DB if not exists
    create_database()
    
    # 2) Scrape pages
    scrape_bjjfanatics_collections(pages=2)
    
    print("[DEBUG] main(): Script completed. Check for 'bjjfanatics.db' and confirm data.")

if __name__ == "__main__":
    main()
