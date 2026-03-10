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

# ─────────────────────────────────────────────────────────────────────────────
# Logging setup — captured in console + HTML report
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Browser factory
# Window size set via launch args (1920x1080) — maximize_window() skipped
# because it causes ReadTimeoutError in headless Linux CI environments
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

    else:  # chrome default
        opts = ChromeOptions()
        opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--remote-debugging-port=9222")
        driver = webdriver.Chrome(options=opts)

    return driver


# ─────────────────────────────────────────────────────────────────────────────
# Pytest fixture — driver setup + teardown + failure screenshot
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture()
def driver(request, browser):
    drv = get_driver(browser)
    yield drv

    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        os.makedirs("screenshots", exist_ok=True)
        path = f"screenshots/failure_{browser}_{request.node.name}.png"
        drv.save_screenshot(path)
        log.error(f"FAILED — screenshot saved: {path}")

    drv.quit()
    log.info(f"Browser closed: {browser}")


# Hook — exposes rep_call to fixture for failure detection
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# ─────────────────────────────────────────────────────────────────────────────
# Validation helper — senior QA assertion wrapper
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
# TEST
# ─────────────────────────────────────────────────────────────────────────────
def test_link_and_dropdown(driver, browser):
    """
    Senior QA Test — Automation Practice Site
    Browsers : Chrome, Firefox (parametrized via conftest.py)
    Steps:
      1. Open website
      2. Maximise window (1920x1080 via launch args)
      3. Click 'Get Shortlisted...' link → new tab opens
      4. Verify new tab opened → switch BACK to main tab
      5. Select dropdown > Option2
    Validations:
      V1 — Page title is correct
      V2 — 'Get Shortlisted' link is visible and clickable
      V3 — New tab was opened after clicking the link
      V4 — Successfully switched back to the original main tab
      V5 — Dropdown is visible and enabled
      V6 — Option2 exists in dropdown options list
      V7 — Selected text matches 'Option2'
      V8 — DOM value attribute is set correctly
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
        # STEP 2: Maximise window
        # ─────────────────────────────────────────────────
        log.info(f"[{browser.upper()}] [STEP 2] Window maximised at 1920x1080 via launch args.")
        driver.save_screenshot(f"screenshots/step2_maximised_{browser}.png")

        # ─────────────────────────────────────────────────
        # STEP 3: Click "Get Shortlisted..." link (top right)
        # ─────────────────────────────────────────────────
        log.info(f"[{browser.upper()}] [STEP 3] Locating 'Get Shortlisted...' link...")

        # The link text may be truncated — use partial link text for resilience
        get_shortlisted_link = wait.until(
            EC.element_to_be_clickable(
                (By.PARTIAL_LINK_TEXT, "Get Shortlisted")
            )
        )
        link_text = get_shortlisted_link.text
        link_href = get_shortlisted_link.get_attribute("href")
        log.info(f"[{browser.upper()}]          Link text: '{link_text}'")
        log.info(f"[{browser.upper()}]          Link href: '{link_href}'")
        driver.save_screenshot(f"screenshots/step3_before_click_{browser}.png")

        # V2 — Link is visible and clickable
        validate(
            get_shortlisted_link.is_displayed() and get_shortlisted_link.is_enabled(),
            f"[{browser.upper()}] 'Get Shortlisted' link is visible and clickable",
            f"[{browser.upper()}] 'Get Shortlisted' link is NOT visible or not enabled"
        )

        # Record existing tabs before click
        tabs_before = driver.window_handles
        main_tab    = driver.current_window_handle
        log.info(f"[{browser.upper()}]          Tabs before click: {len(tabs_before)}")

        # Click the link
        get_shortlisted_link.click()
        log.info(f"[{browser.upper()}]          Clicked 'Get Shortlisted...' link.")
        time.sleep(2)  # allow new tab to open

        # ─────────────────────────────────────────────────
        # STEP 4: Verify new tab opened → switch back to main tab
        # ─────────────────────────────────────────────────
        log.info(f"[{browser.upper()}] [STEP 4] Checking for new tab and switching back...")

        tabs_after = driver.window_handles
        log.info(f"[{browser.upper()}]          Tabs after click: {len(tabs_after)}")

        # V3 — New tab was opened
        validate(
            len(tabs_after) > len(tabs_before),
            f"[{browser.upper()}] New tab opened successfully — total tabs: {len(tabs_after)}",
            f"[{browser.upper()}] No new tab was opened — still {len(tabs_after)} tab(s)"
        )

        # Identify and log the new tab
        new_tab = [t for t in tabs_after if t != main_tab][0]
        log.info(f"[{browser.upper()}]          New tab handle: {new_tab}")

        # Switch to new tab briefly to log its title
        driver.switch_to.window(new_tab)
        time.sleep(1)
        new_tab_title = driver.title
        new_tab_url   = driver.current_url
        log.info(f"[{browser.upper()}]          New tab title  : '{new_tab_title}'")
        log.info(f"[{browser.upper()}]          New tab URL    : '{new_tab_url}'")
        driver.save_screenshot(f"screenshots/step4_new_tab_{browser}.png")

        # Switch BACK to the main tab
        driver.switch_to.window(main_tab)
        time.sleep(0.5)
        current_title = driver.title
        log.info(f"[{browser.upper()}]          Switched back — current title: '{current_title}'")
        driver.save_screenshot(f"screenshots/step4_back_to_main_{browser}.png")

        # V4 — Successfully back on main tab
        validate(
            EXPECTED_TITLE_PART in current_title,
            f"[{browser.upper()}] Switched back to main tab — title: '{current_title}'",
            f"[{browser.upper()}] Failed to switch back — title: '{current_title}'"
        )

        print(f"\n  📌 [{browser.upper()}] New tab opened: '{new_tab_title}' | URL: {new_tab_url}")
        print(f"  📌 [{browser.upper()}] Switched back to main tab: '{current_title}'")

        # ─────────────────────────────────────────────────
        # STEP 5: Select Dropdown > Option2
        # ─────────────────────────────────────────────────
        log.info(f"[{browser.upper()}] [STEP 5] Locating dropdown...")
        dropdown_element = wait.until(
            EC.presence_of_element_located((By.ID, "dropdown-class-example"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown_element)
        time.sleep(0.5)

        # V5 — Dropdown visible and enabled
        validate(
            dropdown_element.is_displayed() and dropdown_element.is_enabled(),
            f"[{browser.upper()}] Dropdown is visible and enabled",
            f"[{browser.upper()}] Dropdown is not visible or not enabled"
        )

        select      = Select(dropdown_element)
        all_options = [opt.text for opt in select.options]
        log.info(f"[{browser.upper()}]          All options: {all_options}")
        print(f"\n  📋 [{browser.upper()}] Dropdown options found: {all_options}")

        # V6 — Option2 exists
        validate(
            EXPECTED_OPTION in all_options,
            f"[{browser.upper()}] '{EXPECTED_OPTION}' is present in options {all_options}",
            f"[{browser.upper()}] '{EXPECTED_OPTION}' NOT found in options: {all_options}"
        )

        # Select Option2
        log.info(f"[{browser.upper()}] [STEP 5] Selecting '{EXPECTED_OPTION}'...")
        select.select_by_visible_text(EXPECTED_OPTION)
        time.sleep(0.5)

        selected_text  = select.first_selected_option.text
        selected_value = select.first_selected_option.get_attribute("value")
        log.info(f"[{browser.upper()}]          Selected text : '{selected_text}'")
        log.info(f"[{browser.upper()}]          Selected value: '{selected_value}'")
        driver.save_screenshot(f"screenshots/step5_dropdown_selected_{browser}.png")

        # V7 — Text matches
        validate(
            selected_text == EXPECTED_OPTION,
            f"[{browser.upper()}] Selected text '{selected_text}' matches '{EXPECTED_OPTION}'",
            f"[{browser.upper()}] Selected text '{selected_text}' does NOT match '{EXPECTED_OPTION}'"
        )

        # V8 — DOM value set
        validate(
            selected_value is not None and len(selected_value) > 0,
            f"[{browser.upper()}] DOM value attribute is set: value='{selected_value}'",
            f"[{browser.upper()}] DOM value attribute is empty or None"
        )

        # ─────────────────────────────────────────────────
        # FINAL PRINT
        # ─────────────────────────────────────────────────
        print(f"\n  {'='*55}")
        print(f"  ✅ ALL STEPS PASSED")
        print(f"     Browser          : {browser.upper()}")
        print(f"     Link Clicked     : {link_text}")
        print(f"     New Tab Title    : {new_tab_title}")
        print(f"     Switched Back To : {current_title}")
        print(f"     Dropdown Selected: {selected_text} (value='{selected_value}')")
        print(f"     All Options      : {all_options}")
        print(f"  {'='*55}\n")

        log.info("=" * 60)
        log.info(f"  ✅ [{browser.upper()}] ALL STEPS COMPLETED SUCCESSFULLY")
        log.info(f"  Link: {link_text} | New tab: {new_tab_title}")
        log.info(f"  Dropdown: {selected_text} (value='{selected_value}')")
        log.info("=" * 60)

        driver.save_screenshot(f"screenshots/final_passed_{browser}.png")

    except Exception as e:
        log.error(f"[{browser.upper()}] [FAIL] {e}")
        driver.save_screenshot(f"screenshots/failure_{browser}.png")
        raise