from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import requests
import os
import time
import logging
from datetime import datetime
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Step 1: Set up the webdriver (Edge in this example)
current_dir = os.path.dirname(os.path.abspath(__file__))
webdriver_path = os.path.join(current_dir, 'msedgedriver.exe')
download_dir = r"C:\Users\npath\Desktop\19-cv-1046"
if not os.path.exists(webdriver_path):
    raise FileNotFoundError(f"The WebDriver executable was not found at path: {webdriver_path}")

options = webdriver.EdgeOptions()
options.add_argument('--headless')  # Run in headless mode to improve performance
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_experimental_option('prefs', {
    "download.default_directory": download_dir,  # Set default download directory
    "download.prompt_for_download": False,       # Avoid prompting for download
    "plugins.always_open_pdf_externally": True   # Open PDFs directly in the browser
})

service = Service(webdriver_path)
driver = webdriver.Edge(service=service, options=options)
driver.implicitly_wait(10)

try:
    # Step 2: Open the website
    driver.get("https://publicaccess.galvestoncountytx.gov/PublicAccess/default.aspx")
    logging.info("Website opened successfully.")

    # Step 3: Click on "Civil and Family Case Records"
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.LINK_TEXT, "Civil and Family Case Records"))).click()
    logging.info("Clicked on 'Civil and Family Case Records' link.")

    # Step 4: Select the first radio button
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "(//input[@type='radio'])[1]"))).click()
    logging.info("Selected the first radio button.")

    # Step 5: Enter the case number
    case_number = "19-cv-1046"
    case_number_input = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "CaseSearchValue")))
    case_number_input.send_keys(case_number)
    case_number_input.send_keys(Keys.ENTER)
    logging.info(f"Entered case number: {case_number}")

    # Step 6: Click on the case link
    case_link = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'CaseDetail.aspx')]")))
    case_link.click()
    logging.info("Clicked on the case link.")

    # Step 7: Click on the link under 'CASE SUMMARY' to access the full list of filed documents
    case_summary_element = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'CPR.aspx')]"))
    )
    case_summary_element.click()
    logging.info("Clicked on the case link to access the full list of filed documents.")

    # Step 8: Locate all filed documents and download them
    time.sleep(10)  # Increase delay to ensure page is fully loaded
    document_rows = WebDriverWait(driver, 40).until(
        EC.presence_of_all_elements_located((By.XPATH, "//tr[td/a[contains(@href, 'ViewDocumentFragment.aspx')]]"))
    )

    for document_row in document_rows:
        try:
            document_link = document_row.find_element(By.XPATH, ".//a[contains(@href, 'ViewDocumentFragment.aspx')]")
            date_cell = document_row.find_element(By.XPATH, ".//td[1]")
            document_date_raw = date_cell.text.strip()

            # Use regex to extract the date in MM/DD/YYYY format
            date_match = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", document_date_raw)
            if date_match:
                document_date = datetime.strptime(date_match.group(1), "%m/%d/%Y").strftime("%Y.%m.%d")
            else:
                raise ValueError(f"Failed to extract date from text: {document_date_raw}")

            document_title = document_link.text.strip().replace("/", "-").replace(" ", "_")

            # Navigate to the document fragment link
            document_url = document_link.get_attribute('href')
            driver.get(document_url)
            logging.info("Navigated to the document fragment link.")

            # Wait for the document to load and locate the download link
            download_link = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '.pdf')]"))
            )
            ActionChains(driver).move_to_element(download_link).perform()  # Scroll into view if needed
            pdf_url = download_link.get_attribute('href')

            # Download the file using requests with retry logic and User-Agent
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
            retries = 3
            for attempt in range(retries):
                try:
                    response = requests.get(pdf_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        file_name = os.path.join(download_dir, f"{document_date}_{document_title}.pdf")
                        with open(file_name, 'wb') as file:
                            file.write(response.content)
                        logging.info(f"Downloaded document: {file_name}")
                        break
                    else:
                        logging.error(f"Failed to download the document. HTTP Status Code: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    logging.error(f"Attempt {attempt + 1} failed with error: {e}")
                    if attempt < retries - 1:
                        time.sleep(5)
                    else:
                        logging.error("All download attempts failed.")
        except Exception as e:
            logging.error(f"Failed to locate or download a document: {e}")

except Exception as e:
    logging.error(f"Failed to complete the process: {e}")
    driver.save_screenshot(os.path.join(current_dir, 'error_screenshot.png'))
    with open(os.path.join(current_dir, 'error_page_source.html'), 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    logging.info("Saved screenshot and page source of the error state.")

finally:
    driver.quit()
    logging.info("Browser closed successfully.")
