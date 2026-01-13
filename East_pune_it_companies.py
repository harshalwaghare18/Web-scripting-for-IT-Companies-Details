
# This is the script for the product base companies and other east pune side companies
# Area coverd :
# Viman Nagar
# Yerwada
# Kalyani Nagar
# Magarpatta
# Hadapsar


import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ---------- CONFIG ----------
AREAS = [
    "viman nagar it companies",
    "yerwada it companies",
    "kalyani nagar it companies",
    "koregaon park it companies",
    "magarpatta it companies"
]

OUTPUT_FILE = "East_pune_it_companies.xlsx"
MAX_SCROLLS = 20
SCROLL_PAUSE = 2

# ---------- DRIVER SETUP ----------
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# ---------- HELPERS ----------
def safe_text(xpath):
    try:
        return driver.find_element(By.XPATH, xpath).text
    except:
        return ""

def safe_attr(xpath, attr):
    try:
        return driver.find_element(By.XPATH, xpath).get_attribute(attr)
    except:
        return ""

def is_closed():
    try:
        driver.find_element(
            By.XPATH,
            "//*[contains(text(),'Permanently closed') or contains(text(),'Temporarily closed')]"
        )
        return True
    except:
        return False

all_rows = []
skipped_closed = 0

# ---------- LOOP AREAS ----------
for area in AREAS:
    search_url = f"https://www.google.com/maps/search/{area.replace(' ', '+')}"
    print(f"\nSearching area: {area}")

    driver.get(search_url)
    time.sleep(6)

    # Scroll results
    scrollable = driver.find_element(By.XPATH, "//div[contains(@aria-label,'Results for')]")
    for _ in range(MAX_SCROLLS):
        driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight",
            scrollable
        )
        time.sleep(SCROLL_PAUSE)

    # Collect place URLs
    place_links = set()
    anchors = driver.find_elements(By.XPATH, "//a[contains(@class,'hfpxzc')]")
    for a in anchors:
        href = a.get_attribute("href")
        if href and "/maps/place/" in href:
            place_links.add(href)

    print(f"Found {len(place_links)} places in {area}")

    # Visit each place
    for idx, url in enumerate(place_links, start=1):
        print(f"Scraping {idx}/{len(place_links)}")
        driver.get(url)
        time.sleep(5)

        if is_closed():
            skipped_closed += 1
            continue

        row = {
            "Company Name": safe_text("//h1"),
            "Area": area.title(),
            "Address": safe_text("//button[contains(@data-item-id,'address')]"),
            "Rating": safe_attr("//div[@role='img']", "aria-label"),
            "Reviews": safe_text("//button[contains(@aria-label,'reviews')]"),
            "Phone": safe_text("//button[contains(@data-item-id,'phone')]"),
            "Website": safe_attr("//a[contains(@data-item-id,'authority')]", "href"),
            "Maps URL": url,
            "Status": "Open"
        }

        all_rows.append(row)

# ---------- SAVE TO EXCEL ----------
df = pd.DataFrame(all_rows)
df.drop_duplicates(subset=["Company Name"], inplace=True)
df.to_excel(OUTPUT_FILE, index=False)

print("\n========== DONE ==========")
print(f"Saved {len(df)} OPEN companies")
print(f"Skipped {skipped_closed} closed companies")
print(f"File: {OUTPUT_FILE}")

driver.quit()
