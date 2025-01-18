#!/usr/bin/env python3
"""
fanatics_selenium_scraper_verbose_wait.py

Scrapes BJJFanatics.com using a headless Chrome browser (via Selenium),
with a more robust wait (WebDriverWait) instead of fixed sleeps.

Data is stored in a local SQLite database (bjjfanatics.db),
with a table named 'instructionals'.

Now includes traceback.print_exc() for detailed error info.
"""

import os
import sqlite3

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

DB_NAME = "bjjfanatics.db"

def create_database():
    """
    Create a local SQLite database if it doesn't exist,
    with a table for storing BJJ instructional data.
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

def scrape_bjjfanatics_selenium(pages=2):
    """
    Use Selenium (headless Chrome) to scrape BJJFanatics /collections/all
    for the specified number of pages (default=2, can be increased).

    Instead of a fixed time.sleep, we use WebDriverWait to wait for the 
    product elements to appear (up to 15 seconds).

    Steps:
    1) Launch headless Chrome
    2) For each page, driver.get() the URL
    3) Use WebDriverWait to detect product elements
    4) Parse final rendered HTML with BeautifulSoup
    5) Locate product elements, extract data, insert into SQLite DB
    """

    print(f"[DEBUG] scrape_bjjfanatics_selenium(): Starting to scrape {pages} pages.")

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless mode
    
    driver = webdriver.Chrome(options=chrome_options)
    base_url = "https://bjjfanatics.com"

    for page_num in range(1, pages + 1):
        url = f"{base_url}/collections/all?page={page_num}"
        print(f"[DEBUG] Navigating to page {page_num}: {url}")

        try:
            driver.get(url)
            
            wait = WebDriverWait(driver, 15)
            wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-card"))
            )

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            products = soup.find_all("div", class_="product-card")
            print(f"[DEBUG] Found {len(products)} products on page {page_num}.")

            if len(products) == 0:
                print("[WARN] 0 products found. Possibly structure changed or still blocked?")

            for product in products:
                title_tag = product.find("h2", class_="product-card__item-title")
                if not title_tag:
                    continue

                product_name = title_tag.get_text(strip=True)

                link_tag = product.find("a", class_="product-card__item-title")
                if link_tag:
                    product_url = base_url + link_tag.get("href", "")
                else:
                    product_url = None

                price_tag = product.find("span", class_="product-card__price")
                price = price_tag.get_text(strip=True) if price_tag else "N/A"

                creator = None
                if " - " in product_name:
                    parts = product_name.split(" - ", 1)
                    if len(parts) == 2:
                        creator = parts[0].strip()
                        product_name = parts[1].strip()

                insert_instructional(product_name, creator, price, product_url)

        except Exception as e:
            print("[ERROR] scrape_bjjfanatics_selenium():", e)
            import traceback
            traceback.print_exc()  # prints the full stack trace
            break

    driver.quit()
    print("[DEBUG] Done scraping with Selenium + WebDriverWait.")

def main():
    print("[DEBUG] main(): Starting script execution...")

    create_database()
    scrape_bjjfanatics_selenium(pages=2)

    print("[DEBUG] main(): Script completed. Check for 'bjjfanatics.db' and confirm data.")

if __name__ == "__main__":
    main()
