# scraper.py
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

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

            # Click to expand the details section
            try:
                header = card.find_element(By.CSS_SELECTOR, ".exhibitor__header")
                # Check if the body is already visible
                body = card.find_element(By.CSS_SELECTOR, ".exhibitor__body")
                if not body.is_displayed():
                    driver.execute_script("arguments[0].click();", header)
                    # Wait for the body to become visible
                    WebDriverWait(driver, 5).until(
                        lambda d: body.is_displayed()
                    )
            except Exception as e:
                print(f"⚠️ Could not expand dropdown for card {i}: {e}")

            # Parse the HTML with BeautifulSoup
            soup = BeautifulSoup(card.get_attribute("outerHTML"), "html.parser")

            name = soup.select_one(".exhibitor__title h3")
            country = soup.select_one(".exhibitor__h-info .m-tag--country .m-tag__txt")
            location_zone = soup.select_one(".exhibitor__place p")
            description = soup.select_one(".exhibitor__description p")

            exhibitors.append({
                "Company Name": name.get_text(strip=True) if name else "N/A",
                "Country": country.get_text(strip=True) if country else "N/A",
                "Location & Zone": location_zone.get_text(strip=True).replace('\n', ' ').strip() if location_zone else "N/A",
                "Description": description.get_text(strip=True) if description else "N/A"
            })

            print(f"{i}: {exhibitors[-1]['Company Name']} | {exhibitors[-1]['Country']}")

        except Exception as e:
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
