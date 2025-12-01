import time
import unicodedata

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from pages.base import Base
from pages.yopmail_page import YopmailPage


class TwoFactorPage(Base):
    _code_inputs = (By.CSS_SELECTOR, "input[type='text'][maxlength='1']")
    _verify_button = (By.XPATH, "//button[contains(., 'Verificar')]")
    _possible_send_buttons = [
        (
            By.XPATH,
            "//form[contains(translate(., 'ÁÉÍÓÚ', 'AEIOU'), 'ENVIAR CODIGO')]//button[@type='submit']",
        ),
        (
            By.XPATH,
            "//form[contains(translate(., 'ÁÉÍÓÚ', 'AEIOU'), 'ENVIAR CORREO')]//button[@type='submit']",
        ),
        (
            By.XPATH,
            "//button[contains(translate(., 'ÁÉÍÓÚ', 'AEIOU'), 'ENVIAR CODIGO')]",
        ),
        (
            By.XPATH,
            "//button[contains(translate(., 'ÁÉÍÓÚ', 'AEIOU'), 'ENVIAR CORREO')]",
        ),
        (
            By.XPATH,
            "//form[contains(@action, 'two-factor')]//button[@type='submit']",
        ),
    ]

    def request_code(self):
        for locator in self._possible_send_buttons:
            try:
                boton = self.wait_for_locator(locator, "clickable", timeout=15)
                self.scroll_into_view(boton)
                self.safe_click(boton)
                time.sleep(0.2)
                return
            except TimeoutException:
                continue
        botones = self.driver.find_elements(By.XPATH, "//button[@type='submit' or @type='button']")
        for boton in botones:
            texto = unicodedata.normalize("NFKD", boton.text).encode("ASCII", "ignore").decode().lower()
            if "enviar" in texto and ("codigo" in texto or "correo" in texto):
                self.scroll_into_view(boton)
                self.safe_click(boton)
                return
        raise TimeoutException("No se encontró un botón para enviar el código 2FA.")

    def enter_code(self, code: str):
        inputs = self.wait_for_locator(self._code_inputs, "all_visible")
        for idx, digit in enumerate(code):
            inputs[idx].clear()
            inputs[idx].send_keys(digit)
            time.sleep(0.1)

    def confirm(self):
        boton_verificar = self.wait_for_locator(self._verify_button, "clickable")
        self.safe_click(boton_verificar)

    def complete_two_factor_flow(self, carnet: str) -> str:
        self.request_code()
        yopmail = YopmailPage(self.driver)
        codigo = yopmail.fetch_code(carnet)
        self.enter_code(codigo)
        self.confirm()
        return codigo
