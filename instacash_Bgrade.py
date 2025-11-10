
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pickle
import re
from instacashmultiprocessing import scrape_brand_links, get_model_links
from selenium.common.exceptions import TimeoutException
import multiprocessing
from itertools import islice
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from selenium.common.exceptions import StaleElementReferenceException
import mysql.connector
import os
from dotenv import load_dotenv
from functools import partial
import json
import threading
import concurrent.futures
import threading

load_dotenv()

def store_device_details_in_db(device_name, ram, rom, price):
    """Stores or updates the device details in the MySQL database."""
    
    # Database connection details
    db_config = {
         "host": os.getenv("DB_HOST"),
         "user": os.getenv("DB_USER"),
         "password": os.getenv("DB_PASSWORD"),
         "database": os.getenv("DB_NAME"),
    }
    
    try:
        # Establish connection
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Create table if not exists
        create_table_query = """
        CREATE TABLE IF NOT EXISTS instacash_bgrade_prices (
            model_name VARCHAR(255) NOT NULL,
            ram VARCHAR(10),
            rom VARCHAR(10),
            price VARCHAR(50),
            PRIMARY KEY (model_name, ram, rom)
        )
        """
        cursor.execute(create_table_query)

        # Insert or update query
        insert_query = """
        INSERT INTO instacash_bgrade_prices (model_name, ram, rom, price)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE price = VALUES(price)
        """
        cursor.execute(insert_query, (device_name, ram, rom, price))
        conn.commit()

        print(f"Successfully stored/updated: {device_name}, RAM: {ram}, ROM: {rom}, Price: {price}")

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    
    finally:
        cursor.close()
        conn.close()

def get_all_links():

    brand_links = scrape_brand_links()
    
    if not isinstance(brand_links, dict):
        raise ValueError("Expected 'scrape_brand_links' to return a dictionary with brand names as keys and URLs as values.")
    
    # Step 2: Use multiprocessing to scrape models for each brand
    with multiprocessing.Pool(processes=8) as pool:
        all_model_links = pool.starmap(get_model_links, brand_links.items())  # Using starmap to pass (brand_name, brand_url)
    
    # Flatten the list of lists
    all_model_links = [link for sublist in all_model_links for link in sublist]

    return all_model_links


def setup_driver():
    """Automatically sets up and returns a Selenium WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())  
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def click_getquote(driver, url):
    driver.get(url)  # Open the correct URL
    wait = WebDriverWait(driver, 15)  # Increased wait time
    
    try:
        a_xpath = '//a[(contains(@class, "btn green getQuoteBtn ladda-exactQuote ladda-button"))]'
        a_element = wait.until(EC.element_to_be_clickable((By.XPATH, a_xpath)))
        print("Found 'Get Quote' button!")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", a_element)
        time.sleep(1)  # Allow UI to stabilize
        driver.execute_script("arguments[0].click();", a_element)

        print("Clicked on 'Get Quote' button!")

        # Wait for page transition
        time.sleep(5)

    except Exception as e:
        print("Error clicking 'Get Exact Value' button:", e)

def click_radio_1_button(driver):
    try:

        ids=["STON0", "SPTS1"]
        for id in ids:
            radio_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, id))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio_button)
            driver.execute_script("arguments[0].click();", radio_button)
            print("Radio button clicked successfully")

    except Exception as e:
        print("Error clicking radio button:", e)

def skip_button(driver):
    try:
        skip_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//a[(contains(@class, "btn default skipBtn"))]'))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", skip_button)
        driver.execute_script("arguments[0].click();", skip_button)
        print("Skip button clicked successfully")

    except Exception as e:
        print("Error clicking skip button:", e)

def click_radio_2_button(driver):
    try:
            radio_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "yesNo2"))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio_button)
            driver.execute_script("arguments[0].click();", radio_button)
            print("Radio button clicked successfully")

    except Exception as e:
        print("Error clicking radio button:", e)

def radio_3_button(driver):

    ids=["CAGE3", "CPBP1", "CPBT1","CPSF1","CPCG0"]
    for id in ids:
        try:
            radio_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, id))
            )
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio_button)
            driver.execute_script("arguments[0].click();", radio_button)
            print("Radio button clicked successfully")

        except Exception as e:
            print("Error clicking radio button:", e)

def get_final_quote(driver):
    try:
        quote_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//button[(contains(@id, "getQuoteBtn"))]'))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", quote_button)
        driver.execute_script("arguments[0].click();", quote_button)
        print("Final quote button clicked successfully")

    except Exception as e:
        print("Error getting final quote:", e)

def select_city(driver):
    try:
        city_xpath = "//li[contains(@id,'popJaipur')]"
        city_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, city_xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", city_element)
        driver.execute_script("arguments[0].click();", city_element)
        print("City selected successfully.")
        time.sleep(1)
   
    except Exception as e:
        print("Error entering city:", e)


def fill_mobile_number(driver, mobile_number):
    """
    This function locates the mobile number input field inside the form,
    enters the given mobile number, and clicks the submit button using JavaScript.

    :param driver: Selenium WebDriver instance
    :param mobile_number: Mobile number to be entered (10-digit string)
    """
    try:
        # Locate the form by ID
        form = driver.find_element(By.ID, "mobileQuest")

        # Find the input field inside the form
        input_field = form.find_element(By.NAME, "popMobile")

        # Clear the field and enter the mobile number
        input_field.clear()
        input_field.send_keys(mobile_number)

        # Find the button inside the form
        submit_button = form.find_element(By.XPATH, "//button[contains(@class, 'btn green mobileContinue ladda-mobC ladda-button')]")

        # Click the button using JavaScript
        driver.execute_script("arguments[0].click();", submit_button)

        print("Mobile number submitted successfully using JavaScript.")

    except Exception as e:
        print(f"An error occurred: {e}")

def extract_details(driver, index=0):
    try:
        div_xpath = "(//div[contains(@class,'data')])[{}]".format(index + 1)
        div_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, div_xpath)))
        
        h2_xpath = div_xpath + "//h2[contains(@class,'deviceName')]"
        h2_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, h2_xpath)))
        
        h3_xpath = div_xpath + "//h3"
        h3_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, h3_xpath)))

        device_details = h2_element.text
        price = h3_element.get_attribute("textContent").strip()  # Corrected this

        parts = device_details.rsplit(" ", 1)  # Split from the right, once
        device_name = parts[0]  # Take everything before the last space
        ram = "N/A"  # Default RAM
        rom = "N/A"  # Default ROM

        if "/" in parts[1]:  # If RAM/ROM is present
            ram, rom = parts[1].split("/")  # Split RAM and ROM
        else:
            rom = parts[1]  # If no "/", it's only ROM

        details = {"device_name": device_name, "ram": ram, "rom": rom, "price": price}
        store_device_details_in_db(device_name, ram, rom, price)
        print(details)
        return details

    except Exception as e:
        print("Error extracting details:", e)
        return None

def process_variant_link(url):
    """Process a variant link in an already opened tab."""
    driver = setup_driver()
    try:
        #driver.switch_to.window(driver.window_handles[-1])  # Switch to the newly opened tab
        print(f"Processing: {url}")
        driver.get(url)
        time.sleep(2)

        # Perform the required actions
        click_getquote(driver, url)
        click_radio_1_button(driver)
        skip_button(driver)
        click_radio_2_button(driver)
        radio_3_button(driver)
        skip_button(driver)
        time.sleep(3)
        get_final_quote(driver)
        time.sleep(5)
        select_city(driver)
        time.sleep(3)
        fill_mobile_number(driver, "9779626274")
        time.sleep(10)
        extract_details(driver, index=0)

    except Exception as e:
        print(f"Error processing {url}: {e}")
    finally:
        driver.quit()

def run_scraping():
    
    links_data = get_all_links()
    if not links_data:
        print("No links found. Trying again")
        links_data = get_all_links()
        
    print(f"Total links found: {len(links_data)}")
    links = [f"https://getinstacash.in{link_dict['href']}" for link_dict in links_data if 'href' in link_dict]

    NUM_PROCESSES=10

    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.map(process_variant_link, links)  # Only pass URLs, not `driver`

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)  # Fix Windows issues
    run_scraping()
