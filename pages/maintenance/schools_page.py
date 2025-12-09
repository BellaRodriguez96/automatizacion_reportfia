import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from pages.base import Base


class MaintenanceSchoolsPage(Base):
    _add_button = (
        By.CSS_SELECTOR,
        "button[data-modal-toggle='static-modal'], button[data-modal-target='static-modal']",
    )
    _select_facultad = (By.ID, "id_facultad")
    _field_name = (By.NAME, "nombre")
    _save_button = (By.CSS_SELECTOR, "button[type='submit'][form='add-escuela-form']")
    _notification = (By.CSS_SELECTOR, "div.notyf__message")
    _filter_name = (By.ID, "nombre-filter")
    _filters_button = (By.CSS_SELECTOR, "button[data-tooltip-target='tooltip-aplicar-filtros']")

    def open_add_modal(self):
        locators = [
            self._add_button,
            (By.ID, "add-button"),
            (By.CSS_SELECTOR, "button[data-modal-toggle*='escuela']"),
            (By.XPATH, "//button[contains(translate(., 'ÁÉÍÓÚ', 'AEIOU'), 'ESCUELA')]"),
        ]
        btn = self.wait_for_any_locator(locators, "clickable")
        self.scroll_into_view(btn)
        self.safe_click(btn)

    def fill_form(self, name: str, faculty_value: str = "1"):
        select = Select(self.wait_for_locator(self._select_facultad, "visible"))
        select.select_by_value(faculty_value)
        time.sleep(0.25)
        self.type_into(self._field_name, name)

    def save_school(self):
        btn = self.wait_for_locator(self._save_button, "clickable")
        self.scroll_into_view(btn)
        self.safe_click(btn)

    def get_notification(self, timeout: int = 5):
        try:
            return self.wait_for_locator(self._notification, "visible").text.strip()
        except TimeoutException:
            return ""

    def filter_by_name(self, name: str):
        campo = self.wait_for_locator(self._filter_name, "visible")
        campo.clear()
        campo.send_keys(name)
        time.sleep(0.25)

    def apply_filters(self):
        btn = self.wait_for_locator(self._filters_button, "clickable")
        self.scroll_into_view(btn)
        self.safe_click(btn)
        self.pause_for_visual(2)

    def table_contains_school(self, name: str) -> bool:
        lower = name.lower()
        locator = (
            By.XPATH,
            f"//table//td[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{lower}')]",
        )
        try:
            self.wait_for_locator(locator, "presence")
            return True
        except TimeoutException:
            return False
