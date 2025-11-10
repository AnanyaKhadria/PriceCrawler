
import requests
from bs4 import BeautifulSoup
import mysql.connector
from multiprocessing import Pool
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import random

load_dotenv()

# Database Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Database Connection
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Create Table if not exists
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cashify_prices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            model_name VARCHAR(255),
            ram VARCHAR(50),
            rom VARCHAR(50),
            price VARCHAR(50),
            UNIQUE KEY unique_model (model_name, ram, rom)
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Scrape Brand Links
def scrape_brand_links():
    base_url = "https://www.cashify.in/sell-old-mobile-phone/brands"
    response = requests.get(base_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        divs = soup.find_all("div", class_=[
            "basis-full sm:rounded-lg border-b border-r border-gray-200 border-solid sm:shadow-md h-40 flex flex-col",
            "basis-full sm:rounded-lg border-b border-r border-gray-200 border-solid sm:shadow-md h-40 border-r-0 flex flex-col"
        ])
        print(f"Extracted {len(divs)} brand links")
        return [a['href'] for div in divs for a in div.find_all("a", href=True)]
    return []

# Scrape Model Links from Brand Pages
'''
def scrape_models_from_brand(brand_url):
    full_url = f"https://www.cashify.in{brand_url}"
    response = requests.get(full_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        divs = soup.find_all("div", class_=[
            "basis-full sm:rounded-lg border-b border-r border-gray-200 border-solid sm:shadow-md h-44 sm:h-auto flex flex-col",
            "basis-full sm:rounded-lg border-b border-r border-gray-200 border-solid sm:shadow-md h-44 sm:h-auto border-r-0 flex flex-col",
            "basis-full sm:rounded-lg border-b border-r border-gray-200 border-solid sm:shadow-md h-44 sm:h-auto border-b-0 flex flex-col",
            "basis-full sm:rounded-lg border-b border-r border-gray-200 border-solid sm:shadow-md h-44 sm:h-auto border-r-0 border-b-0 flex flex-col"
        ])
        print(f"Extracted {len(divs)} model links from {brand_url}")
        return [a['href'] for div in divs for a in div.find_all("a", href=True)]
    return []
'''
def init_driver():
    """Initialize and return a Selenium WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless")  # Uncomment to run headless
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def scrape_models_from_brand(brand_url):
    """Scrolls through the page and extracts all model links."""
    print(f"[INFO] Processing brand: {brand_url}")
    driver = init_driver()
    
    try:
        full_url = f"https://www.cashify.in{brand_url}"
        driver.get(full_url)
        time.sleep(3)  # Initial page load wait

        last_count = 0  # Track last model count

        while True:
            # Find all loaded model elements using your provided classes
            model_elements = driver.find_elements(By.XPATH, "//div[@class='basis-full sm:rounded-lg border-b border-r border-gray-200 border-solid sm:shadow-md h-44 sm:h-auto flex flex-col'] | \
                //div[@class='basis-full sm:rounded-lg border-b border-r border-gray-200 border-solid sm:shadow-md h-44 sm:h-auto border-r-0 flex flex-col'] | \
                //div[@class='basis-full sm:rounded-lg border-b border-r border-gray-200 border-solid sm:shadow-md h-44 sm:h-auto border-b-0 flex flex-col'] | \
                //div[@class='basis-full sm:rounded-lg border-b border-r border-gray-200 border-solid sm:shadow-md h-44 sm:h-auto border-r-0 border-b-0 flex flex-col']")

            if len(model_elements) == last_count:  # Stop if no new models loaded
                break

            last_model = model_elements[-1]  # Get last model element
            driver.execute_script("arguments[0].scrollIntoView();", last_model)  # Scroll to last model
            time.sleep(2)  # Wait for new models to load

            last_count = len(model_elements)  # Update last model count

        print("[INFO] Finished scrolling, extracting models...")

        # Extract model links using BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")
        divs = soup.find_all("div", class_=[
            "basis-full sm:rounded-lg border-b border-r border-gray-200 border-solid sm:shadow-md h-44 sm:h-auto flex flex-col",
            "basis-full sm:rounded-lg border-b border-r border-gray-200 border-solid sm:shadow-md h-44 sm:h-auto border-r-0 flex flex-col",
            "basis-full sm:rounded-lg border-b border-r border-gray-200 border-solid sm:shadow-md h-44 sm:h-auto border-b-0 flex flex-col",
            "basis-full sm:rounded-lg border-b border-r border-gray-200 border-solid sm:shadow-md h-44 sm:h-auto border-r-0 border-b-0 flex flex-col"
        ])

        links = [a['href'] for div in divs for a in div.find_all("a", href=True)]
        print(f"[INFO] Found {len(links)} model links in brand {brand_url}")
        return links

    except Exception as e:
        print(f"[ERROR] Error in scrape_models_from_brand: {e}")
        return []
    
    finally:
        driver.quit()

def scrape_variants(model_url):
    full_url = f"https://www.cashify.in{model_url}"
    print(f"Fetching variants from: {full_url}")  # Debugging step
    
    try:
        response = requests.get(full_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            # First, try extracting variant links from `li` elements
            lis = soup.find_all("li", class_="w-[47%] sm:w-48 sm:max-w-full flex flex-col")
            variant_links = [a['href'] for li in lis for a in li.find_all("a", href=True)]
            
            # Debugging: Log extracted links
            print(f"Extracted {len(variant_links)} variant links from <li> for {model_url}")

            # If `lis` is empty, try the fallback method
            '''
            if not variant_links:
                divs = soup.find_all("div", class_="w-1/3 sm:w-auto sm:col-span-1 h-auto sm:max-h-56 sm:rounded-lg border-b border-r border-gray-200 border-solid sm:shadow-md flex flex-col")
                variant_links = [a['href'] for div in divs for a in div.find_all("a", href=True)]
                
                print(f"Extracted {len(variant_links)} variant links from <div> for {model_url}")
            '''
            # If still no variant links, add the current model_url
            if not variant_links:
                variant_links.append(model_url)
                print(f"No variant links found, adding model URL itself: {model_url}")

            return variant_links
        
        else:
            print(f"Failed to fetch {full_url}, Status Code: {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {full_url}: {e}")
    
    return []

# Extract Price and Store in Database
def extract_model_ram_rom(soup):
    model_info_div = soup.find("div", class_="inherit hidden", itemprop="name")
    if model_info_div:
        text = model_info_div.get_text(strip=True)
        print(f"Raw extracted text: {text}")  # Debugging
        
        if "(" in text and ")" in text:
            model_name, specs = text.rsplit("(", 1)  # Use `rsplit` to split from the last '('
            specs = specs.rstrip(")")
            ram, rom = specs.split("/") if "/" in specs else ("Unknown", "Unknown")
            return model_name.strip(), ram.strip(), rom.strip()
    
    print("Extraction failed, returning Unknown values")  # Debugging
    return "Unknown", "Unknown", "Unknown"


def store_price_in_db(model_name, ram, rom, price):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cashify_prices (model_name, ram, rom, price)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE price = VALUES(price)
    """, (model_name, ram, rom, price))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Updated: {model_name} {ram} {rom} -> {price}".encode("utf-8", "ignore").decode("utf-8"))

def extract_price_and_store(product_url):
    full_url = f"https://www.cashify.in{product_url}"
    response = requests.get(full_url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        price_span = soup.find("span", class_="extraFont1 text-error")
        price = price_span.get_text(strip=True) if price_span else "Price Not Found"
        
        model_name, ram, rom = extract_model_ram_rom(soup)
        store_price_in_db(model_name, ram, rom, price)
    else:
        print(f"Failed to fetch data for {full_url}")

# Multiprocessing Function
def process_brand(brand_url):
    """Scrapes all model variant links for a given brand"""
    model_links = scrape_models_from_brand(brand_url)
    
    # Instead of using a new pool, process sequentially here
    variant_links = []
    for model_link in model_links:
        variant_links.extend(scrape_variants(model_link))
    
    return variant_links
    

def main():
    create_table()  # Ensure table exists

    brand_links = scrape_brand_links()  # Step 1: Scrape brand links
    
    if brand_links:
        with Pool(processes=8) as pool:
            model_page_hrefs = pool.map(process_brand, brand_links)

        # Flatten the list
        model_page_hrefs = [href for sublist in model_page_hrefs for href in sublist]

        if model_page_hrefs:
            with Pool(processes=8) as pool:
                pool.map(extract_price_and_store, model_page_hrefs)

if __name__ == "__main__":
    main()
