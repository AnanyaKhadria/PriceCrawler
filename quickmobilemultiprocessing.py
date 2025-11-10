
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import mysql.connector
import re
import os
from dotenv import load_dotenv

load_dotenv()
# Global session object to reuse connections
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

BASE_URL = "https://www.quickmobile.in/sell-old-mobile-phone"


def fetch_url(url):
    """Fetch a URL using a persistent session."""
    try:
        response = session.get(url, timeout=10)
        return response.text if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None


def extract_brand_links():
    """Extract brand links from the base URL."""
    html = fetch_url(BASE_URL)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    return [a['href'] for div in soup.find_all("div", class_="col-md-3 col-lg-2 col-xl-2") for a in div.find_all("a", href=True)]


def extract_models_from_brand(link):
    """Extract model links from a brand page."""
    html = fetch_url(link)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    return [a['href'] for div in soup.find_all("div", class_="image-frame") for a in div.find_all("a", href=True)]


def extract_variants(model_link):
    """Extract model variants with RAM and ROM details."""
    full_url = model_link if model_link.startswith("http") else BASE_URL + model_link
    html = fetch_url(full_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    return [
        f"{full_url}-{div['data-ram']}gb-{div['data-storage']}gb"
        for div in soup.find_all("div", class_="select-ram hovercls ram-phone")
        if div.get("data-ram") and div.get("data-storage")
    ]


def extract_price_and_model(link):
    """Extract model name, RAM, ROM, and price from a product page."""
    html = fetch_url(link)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    
    # Extract price
    price_tag = soup.find("div", class_="getup-price")
    price_text = price_tag.find("h3").text.strip() if price_tag else "0"
    price_match = re.search(r"(\d{4,6})", price_text)
    price = price_match.group(1) if price_match else "0"

    # Extract model name, RAM, and ROM
    model_tag = soup.find("h1", class_="span_btn1")
    if not model_tag:
        return None

    model_name = model_tag.text.replace("Sell Old", "").strip()
    model_split = model_name.split("(")
    model_clean = model_split[0].strip()
    ram_rom = model_split[1].replace(")", "").split("/") if len(model_split) > 1 else ["Unknown", "Unknown"]

    return (model_clean, ram_rom[0].strip(), ram_rom[1].strip(), price)


def store_prices_in_db(data):
    """Batch insert or update extracted data into MySQL."""
    if not data:
        return

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Ensure the table exists with a UNIQUE constraint on model_name, ram, and rom
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quickmobile_prices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                model_name VARCHAR(255),
                ram VARCHAR(10),
                rom VARCHAR(10),
                price VARCHAR(50),
                UNIQUE KEY unique_model (model_name, ram, rom)
            )
        """)

        sql = """
            INSERT INTO quickmobile_prices (model_name, ram, rom, price)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE price = VALUES(price)
        """
        
        cursor.executemany(sql, data)
        conn.commit()

        print(f"Updated {len(data)} records in quickmobile_prices.")

    except mysql.connector.Error as err:
        print(f"Database error: {err}")

    finally:
        cursor.close()
        conn.close()


def main():
    brand_links = extract_brand_links()

    with ThreadPoolExecutor(max_workers=8) as executor:
        model_links = list(executor.map(extract_models_from_brand, brand_links))

    model_links = [item for sublist in model_links for item in sublist]

    with ThreadPoolExecutor(max_workers=8) as executor:
        variant_links = list(executor.map(extract_variants, model_links))

    variant_links = [item for sublist in variant_links for item in sublist]

    with ThreadPoolExecutor(max_workers=8) as executor:
        price_data = list(executor.map(extract_price_and_model, variant_links))

    price_data = [item for item in price_data if item is not None]

    store_prices_in_db(price_data)


if __name__ == "__main__":
    main()
