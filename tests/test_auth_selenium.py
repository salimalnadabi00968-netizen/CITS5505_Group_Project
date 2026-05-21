from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert


def dismiss_any_alert(driver, timeout=3):
    """Dismiss any native browser alert that may be present."""
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        Alert(driver).accept()
    except Exception:
        pass


# ------------------------------------------------------------------ #
# Selenium Test: Login with valid credentials redirects to home #127  #
# ------------------------------------------------------------------ #
class TestLoginRedirect:

    def test_login_valid_credentials_redirects_to_home(
        self, driver, base_url, selenium_user
    ):
        # Navigate to /login.html
        driver.get(f"{base_url}/login.html")

        # Wait for the login form to be visible
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "login-username"))
        )

        # Fill in valid username and password
        driver.find_element(By.ID, "login-username").send_keys(selenium_user.username)
        driver.find_element(By.ID, "login-password").send_keys("TestPassword123")

        # Click the submit button
        driver.find_element(
            By.CSS_SELECTOR, "#login-form button[type='submit']"
        ).click()

        # Dismiss any alert that may appear on successful login
        dismiss_any_alert(driver)

        # Verify the URL no longer contains "login"
        WebDriverWait(driver, 10).until(
            lambda d: "login" not in d.current_url
        )
        assert "login" not in driver.current_url

        # Verify the user is on the home page
        assert driver.current_url == f"{base_url}/" or ("/index" in driver.current_url)


# ------------------------------------------------------------------ #
# Selenium Test: Login with invalid credentials shows error    #128   #
# ------------------------------------------------------------------ #
class TestLoginInvalidCredentials:

    def test_login_invalid_credentials_stays_on_login(self, driver, base_url):
        # Navigate to /login.html
        driver.get(f"{base_url}/login.html")

        # Wait for the login form to be visible
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "login-username"))
        )

        # Fill in a non-existent username and wrong password
        driver.find_element(By.ID, "login-username").send_keys("nonexistentuser")
        driver.find_element(By.ID, "login-password").send_keys("wrongpassword123")

        # Click the submit button
        driver.find_element(
            By.CSS_SELECTOR, "#login-form button[type='submit']"
        ).click()

        # Dismiss any alert that may appear
        dismiss_any_alert(driver)

        # Verify the URL still contains "login"
        WebDriverWait(driver, 10).until(
            lambda d: "login" in d.current_url
        )
        assert "login" in driver.current_url

        # Verify an error message is visible and contains error text
        error_alert = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".alert"))
        )
        assert error_alert.is_displayed()
        assert "invalid" in error_alert.text.lower()
