import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from pages.base import Base


class MaintenanceFundsPage(Base):
    _table = (By.CSS_SELECTOR, "table")
    _add_button = (By.CSS_SELECTOR, "button[data-modal-target='static-modal']")
    _modal = (By.ID, "static-modal")
    _name_input = (By.ID, "nombre")
    _description_input = (By.ID, "descripcion")
    _state_select = (By.ID, "activo")
    _save_button = (By.CSS_SELECTOR, "button[type='submit'][form='fondo-form']")
    _filter_name = (By.ID, "nombre-filter")
    _apply_filters_button = (By.CSS_SELECTOR, "button[data-tooltip-target='tooltip-aplicar-filtros']")

    def table_is_visible(self) -> bool:
        elemento = self.wait_for_locator(self._table, "visible")
        return elemento is not None

    def open_add_modal(self):
        button = self.wait_for_locator(self._add_button, "clickable")
        self.scroll_into_view(button)
        self.safe_click(button)
        self.wait_for_locator(self._modal, "visible")

    def fill_form(self, nombre: str, descripcion: str, activo: bool = True):
        self.type_into(self._name_input, nombre)
        self.type_into(self._description_input, descripcion)
        select = Select(self.wait_for_locator(self._state_select, "visible"))
        select.select_by_value("1" if activo else "0")
        time.sleep(0.2)

    def save(self):
        button = self.wait_for_locator(self._save_button, "clickable")
        self.safe_click(button)
        self.wait_for_page_ready(timeout=10)

    def filter_by_name(self, nombre: str):
        field = self.wait_for_locator(self._filter_name, "visible", timeout=10)
        field.clear()
        field.send_keys(nombre)
        time.sleep(0.2)

    def apply_filters(self):
        button = self.wait_for_locator(self._apply_filters_button, "clickable", timeout=10)
        self.safe_click(button)
        self.wait_for_page_ready(timeout=10)

    def refresh_table(self):
        self.driver.refresh()
        self.wait_for_page_ready(timeout=15)
        self.wait_for_locator(self._table, "visible", timeout=15)

    def table_contains_fund(self, nombre: str, timeout: int = 30) -> bool:
        locator = (
            By.XPATH,
            f"//table//td[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{nombre.lower()}')]",
        )
        deadline = time.time() + timeout
        next_refresh = time.time()

        while time.time() < deadline:
            if self.driver.find_elements(*locator):
                return True
            if time.time() >= next_refresh:
                self.refresh_table()
                next_refresh = time.time() + 5
            time.sleep(0.5)
        return False
