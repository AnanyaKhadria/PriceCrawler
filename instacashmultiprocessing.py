import time
import random
import threading
import mysql.connector
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

# Global driver dictionary for threading
thread_local = threading.local()

def get_driver():
    """Ensures each thread gets its own WebDriver instance with headers."""
    if not hasattr(thread_local, "driver"):
        options = Options()
        options.add_argument("--headless")  
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        options.add_argument("lang=en-US")
        thread_local.driver = webdriver.Chrome(options=options)
    return thread_local.driver

def scrape_brand_links():
    """Scrapes all brand links."""
    url = "https://getinstacash.in/sell/used-smartphone"
    driver = get_driver()
    print("Fetching brand links...")
    
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.manufacturer-list li")))

    soup = BeautifulSoup(driver.page_source, "html.parser")
    brand_links = {
        li.get("data-term-search"): f"{url}/{li.get('data-term-search')}-{li.get('data-id')}"
        for li in soup.select("ul.manufacturer-list li") if li.get("data-term-search") and li.get("data-id")
    }
    
    print(f"Extracted {len(brand_links)} unique brand links.")
    return brand_links

def get_model_links(brand_name, brand_url):
    """Fetches model links for a specific brand."""
    driver = get_driver()
    print(f"Scraping models for {brand_name} from: {brand_url}")

    driver.get(brand_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.list-unstyled.variantUl li a")))

    soup = BeautifulSoup(driver.page_source, "html.parser")
    model_links = {
        a["href"]: {"href": a["href"], "ram": a.get_text(strip=True).split("/")[0] if "/" in a.get_text() else "N/A", 
                    "rom": a.get_text(strip=True).split("/")[1] if "/" in a.get_text() else a.get_text(strip=True)}
        for a in soup.select("ul.list-unstyled.variantUl li a[href]")
    }

    print(f"Extracted {len(model_links)} unique models for {brand_name}")
    return list(model_links.values())

def scrape_price(model):
    """Scrapes the price for a given model."""
    base_url = "https://getinstacash.in"
    full_url = base_url + model["href"]
    driver = get_driver()
    #print(f"Scraping price from: {full_url}")

    driver.get(full_url)

    try:
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "uptoPriceSpan")))
        time.sleep(random.uniform(2, 5))  # Random delay to avoid detection
        price = driver.find_element(By.CLASS_NAME, "uptoPriceSpan").text.strip()
    except:
        print(f" Price not found for {full_url}")
        price = "Not Found"

    try:
        model_name = driver.find_element(By.CLASS_NAME, "deviceName").text.strip()
    except:
        model_name = "Unknown"

    print(f" Price found: {price}, Model: {model_name}")
    return {"model_name": model_name, "ram": model["ram"], "rom": model["rom"], "price": price}

def store_in_db(data_list):
    """Updates extracted data in the MySQL database."""
    if not data_list:
        return

    try:
        connection = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME")

        )
        cursor = connection.cursor()

        # Ensure the table exists with a UNIQUE constraint on model_name, ram, and rom
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instacash_prices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                model_name VARCHAR(255),
                ram VARCHAR(50),
                rom VARCHAR(50),
                price VARCHAR(50),
                UNIQUE KEY unique_model (model_name, ram, rom)
            )
        """)

        # Insert or update the price if the model exists
        query = """
            INSERT INTO instacash_prices (model_name, ram, rom, price)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE price = VALUES(price)
        """
        
        values = [(data["model_name"], data["ram"], data["rom"], data["price"]) for data in data_list]

        cursor.executemany(query, values)
        connection.commit()

        print(f"Updated {len(values)} records successfully.")

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")

    finally:
        cursor.close()
        connection.close()
        
def main():
    driver = get_driver()

    # Step 1: Get all unique brand links
    brand_links = scrape_brand_links()
    print(f"Total unique brands found: {len(brand_links)}")

    # Step 2: Get unique model links per brand using ThreadPoolExecutor
    model_links = []
    with ThreadPoolExecutor(max_workers=10) as executor:  # Increased max_workers
        results = executor.map(lambda b: get_model_links(b, brand_links[b]), brand_links)

    for res in results:
        model_links.extend(res)

    print(f"Total unique models found: {len(model_links)}")

    # Step 3: Scrape prices using ThreadPoolExecutor
    price_dicts = []
    with ThreadPoolExecutor(max_workers=10) as executor:  # Increased max_workers
        results = executor.map(scrape_price, model_links)

    for res in results:
        price_dicts.append(res)

    driver.quit()  # Close the browser instance
    
    # Step 4: Store in database
    store_in_db(price_dicts)
    print("Data stored in database successfully.")

if __name__ == "__main__":
    main()
