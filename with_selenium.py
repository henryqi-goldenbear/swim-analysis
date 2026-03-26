"""
Uses DuckDuckGo instead of Google - no bot detection, regular Selenium only.
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

driver = webdriver.Chrome()
# Use HTML version - static page, no JS, reliable selectors
driver.get("https://html.duckduckgo.com/html/")

search_box = driver.find_element(By.NAME, "q")
search_box.send_keys("gmail.com")
search_box.send_keys(Keys.RETURN)

# Wait for results page to load
WebDriverWait(driver, 10).until(lambda d: "gmail" in d.title.lower() or "duckduckgo" in d.title.lower())
# Click the first result link (HTML version uses class result__a)
first_result = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.result__a"))
)
first_result.click()
# wait for the new page to load
WebDriverWait(driver, 1000000).until(lambda d: "gmail.com" in d.title.lower())
# print the title of the new page
print(driver.title)
# Keep browser open until you press Enter
input("Press Enter to close the browser...")
driver.quit()