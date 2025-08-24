import os
import time
import pytest

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager


def _build_chrome(headless: bool = True, mobile: bool = False, device_name: str | None = None):
    options = ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1400,900")
    if mobile:
        mobile_emulation = {"deviceName": device_name or "iPhone X"}
        options.add_experimental_option("mobileEmulation", mobile_emulation)
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    return driver


def _build_firefox(headless: bool = True, mobile: bool = False):
    options = FirefoxOptions()
    if headless:
        options.add_argument("-headless")
    driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
    if mobile:
        driver.set_window_size(375, 812)  # iPhone X-ish
    else:
        driver.set_window_size(1400, 900)
    return driver


@pytest.fixture(scope="session")
def base_url():
    return os.environ.get("TEST_BASE_URL", "http://localhost:5000")


@pytest.fixture(scope="session")
def browser_name(pytestconfig):
    return os.environ.get("BROWSER", pytestconfig.getoption("--browser") or "chrome")


def pytest_addoption(parser):
    parser.addoption("--browser", action="store", default=None, help="chrome or firefox")
    parser.addoption("--headed", action="store_true", help="Run browsers in headed mode")
    parser.addoption("--mobile", action="store_true", help="Enable mobile viewport simulation")


@pytest.fixture(scope="function")
def driver(pytestconfig, browser_name):
    headless = not pytestconfig.getoption("--headed")
    mobile = pytestconfig.getoption("--mobile")
    if browser_name.lower() == "firefox":
        _driver = _build_firefox(headless=headless, mobile=mobile)
    else:
        _driver = _build_chrome(headless=headless, mobile=mobile)

    _driver.set_page_load_timeout(40)
    yield _driver
    try:
        _driver.quit()
    except Exception:
        pass


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    # On failure, capture screenshot if driver is available
    if rep.when == "call" and rep.failed:
        driver = item.funcargs.get("driver")
        base_url = item.funcargs.get("base_url", "")
        if driver:
            ts = time.strftime("%Y%m%d-%H%M%S")
            os.makedirs("reports/screenshots", exist_ok=True)
            filename = f"reports/screenshots/{item.name}_{ts}.png"
            try:
                driver.save_screenshot(filename)
            except Exception:
                pass


