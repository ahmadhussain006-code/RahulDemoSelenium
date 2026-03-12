# Think and act like you are a senior software tester. Write a script to automate. Additionally, I require an HTML report, cross-browser testing, screenshots, and a test report for all browsers on GitHub, including all logs of this website, using the PyCharm framework with Selenium and Python. Also, generate a .yml file script to push files to GitHub accordingly.
# 1. Open this website- https://rahulshettyacademy.com/AutomationPractice/
# 2. Maximise the window
# 3. click on "open" window, a window will be opened, after that switch to the main page and continue on the other script.
# 4. click on "open" tab, a new tab will be opened, after that switch to the main page and continue on the other script.
# 3. Select dropdown > option2


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
# Window size set via launch args — maximize_window() NOT called
# (causes ReadTimeoutError on headless Linux CI)
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
# Pytest fixture — driver setup / teardown / failure screenshot
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
def test_window_tab_dropdown(driver, browser):
    """
    Senior QA Test — Automation Practice Site
    Browsers : Chrome, Firefox (parametrized via conftest.py)

    Steps:
      1. Open website
      2. Maximise window (1920x1080 via launch args)
      3. Click 'Open' button under Window section
             → new browser WINDOW opens
             → log new window title/URL
             → switch BACK to main window
      4. Click 'Open' button under Tab section
             → new browser TAB opens
             → log new tab title/URL
             → switch BACK to main tab
      5. Select Dropdown > Option2

    Validations:
      V1  — Page title is correct
      V2  — Window 'Open' button is visible & clickable
      V3  — New window was opened
      V4  — New window has a valid title/URL
      V5  — Switched back successfully to main window
      V6  — Tab 'Open' button is visible & clickable
      V7  — New tab was opened
      V8  — New tab has a valid title/URL
      V9  — Switched back successfully to main tab
      V10 — Dropdown is visible & enabled
      V11 — Option2 exists in dropdown list
      V12 — Selected text matches 'Option2'
      V13 — DOM value attribute is set correctly
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

        # V1 — Page title correct
        validate(
            EXPECTED_TITLE_PART in actual_title,
            f"[{browser.upper()}] Page title contains '{EXPECTED_TITLE_PART}' → '{actual_title}'",
            f"[{browser.upper()}] Page title '{actual_title}' does not contain '{EXPECTED_TITLE_PART}'"
        )

        # ─────────────────────────────────────────────────
        # STEP 2: Maximise window
        # ─────────────────────────────────────────────────
        log.info(f"[{browser.upper()}] [STEP 2] Window set to 1920x1080 via launch arguments.")
        driver.save_screenshot(f"screenshots/step2_maximised_{browser}.png")

        # ─────────────────────────────────────────────────
        # STEP 3: Click "Open" button → New WINDOW
        # Section label: "Switch To Window Example"
        # The button ID is: openwindow
        # ─────────────────────────────────────────────────
        log.info(f"[{browser.upper()}] [STEP 3] Locating 'Open Window' button...")

        window_open_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "openwindow"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", window_open_btn)
        time.sleep(0.5)

        # V2 — Window Open button visible & clickable
        validate(
            window_open_btn.is_displayed() and window_open_btn.is_enabled(),
            f"[{browser.upper()}] 'Open Window' button is visible and clickable",
            f"[{browser.upper()}] 'Open Window' button is NOT visible or not enabled"
        )

        main_window      = driver.current_window_handle
        handles_before   = set(driver.window_handles)
        log.info(f"[{browser.upper()}]          Handles before click: {len(handles_before)}")

        window_open_btn.click()
        log.info(f"[{browser.upper()}]          Clicked 'Open Window' button.")
        time.sleep(2)

        handles_after = set(driver.window_handles)
        log.info(f"[{browser.upper()}]          Handles after click : {len(handles_after)}")

        # V3 — New window opened
        validate(
            len(handles_after) > len(handles_before),
            f"[{browser.upper()}] New window opened — total handles: {len(handles_after)}",
            f"[{browser.upper()}] No new window detected — still {len(handles_after)} handle(s)"
        )

        # Switch to new window
        new_window = (handles_after - handles_before).pop()
        driver.switch_to.window(new_window)
        time.sleep(1)

        new_window_title = driver.title
        new_window_url   = driver.current_url
        log.info(f"[{browser.upper()}]          New window title : '{new_window_title}'")
        log.info(f"[{browser.upper()}]          New window URL   : '{new_window_url}'")
        driver.save_screenshot(f"screenshots/step3_new_window_{browser}.png")

        # V4 — New window has content
        validate(
            len(new_window_url) > 0,
            f"[{browser.upper()}] New window URL is valid: '{new_window_url}'",
            f"[{browser.upper()}] New window URL is empty"
        )

        print(f"\n  🪟 [{browser.upper()}] New WINDOW → Title: '{new_window_title}' | URL: {new_window_url}")

        # Switch BACK to main window
        driver.switch_to.window(main_window)
        time.sleep(0.5)
        back_title = driver.title
        log.info(f"[{browser.upper()}]          Switched back — current title: '{back_title}'")
        driver.save_screenshot(f"screenshots/step3_back_to_main_window_{browser}.png")

        # V5 — Back on main window
        validate(
            EXPECTED_TITLE_PART in back_title,
            f"[{browser.upper()}] Switched back to main window — title: '{back_title}'",
            f"[{browser.upper()}] NOT on main window — title: '{back_title}'"
        )
        print(f"  ✅ [{browser.upper()}] Switched back to main window: '{back_title}'")

        # ─────────────────────────────────────────────────
        # STEP 4: Click "Open" button → New TAB
        # Section label: "Switch To Tab Example"
        # The button ID is: opentab
        # ─────────────────────────────────────────────────
        log.info(f"[{browser.upper()}] [STEP 4] Locating 'Open Tab' button...")

        tab_open_btn = wait.until(
            EC.element_to_be_clickable((By.ID, "opentab"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", tab_open_btn)
        time.sleep(0.5)

        # V6 — Tab Open button visible & clickable
        validate(
            tab_open_btn.is_displayed() and tab_open_btn.is_enabled(),
            f"[{browser.upper()}] 'Open Tab' button is visible and clickable",
            f"[{browser.upper()}] 'Open Tab' button is NOT visible or not enabled"
        )

        main_tab       = driver.current_window_handle
        tabs_before    = set(driver.window_handles)
        log.info(f"[{browser.upper()}]          Tabs before click: {len(tabs_before)}")

        tab_open_btn.click()
        log.info(f"[{browser.upper()}]          Clicked 'Open Tab' button.")
        time.sleep(2)

        tabs_after = set(driver.window_handles)
        log.info(f"[{browser.upper()}]          Tabs after click : {len(tabs_after)}")

        # V7 — New tab opened
        validate(
            len(tabs_after) > len(tabs_before),
            f"[{browser.upper()}] New tab opened — total handles: {len(tabs_after)}",
            f"[{browser.upper()}] No new tab detected — still {len(tabs_after)} handle(s)"
        )

        # Switch to new tab
        new_tab = (tabs_after - tabs_before).pop()
        driver.switch_to.window(new_tab)
        time.sleep(1)

        new_tab_title = driver.title
        new_tab_url   = driver.current_url
        log.info(f"[{browser.upper()}]          New tab title : '{new_tab_title}'")
        log.info(f"[{browser.upper()}]          New tab URL   : '{new_tab_url}'")
        driver.save_screenshot(f"screenshots/step4_new_tab_{browser}.png")

        # V8 — New tab has content
        validate(
            len(new_tab_url) > 0,
            f"[{browser.upper()}] New tab URL is valid: '{new_tab_url}'",
            f"[{browser.upper()}] New tab URL is empty"
        )

        print(f"\n  🗂️  [{browser.upper()}] New TAB    → Title: '{new_tab_title}' | URL: {new_tab_url}")

        # Switch BACK to main tab
        driver.switch_to.window(main_tab)
        time.sleep(0.5)
        back_tab_title = driver.title
        log.info(f"[{browser.upper()}]          Switched back — current title: '{back_tab_title}'")
        driver.save_screenshot(f"screenshots/step4_back_to_main_tab_{browser}.png")

        # V9 — Back on main tab
        validate(
            EXPECTED_TITLE_PART in back_tab_title,
            f"[{browser.upper()}] Switched back to main tab — title: '{back_tab_title}'",
            f"[{browser.upper()}] NOT on main tab — title: '{back_tab_title}'"
        )
        print(f"  ✅ [{browser.upper()}] Switched back to main tab: '{back_tab_title}'")

        # ─────────────────────────────────────────────────
        # STEP 5: Select Dropdown > Option2
        # ─────────────────────────────────────────────────
        log.info(f"[{browser.upper()}] [STEP 5] Locating dropdown...")
        dropdown_element = wait.until(
            EC.presence_of_element_located((By.ID, "dropdown-class-example"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown_element)
        time.sleep(0.5)

        # V10 — Dropdown visible and enabled
        validate(
            dropdown_element.is_displayed() and dropdown_element.is_enabled(),
            f"[{browser.upper()}] Dropdown is visible and enabled",
            f"[{browser.upper()}] Dropdown is not visible or not enabled"
        )

        select      = Select(dropdown_element)
        all_options = [opt.text for opt in select.options]
        log.info(f"[{browser.upper()}]          All options: {all_options}")
        print(f"\n  📋 [{browser.upper()}] Dropdown options found: {all_options}")

        # V11 — Option2 exists
        validate(
            EXPECTED_OPTION in all_options,
            f"[{browser.upper()}] '{EXPECTED_OPTION}' is present in options {all_options}",
            f"[{browser.upper()}] '{EXPECTED_OPTION}' NOT found in options: {all_options}"
        )

        log.info(f"[{browser.upper()}]          Selecting '{EXPECTED_OPTION}'...")
        select.select_by_visible_text(EXPECTED_OPTION)
        time.sleep(0.5)

        selected_text  = select.first_selected_option.text
        selected_value = select.first_selected_option.get_attribute("value")
        log.info(f"[{browser.upper()}]          Selected text : '{selected_text}'")
        log.info(f"[{browser.upper()}]          Selected value: '{selected_value}'")
        driver.save_screenshot(f"screenshots/step5_dropdown_selected_{browser}.png")

        # V12 — Text matches
        validate(
            selected_text == EXPECTED_OPTION,
            f"[{browser.upper()}] Selected text '{selected_text}' matches '{EXPECTED_OPTION}'",
            f"[{browser.upper()}] Selected text '{selected_text}' does NOT match '{EXPECTED_OPTION}'"
        )

        # V13 — DOM value set
        validate(
            selected_value is not None and len(selected_value) > 0,
            f"[{browser.upper()}] DOM value attribute is set: value='{selected_value}'",
            f"[{browser.upper()}] DOM value attribute is empty or None"
        )

        # ─────────────────────────────────────────────────
        # FINAL PRINT SUMMARY
        # ─────────────────────────────────────────────────
        print(f"\n  {'='*60}")
        print(f"  ✅ ALL STEPS PASSED — {browser.upper()}")
        print(f"  {'─'*60}")
        print(f"  STEP 1 → Website opened      : '{actual_title}'")
        print(f"  STEP 2 → Window maximised    : 1920x1080")
        print(f"  STEP 3 → New WINDOW opened   : '{new_window_title}'")
        print(f"           URL                 : {new_window_url}")
        print(f"           Switched back to    : '{back_title}'")
        print(f"  STEP 4 → New TAB opened      : '{new_tab_title}'")
        print(f"           URL                 : {new_tab_url}")
        print(f"           Switched back to    : '{back_tab_title}'")
        print(f"  STEP 5 → Dropdown selected   : '{selected_text}' (value='{selected_value}')")
        print(f"           All options         : {all_options}")
        print(f"  {'='*60}\n")

        log.info("=" * 65)
        log.info(f"  ✅ [{browser.upper()}] ALL STEPS COMPLETED SUCCESSFULLY")
        log.info(f"  Window → {new_window_title} | Tab → {new_tab_title} | Dropdown → {selected_text}")
        log.info("=" * 65)

        driver.save_screenshot(f"screenshots/final_passed_{browser}.png")

    except Exception as e:
        log.error(f"[{browser.upper()}] [FAIL] {e}")
        driver.save_screenshot(f"screenshots/failure_{browser}.png")
        raise