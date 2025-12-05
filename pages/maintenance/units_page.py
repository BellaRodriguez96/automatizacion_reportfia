from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from pages.base import Base


class MaintenanceUnitsPage(Base):
    _add_button = (By.CSS_SELECTOR, "button[data-modal-target='static-modal']")
    _modal = (By.ID, "static-modal")
    _name_input = (By.ID, "nombre")
    _state_select = (By.ID, "activo")
    _save_button = (By.CSS_SELECTOR, "button[form='unidad-form'][type='submit']")
    _table = (By.CSS_SELECTOR, "table")
    _filter_name = (By.ID, "nombre-filter")
    _filters_button = (By.CSS_SELECTOR, "button[data-tooltip-target='tooltip-aplicar-filtros']")

    def open_add_modal(self):
        button = self.wait_for_locator(self._add_button, "clickable")
        self.scroll_into_view(button)
        self.safe_click(button)
        self.wait_for_locator(self._modal, "visible")

    def fill_form(self, nombre: str, activo: bool = True):
        self.type_into(self._name_input, nombre)
        select = Select(self.wait_for_locator(self._state_select, "visible"))
        select.select_by_value("1" if activo else "0")

    def save(self):
        boton = self.wait_for_locator(self._save_button, "clickable")
        self.safe_click(boton)
        self.wait_for_page_ready(timeout=10)

    def filter_by_name(self, name: str):
        campo = self.wait_for_locator(self._filter_name, "visible")
        campo.clear()
        campo.send_keys(name)
        self.pause_for_visual(0.2)

    def apply_filters(self):
        boton = self.wait_for_locator(self._filters_button, "clickable")
        self.scroll_into_view(boton)
        self.safe_click(boton)
        self.wait_for_page_ready(timeout=10)
        self.pause_for_visual(0.5)

    def table_contains_unit(self, nombre: str) -> bool:
        locator = (
            By.XPATH,
            f"//table//td[contains(translate(normalize-space(.), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '{nombre.upper()}')]",
        )
        try:
            self.wait_for_locator(locator, "presence", timeout=10)
            return True
        except Exception:
            return False

    def table_is_visible(self) -> bool:
        try:
            self.wait_for_locator(self._table, "visible", timeout=10)
            return True
        except Exception:
            return False
