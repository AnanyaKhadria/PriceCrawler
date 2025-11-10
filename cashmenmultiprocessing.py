import mysql.connector
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
import time
from concurrent.futures import ThreadPoolExecutor
import threading
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Auto-install ChromeDriver
chromedriver_autoinstaller.install()

# Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (remove if debugging)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Database connection details
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Thread-local storage for WebDriver instances
thread_local = threading.local()

def get_driver():
    """Reuse WebDriver instances within the same thread."""
    if not hasattr(thread_local, "driver"):
        service = Service()
        thread_local.driver = webdriver.Chrome(service=service, options=chrome_options)
    return thread_local.driver

# Function to extract model details and save to MySQL database
def extract_model_details(model_name, model_url):
    driver = get_driver()
    driver.get(model_url)
    wait = WebDriverWait(driver, 10)

    try:
        fieldset = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ModelDetails_fieldset___Y0_D")))

        inputs = fieldset.find_elements(By.TAG_NAME, "input")
        data = []

        for input_element in inputs:
            label_id = input_element.get_attribute("id")
            value = input_element.get_attribute("value")

            if label_id and ',' in label_id:
                ram, rom = label_id.split(',', 1)
            else:
                ram, rom = label_id, ""

            data.append((model_name, ram.strip(), rom.strip(), value))

        # Insert data into MySQL database in bulk
        if data:
            insert_into_db(data)

        print(f" Data saved for {model_name}")

    except Exception as e:
        print(f" Error extracting {model_name}: {e}")

# Function to insert data into MySQL **in bulk**
def insert_into_db(data):
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = connection.cursor()

        # Insert or update if the model_name, ram, and rom already exist
        cursor.executemany("""
            INSERT INTO cashmen_prices (model_name, ram, rom, price)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE price = VALUES(price)
        """, data)

        connection.commit()
        print(f" Updated database with new prices.")

    except mysql.connector.Error as err:
        print(f" Database Error: {err}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Function to scrape brand and models
def scrape_brand(brand_url):
    driver = get_driver()
    driver.get(brand_url)
    wait = WebDriverWait(driver, 10)

    try:
        time.sleep(3)  # Allow JavaScript to load
        model_links = driver.find_elements(By.CSS_SELECTOR, 'div[style*="opacity"] a')

        models = []
        for model in model_links:
            model_name = model.text.strip()
            model_url = model.get_attribute("href")
            if model_name and model_url:
                models.append((model_name, model_url))

        print(f" Found {len(models)} models for brand {brand_url}")
        return models

    except Exception as e:
        print(f" Error scraping brand {brand_url}: {e}")
        return []

# Main function
def main():
    base_url = "https://cashmen.in/sell-used-mobile-phone"
    driver = get_driver()
    driver.get(base_url)
    wait = WebDriverWait(driver, 10)

    # Get all brand URLs
    brand_links = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "BrandsList_list__bbs3s"))).find_elements(By.TAG_NAME, "a")
    brand_urls = [brand.get_attribute("href") for brand in brand_links]

    # Scrape brands concurrently using threading (5 threads)
    models_list = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(scrape_brand, brand_urls)

    for result in results:
        models_list.extend(result)

    print(f" Total models found: {len(models_list)}")

    # Scrape models in parallel (10 threads for better performance)
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(lambda model: extract_model_details(*model), models_list)

if __name__ == "__main__":
    main()
