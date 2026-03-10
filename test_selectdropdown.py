import os
import time
import logging
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

# ─────────────────────────────────────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Browser factory
# ─────────────────────────────────────────────────────────────────────────────
def get_driver(browser_name: str):
    browser_name = browser_name.lower()
    log.info(f"Launching browser: {browser_name}")

    if browser_name == "firefox":
        opts = FirefoxOptions()
        opts.add_argument("--headless")
        opts.add_argument("--width=1920")
        opts.add_argument("--height=1080")
        driver = webdriver.Firefox(options=opts)

    elif browser_name == "edge":
        opts = EdgeOptions()
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Edge(options=opts)

    else:  # chrome (default)
        opts = ChromeOptions()
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=opts)

    driver.maximize_window()
    return driver


# ─────────────────────────────────────────────────────────────────────────────
# Driver fixture — scoped per test, browser comes from conftest parametrize
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture()
def driver(request, browser):
    drv = get_driver(browser)
    yield drv

    # Screenshot on failure
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        os.makedirs("screenshots", exist_ok=True)
        path = f"screenshots/failure_{browser}_{request.node.name}.png"
        drv.save_screenshot(path)
        log.error(f"FAILED screenshot saved: {path}")

    drv.quit()
    log.info(f"Browser closed: {browser}")


# Hook to expose rep_call to fixture
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# ─────────────────────────────────────────────────────────────────────────────
# Validation helper
# ─────────────────────────────────────────────────────────────────────────────
def validate(condition: bool, pass_msg: str, fail_msg: str):
    if condition:
        print(f"\n  ✅ PASS — {pass_msg}")
        log.info(f"VALIDATION PASSED: {pass_msg}")
    else:
        print(f"\n  ❌ FAIL — {fail_msg}")
        log.error(f"VALIDATION FAILED: {fail_msg}")
        raise AssertionError(f"FAILED: {fail_msg}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST — runs once per browser (chrome, firefox, edge)
# ─────────────────────────────────────────────────────────────────────────────
def test_select_dropdown_option2(driver, browser):
    """
    Senior QA Test — Automation Practice Site
    Runs on: Chrome, Firefox, Edge (parametrized via conftest.py)
    Steps:
      1. Open website
      2. Maximise window
      3. Select dropdown > Option2
    Validations:
      V1 — Page title is correct
      V2 — Dropdown is present and enabled
      V3 — Option2 exists in the dropdown options list
      V4 — After selection, selected value equals 'Option2'
      V5 — DOM value attribute confirms selection
    """
    wait = WebDriverWait(driver, 15)
    os.makedirs("screenshots", exist_ok=True)

    EXPECTED_OPTION     = "Option2"
    EXPECTED_TITLE_PART = "Practice Page"

    try:
        # ─────────────────────────────────────────────────
        # STEP 1: Open the website
        # ─────────────────────────────────────────────────
        log.info(f"[{browser.upper()}] [STEP 1] Opening website...")
        driver.get("https://rahulshettyacademy.com/AutomationPractice/")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        actual_title = driver.title
        log.info(f"[{browser.upper()}]          Page title: '{actual_title}'")
        driver.save_screenshot(f"screenshots/step1_opened_{browser}.png")

        # V1 — Page title
        validate(
            EXPECTED_TITLE_PART in actual_title,
            f"[{browser.upper()}] Page title contains '{EXPECTED_TITLE_PART}' → '{actual_title}'",
            f"[{browser.upper()}] Page title '{actual_title}' does not contain '{EXPECTED_TITLE_PART}'"
        )

        # ─────────────────────────────────────────────────
        # STEP 2: Maximise the window
        # ─────────────────────────────────────────────────
        log.info(f"[{browser.upper()}] [STEP 2] Maximising window...")
        driver.maximize_window()
        driver.set_window_size(1920, 1080)
        log.info(f"[{browser.upper()}]          Window size: {driver.get_window_size()}")
        driver.save_screenshot(f"screenshots/step2_maximised_{browser}.png")

        # ─────────────────────────────────────────────────
        # STEP 3: Locate dropdown
        # ─────────────────────────────────────────────────
        log.info(f"[{browser.upper()}] [STEP 3] Locating dropdown...")
        dropdown_element = wait.until(
            EC.presence_of_element_located((By.ID, "dropdown-class-example"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown_element)
        time.sleep(0.5)

        # V2 — Dropdown visible and enabled
        validate(
            dropdown_element.is_displayed() and dropdown_element.is_enabled(),
            f"[{browser.upper()}] Dropdown is visible and enabled",
            f"[{browser.upper()}] Dropdown is not visible or not enabled"
        )

        # ─────────────────────────────────────────────────
        # STEP 4: Inspect options
        # ─────────────────────────────────────────────────
        select     = Select(dropdown_element)
        all_options = [opt.text for opt in select.options]
        log.info(f"[{browser.upper()}]          All options: {all_options}")
        print(f"\n  📋 [{browser.upper()}] Dropdown options found: {all_options}")

        # V3 — Option2 exists in list
        validate(
            EXPECTED_OPTION in all_options,
            f"[{browser.upper()}] '{EXPECTED_OPTION}' is present in options {all_options}",
            f"[{browser.upper()}] '{EXPECTED_OPTION}' NOT found in options: {all_options}"
        )

        # ─────────────────────────────────────────────────
        # STEP 5: Select Option2
        # ─────────────────────────────────────────────────
        log.info(f"[{browser.upper()}] [STEP 5] Selecting '{EXPECTED_OPTION}'...")
        select.select_by_visible_text(EXPECTED_OPTION)
        time.sleep(0.5)

        selected_text  = select.first_selected_option.text
        selected_value = select.first_selected_option.get_attribute("value")
        log.info(f"[{browser.upper()}]          Selected text : '{selected_text}'")
        log.info(f"[{browser.upper()}]          Selected value: '{selected_value}'")
        driver.save_screenshot(f"screenshots/step3_dropdown_selected_{browser}.png")

        # V4 — Visible text matches
        validate(
            selected_text == EXPECTED_OPTION,
            f"[{browser.upper()}] Selected text '{selected_text}' matches '{EXPECTED_OPTION}'",
            f"[{browser.upper()}] Selected text '{selected_text}' does NOT match '{EXPECTED_OPTION}'"
        )

        # V5 — DOM value attribute set
        validate(
            selected_value is not None and len(selected_value) > 0,
            f"[{browser.upper()}] DOM value attribute is set: value='{selected_value}'",
            f"[{browser.upper()}] DOM value attribute is empty or None"
        )

        # ─────────────────────────────────────────────────
        # FINAL PRINT
        # ─────────────────────────────────────────────────
        print(f"\n  {'='*52}")
        print(f"  ✅ Dropdown Option2 Selected")
        print(f"     Browser        : {browser.upper()}")
        print(f"     Selected Text  : {selected_text}")
        print(f"     Selected Value : {selected_value}")
        print(f"     All Options    : {all_options}")
        print(f"  {'='*52}\n")

        log.info("=" * 55)
        log.info(f"  ✅ [{browser.upper()}] DROPDOWN OPTION2 SELECTED SUCCESSFULLY")
        log.info(f"  Text: {selected_text} | Value: {selected_value}")
        log.info("=" * 55)

        driver.save_screenshot(f"screenshots/final_passed_{browser}.png")

    except Exception as e:
        log.error(f"[{browser.upper()}] [FAIL] {e}")
        driver.save_screenshot(f"screenshots/failure_{browser}.png")
        raise