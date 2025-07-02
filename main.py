from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)

driver.get("https://www.duckduckgo.com")

# Handle cookie consent window
try:
    # Wait for cookie consent button to appear and click it
    wait = WebDriverWait(driver, 3)

    # Common selectors for Google's cookie consent
    cookie_selectors = [
        "button[id='L2AGLb']",  # "Accept all" button
        "button[aria-label='Accept all']",
        "button[data-ved]",  # Generic Google button
        "//button[contains(text(), 'Accept all')]",  # XPath for text content
        "//button[contains(text(), 'I agree')]",
        "//div[@role='button'][contains(text(), 'Accept')]",
    ]

    cookie_accepted = False
    for selector in cookie_selectors:
        try:
            if selector.startswith("//"):
                # XPath selector
                cookie_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
            else:
                # CSS selector
                cookie_button = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )

            cookie_button.click()
            print("Cookie consent accepted!")
            cookie_accepted = True
            time.sleep(2)  # Wait a moment for the popup to disappear
            break
        except TimeoutException:
            continue

    if not cookie_accepted:
        print("No cookie consent popup found or couldn't accept it")

except Exception as e:
    print(f"Error handling cookie consent: {e}")

# Now proceed with the search
try:
    input_element = driver.find_element(By.CLASS_NAME, "gLFyf")
    input_element.send_keys("Selenium WebDriver" + Keys.ENTER)
except NoSuchElementException:
    # Alternative selector for search box

    input_element = driver.find_element(By.NAME, "q")
    input_element.send_keys("Selenium WebDriver" + Keys.ENTER)
    link = driver.find_element(By.PARTIAL_LINK_TEXT, "Selenium")
    link.click()


time.sleep(10)  # Wait for 5 seconds to see the page
driver.quit()  # Close the browser
