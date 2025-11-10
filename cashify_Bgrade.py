
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
import cashifymultiprocessing
from selenium.common.exceptions import TimeoutException
import multiprocessing
from itertools import islice
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from selenium.common.exceptions import StaleElementReferenceException
import mysql.connector
import os
from dotenv import load_dotenv

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
        CREATE TABLE IF NOT EXISTS cashify_bgrade_prices (
            model_name VARCHAR(255) NOT NULL,
            ram VARCHAR(10),
            rom VARCHAR(10),
            price VARCHAR(50),
            UNIQUE KEY unique_model (model_name, ram, rom)
        )
        """
        cursor.execute(create_table_query)

        # Insert or update query
        insert_query = """
        INSERT INTO cashify_bgrade_prices (model_name, ram, rom, price)
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
    brand_links = cashifymultiprocessing.scrape_brand_links()

    with multiprocessing.Pool(processes=8) as pool:  # Parallel scraping
        all_model_links = pool.map(cashifymultiprocessing.scrape_models_from_brand, brand_links)

    all_model_links = [link for sublist in all_model_links for link in sublist]  # Flatten list

    with multiprocessing.Pool(processes=8) as pool:
        all_variant_links = pool.map(cashifymultiprocessing.scrape_variants, all_model_links)

    all_variant_links = [link for sublist in all_variant_links for link in sublist]  # Flatten list

    return all_variant_links

def setup_driver():
    """Automatically sets up and returns a Selenium WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    #chrome_options.add_argument("headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())  
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver
    

def click_exact_value_button(driver, url):
    """Clicks the 'Get Exact Value' button on the given URL."""
    base_url = "https://www.cashify.in"  # Ensure full URLpython 
    full_url = url if url.startswith("http") else base_url + url  # Fix invalid URL
    driver.get(full_url)  # Open the correct URL
   
    wait = WebDriverWait(driver, 15)  # Increased wait time

    try:
        # Wait for the button to be clickable
        span_xpath = "//span[contains(@class, 'h3 text-primary-text-contrast') and text()='Get Exact Value']"
        button = wait.until(EC.element_to_be_clickable((By.XPATH, span_xpath + "/ancestor::button")))

        # Scroll to button & Click using JS (to prevent interception issues)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(1)  # Allow UI to stabilize
        driver.execute_script("arguments[0].click();", button)

        print("Clicked on 'Get Exact Value' button!")

        # Wait for page transition
        time.sleep(5)

    except Exception as e:
        print("Error clicking 'Get Exact Value' button:", e)

def click_answers(driver):
    """Clicks 'Yes', 'No', or 'Dual eSIM' based on the detected question."""
    wait = WebDriverWait(driver, 20)

    try:
        time.sleep(3)  # Allow page to load

        # Locate all sections dynamically
        sections_xpath = "//section[contains(@class, 'flex flex-col mb-5 w-full')]"
        sections = wait.until(EC.presence_of_all_elements_located((By.XPATH, sections_xpath)))

        print(f" Found {len(sections)} sections.")

        # Define logic for different responses
        yes_questions = [
            "1. Are you able to make and receive calls?",
            "2. Is your device's touch screen working properly?",
            "3. Is your phone's screen original?",
            "4. Is your device under manufacturer warranty?",
            "5. Do you have GST valid bill with the same IMEI?"
        ]
    
        dual_esim_question = "6. How many eSIMs does your device support?"  # Adjust the question text if needed

        # Last three questions to skip if not found
        skip_if_not_found = [
            "4. Is your device under manufacturer warranty?",
            "5. Do you have GST valid bill with the same IMEI?",
            "6. How many eSIMs does your device support?"
        ]

        # Loop through each section
        for idx, section_element in enumerate(sections):
            try:
                # Find the question inside this section
                question_xpath = ".//div[contains(@class, 'inherit w-full mt-5 mb-2 body1')]"
                question_div = section_element.find_element(By.XPATH, question_xpath)
                question_text = question_div.text.strip()

                print(f" Section {idx + 1}: Found Question - {question_text}")

                # Determine the correct answer
                if question_text in yes_questions:
                    button_text = "Yes"
                elif question_text == dual_esim_question:
                    button_text = "Dual eSIM"
                elif question_text in skip_if_not_found:
                    print(f" Skipping section {idx + 1} (allowed to skip)")
                    continue
                else:
                    print(f" Skipping section {idx + 1}, unknown question.")
                    continue

                # Locate the correct button
                button_xpath = f".//div[contains(@class, 'inherit body2 flex-1') and contains(., '{button_text}')]"
                button = section_element.find_element(By.XPATH, button_xpath)

                # Locate the checkbox (if applicable)
                checkbox_xpath = ".//div[contains(@class, 'rounded-full') and contains(@class, 'border')]"
                checkbox_elements = section_element.find_elements(By.XPATH, checkbox_xpath)

                # Scroll elements into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(0.5)
                if checkbox_elements:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox_elements[0])
                    time.sleep(0.5)

                # Click checkbox (if applicable) and button
                for attempt in range(3):
                    try:
                        if checkbox_elements:
                            driver.execute_script("arguments[0].click();", checkbox_elements[0])
                            print(f" Clicked checkbox in section {idx + 1}")
                        driver.execute_script("arguments[0].click();", button)
                        print(f" Clicked '{button_text}' in section {idx + 1}")
                        break  # Exit loop if successful
                    except Exception as e:
                        print(f" Attempt {attempt + 1}: Error clicking elements in section {idx + 1}: {e}")
                        time.sleep(1)
                else:
                    print(f" Failed to click elements in section {idx + 1}")

            except Exception as e:
                if any(q in str(e) for q in skip_if_not_found):
                    print(f" Skipping section {idx + 1} (question not found and allowed to skip)")
                    continue
                print(f" Error in section {idx + 1}: {e}")

    except Exception as e:
        print(f" Unexpected Error: {e}")

def click_continue_button(driver):
    """Clicks the 'Continue' button on the given URL."""
    wait = WebDriverWait(driver, 20)  # Increased wait time
    span_xpath = "//span[contains(@class, 'h3 text-primary-text-contrast') and text()='Continue']"
    
    for _ in range(3):  # Retry up to 3 times if StaleElementReferenceException occurs
        try:
            # Wait for the button to be clickable
            button = wait.until(EC.element_to_be_clickable((By.XPATH, span_xpath + "/ancestor::button")))

            # Scroll & Click using JS
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(1)  # Allow UI to stabilize
            driver.execute_script("arguments[0].click();", button)

            print("Clicked on 'Continue' button!")
            time.sleep(5)  # Wait for page transition
            return  # Exit function if successful

        except StaleElementReferenceException:
            print("StaleElementReferenceException occurred, retrying...")
            time.sleep(2)  # Short wait before retrying
        except Exception as e:
            print("Error clicking 'Continue' button:", e)
            break  # Exit loop if other error occurs

def screen_defects(driver):
    wait = WebDriverWait(driver, 15)
    defect_options = [
        "Broken/scratch on device screen",
        "Dead Spot/Visible line and Discoloration on screen",
        "Scratch/Dent on device body",
        "Device panel missing/broken"
    ]

    for defect in defect_options:
        condition_xpath = f"//div[contains(@class, 'inherit text-center caption p-4 native:px-4 native:py-3 flex items-center justify-center line-clamp-3') and contains(text(), '{defect}')]"
        
        for _ in range(3):  # Retry loop
            try:
                condition = wait.until(EC.element_to_be_clickable((By.XPATH, condition_xpath)))
                
                # Scroll & Click
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", condition)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", condition)

                print(f"Clicked on '{defect}'")
                break  # Break loop on success
            
            except StaleElementReferenceException:
                print(f"Stale element detected for '{defect}', retrying...")
                time.sleep(2)
            except Exception as e:
                print("Error clicking on screen defects:", e)
                break


def select_screen_physical_condition(driver):
    wait = WebDriverWait(driver, 15)  # Wait for element to appear

    try:
        # Locate the first matching element
        phycond_xpath = "//div[contains(@class, 'inherit text-center caption') and contains(text(), '1-2 scratches')]"
        phycond = wait.until(EC.element_to_be_clickable((By.XPATH, phycond_xpath)))

        # Scroll to the element & Click using JS
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", phycond)
        time.sleep(1)  # UI stabilization
        driver.execute_script("arguments[0].click();", phycond)

        print(" Clicked on '1-2 scratches on screen' button!")

    except Exception as e:
        print(" Error clicking 'physical condition' button:", e)


def screen_final_defects(driver):
    wait = WebDriverWait(driver, 15)

    try:
        # List of screen defect options to click
        defect_options = [
            "1-2 minor spots on screen",
            "Display faded along edges",
            "No Discoloration",
        ]

        for defect in defect_options:
            condition_xpath = f"//div[contains(@class, 'inherit text-center caption p-4 native:px-4 native:py-3 flex items-center justify-center line-clamp-3') and contains(text(), '{defect}')]"
            condition = wait.until(EC.element_to_be_clickable((By.XPATH, condition_xpath)))
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", condition)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", condition)  # JavaScript click to avoid interception issues
            
            print(f"Clicked on '{defect}'")

    except Exception as e:
        print("Error clicking on screen defects:", e)

def body_final_defects(driver):
    wait = WebDriverWait(driver, 15)

    try:
        # List of screen defect options to click
        defect_options = [
            "1-2 scratches",
            "1-2 minor dents",
        ]

        for defect in defect_options:
            condition_xpath = f"//div[contains(@class, 'inherit text-center caption p-4 native:px-4 native:py-3 flex items-center justify-center line-clamp-3') and contains(text(), '{defect}')]"
            condition = wait.until(EC.element_to_be_clickable((By.XPATH, condition_xpath)))
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", condition)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", condition)  # JavaScript click to avoid interception issues
            
            print(f"Clicked on '{defect}'")

    except Exception as e:
        print("Error clicking on screen defects:", e)

def more_defects(driver):
    wait = WebDriverWait(driver, 15)

    try:
        # List of screen defect options to click
        defect_options = [
            "Missing side or back panel",
            "Phone not bent",
        ]

        for defect in defect_options:
            condition_xpath = f"//div[contains(@class, 'inherit text-center caption p-4 native:px-4 native:py-3 flex items-center justify-center line-clamp-3') and contains(text(), '{defect}')]"
            condition = wait.until(EC.element_to_be_clickable((By.XPATH, condition_xpath)))
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", condition)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", condition)  # JavaScript click to avoid interception issues
            
            print(f"Clicked on '{defect}'")

    except Exception as e:
        print("Error clicking on screen defects:", e)


def functional_defects(driver):
    wait = WebDriverWait(driver, 15)

    try:
        # List of screen defect options to click
        defect_options = [
            "Camera Glass Broken"
        ]

        for defect in defect_options:
            condition_xpath = f"//div[contains(@class, 'inherit text-center caption p-4 native:px-4 native:py-3 flex items-center justify-center line-clamp-3') and contains(text(), '{defect}')]"
            condition = wait.until(EC.element_to_be_clickable((By.XPATH, condition_xpath)))
            
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", condition)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", condition)  # JavaScript click to avoid interception issues
            
            print(f"Clicked on '{defect}'")

    except Exception as e:
        print("Error clicking on screen defects:", e)

def enter_mobile_number(driver):
    """Enters a mobile number taken from the console and submits it."""
    wait = WebDriverWait(driver, 15)
    try:
        mobile_number = input("Enter your mobile number: ")
        input_xpath = "//input[@type='tel']"
        input_field = wait.until(EC.presence_of_element_located((By.XPATH, input_xpath)))
        input_field.send_keys(mobile_number)
        print("Mobile number entered successfully.")
        time.sleep(1)

        continue_button_xpath = "//button[contains(@class, 'bg-primary')]//div[contains(text(), 'CONTINUE')]"
        continue_button = wait.until(EC.element_to_be_clickable((By.XPATH, continue_button_xpath)))

        # Scroll into view and click using JavaScript
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", continue_button)
        time.sleep(1)  # Short delay before clicking
        driver.execute_script("arguments[0].click();", continue_button)

        print("Clicked the CONTINUE button successfully.")
    except Exception as e:
        print("Error entering mobile number:", e)


def enter_otp(driver):
    """Enters the OTP manually after user inputs it."""
    time.sleep(5)
    otp = input("Enter the OTP received: ")
    otp_input_xpath = "//input[@type='tel']"
    otp_field = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, otp_input_xpath)))
    otp_field.send_keys(otp)
    print("OTP entered and verified.")

    # Save session cookies
    time.sleep(5)
    with open("session.pkl", "wb") as f:
        pickle.dump(driver.get_cookies(), f)
    print("Session saved.")


def extract_device_details(driver):
    """Extracts device name, RAM, ROM, and price from the page."""
    wait = WebDriverWait(driver, 20)

    for _ in range(3):  # Retry loop
        try:
            # Extract device name and RAM/ROM from h1 tag
            h1_xpath = "//h1[contains(@class, 'h1')]"
            h1_element = wait.until(EC.presence_of_element_located((By.XPATH, h1_xpath)))
            h1_text = h1_element.text.strip()

            # Use regex to split device name and RAM/ROM
            match = re.match(r"(.+?)\s*\((\d+ GB)/(\d+ GB)\)", h1_text)
            if match:
                device_name = match.group(1).strip()
                ram = match.group(2)
                rom = match.group(3)
            else:
                device_name, ram, rom = h1_text, "Unknown", "Unknown"

            # Extract price from span tag
            price_xpath = "//span[contains(@class, 'extraFont1 text-error')]"
            price = "Price Not Found"

            for _ in range(3):  # Retry loop for price
                try:
                    price_element = wait.until(EC.presence_of_element_located((By.XPATH, price_xpath)))
                    price = price_element.text.strip() if price_element else "Price Not Found"
                    break
                except StaleElementReferenceException:
                    print("Stale element detected for price, retrying...")
                    time.sleep(2)
                except TimeoutException:
                    print("Price not found for this variant.")
                    break

            # Print extracted values
            print(f"Device Name: {device_name}")
            print(f"RAM: {ram}")
            print(f"ROM: {rom}")
            print(f"Price: {price}")
            store_device_details_in_db(device_name, ram, rom, price)
            return device_name, ram, rom, price

        except StaleElementReferenceException:
            print("Stale element detected while extracting device details, retrying...")
            time.sleep(2)
        except Exception as e:
            print("Error extracting device details:", e)
            return None, None, None, None

def login(driver):
    """Logs into the Cashify website and returns session cookies."""
    base_url = "https://www.cashify.in"
    driver.get(base_url)

    wait = WebDriverWait(driver, 15)
    span_xpath = "//span[contains(@class, 'inherit text-cta-text-contrast text-md font-medium py-1.5 px-4') and text()='Login']"
    button_xpath = span_xpath + "/ancestor::button"

    try:
        for _ in range(3):  # Retry up to 3 times
            try:
                button = wait.until(EC.element_to_be_clickable((By.XPATH, button_xpath)))

                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", button)
                print("Clicked on 'Login' button!")

                #  Wait for Mobile Number Input Field to Appear
                mobile_input_xpath = "//input[@type='tel']"
                wait.until(EC.presence_of_element_located((By.XPATH, mobile_input_xpath)))

                enter_mobile_number(driver)  # Implement this function to input mobile number
                enter_otp(driver)  # Implement this function to input OTP

                time.sleep(5)  # Allow login to complete
                cookies = driver.get_cookies()  # Extract session cookies
                print(cookies)
                print("Login successful. Cookies saved.")

                return cookies  # Return cookies for reuse

            except Exception as e:
                print("Error during login:", e)


    except Exception as e:
        print("Error clicking 'Login' button:", e)

    return None  # Return None if login fails

def load_cookies(driver, cookies):
    """Load session cookies into a new WebDriver instance."""
    driver.get("https://www.cashify.in")  # Open base page first
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()
    time.sleep(3)  # Allow session to load

def process_variant_link(url, cookies):
    """Each process runs independently but shares the same session via cookies."""
    driver = setup_driver()
    load_cookies(driver, cookies)  # Load shared session

    final_url = "https://www.cashify.in" + url
    try:
        print(f"Processing: {final_url}")
        driver.get(final_url)
        time.sleep(5)  # Allow page to load

        # Perform scraping actions
        click_exact_value_button(driver, final_url)
        click_answers(driver)
        click_continue_button(driver)
        screen_defects(driver)
        click_continue_button(driver)
        select_screen_physical_condition(driver)
        click_continue_button(driver)
        screen_final_defects(driver)
        click_continue_button(driver)
        body_final_defects(driver)
        click_continue_button(driver)
        more_defects(driver)
        click_continue_button(driver)
        functional_defects(driver)
        click_continue_button(driver)
        click_continue_button(driver)

        # Extract data
        extract_device_details(driver)

    except Exception as e:
        print(f"Error processing {final_url}: {e}")

    finally:
        driver.quit()

def run_scraping():
    """Use multiprocessing to open links in different processes while maintaining session."""
    driver = setup_driver()
    cookies = login(driver)  # Perform login once and get session cookies

    if not cookies:
        print("Login failed. Exiting.")
        driver.quit()
        return

    links = get_all_links()  # Fetch all variant links
    driver.quit()  # Close initial session after extracting cookies

    if not links:
        print("No links found.")
        return

    NUM_PROCESSES = 10 # Run 4 parallel browser instances
    with multiprocessing.Pool(NUM_PROCESSES) as pool:
        pool.starmap(process_variant_link, [(url, cookies) for url in links])

if __name__ == "__main__":
    run_scraping()