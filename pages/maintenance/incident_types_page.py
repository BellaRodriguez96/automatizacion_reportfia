from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from pages.base import Base


class IncidentTypesPage(Base):
    _table = (By.CSS_SELECTOR, "table")
    _add_button_locators = (
        (By.CSS_SELECTOR, "button[data-modal-target='static-modal']"),
        (By.CSS_SELECTOR, "button[data-modal-toggle='static-modal']"),
        (By.ID, "add-button"),
        (By.XPATH, "//button[contains(translate(., 'ÁÉÍÓÚÃÕÂÊÔÄËÏÖÜáéíóúãõâêôäëïöü', 'AEIOUAOAEOAEIOUaeiouaoaeou'), 'ANADIR')]"),
    )
    _modal = (By.ID, "static-modal")
    _name_field = (By.ID, "nombre")
    _description_field = (By.ID, "descripcion")
    _status_select = (By.ID, "activo")
    _save_button = (By.CSS_SELECTOR, "button[form='tipo-incidencia-form'][type='submit']")
    _name_filter = (By.ID, "nombre-filter")

    def is_loaded(self) -> bool:
        return self.wait_for_locator(self._table, "visible") is not None

    def open_add_modal(self):
        button = self.wait_for_any_locator(self._add_button_locators, "clickable")
        self.scroll_into_view(button)
        self.safe_click(button)
        self.wait_for_locator(self._modal, "visible")

    def fill_form(self, name: str, description: str, active: bool = True):
        self.type_into(self._name_field, name)
        self.type_into(self._description_field, description)
        select = self.wait_for_locator(self._status_select, "visible")
        value = "1" if active else "0"
        self.driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            select,
            value,
        )

    def submit(self):
        self.click_locator(self._save_button)
        # esperar a que el modal desaparezca antes de continuar
        try:
            self.wait_for_locator(self._modal, "invisible", timeout=10)
        except TimeoutException:
            pass

    def filter_by_name(self, name: str):
        campo = self.wait_for_locator(self._name_filter, "visible")
        campo.clear()
        campo.send_keys(name)
        self.driver.execute_script(
            "var form = arguments[0].closest('form'); if (form) { form.submit(); } else { arguments[0].dispatchEvent(new KeyboardEvent('keydown', {key:'Enter'})); }",
            campo,
        )
        self.wait_for_page_ready()

    def table_contains(self, text: str) -> bool:
        locator = (
            By.XPATH,
            f"//table//td[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]",
        )
        try:
            self.wait_for_locator(locator, "presence", timeout=10)
            return True
        except TimeoutException:
            return False
