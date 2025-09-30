# scraper.py
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://exhibitors.cphi.com/cpww25/"

def make_driver(headless=False):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def handle_cookie_banner(driver):
    """Waits for and clicks the cookie acceptance button."""
    try:
        cookie_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))
        )
        driver.execute_script("arguments[0].click();", cookie_button)
        print("🍪 Cookie banner handled.")
        time.sleep(2)
    except TimeoutException:
        print("ℹ️ Cookie banner not found or did not appear in time.")

def parse_card_details(driver, card):
    """Extracts all required information from a single exhibitor card element."""
    try:
        # Scroll the card into a stable position
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
        time.sleep(0.5)

        # --- Extract data from the card ---
        name = card.find_element(By.CSS_SELECTOR, ".exhibitor__title h3").text.strip()
        country = card.find_element(By.CSS_SELECTOR, ".exhibitor__h-info .m-tag--country .m-tag__txt").text.strip()

        location_zone = "N/A"
        description = "N/A"

        # Expand the card body to get location and description
        body = card.find_element(By.CSS_SELECTOR, ".exhibitor__body")
        if not body.is_displayed():
            header = card.find_element(By.CSS_SELECTOR, ".exhibitor__header")
            driver.execute_script("arguments[0].click();", header)
            WebDriverWait(driver, 5).until(lambda d: body.is_displayed())
        
        location_zone_element = body.find_element(By.CSS_SELECTOR, ".exhibitor__place p")
        location_zone = location_zone_element.text.strip().replace('\n', ' ').strip()

        description_element = body.find_element(By.CSS_SELECTOR, ".exhibitor__description p")
        description = description_element.text.strip()

        exhibitor_data = {
            "Company Name": name,
            "Country": country,
            "Location & Zone": location_zone,
            "Description": description
        }
        
        print(f"Scraped: {name} | {country} | {location_zone} | Description: {description[:30]}...")
        return exhibitor_data

    except Exception as e:
        print(f"❌ Error parsing a card: {e}")
        return None

def main():
    driver = make_driver(headless=False)
    driver.get(URL)
    
    handle_cookie_banner(driver)

    all_exhibitors_data = []
    processed_card_ids = set()

    while True:
        # Find all cards currently in the DOM
        cards = driver.find_elements(By.CSS_SELECTOR, ".exhibitor")
        
        new_cards_found_in_batch = 0
        for card in cards:
            try:
                # Use the unique data-id from a checkbox inside the card to track it
                card_id = card.find_element(By.CSS_SELECTOR, ".shortlist-checkbox").get_attribute("data-id")
                if card_id not in processed_card_ids:
                    processed_card_ids.add(card_id)
                    new_cards_found_in_batch += 1
                    
                    # Scrape the new card's details
                    exhibitor_data = parse_card_details(driver, card)
                    if exhibitor_data:
                        all_exhibitors_data.append(exhibitor_data)

            except NoSuchElementException:
                print("Could not find a unique ID for a card, it might be structured differently. Skipping.")
                continue
        
        print(f"Batch summary: Scraped {new_cards_found_in_batch} new exhibitors. Total scraped: {len(all_exhibitors_data)}")

        # Try to find and click the 'Show more results' button
        try:
            show_more_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".paging a.button"))
            )
            driver.execute_script("arguments[0].scrollIntoView();", show_more_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", show_more_button)
            print("\n⏳ Clicked 'Show more results', waiting for new cards...\n")
            time.sleep(3) # Wait for new cards to load
        except TimeoutException:
            print("✅ No more 'Show more results' button found. Scraping complete.")
            break

    print(f"\n✅ Extracted a total of {len(all_exhibitors_data)} exhibitors.")

    if all_exhibitors_data:
        df = pd.DataFrame(all_exhibitors_data)
        df.to_csv("exhibitors.csv", index=False)
        print("📂 Data successfully saved to exhibitors.csv")
    else:
        print("No exhibitors were extracted.")

    driver.quit()

if __name__ == "__main__":
    main()
