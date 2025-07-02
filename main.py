from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import subprocess
import json
import os

service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)


def check_for_captcha():
    """Check if there's a captcha on the current page"""
    try:
        captcha_indicators = [
            "div[id*='captcha']",
            "iframe[src*='recaptcha']",
            "div[class*='captcha']",
            ".g-recaptcha",
            "form[action*='captcha']",
        ]

        for indicator in captcha_indicators:
            try:
                element = driver.find_element(By.CSS_SELECTOR, indicator)
                if element.is_displayed():
                    return True
            except NoSuchElementException:
                continue

        # Check page source for captcha text
        page_source = driver.page_source.lower()
        captcha_texts = [
            "captcha",
            "unusual traffic",
            "verify you're not a robot",
            "prove you're human",
        ]

        for text in captcha_texts:
            if text in page_source:
                return True

        return False
    except Exception as e:
        print(f"Error checking for captcha: {e}")
        return False


def solve_captcha_with_brightdata():
    """Use main2.py to solve captcha and get session data"""
    print("Captcha detected! Using Bright Data to solve...")

    try:
        # Save current URL and any necessary state
        current_url = driver.current_url
        current_cookies = driver.get_cookies()

        # Save state to file for main2.py to use
        state_data = {
            "url": current_url,
            "cookies": current_cookies,
            "task": "solve_captcha",
        }

        with open("session_state.json", "w") as f:
            json.dump(state_data, f)

        # Run main2.py to solve captcha
        print("Running Bright Data script...")
        result = subprocess.run(
            ["python", "main2.py"], capture_output=True, text=True, cwd=os.getcwd()
        )
        time.sleep(1)

        if result.returncode == 0:
            print("Bright Data script completed successfully")

            # Check if solution data was saved
            if os.path.exists("captcha_solution.json"):
                with open("captcha_solution.json", "r") as f:
                    solution_data = json.load(f)

                # Apply the solution (cookies, etc.) to current session
                if "cookies" in solution_data:
                    # Clear existing cookies and add new ones
                    driver.delete_all_cookies()
                    for cookie in solution_data["cookies"]:
                        try:
                            driver.add_cookie(cookie)
                        except Exception as e:
                            print(f"Could not add cookie: {e}")

                # Navigate to the URL from the solution
                if "final_url" in solution_data:
                    driver.get(solution_data["final_url"])

                print("Captcha solution applied successfully!")
                return True
            else:
                print("No solution data found from Bright Data script")
                return False
        else:
            print(f"Bright Data script failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"Error solving captcha with Bright Data: {e}")
        return False


driver.get("https://www.google.com")

# Handle cookie consent window
try:
    # Wait for cookie consent button to appear and click it
    wait = WebDriverWait(driver, 10)

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
    # Check for captcha before searching
    if check_for_captcha():
        if solve_captcha_with_brightdata():
            print("Captcha solved, continuing with search...")
        else:
            print("Failed to solve captcha, but continuing anyway...")

    input_element = driver.find_element(By.CLASS_NAME, "gLFyf")
    input_element.send_keys("Selenium WebDriver" + Keys.ENTER)
except NoSuchElementException:
    # Alternative selector for search box
    input_element = driver.find_element(By.NAME, "q")

    input_element.send_keys("Selenium WebDriver" + Keys.ENTER)


time.sleep(10)  # Wait for 5 seconds to see the page
driver.quit()  # Close the browser
