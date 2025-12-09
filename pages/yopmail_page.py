import re
import time
from contextlib import suppress

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from helpers import config
from pages.base import Base


class YopmailPage(Base):
    """Gestiona la lectura del correo 2FA en la version estable de Yopmail."""

    _login_field = (By.ID, "login")
    _iframe_mail = (By.CSS_SELECTOR, "iframe#ifmail, iframe[name='ifmail']")
    _refresh_button = (By.CSS_SELECTOR, "#refresh, button[onclick*='Refresh']")
    _message_strong = (By.CSS_SELECTOR, "#mail strong, #mail b, .mail strong")
    _message_body = (By.CSS_SELECTOR, "#mail, body")

    def fetch_code(self, carnet: str, *, attempt: int = 1, max_retries: int = 3) -> str:
        carnet = carnet.strip().lower()
        if not carnet:
            raise ValueError("No se proporciono un carnet para consultar en Yopmail.")

        main_window = self.driver.current_window_handle
        tab_handle = self._open_helper_tab()

        try:
            self._load_inbox(carnet)
            for retry in range(1, max_retries + 1):
                try:
                    iframe = self._wait_for_iframe(timeout=20)
                    self.driver.switch_to.frame(iframe)
                    code = self._extract_code_from_email(timeout=35)
                    if code:
                        return code
                except TimeoutException:
                    if retry == max_retries:
                        raise
                finally:
                    self.driver.switch_to.default_content()
                self._refresh_inbox()
            raise TimeoutException("No se encontro el codigo 2FA en Yopmail tras multiples intentos.")
        finally:
            self._close_helper_tab(main_window, tab_handle)

    # ------------------------------------------------------------------ #
    #   FLUJO DE NAVEGACION
    # ------------------------------------------------------------------ #
    def _open_helper_tab(self) -> str:
        try:
            self.driver.switch_to.new_window("tab")
        except Exception:
            self.driver.execute_script("window.open('about:blank', '_blank');")
            time.sleep(0.5)
            self.driver.switch_to.window(self.driver.window_handles[-1])
        return self.driver.current_window_handle

    def _close_helper_tab(self, main_window: str, helper_window: str):
        with suppress(Exception):
            self.driver.close()
        with suppress(Exception):
            self.driver.switch_to.window(main_window)
        # Limpia pestanas adicionales que Yopmail pueda abrir sin permiso.
        for handle in list(self.driver.window_handles):
            if handle == main_window:
                continue
            with suppress(Exception):
                self.driver.switch_to.window(handle)
                self.driver.close()
        with suppress(Exception):
            self.driver.switch_to.window(main_window)

    def _load_inbox(self, carnet: str):
        target_url = self._compose_yopmail_url()
        self.driver.get(target_url)
        campo = self.wait_for_locator(self._login_field, "visible", timeout=20)
        campo.clear()
        campo.send_keys(carnet)
        campo.send_keys(Keys.ENTER)
        self.wait_for_page_ready(timeout=20)

    def _compose_yopmail_url(self) -> str:
        base_url = config.YOPMAIL_URL.rstrip("/")
        if "?v=2" not in base_url.lower():
            if "?" in base_url:
                base_url = f"{base_url}&v=2"
            else:
                base_url = f"{base_url}?v=2"
        return base_url

    def _wait_for_iframe(self, timeout: int = 20):
        wait = WebDriverWait(self.driver, timeout)
        try:
            return wait.until(EC.presence_of_element_located(self._iframe_mail))
        except TimeoutException as exc:
            raise TimeoutException("No se encontro el iframe del correo (ifmail).") from exc

    def _refresh_inbox(self):
        # Intentamos el boton de refresco; si falla, recargamos la pagina.
        try:
            button = self.wait_for_locator(self._refresh_button, "clickable", timeout=5)
            self.safe_click(button)
            self.wait_for_page_ready(timeout=15)
            return
        except TimeoutException:
            pass
        with suppress(WebDriverException):
            self.driver.refresh()
            self.wait_for_page_ready(timeout=20)

    def _extract_code_from_email(self, timeout: int = 30) -> str:
        wait = WebDriverWait(self.driver, timeout)
        try:
            element = wait.until(EC.visibility_of_element_located(self._message_strong))
            texto = element.text.strip()
            code = self._find_code_in_text(texto)
            if code:
                return code
        except TimeoutException:
            pass

        body = self.wait_for_locator(self._message_body, "visible", timeout=timeout)
        texto = body.text.strip()
        code = self._find_code_in_text(texto)
        if not code:
            raise TimeoutException("El correo no contiene un codigo 2FA legible.")
        return code

    @staticmethod
    def _find_code_in_text(text: str) -> str | None:
        match = re.search(r"\b\d{6}\b", text)
        return match.group(0) if match else None
