from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from helpers.data_factory import StudentData
from pages.base import Base


class SecurityUsersPage(Base):
    _add_button = (By.ID, "add-button")
    _field_nombre = (By.NAME, "nombre")
    _field_apellido = (By.NAME, "apellido")
    _field_fecha = (By.NAME, "fecha_nacimiento")
    _field_telefono = (By.NAME, "telefono")
    _field_email = (By.NAME, "email")
    _field_carnet = (By.ID, "carnet")
    _select_tipo = (By.NAME, "tipo_user")
    _select_escuela = (By.ID, "escuela")
    _checkbox_activo = (By.XPATH, "//input[@type='checkbox']")
    _save_button = (By.ID, "guardar")
    _filter_email = (By.ID, "email-filter")
    _filters_button = (By.CSS_SELECTOR, "button[data-tooltip-target='tooltip-aplicar-filtros']")
    _notification = (By.CSS_SELECTOR, "div.notyf__message")

    def open_add_modal(self):
        locators = [
            (By.ID, "add-button"),
            (By.CSS_SELECTOR, "button#add-button"),
            (By.CSS_SELECTOR, "button[data-modal-toggle*='usuario']"),
            (By.CSS_SELECTOR, "button[data-tooltip-target*='add']"),
            (By.XPATH, "//button[contains(translate(., 'ÁÉÍÓÚ', 'AEIOU'), 'AGREGAR')]"),
        ]
        button = self.wait_for_any_locator(locators, "visible")
        self.scroll_into_view(button)
        try:
            button.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", button)

    def fill_user_form(self, data: StudentData):
        self.type_into(self._field_nombre, data.first_name)
        self.type_into(self._field_apellido, data.last_name)
        fecha_input = self.wait_for_locator(self._field_fecha, "clickable")
        self.driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
            fecha_input,
            data.birthdate,
        )
        self.wait_for_page_ready(timeout=3)
        self.type_into(self._field_telefono, data.phone)
        self.type_into(self._field_email, data.email)
        self.type_into(self._field_carnet, data.carnet)

        tipo_select = Select(self.wait_for_locator(self._select_tipo, "visible"))
        try:
            tipo_select.select_by_visible_text(data.user_type)
        except NoSuchElementException:
            for option in tipo_select.options:
                if data.user_type.lower() in option.text.lower():
                    option.click()
                    break

        escuela_select = Select(self.wait_for_locator(self._select_escuela, "visible"))
        escuela_select.select_by_value(data.school_value)

        checkbox = self.wait_for_locator(self._checkbox_activo, "clickable")
        is_selected = checkbox.is_selected()
        if data.active and not is_selected:
            checkbox.click()
        elif not data.active and is_selected:
            checkbox.click()

    def save_user(self):
        self.click_locator(self._save_button)

    def get_notification(self, timeout: int = 5):
        try:
            element = self.wait_for_locator(self._notification, "visible")
            return element.text.strip()
        except TimeoutException:
            return ""

    def filter_by_email(self, email: str):
        campo = self.wait_for_locator(self._filter_email, "visible")
        campo.clear()
        campo.send_keys(email)
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', {bubbles: true})); arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            campo,
        )

    def apply_filters(self):
        btn = self.wait_for_locator(self._filters_button, "clickable", timeout=5)
        self.scroll_into_view(btn)
        self.safe_click(btn)
        self.wait_for_page_ready(timeout=6)

    def table_contains_email(self, email: str) -> bool:
        locator = (
            By.XPATH,
            f"//table//td[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{email.lower()}')]",
        )
        try:
            self.wait_for_locator(locator, "presence")
            return True
        except TimeoutException:
            return False
