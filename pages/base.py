import shutil
import subprocess
import sys
import time
from typing import Iterable, Sequence, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from helpers import config


class Base:
    """Clase base reutilizada por todos los Page Objects."""

    URL = f"{config.BASE_URL}/"

    def __init__(self, driver=None, default_timeout: int = config.DEFAULT_WAIT_TIMEOUT):
        self.driver = driver
        self.default_timeout = default_timeout
        self._wait = WebDriverWait(self.driver, self.default_timeout) if self.driver else None

    # ------------------------------------------------------------------ #
    #   WEB DRIVER
    # ------------------------------------------------------------------ #
    def get_driver(self, *, use_profile: bool = True):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.page_load_strategy = "normal"
        if use_profile:
            chrome_options.add_argument(f"--user-data-dir={config.CHROME_PROFILE_DIR}")
            chrome_options.add_argument(f"--profile-directory={config.CHROME_SUBPROFILE}")

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver = driver
        self._wait = WebDriverWait(self.driver, self.default_timeout)
        return driver

    def quit_driver(self, driver):
        driver.quit()

    def reset_profile(self):
        shutil.rmtree(config.CHROME_PROFILE_DIR, ignore_errors=True)

    def close_residual_chrome(self):
        if not sys.platform.startswith("win"):
            return
        for proc in ("chromedriver.exe", "chrome.exe"):
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", proc],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except Exception:
                continue

    # ------------------------------------------------------------------ #
    #   UTILIDADES DE ESPERA
    # ------------------------------------------------------------------ #
    def _ensure_driver(self):
        if not self.driver:
            raise RuntimeError("No hay WebDriver inicializado para este PageObject.")

    def open_page(self, driver=None, url: str | None = None):
        driver = driver or self.driver
        if not driver:
            raise RuntimeError("No es posible abrir una página sin WebDriver.")
        self.driver = driver
        driver.get(url or self.URL)

    def wait_for_locator(self, locator: Tuple[str, str], attribute: str = "visible", timeout: int | None = None):
        self._ensure_driver()
        wait = WebDriverWait(self.driver, timeout or self.default_timeout)
        attribute_map = {
            "clickable": EC.element_to_be_clickable(locator),
            "visible": EC.visibility_of_element_located(locator),
            "presence": EC.presence_of_element_located(locator),
            "all_visible": EC.visibility_of_all_elements_located(locator),
            "invisible": EC.invisibility_of_element_located(locator),
        }
        if attribute not in attribute_map:
            raise ValueError(f"Condición '{attribute}' no soportada para wait_for_locator.")
        return wait.until(attribute_map[attribute])

    def wait_for_any_locator(self, locators: Sequence[Tuple[str, str]], attribute: str = "visible", timeout: int | None = None):
        last_error: TimeoutException | None = None
        for locator in locators:
            try:
                return self.wait_for_locator(locator, attribute, timeout=timeout)
            except TimeoutException as exc:
                last_error = exc
                continue
        raise last_error or TimeoutException("No se encontró un locator que cumpliera la condición solicitada.")

    def wait_for(self, element, attribute):
        """Mantiene compatibilidad con PageObjects existentes."""
        self._ensure_driver()
        wait = WebDriverWait(self.driver, self.default_timeout)
        attribute_map = {
            "clickable": EC.element_to_be_clickable(element),
            "visible": EC.visibility_of(element),
            "invisible": EC.invisibility_of_element(element),
            "staleness": EC.staleness_of(element),
        }
        if attribute not in attribute_map:
            raise ValueError(f"Condición '{attribute}' no soportada.")
        return wait.until(attribute_map[attribute])

    # ------------------------------------------------------------------ #
    #   OPERACIONES COMUNES
    # ------------------------------------------------------------------ #
    def enter_text(self, element, text: str):
        element.clear()
        element.send_keys(text)
        time.sleep(0.25)

    def type_into(self, locator: Tuple[str, str], text: str, *, clear: bool = True, wait_attr: str = "visible"):
        element = self.wait_for_locator(locator, wait_attr)
        if clear:
            element.clear()
        element.send_keys(text)
        time.sleep(0.25)
        return element

    def clickElement(self, element):
        elem = self.wait_for(element, "clickable")
        elem.click()

    def safe_click(self, element):
        self._ensure_driver()
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def click_locator(self, locator: Tuple[str, str]):
        element = self.wait_for_locator(locator, "clickable")
        self.safe_click(element)
        return element

    def find(self, locator: Tuple[str, str]):
        self._ensure_driver()
        return self.driver.find_element(*locator)

    def find_all(self, locator: Tuple[str, str]):
        self._ensure_driver()
        return self.driver.find_elements(*locator)

    def scroll_into_view(self, element):
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)

    def wait_for_url_contains(self, fragment: str, timeout: int | None = None):
        self._ensure_driver()
        wait = WebDriverWait(self.driver, timeout or self.default_timeout)
        wait.until(EC.url_contains(fragment))

    def pause_for_visual(self, seconds: float = 2.0):
        time.sleep(seconds)

    def detect_http_500(self) -> bool:
        html = self.driver.page_source.lower()
        patterns: Iterable[str] = (
            "500 internal server error",
            "ha ocurrido un error inesperado",
            "por favor vuelve a intentarlo mas tarde",
        )
        return any(p in html for p in patterns)
