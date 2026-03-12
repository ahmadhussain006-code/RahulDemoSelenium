"""

"""

import os
import sys
import time
import logging
from datetime import datetime

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    NoSuchElementException,
)
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager


# ══════════════════════════════════════════════════════════════════════════════
#  Constants
# ══════════════════════════════════════════════════════════════════════════════

BASE_URL = "https://rahulshettyacademy.com/AutomationPractice/"
TIMEOUT  = 25
PAUSE    = 1.5


# ══════════════════════════════════════════════════════════════════════════════
#  Logger
# ══════════════════════════════════════════════════════════════════════════════

def create_logger() -> logging.Logger:
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("rahul_shetty_selenium")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s  [%(levelname)8s]  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_name = datetime.now().strftime("logs/test_run_%Y%m%d_%H%M%S.log")
        fh = logging.FileHandler(file_name, encoding="utf-8")
        fh.setFormatter(formatter)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger

log = create_logger()


# ══════════════════════════════════════════════════════════════════════════════
#  Screenshot helper
# ══════════════════════════════════════════════════════════════════════════════

def take_screenshot(driver, label: str, browser: str, status: str = "STEP") -> str:
    os.makedirs("screenshots", exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"screenshots/{label}_{browser.upper()}_{status}_{ts}.png"
    try:
        driver.save_screenshot(path)
        log.info("  📸  [%s] → %s", status, path)
    except Exception as exc:
        log.warning("  Screenshot failed: %s", exc)
    return path


# ══════════════════════════════════════════════════════════════════════════════
#  Locators
# ══════════════════════════════════════════════════════════════════════════════

class L:
    # ── AutomationPractice main page ──────────────────────────────────────────
    IFRAME_HEADING  = (By.XPATH, "//*[normalize-space()='iFrame Example']")

    # ✅ FIX 1: By.ID is correct — not By.CSS_SELECTOR
    IFRAME          = (By.ID, "courses-iframe")

    # ── Inside iframe ─────────────────────────────────────────────────────────
    VIEW_ALL_COURSES = (By.XPATH,
        "//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
        "'abcdefghijklmnopqrstuvwxyz'),'view all courses')] | "
        "//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
        "'abcdefghijklmnopqrstuvwxyz'),'view all courses')] | "
        "//*[contains(@class,'see-all-btn')]")

    # ✅ FIX 3: "Search Course" is the actual placeholder on legacy site
    SEARCH_FIELD = (By.XPATH,
        "//input[contains(@placeholder,'Search product')] | "
        "//input[contains(@placeholder,'search product')] | "
        "//input[contains(@placeholder,'Search Course')]  | "
        "//input[contains(@placeholder,'search course')]")

    # Radix UI author combobox (confirmed from Playwright script)
    AUTHORS_BTN  = (By.CSS_SELECTOR, "button[aria-label='Filter by author']")
    RAYMOND_OPT  = (By.XPATH, "//*[@role='option' and contains(.,'Raymond')]")

    # Radix UI sort combobox
    SORT_BUTTONS = (By.CSS_SELECTOR,
        "button[aria-label='Product sort options'], "
        "button[aria-label='Sort products']")
    NAME_AZ_OPT  = (By.XPATH,
        "//*[@role='option' and (contains(.,'Name') or contains(.,'A-Z'))]")

    # No-products message
    NO_MATCH_TEXT = (By.XPATH,
        "//*[contains(text(),'No products match your current filters')]")

    # ── Main page — Step 10 ───────────────────────────────────────────────────
    MAIN_DROPDOWN = (By.ID, "dropdown-class-example")


# ══════════════════════════════════════════════════════════════════════════════
#  Switch-into-iframe helper
#  ✅ FIX 2: EC.frame_to_be_available_and_switch_to_it waits for frame
#            readiness AND switches atomically — handles stale frame perfectly
# ══════════════════════════════════════════════════════════════════════════════

def switch_into_courses_iframe(driver, timeout: int = TIMEOUT) -> None:
    """Switch Selenium context into iframe#courses-iframe safely."""
    driver.switch_to.default_content()
    WebDriverWait(driver, timeout).until(
        EC.frame_to_be_available_and_switch_to_it(L.IFRAME)
    )
    log.info("  ✓ Switched into iframe#courses-iframe")


# ══════════════════════════════════════════════════════════════════════════════
#  Driver factory
# ══════════════════════════════════════════════════════════════════════════════

_HEADLESS = bool(os.environ.get("CI") or
                 os.environ.get("HEADLESS", "").lower() == "true")


def _build_chrome() -> webdriver.Chrome:
    opts = ChromeOptions()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1920,1080")
    if _HEADLESS:
        opts.add_argument("--headless=new")
    d = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=opts)
    d.implicitly_wait(2)   # ✅ FIX 5: allows DOM to settle after SPA transitions
    log.info("✓  Chrome WebDriver ready")
    return d


def _build_firefox() -> webdriver.Firefox:
    opts = FirefoxOptions()
    if _HEADLESS:
        opts.add_argument("-headless")
    d = webdriver.Firefox(
        service=FirefoxService(GeckoDriverManager().install()), options=opts)
    d.set_window_size(1920, 1080)
    d.implicitly_wait(2)   # ✅ FIX 5
    log.info("✓  Firefox WebDriver ready")
    return d


# ══════════════════════════════════════════════════════════════════════════════
#  Pytest fixtures + hooks (inline — no conftest.py needed)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(params=["chrome", "firefox"], scope="function")
def driver(request):
    browser: str = request.param
    request.node._browser_name = browser
    log.info("=================================================================")
    log.info("  BROWSER : %s", browser.upper())
    log.info("  TEST    : %s", request.node.name)
    log.info("=================================================================")
    drv = _build_chrome() if browser == "chrome" else _build_firefox()
    yield drv
    log.info("  Quitting %s WebDriver …", browser.upper())
    try:
        drv.quit()
    except Exception:
        pass


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report  = outcome.get_result()
    if report.when == "call" and report.failed:
        drv = item.funcargs.get("driver")
        if drv:
            browser = getattr(item.node, "_browser_name", "unknown")
            path    = take_screenshot(drv, "FAILURE", browser, status="FAIL")
            try:
                from pytest_html import extras as _ex
                extra = getattr(report, "extras", [])
                extra.append(_ex.image(path))
                report.extras = extra
            except ImportError:
                pass


def pytest_html_report_title(report):
    report.title = "Selenium Cross-Browser Report – Rahul Shetty Academy"


def pytest_configure(config):
    import platform
    config._metadata = getattr(config, "_metadata", {})
    config._metadata.update({
        "Project"    : "Rahul Shetty Academy – Automation Practice",
        "URL"        : BASE_URL,
        "Browsers"   : "Chrome, Firefox",
        "Python"     : sys.version.split()[0],
        "Platform"   : platform.platform(),
        "Executed At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


# ══════════════════════════════════════════════════════════════════════════════
#  Test Class
# ══════════════════════════════════════════════════════════════════════════════

class TestAutomationPracticeWorkflow:

    def _wait(self, driver, timeout: int = TIMEOUT) -> WebDriverWait:
        return WebDriverWait(driver, timeout)

    def _scroll_to(self, driver, element) -> None:
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center', inline:'nearest'});",
            element)
        time.sleep(0.8)

    def _safe_click(self, driver, element) -> None:
        try:
            element.click()
        except (ElementClickInterceptedException, StaleElementReferenceException):
            driver.execute_script("arguments[0].click();", element)

    def _shot(self, driver, name: str, browser: str, shot_type: str = "STEP") -> None:
        take_screenshot(driver, name, browser, status=shot_type)

    def _find_visible(self, driver, locator) -> list:
        """Return all visible elements matching locator."""
        return [el for el in driver.find_elements(*locator) if el.is_displayed()]

    # ─────────────────────────────────────────────────────────────────────────

    def test_full_workflow(self, driver, request):
        browser = getattr(request.node, "_browser_name", "unknown")
        wait    = self._wait(driver)
        os.makedirs("reports", exist_ok=True)

        try:
            # ── STEP 1 & 2 · Open website + maximise ─────────────────────────
            log.info("── STEP 1-2 : Open website and maximise window ──")
            driver.get(BASE_URL)
            driver.maximize_window()
            time.sleep(PAUSE)

            assert "rahulshettyacademy" in driver.current_url.lower(), \
                f"Page did not load. URL={driver.current_url}"
            log.info("  ✓ Title : %s", driver.title)
            log.info("  ✓ URL   : %s", driver.current_url)
            self._shot(driver, "01_homepage_loaded", browser)

            # ── STEP 3 · Scroll to iFrame Example section ─────────────────────
            log.info("── STEP 3 : Scroll to iFrame Example section ──")
            heading = wait.until(EC.presence_of_element_located(L.IFRAME_HEADING))
            self._scroll_to(driver, heading)
            log.info("  ✓ Scrolled to iFrame Example heading")
            self._shot(driver, "02_iframe_section", browser)

            # ── STEP 4 · Switch into iframe → scroll sidebar ──────────────────
            log.info("── STEP 4 : Switch into iframe and scroll sidebar ──")

            # ✅ FIX 2: EC.frame_to_be_available_and_switch_to_it handles
            #           frame readiness + switching atomically
            switch_into_courses_iframe(driver, TIMEOUT)
            time.sleep(1)

            # Scroll the sidebar inside the iframe
            sidebar = None
            for sel in [
                (By.CSS_SELECTOR, "[class*='sidebar']"),
                (By.CSS_SELECTOR, "[class*='left']"),
                (By.CSS_SELECTOR, "ul"),
                (By.TAG_NAME,     "body"),
            ]:
                visible = self._find_visible(driver, sel)
                if visible:
                    sidebar = visible[0]
                    break

            if sidebar:
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight;", sidebar)
                log.info("  ✓ Sidebar scrolled inside iframe")
            else:
                driver.execute_script("window.scrollTo(0, 500);")
                log.info("  ✓ iframe window scrolled (fallback)")

            time.sleep(PAUSE)
            self._shot(driver, "03_iframe_sidebar_scrolled", browser)

            # ── STEP 5 · Click "View All Courses" ─────────────────────────────
            log.info("── STEP 5 : Open courses listing ──")

            # Check if search field is already visible (courses already loaded)
            search_already_visible = False
            try:
                probe = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(L.SEARCH_FIELD))
                search_already_visible = probe.is_displayed()
            except TimeoutException:
                pass

            if search_already_visible:
                log.info("  ✓ Courses listing already visible — skip button click")
            else:
                # Find and click the visible "View All Courses" button
                visible_btns = self._find_visible(driver, L.VIEW_ALL_COURSES)
                if not visible_btns:
                    raise NoSuchElementException(
                        "No visible 'View All Courses' button found inside iframe")

                view_btn = visible_btns[0]
                self._scroll_to(driver, view_btn)
                self._safe_click(driver, view_btn)
                log.info("  ✓ Clicked 'View All Courses'")

                # ✅ FIX 2: After SPA navigation inside iframe, re-enter frame
                log.info("  ↺ Re-entering iframe after internal navigation …")
                time.sleep(2)
                switch_into_courses_iframe(driver, TIMEOUT)
                log.info("  ✓ Re-entered iframe — context is fresh")

            # Confirm search field is now present
            wait.until(EC.presence_of_element_located(L.SEARCH_FIELD))
            time.sleep(PAUSE)
            self._shot(driver, "04_after_view_courses_click", browser)

            # ── STEP 6 · Enter "Test" in Search Product Names field ────────────
            log.info("── STEP 6 : Enter 'Test' in Search Product Names field ──")
            search = wait.until(EC.presence_of_element_located(L.SEARCH_FIELD))
            self._scroll_to(driver, search)
            wait.until(EC.visibility_of(search))
            search.clear()
            search.send_keys("Test")
            time.sleep(PAUSE)

            assert search.get_attribute("value") == "Test", \
                "Search text was not entered properly"
            log.info("  ✓ Typed 'Test' in search field")
            self._shot(driver, "05_search_text_entered", browser)

            # ── STEP 7 · "All Authors" combobox → "Raymond" ───────────────────
            log.info("── STEP 7 : Select 'Raymond' from All Authors dropdown ──")
            authors_btn = wait.until(EC.element_to_be_clickable(L.AUTHORS_BTN))
            self._scroll_to(driver, authors_btn)
            self._safe_click(driver, authors_btn)
            time.sleep(1)

            raymond = wait.until(EC.element_to_be_clickable(L.RAYMOND_OPT))
            self._safe_click(driver, raymond)
            time.sleep(PAUSE)
            log.info("  ✓ Selected 'Raymond'")
            self._shot(driver, "06_author_selected", browser)

            # ── STEP 8 · "Recommended" combobox → "Name(A-Z)" ─────────────────
            log.info("── STEP 8 : Select 'Name(A-Z)' from Recommended dropdown ──")
            visible_sort = self._find_visible(driver, L.SORT_BUTTONS)
            assert visible_sort, "No visible sort dropdown button found"
            sort_btn = visible_sort[-1]   # last visible one (Playwright used .last)

            self._scroll_to(driver, sort_btn)
            try:
                ActionChains(driver).move_to_element(sort_btn).click().perform()
            except Exception:
                self._safe_click(driver, sort_btn)
            time.sleep(1)

            name_az = wait.until(EC.element_to_be_clickable(L.NAME_AZ_OPT))
            self._safe_click(driver, name_az)
            time.sleep(PAUSE)
            log.info("  ✓ Selected 'Name(A-Z)'")
            self._shot(driver, "07_sort_selected", browser)

            # ── STEP 9 · Assert + PRINT "No products match …" ─────────────────
            log.info("── STEP 9 : Verify no-match message ──")
            no_match = wait.until(EC.visibility_of_element_located(L.NO_MATCH_TEXT))
            msg      = no_match.text.strip()

            # Prominent console print (as required by spec)
            border = "=" * 60
            print(f"\n{border}")
            print(f"  BROWSER : {browser.upper()}")
            print(f"  STEP 9  : Text verified on page")
            print(f'  TEXT    : "{msg}"')
            print(f"{border}\n")

            log.info("  ✓ Final text shown : %s", msg)
            assert msg == "No products match your current filters", \
                f"Unexpected final message: '{msg}'"
            self._shot(driver, "08_no_match_message", browser)

            # ── STEP 10 · Switch back to main page → Select option2 ───────────
            log.info("── STEP 10 : Select option2 from main-page dropdown ──")
            driver.switch_to.default_content()

            main_dropdown = wait.until(EC.element_to_be_clickable(L.MAIN_DROPDOWN))
            self._scroll_to(driver, main_dropdown)

            sel = Select(main_dropdown)
            # ✅ FIX 4: use select_by_value("option2") — visible text is "Option2"
            sel.select_by_value("option2")
            selected_text = sel.first_selected_option.text.strip()

            log.info("  ✓ Main dropdown selected : %s", selected_text)
            assert selected_text == "Option2", \
                f"Expected 'Option2', got '{selected_text}'"
            self._shot(driver, "09_main_dropdown_option2", browser)

            log.info("── TEST COMPLETED SUCCESSFULLY ──")

        except Exception as e:
            self._shot(driver, "FAILURE", browser, shot_type="FAIL")
            log.exception("Test failed: %s", e)
            raise