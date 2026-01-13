import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ---------- CONFIG ----------
SEARCH_URL = "https://www.google.com/maps/search/hinjewadi+it+companies"
OUTPUT_FILE = "hinjewadi_open_it_companies.xlsx"
MAX_SCROLLS = 25
SCROLL_PAUSE = 2

# ---------- DRIVER SETUP ----------
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

driver.get(SEARCH_URL)
time.sleep(6)

# ---------- SCROLL RESULTS ----------
scrollable = driver.find_element(By.XPATH, "//div[contains(@aria-label,'Results for')]")

for _ in range(MAX_SCROLLS):
    driver.execute_script(
        "arguments[0].scrollTop = arguments[0].scrollHeight",
        scrollable
    )
    time.sleep(SCROLL_PAUSE)

# ---------- COLLECT PLACE LINKS ----------
place_links = set()
anchors = driver.find_elements(By.XPATH, "//a[contains(@class,'hfpxzc')]")

for a in anchors:
    href = a.get_attribute("href")
    if href and "/maps/place/" in href:
        place_links.add(href)

print(f"Found {len(place_links)} place URLs")

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

def is_permanently_closed():
    """Detect permanently or temporarily closed businesses"""
    try:
        status_text = driver.find_element(
            By.XPATH,
            "//*[contains(text(),'Permanently closed') or contains(text(),'Temporarily closed')]"
        ).text.lower()
        return True
    except:
        return False

# ---------- VISIT EACH PLACE ----------
rows = []
skipped_closed = 0

for idx, url in enumerate(place_links, start=1):
    print(f"Scraping {idx}/{len(place_links)}")
    driver.get(url)
    time.sleep(5)

    # 🚫 Skip closed companies
    if is_permanently_closed():
        skipped_closed += 1
        print("Skipped permanently closed company")
        continue

    row = {
        "Company Name": safe_text("//h1"),
        "Address": safe_text("//button[contains(@data-item-id,'address')]"),
        "Rating": safe_attr("//div[@role='img']", "aria-label"),
        "Reviews": safe_text("//button[contains(@aria-label,'reviews')]"),
        "Phone": safe_text("//button[contains(@data-item-id,'phone')]"),
        "Website": safe_attr("//a[contains(@data-item-id,'authority')]", "href"),
        "Maps URL": url,
        "Status": "Open"
    }

    rows.append(row)

# ---------- SAVE TO EXCEL ----------
df = pd.DataFrame(rows)
df.drop_duplicates(subset=["Company Name"], inplace=True)
df.to_excel(OUTPUT_FILE, index=False)

print(f"Saved {len(df)} OPEN companies")
print(f"Skipped {skipped_closed} permanently closed companies")
print(f"File: {OUTPUT_FILE}")

driver.quit()
