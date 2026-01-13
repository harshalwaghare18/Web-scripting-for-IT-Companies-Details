import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

SEARCH_URL = "https://www.google.com/maps/search/baner+it+companies"
OUTPUT_FILE = "baner_it_companies.xlsx"
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

driver.get(SEARCH_URL)
time.sleep(6)


# ---------- SCROLL & COLLECT PLACE LINKS ----------
scrollable = driver.find_element(By.XPATH, "//div[contains(@aria-label,'Results for')]")

for _ in range(MAX_SCROLLS):
    driver.execute_script(
        "arguments[0].scrollTop = arguments[0].scrollHeight",
        scrollable
    )
    time.sleep(SCROLL_PAUSE)

place_links = set()
anchors = driver.find_elements(By.XPATH, "//a[contains(@class,'hfpxzc')]")

for a in anchors:
    link = a.get_attribute("href")
    if "/maps/place/" in link:
        place_links.add(link)

print(f"Found {len(place_links)} place URLs")



# ---------- VISIT EACH PLACE ----------
data = []

for idx, url in enumerate(place_links, start=1):
    driver.get(url)
    time.sleep(5)

    print(f"Scraping {idx}/{len(place_links)}")

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

    record = {
        "Company Name": safe_text("//h1"),
        "Address": safe_text("//button[contains(@data-item-id,'address')]"),
        "Rating": safe_attr("//div[@role='img']", "aria-label"),
        "Reviews": safe_text("//button[contains(@aria-label,'reviews')]"),
        "Phone": safe_text("//button[contains(@data-item-id,'phone')]"),
        "Website": safe_attr("//a[contains(@data-item-id,'authority')]", "href"),
        "Maps URL": url
    }

    data.append(record)


# ---------- SAVE TO EXCEL ----------
df = pd.DataFrame(data)
df.drop_duplicates(subset=["Company Name"], inplace=True)
df.to_excel(OUTPUT_FILE, index=False)

print(f"Saved {len(df)} companies to {OUTPUT_FILE}")

driver.quit()
