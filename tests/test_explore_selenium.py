from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


def test_search_returns_results_page(driver, base_url):
    driver.get(f"{base_url}/explore.html")

    search_input = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input[placeholder='Search by place name or description...']")
        )
    )
    search_input.clear()
    search_input.send_keys("park")
    search_input.send_keys(Keys.ENTER)

    WebDriverWait(driver, 10).until(
        lambda browser: "/search" in browser.current_url and "q=park" in browser.current_url
    )

    assert "/search" in driver.current_url
    assert "q=park" in driver.current_url


def test_category_filter_updates_url(driver, base_url):
    driver.get(f"{base_url}/explore.html")

    category_select = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "select[name='category']"))
    )
    Select(category_select).select_by_value("nature")

    filter_form = driver.find_element(By.CSS_SELECTOR, "form.filter-bar")
    filter_form.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    WebDriverWait(driver, 10).until(
        lambda browser: "category=nature" in browser.current_url
    )

    assert "category=nature" in driver.current_url
