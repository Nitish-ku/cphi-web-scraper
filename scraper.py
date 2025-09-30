# scraper.py
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
        time.sleep(2)  # Give time for the banner to disappear
    except Exception as e:
        print(f"ℹ️ Cookie banner not found or could not be clicked. Continuing... Error: {e}")


def load_all_exhibitors(driver):
    """Keep clicking 'Show more results' until all exhibitors are loaded."""
    while True:
        try:
            show_more = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".paging a.button"))
            )
            driver.execute_script("arguments[0].click();", show_more)
            time.sleep(2)
        except:
            print("✅ All exhibitors loaded.")
            break

def parse_exhibitors(driver):
    exhibitors = []
    cards = driver.find_elements(By.CSS_SELECTOR, ".exhibitor")
    print(f"DEBUG: Found {len(cards)} exhibitor cards")

    for i, card in enumerate(cards, start=1):
        try:
            # Scroll into view to ensure it's interactable
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
            time.sleep(0.5)

            # --- Data from visible part (Header) ---
            name = card.find_element(By.CSS_SELECTOR, ".exhibitor__title h3").text.strip()
            country = card.find_element(By.CSS_SELECTOR, ".exhibitor__h-info .m-tag--country .m-tag__txt").text.strip()

            # --- Data from collapsible part (Body) ---
            location_zone = "N/A"
            description = "N/A"
            
            try:
                header = card.find_element(By.CSS_SELECTOR, ".exhibitor__header")
                body = card.find_element(By.CSS_SELECTOR, ".exhibitor__body")
                if not body.is_displayed():
                    driver.execute_script("arguments[0].click();", header)
                    # Wait for the body to become visible
                    WebDriverWait(driver, 5).until(
                        lambda d: body.is_displayed()
                    )
                
                # Now that it's visible, extract the data using Selenium
                location_zone_element = body.find_element(By.CSS_SELECTOR, ".exhibitor__place p")
                location_zone = location_zone_element.text.strip().replace('\n', ' ').strip()

                description_element = body.find_element(By.CSS_SELECTOR, ".exhibitor__description p")
                description = description_element.text.strip()

            except Exception as e:
                print(f"⚠️ Could not get description/location for card {i} ({name}): {e}")

            exhibitors.append({
                "Company Name": name,
                "Country": country,
                "Location & Zone": location_zone,
                "Description": description
            })

            # This print statement is for user feedback in the terminal
            print(f"{i}: {name} | {country} | {location_zone} | Description found: {description != 'N/A'}")

        except Exception as e:
            # This will catch errors if the main card structure is different
            print(f"❌ Error parsing card {i}: {e}")

    return exhibitors


def main():
    driver = make_driver(headless=False)
    driver.get(URL)
    
    handle_cookie_banner(driver)

    print("⏳ Loading all exhibitors...")
    load_all_exhibitors(driver)

    exhibitors = parse_exhibitors(driver)
    print(f"✅ Extracted {len(exhibitors)} exhibitors")

    if exhibitors:
        df = pd.DataFrame(exhibitors)
        df.to_csv("exhibitors.csv", index=False)
        print("📂 Data saved to exhibitors.csv")
    else:
        print("No exhibitors were extracted.")


    driver.quit()

if __name__ == "__main__":
    main()
