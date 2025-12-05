import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from pages.base import Base


class EntitiesPage(Base):
    _table = (By.CSS_SELECTOR, "table")
    _add_button_candidates = (
        (By.CSS_SELECTOR, "button[data-modal-target='entity-modal']"),
        (By.CSS_SELECTOR, "button[data-modal-toggle='entity-modal']"),
        (By.CSS_SELECTOR, "button[data-modal-target='static-modal']"),
        (By.CSS_SELECTOR, "button[data-modal-toggle='static-modal']"),
        (By.ID, "add-entity-button"),
        (
            By.XPATH,
            "//button[contains(translate(normalize-space(.), 'áéíóúÁÉÍÓÚ', 'aeiouAEIOU'), 'ANADIR ENTIDAD')]",
        ),
        (
            By.XPATH,
            "//button[contains(translate(normalize-space(.), 'áéíóúÁÉÍÓÚ', 'aeiouAEIOU'), 'AGREGAR ENTIDAD')]",
        ),
        (
            By.XPATH,
            "//button[contains(translate(normalize-space(.), 'áéíóúÁÉÍÓÚ', 'aeiouAEIOU'), 'ANADIR')]",
        ),
    )
    _modal_candidates = (
        (By.ID, "entity-modal"),
        (By.CSS_SELECTOR, "[data-modal-placement][role='dialog']"),
        (By.CSS_SELECTOR, "form[action*='entidades']"),
    )
    _name_input = (By.ID, "nombre")
    _description_input = (By.ID, "descripcion")
    _state_select = (By.ID, "activo")
    _save_button = (By.CSS_SELECTOR, "button[type='submit'][form]")
    _notification = (By.CSS_SELECTOR, "div.notyf__message")
    _filter_name = (By.ID, "nombre-filter")
    _apply_filters_button = (By.CSS_SELECTOR, "button[data-tooltip-target='tooltip-aplicar-filtros']")
    _clear_filters_button = (By.CSS_SELECTOR, "button[data-tooltip-target='tooltip-limpiar-filtros']")

    def wait_until_ready(self):
        self.wait_for_locator(self._table, "visible", timeout=20)

    def open_add_modal(self):
        button = self._find_quick_button()
        self.scroll_into_view(button)
        self.safe_click(button)
        try:
            self.wait_for_any_locator(self._modal_candidates, "visible", timeout=3)
        except TimeoutException:
            self.wait_for_locator(self._name_input, "visible", timeout=3)

    def fill_form(self, nombre: str, descripcion: str, activo: bool = True):
        self.type_into(self._name_input, nombre)
        self.type_into(self._description_input, descripcion)
        try:
            select_element = self.wait_for_locator(self._state_select, "visible", timeout=5)
            Select(select_element).select_by_value("1" if activo else "0")
        except TimeoutException:
            pass

    def save(self):
        button = self.wait_for_locator(self._save_button, "clickable", timeout=10)
        self.safe_click(button)
        self.wait_for_page_ready(timeout=15)

    def get_notification(self) -> str:
        try:
            return self.wait_for_locator(self._notification, "visible", timeout=10).text.strip()
        except TimeoutException:
            return ""

    def filter_by_name(self, nombre: str):
        campo = self.wait_for_locator(self._filter_name, "visible", timeout=5)
        campo.clear()
        campo.send_keys(nombre)

    def apply_filters(self):
        boton = self.wait_for_locator(self._apply_filters_button, "clickable", timeout=5)
        self.safe_click(boton)
        self.wait_for_page_ready(timeout=5)

    def clear_filters(self):
        boton = self.wait_for_locator(self._clear_filters_button, "clickable", timeout=5)
        self.safe_click(boton)
        self.wait_for_page_ready(timeout=5)

    def table_contains_entity(self, nombre: str, timeout: int = 8) -> bool:
        locator = (
            By.XPATH,
            f"//table//tr[td[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ', "
            f"'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), '{nombre.lower()}')]]",
        )
        try:
            self.wait_for_locator(locator, "presence", timeout=timeout)
            return True
        except TimeoutException:
            return False

    def entity_has_status(self, nombre: str, estado: str, timeout: int = 8) -> bool:
        locator = (
            By.XPATH,
            f"//table//tr[td[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÜÑ', "
            f"'abcdefghijklmnopqrstuvwxyzáéíóúüñ'), '{nombre.lower()}')]]",
        )
        try:
            row = self.wait_for_locator(locator, "presence", timeout=timeout)
        except TimeoutException:
            return False
        texto = row.text.lower()
        return estado.lower() in texto

    def _find_quick_button(self):
        deadline = time.time() + 2
        while time.time() < deadline:
            for locator in self._add_button_candidates:
                try:
                    elements = self.driver.find_elements(*locator)
                except Exception:
                    continue
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        return element
            time.sleep(0.1)
        return self.wait_for_any_locator(self._add_button_candidates, "clickable", timeout=3)
