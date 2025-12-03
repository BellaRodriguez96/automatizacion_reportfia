from selenium.webdriver.common.by import By

from helpers import config
from pages.base import Base


class RegistrationPage(Base):
    _register_link = (By.CSS_SELECTOR, "a[href*='/registrarse']")
    _name_input = (By.NAME, "nombre")
    _last_name_input = (By.NAME, "apellido")
    _birthdate_input = (By.NAME, "fecha_nacimiento")
    _school_select = (By.NAME, "escuela")
    _phone_input = (By.NAME, "telefono")
    _submit_button = (By.CSS_SELECTOR, "form button[type='submit']")

    def open(self):
        self.open_page(url=f"{config.BASE_URL}/registrarse")
        self.wait_for_url_contains("/registrarse")
        self.wait_for_locator(self._name_input, "visible")

    def fill_personal_data(self, nombre: str, apellido: str, fecha: str, escuela_value: str, telefono: str):
        self.type_into(self._name_input, nombre)
        self.type_into(self._last_name_input, apellido)
        campo_fecha = self.wait_for_locator(self._birthdate_input, "visible")
        self.driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
            campo_fecha,
            fecha,
        )
        select = self.wait_for_locator(self._school_select, "visible")
        self.driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            select,
            escuela_value,
        )
        self.type_into(self._phone_input, telefono)

    def submit(self):
        self.click_locator(self._submit_button)

    def has_validation_error(self) -> bool:
        invalid_count = self.driver.execute_script(
            "return document.querySelectorAll('input:invalid, select:invalid, textarea:invalid').length;"
        )
        if invalid_count and int(invalid_count) > 0:
            return True
        for notif in self.driver.find_elements(By.CSS_SELECTOR, ".notyf__message, .text-red-500, .text-red-600"):
            try:
                if notif.is_displayed() and notif.text.strip():
                    return True
            except Exception:
                continue
        body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        keywords = ("por favor", "debes", "obligatorio", "completa", "ingresa", "campo")
        return any(k in body_text for k in keywords)
