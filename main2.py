from selenium.webdriver import Remote, ChromeOptions
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json

AUTH = "brd-customer-hl_08a0a299-zone-scraping_browser1:rsmhf56qvcyj"
SBR_WEBDRIVER = f"https://{AUTH}@brd.superproxy.io:9515"


def handle_captcha_and_cookies(driver):
    """Handle both captcha and cookie consent using Bright Data's capabilities"""
    print("Checking for captcha and cookie consent...")
    
    # First, handle cookie consent
    try:
        wait = WebDriverWait(driver, 10)
        
        # Common selectors for Google's cookie consent
        cookie_selectors = [
            "button[id='L2AGLb']",  # "Accept all" button
            "button[aria-label='Accept all']",
            "//button[contains(text(), 'Accept all')]",
            "//button[contains(text(), 'I agree')]",
            "//div[@role='button'][contains(text(), 'Accept')]"
        ]
        
        cookie_accepted = False
        for selector in cookie_selectors:
            try:
                if selector.startswith("//"):
                    cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                else:
                    cookie_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                
                cookie_button.click()
                print("Cookie consent accepted!")
                cookie_accepted = True
                time.sleep(2)
                break
            except TimeoutException:
                continue
        
        if not cookie_accepted:
            print("No cookie consent popup found")
            
    except Exception as e:
        print(f"Error handling cookie consent: {e}")
    
    # Check for captcha - Bright Data should handle this automatically
    try:
        # Look for common captcha indicators
        captcha_indicators = [
            "div[id*='captcha']",
            "iframe[src*='recaptcha']",
            "div[class*='captcha']",
            ".g-recaptcha"
        ]
        
        captcha_found = False
        for indicator in captcha_indicators:
            try:
                captcha_element = driver.find_element(By.CSS_SELECTOR, indicator)
                if captcha_element.is_displayed():
                    print("Captcha detected! Bright Data should handle this automatically...")
                    captcha_found = True
                    # Wait longer for Bright Data to solve captcha
                    time.sleep(10)
                    break
            except NoSuchElementException:
                continue
        
        if not captcha_found:
            print("No captcha detected")
            
    except Exception as e:
        print(f"Error checking for captcha: {e}")


def main():
    print("Connecting to Browser API...")
    
    # Enhanced Chrome options for better captcha handling
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Add Bright Data specific options for captcha solving
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, "goog", "chrome")
    
    with Remote(sbr_connection, options=chrome_options) as driver:
        print("Connected! Navigating...")
        
        # Set a realistic user agent
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        driver.get("https://google.com")
        
        # Handle captcha and cookies
        handle_captcha_and_cookies(driver)
        
        print("Taking page screenshot to file page.png")
        driver.get_screenshot_as_file("./page.png")
        
        # Try to perform a search to test if captcha was solved
        try:
            print("Attempting to search...")
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.send_keys("Selenium WebDriver test")
            search_box.submit()
            
            # Wait for results
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            print("Search successful! Captcha was likely solved.")
            
        except Exception as e:
            print(f"Search failed: {e}")
        
        print("Navigated! Scraping page content...")
        html = driver.page_source
        
        # Check if we got blocked or captcha page
        if "captcha" in html.lower() or "unusual traffic" in html.lower():
            print("WARNING: Page still shows captcha or blocking message")
        else:
            print("SUCCESS: Page loaded successfully")
        
        # Save a portion of HTML for debugging
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Page source saved to page_source.html")


if __name__ == "__main__":
    main()
