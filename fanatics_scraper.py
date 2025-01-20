#!/usr/bin/env python3
"""
fanatics_selenium_scraper_all_pages.py

Scrapes BJJFanatics.com using a headless Chrome browser (via Selenium),
targeting <div class="product-card__grid-item"> as the outer wrapper.
Continues scraping pages until no more products are found.

Data is stored in a local SQLite database (bjjfanatics.db),
with a table named 'instructionals'.
"""

import os
import sqlite3
import traceback

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

DB_NAME = "bjjfanatics.db"

def create_database():
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

def scrape_all_pages():
    print("[DEBUG] scrape_all_pages(): Starting to scrape pages until no more products are found.")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)
    base_url = "https://bjjfanatics.com"
    
    page_num = 1
    while True:
        url = f"{base_url}/collections/all?page={page_num}"
        print(f"[DEBUG] Navigating to page {page_num}: {url}")

        try:
            driver.get(url)
            wait = WebDriverWait(driver, 15)
            # Wait for presence of elements or timeout after 15 seconds
            wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.product-card__grid-item"))
            )
        except Exception as e:
            print(f"[WARN] Wait condition not met on page {page_num}: {e}")
            # Proceed even if wait times out, to check the page content

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        products = soup.find_all("div", class_="product-card__grid-item")
        print(f"[DEBUG] Found {len(products)} products on page {page_num}.")

        if len(products) == 0:
            print(f"[INFO] No products found on page {page_num}. Assuming end of pages.")
            break

        # Process each product on the page
        for product in products:
            title_tag = product.find(class_="product-card__item-title")
            if title_tag:
                product_name = title_tag.get_text(strip=True)
            else:
                product_name = "Unknown Product"

            link_tag = product.find("a", class_="product-card__item-title")
            if link_tag and link_tag.get("href"):
                product_url = base_url + link_tag.get("href", "")
            else:
                product_url = None

            price_tag = product.find("span", class_="product-card__price")
            price = price_tag.get_text(strip=True) if price_tag else "N/A"

            creator = None
            if product_name and " - " in product_name:
                parts = product_name.split(" - ", 1)
                if len(parts) == 2:
                    creator = parts[0].strip()
                    product_name = parts[1].strip()

            insert_instructional(product_name, creator, price, product_url)

        page_num += 1  # Move to the next page

    driver.quit()
    print("[DEBUG] Done scraping all pages with Selenium.")

def main():
    print("[DEBUG] main(): Starting script execution...")
    create_database()
    scrape_all_pages()
    print("[DEBUG] main(): Script completed. Check for 'bjjfanatics.db' and confirm data.")

if __name__ == "__main__":
    main()
