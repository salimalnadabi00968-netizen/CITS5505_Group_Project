import os
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert

SAMPLE_IMAGE_PATH = os.path.abspath("tests/Funny_dogs_2.jpg")

def dismiss_any_alert(driver, timeout=3):
    """Dismiss any alert that may be present."""
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        Alert(driver).accept()
    except Exception:
        pass


def safe_get(driver, url):
    """Navigate to a URL and dismiss any unexpected alerts."""
    driver.get(url)
    dismiss_any_alert(driver)


def login(driver, base_url, selenium_user):
    """Helper function to log in the test user."""
    driver.get(f"{base_url}/login.html")

    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, "login-username"))
    )

    driver.find_element(By.ID, "login-username").send_keys(selenium_user.username)
    driver.find_element(By.ID, "login-password").send_keys("TestPassword123")
    driver.find_element(By.CSS_SELECTOR, "#login-form button[type='submit']").click()

    # Handle the "Logged in successfully" alert
    try:
        WebDriverWait(driver, 10).until(EC.alert_is_present())
        Alert(driver).accept()
    except Exception:
        pass

    # Wait until we are no longer on the login page
    WebDriverWait(driver, 10).until(
        lambda d: "login" not in d.current_url
    )


def fill_checkin_form(driver, include_location=True):
    """Helper function to fill in the check-in form."""
    WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, "title"))
    )

    # Fill in place name
    driver.find_element(By.ID, "place-name").send_keys("Test Place Name")

    # Fill in the title
    driver.find_element(By.ID, "title").send_keys("Test Checkin Place")

    # Select a category
    Select(driver.find_element(By.ID, "category")).select_by_value("nature")

    # Fill in the description
    driver.find_element(By.ID, "description").send_keys("This is a test description.")

    # Click 4th star using JavaScript to avoid interception
    stars = driver.find_elements(By.CSS_SELECTOR, "#star-picker i")
    star = stars[3]
    driver.execute_script("arguments[0].scrollIntoView(true);", star)
    driver.execute_script("arguments[0].click();", star)

    # Upload a photo
    photo_input = driver.find_element(By.ID, "photo-input")
    driver.execute_script("arguments[0].style.display = 'block';", photo_input)
    photo_input.send_keys(SAMPLE_IMAGE_PATH)

    if include_location:
        driver.find_element(By.ID, "pick-on-map").click()

        WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, "map-picker"))
        )

        map_element = driver.find_element(By.ID, "map-picker")
        action = ActionChains(driver)
        action.move_to_element(map_element).click().perform()

        WebDriverWait(driver, 5).until(
            lambda d: d.find_element(By.ID, "lat_input").get_attribute("value") != ""
        )


def js_click(driver, element):
    """Click an element using JavaScript to bypass interception."""
    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    driver.execute_script("arguments[0].click();", element)


def click_submit_button(driver):
    """Submit through the form button while avoiding viewport interception."""
    submit_button = driver.find_element(
        By.CSS_SELECTOR, "#checkin-form button[type='submit']"
    )
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", submit_button
    )
    driver.execute_script("arguments[0].click();", submit_button)

# ------------------------------------------------------------------ #
# Selenium Test 1: Submit new checkin form successfully                #
# ------------------------------------------------------------------ #
class TestCheckinFormSubmit:

    def test_submit_checkin_form_successfully(self, driver, base_url, selenium_user):
        login(driver, base_url, selenium_user)
        safe_get(driver, f"{base_url}/new-checkin.html")
        fill_checkin_form(driver, include_location=True)

        # Set lat/lng directly via JavaScript to bypass JS validation
        driver.execute_script("""
            document.getElementById('lat_input').value = '-31.9505';
            document.getElementById('lng_input').value = '115.8605';
            document.getElementById('rating-value').value = '4';
        """)

        click_submit_button(driver)

        WebDriverWait(driver, 10).until(
            lambda d: "new-checkin" not in d.current_url
        )

        assert driver.current_url == f"{base_url}/" or "/index" in driver.current_url


# ------------------------------------------------------------------ #
# Selenium Test 2: Delete a checkin from profile page                  #
# ------------------------------------------------------------------ #
class TestCheckinDelete:

    def test_delete_checkin_from_profile(self, driver, base_url, selenium_user):
        """
        A logged-in user should be able to delete their own checkin
        from the profile page and it should no longer appear.
        """
        # First create a checkin to delete
        login(driver, base_url, selenium_user)
        safe_get(driver, f"{base_url}/new-checkin.html")
        fill_checkin_form(driver, include_location=True)

        driver.execute_script("""
            document.getElementById('lat_input').value = '-31.9505';
            document.getElementById('lng_input').value = '115.8605';
            document.getElementById('rating-value').value = '4';
        """)

        click_submit_button(driver)

        # Wait for redirect to home page after checkin created
        WebDriverWait(driver, 10).until(
            lambda d: "new-checkin" not in d.current_url
        )

        # Navigate to profile page
        safe_get(driver, f"{base_url}/profile.html")

        # Wait for profile page to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "btn_delete"))
        )

        # Count checkins before deleting
        checkins_before = len(driver.find_elements(By.CLASS_NAME, "card-title"))

        # Click the first delete button
        delete_btn = driver.find_element(By.CLASS_NAME, "btn_delete")
        driver.execute_script("arguments[0].click();", delete_btn)

        # Wait for redirect back to profile
        WebDriverWait(driver, 5).until(
            EC.url_contains("profile")
        )

        # Verify the count decreased by 1
        checkins_after = len(driver.find_elements(By.CLASS_NAME, "card-title"))
        assert checkins_after == checkins_before - 1
