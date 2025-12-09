import re
import time
import unicodedata
from typing import List

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from pages.base import Base
from pages.yopmail_page import YopmailPage


class TwoFactorPage(Base):
    _normalized_expr = "translate(., '\u00c1\u00c9\u00cd\u00d3\u00da\u00e1\u00e9\u00ed\u00f3\u00fa', 'AEIOUAEIOU')"
    _modal_container = (
        By.CSS_SELECTOR,
        "[data-two-factor-modal], div[id*='two-factor'], form[action*='two-factor'], form[id*='twofactor']",
    )
    _code_input_locators: List[tuple[str, str]] = [
        (By.CSS_SELECTOR, "input[type='text'][maxlength='1']"),
        (By.CSS_SELECTOR, "input[data-code-input]"),
        (By.CSS_SELECTOR, "input[name*='codigo' i]"),
        (By.CSS_SELECTOR, "input[id*='codigo' i]"),
        (By.CSS_SELECTOR, "input[name*='otp' i]"),
        (By.CSS_SELECTOR, "input[id*='otp' i]"),
        (By.CSS_SELECTOR, "input[type='number']"),
    ]
    _verify_button = (By.XPATH, "//button[contains(., 'Verificar') or contains(., 'Confirmar')]")
    _possible_send_buttons: List[tuple[str, str]] = [
        (
            By.XPATH,
            f"//form[contains({_normalized_expr}, 'ENVIAR CODIGO')]//button[@type='submit']",
        ),
        (
            By.XPATH,
            f"//button[contains({_normalized_expr}, 'ENVIAR CODIGO')]",
        ),
        (
            By.XPATH,
            f"//form[contains({_normalized_expr}, 'ENVIAR CORREO')]//button[@type='submit']",
        ),
        (
            By.XPATH,
            f"//button[contains({_normalized_expr}, 'ENVIAR CORREO')]",
        ),
        (
            By.XPATH,
            "//form[contains(@action, 'two-factor')]//button[@type='submit']",
        ),
    ]
    _captcha_indicators = [
        (By.CSS_SELECTOR, "iframe[src*='captcha' i]"),
        (By.CSS_SELECTOR, "div[id*='captcha' i]"),
        (By.CSS_SELECTOR, "div[class*='captcha' i]"),
        (By.CSS_SELECTOR, "[data-captcha]"),
    ]
    _notification = (By.CSS_SELECTOR, "div.notyf__message")

    def wait_until_ready(self):
        self.wait_for_locator(self._modal_container, "visible", timeout=30)

    def request_code(self):
        self.wait_until_ready()
        button = self._locate_send_button()
        if not button:
            raise TimeoutException("No se encontro el boton para solicitar el codigo 2FA.")
        self.scroll_into_view(button)
        self.safe_click(button)
        self._wait_for_code_request_ack(button)
        self._ensure_code_inputs(timeout=60)

    def enter_code(self, code: str):
        digits = re.findall(r"\d", code or "")
        inputs = self._ensure_code_inputs(timeout=20)
        if not digits:
            raise TimeoutException("El codigo recibido no contiene digitos.")
        if len(inputs) == 1:
            inputs[0].clear()
            inputs[0].send_keys("".join(digits))
            time.sleep(0.05)
            return
        if len(digits) < len(inputs):
            raise TimeoutException("El codigo recibido no tiene la cantidad esperada de digitos.")
        for idx, input_el in enumerate(inputs):
            input_el.clear()
            input_el.send_keys(digits[idx])
            time.sleep(0.05)

    def confirm(self):
        button = self.wait_for_locator(self._verify_button, "clickable", timeout=20)
        self.safe_click(button)
        self.wait_for_page_ready(timeout=30)

    def complete_two_factor_flow(self, carnet: str, *, max_attempts: int = 3) -> str:
        """Orquesta el flujo completo de 2FA con reintentos controlados."""
        self.wait_until_ready()
        yopmail = YopmailPage(self.driver)
        last_error: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                self.request_code()
                code = yopmail.fetch_code(carnet, attempt=attempt)
                self.enter_code(code)
                self.confirm()
                return code
            except Exception as exc:
                last_error = exc
                self._clear_code_inputs()
                if attempt < max_attempts:
                    self._refresh_two_factor_ui()
                    continue
                raise exc
        if last_error:
            raise last_error
        raise TimeoutException("No fue posible completar el flujo de 2FA.")

    # ------------------------------------------------------------------ #
    #   AUXILIARES
    # ------------------------------------------------------------------ #
    def _locate_send_button(self):
        deadline = time.time() + 15
        while time.time() < deadline:
            for locator in self._possible_send_buttons:
                elements = self.driver.find_elements(*locator)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        return element
            time.sleep(0.2)
        return self._fallback_send_button()

    def _wait_for_code_request_ack(self, button=None, timeout: int = 12):
        end_time = time.time() + timeout
        button = button or self._locate_send_button()
        while time.time() < end_time:
            if self._captcha_present():
                self._wait_for_captcha_resolution()
                return
            if self._notification_mentions_code() or self._modal_mentions_code():
                return
            if button and self._button_looks_disabled(button):
                return
            time.sleep(0.4)
        # No pudimos confirmar, pero continuamos para no bloquear el flujo completo.
        return

    def _notification_mentions_code(self) -> bool:
        for notif in self.driver.find_elements(*self._notification):
            texto = notif.text.lower()
            if "codigo" in texto or "correo" in texto or "enviado" in texto:
                return True
        return False

    def _modal_mentions_code(self) -> bool:
        try:
            contenedor = self.wait_for_locator(self._modal_container, "visible", timeout=5)
        except TimeoutException:
            return False
        textos = contenedor.text.lower()
        return any(palabra in textos for palabra in ("codigo", "correo", "mensaje", "mail"))

    def _captcha_present(self) -> bool:
        for locator in self._captcha_indicators:
            elements = self.driver.find_elements(*locator)
            for element in elements:
                try:
                    if element.is_displayed():
                        return True
                except Exception:
                    continue
        return False

    def _wait_for_captcha_resolution(self, timeout: int = 180):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if not self._captcha_present():
                return
            time.sleep(2)
        raise TimeoutException("El CAPTCHA no se resolvio dentro del tiempo esperado.")

    def _refresh_two_factor_ui(self):
        """Recupera el modal en caso de errores tras un reintento."""
        try:
            self.driver.execute_script("if (window.location) { window.location.reload(); }")
            self.wait_until_ready()
        except Exception:
            self.wait_until_ready()

    def _clear_code_inputs(self):
        for locator in self._code_input_locators:
            for input_el in self.driver.find_elements(*locator):
                try:
                    input_el.clear()
                except Exception:
                    continue

    def _ensure_code_inputs(self, timeout: int = 20):
        end_time = time.time() + timeout
        while time.time() < end_time:
            for locator in self._code_input_locators:
                elements = [
                    element for element in self.driver.find_elements(*locator) if element.is_displayed()
                ]
                if elements:
                    return elements
            time.sleep(0.2)
        raise TimeoutException("No se encontraron los campos para ingresar el codigo 2FA.")

    def _fallback_send_button(self):
        buttons = self.driver.find_elements(By.XPATH, "//button[not(@disabled)]")
        for button in buttons:
            try:
                if not button.is_displayed():
                    continue
                text = unicodedata.normalize("NFKD", button.text).encode("ascii", "ignore").decode("ascii").upper()
            except Exception:
                continue
            if "ENVIAR" in text and ("CODIGO" in text or "CORREO" in text):
                return button
        return None

    def _button_looks_disabled(self, button):
        try:
            if button.get_attribute("disabled"):
                return True
            class_name = button.get_attribute("class") or ""
            if "disabled" in class_name.lower():
                return True
            aria = (button.get_attribute("aria-disabled") or "").lower()
            if aria in ("1", "true", "yes"):
                return True
        except Exception:
            return False
        return False
