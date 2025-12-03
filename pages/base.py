import os
import shutil
import subprocess
import sys
import time
from typing import Callable, Iterable, Sequence, Tuple

from selenium import webdriver
from selenium.common.exceptions import InvalidSessionIdException, NoSuchWindowException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from helpers import config

POST_ACTION_DELAY = float(os.getenv("REPORTFIA_ACTION_DELAY", "0.05"))
DATA_ENTRY_DELAY = float(os.getenv("REPORTFIA_DATA_ENTRY_DELAY", "0.2"))
POST_ACTION_SYNC = os.getenv("REPORTFIA_POST_ACTION_SYNC", "0").lower() in ("1", "true", "yes")


class Base:
    """Utilidades base compartidas por todos los Page Objects."""

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
        try:
            driver.quit()
        except Exception:
            # Cuando Chrome ya cerro la conexion HTTP puede lanzar ConnectionRefusedError.
            # Lo ignoramos para no romper la suite.
            pass

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

    def is_driver_alive(self) -> bool:
        if not self.driver:
            return False
        try:
            _ = self.driver.current_url
            return True
        except (InvalidSessionIdException, NoSuchWindowException, WebDriverException):
            return False

    # ------------------------------------------------------------------ #
    #   UTILIDADES DE ESPERA / NAVEGACION
    # ------------------------------------------------------------------ #
    def _ensure_driver(self):
        if not self.driver:
            raise RuntimeError("No hay WebDriver inicializado para este PageObject.")

    def open_page(self, driver=None, url: str | None = None, *, force_reload: bool = False):
        driver = driver or self.driver
        if not driver:
            raise RuntimeError("No es posible abrir una pagina sin WebDriver.")
        self.driver = driver
        destino = (url or self.URL).rstrip("/")
        if not force_reload and self._is_same_url(destino):
            self.wait_for_page_ready(timeout=10)
            return
        driver.get(destino)
        if not self._wait_for_navigation(destino):
            # Algunos perfiles muestran la URL sin cargar; forzamos con JS como respaldo.
            driver.execute_script("window.location.href = arguments[0];", destino)
            self._wait_for_navigation(destino)
        self._post_action_wait()

    def _is_same_url(self, destino: str) -> bool:
        if not self.driver:
            return False
        try:
            current = (self.driver.current_url or "").rstrip("/")
        except Exception:
            return False
        return current.endswith(destino)

    def _wait_for_navigation(self, expected_url: str | None, timeout: int | None = None) -> bool:
        limite = time.time() + (timeout or min(self.default_timeout, 10))
        esperado = (expected_url or "").rstrip("/")
        while time.time() < limite:
            try:
                current = self.driver.current_url
                ready_state = self.driver.execute_script("return document.readyState")
            except Exception:
                time.sleep(0.2)
                continue
            if ready_state in ("interactive", "complete"):
                if not esperado or esperado in current.rstrip("/"):
                    return True
            time.sleep(0.2)
        return False

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
            raise ValueError(f"Condicion '{attribute}' no soportada para wait_for_locator.")
        return wait.until(attribute_map[attribute])

    def wait_for_any_locator(self, locators: Sequence[Tuple[str, str]], attribute: str = "visible", timeout: int | None = None):
        last_error: TimeoutException | None = None
        for locator in locators:
            try:
                return self.wait_for_locator(locator, attribute, timeout=timeout)
            except TimeoutException as exc:
                last_error = exc
                continue
        raise last_error or TimeoutException("No se encontro un locator que cumpliera la condicion solicitada.")

    def wait_for_condition(self, predicate: Callable, timeout: int | None = None, poll_frequency: float = 0.2):
        self._ensure_driver()
        end_time = time.time() + (timeout or self.default_timeout)
        while time.time() < end_time:
            try:
                result = predicate(self.driver)
            except Exception:
                result = False
            if result:
                return result
            time.sleep(poll_frequency)
        raise TimeoutException("La condicion personalizada no se cumplio dentro del tiempo esperado.")

    def wait_for_page_ready(self, timeout: int | None = None) -> bool:
        """Bloquea hasta que el DOM este al menos en estado interactivo."""
        self._ensure_driver()
        wait = WebDriverWait(self.driver, timeout or self.default_timeout)

        def _ready(_driver):
            try:
                state = _driver.execute_script("return document.readyState")
                return state in ("interactive", "complete")
            except Exception:
                return False

        try:
            wait.until(_ready)
            return True
        except TimeoutException:
            return False

    def wait_for(self, element, attribute):
        """Compatibilidad con PageObjects antiguos que usan wait_for."""
        self._ensure_driver()
        wait = WebDriverWait(self.driver, self.default_timeout)
        attribute_map = {
            "clickable": EC.element_to_be_clickable(element),
            "visible": EC.visibility_of(element),
            "invisible": EC.invisibility_of(element),
            "staleness": EC.staleness_of(element),
        }
        if attribute not in attribute_map:
            raise ValueError(f"Condicion '{attribute}' no soportada.")
        return wait.until(attribute_map[attribute])

    # ------------------------------------------------------------------ #
    #   OPERACIONES COMUNES
    # ------------------------------------------------------------------ #
    def enter_text(self, element, text: str):
        element.clear()
        element.send_keys(text)
        if DATA_ENTRY_DELAY > 0:
            time.sleep(DATA_ENTRY_DELAY)
        self._post_action_wait()

    def type_into(self, locator: Tuple[str, str], text: str, *, clear: bool = True, wait_attr: str = "visible"):
        element = self.wait_for_locator(locator, wait_attr)
        if clear:
            element.clear()
        element.send_keys(text)
        if DATA_ENTRY_DELAY > 0:
            time.sleep(DATA_ENTRY_DELAY)
        self._post_action_wait()
        return element

    def clickElement(self, element):
        elem = self.wait_for(element, "clickable")
        elem.click()
        self._post_action_wait()

    def safe_click(self, element):
        self._ensure_driver()
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)
        self._post_action_wait()

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
        found = any(p in html for p in patterns)
        if found:
            time.sleep(3)
        return found

    def clear_storage(self):
        if not self.driver:
            return
        try:
            self.driver.delete_all_cookies()
        except Exception:
            pass
        try:
            self.driver.execute_script(
                "window.localStorage.clear();"
                "window.sessionStorage.clear();"
                "if (window.indexedDB) {"
                "var req = indexedDB.databases ? indexedDB.databases() : Promise.resolve([]);"
                "req.then(function(list){list.forEach(function(db){indexedDB.deleteDatabase(db.name);});});}"
            )
        except Exception:
            pass

    def _post_action_wait(self, delay: float = POST_ACTION_DELAY):
        """Anade un pequeno margen tras cada accion para no saturar la UI."""
        if POST_ACTION_SYNC:
            try:
                self.wait_for_page_ready(timeout=1)
            except Exception:
                pass
        if delay > 0:
            time.sleep(delay)
