from dataclasses import dataclass
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


DEFAULT_WAIT = 15


@dataclass
class BasePage:
    driver: any
    base_url: str

    def open(self, path: str = "/"):
        self.driver.get(self.base_url + path)
        return self

    def wait_for(self, locator, timeout: int = DEFAULT_WAIT):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def wait_click(self, locator, timeout: int = DEFAULT_WAIT):
        elem = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        elem.click()
        return elem


class LandingPage(BasePage):
    LOGO = (By.CSS_SELECTOR, ".logo")
    LOGIN_BTN = (By.ID, "loginBtn")

    def assert_loaded(self):
        self.wait_for(self.LOGO)
        return self

    def click_login(self):
        self.wait_click(self.LOGIN_BTN)
        return self


class RegisterPage(BasePage):
    # Assuming fields by name/id; adjust to real DOM if different
    FIRST = (By.NAME, "first_name")
    LAST = (By.NAME, "last_name")
    EMAIL = (By.NAME, "email")
    PASS = (By.NAME, "password")
    SUBMIT = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR = (By.CSS_SELECTOR, ".error, .invalid-feedback, .alert-danger")

    def submit(self, first, last, email, password):
        self.wait_for(self.FIRST).send_keys(first)
        self.driver.find_element(*self.LAST).send_keys(last)
        self.driver.find_element(*self.EMAIL).send_keys(email)
        self.driver.find_element(*self.PASS).send_keys(password)
        self.driver.find_element(*self.SUBMIT).click()
        return self

    def has_error(self):
        try:
            self.wait_for(self.ERROR, timeout=5)
            return True
        except Exception:
            return False


class LoginPage(BasePage):
    EMAIL = (By.NAME, "email")
    PASS = (By.NAME, "password")
    SUBMIT = (By.CSS_SELECTOR, "button[type='submit']")

    def login(self, email, password):
        self.wait_for(self.EMAIL).send_keys(email)
        self.driver.find_element(*self.PASS).send_keys(password)
        self.driver.find_element(*self.SUBMIT).click()
        return self


class DashboardPage(BasePage):
    WELCOME = (By.CSS_SELECTOR, "h1, h2, [data-testid='dashboard-welcome']")
    PLAN_BADGE = (By.CSS_SELECTOR, "[data-testid='subscription-tier']")
    HEALTH_WIDGET = (By.CSS_SELECTOR, "[data-testid='health-metrics']")
    FINANCE_WIDGET = (By.CSS_SELECTOR, "[data-testid='financial-insights']")

    def assert_loaded(self):
        self.wait_for(self.WELCOME)
        return self

    def get_tier_text(self):
        try:
            return self.driver.find_element(*self.PLAN_BADGE).text.strip()
        except Exception:
            return None


