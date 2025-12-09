from __future__ import annotations

import time

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from pages.base import Base


class EmployeesPage(Base):
    _assignments_table = (By.CSS_SELECTOR, "table")
    _table_rows = (By.CSS_SELECTOR, "table tbody tr")
    _assign_button_candidates = (
        (By.CSS_SELECTOR, "button[data-modal-target*='puesto']"),
        (By.CSS_SELECTOR, "button[data-modal-toggle*='puesto']"),
        (By.CSS_SELECTOR, "button[data-modal-target='static-modal']"),
        (By.CSS_SELECTOR, "button[data-modal-toggle='static-modal']"),
        (
            By.XPATH,
            "//button[contains(translate(normalize-space(.), '??????????', 'AEIOUaeiou'), 'ASIGNAR PUESTO')]",
        ),
        (
            By.XPATH,
            "//a[contains(translate(normalize-space(.), '??????????', 'AEIOUaeiou'), 'ASIGNAR PUESTO')]",
        ),
    )
    _notification = (By.CSS_SELECTOR, "div.notyf__message")
    _filter_name_candidates = (
        (By.ID, "nombre"),
        (By.ID, "nombre-filter"),
        (By.NAME, "nombre"),
        (By.NAME, "nombre_empleado"),
        (By.CSS_SELECTOR, "input[name='nombre']"),
        (By.CSS_SELECTOR, "input[name*='nombre' i]"),
        (By.CSS_SELECTOR, "input[id*='nombre' i]"),
        (By.CSS_SELECTOR, "input[placeholder*='Nombre']"),
        (By.CSS_SELECTOR, "input[placeholder*='Empleado']"),
        (By.CSS_SELECTOR, "input[type='search']"),
    )
    _filter_search_candidates = (
        (By.CSS_SELECTOR, "button[data-tooltip-target='tooltip-aplicar-filtros']"),
        (By.CSS_SELECTOR, "button[data-tooltip-target='tooltip-aplicar-filter']"),
        (By.CSS_SELECTOR, "button[data-tooltip-target='tooltip-aplicar']"),
        (By.CSS_SELECTOR, "button[data-tooltip-target='tooltip-buscar']"),
        (By.CSS_SELECTOR, "button[type='submit']"),
        (
            By.XPATH,
            "//button[contains(translate(normalize-space(.), '??????????', 'AEIOUaeiou'), 'BUSCAR')]",
        ),
    )

    def wait_until_ready(self):
        self.wait_for_locator(self._assignments_table, "visible", timeout=20)

    def has_existing_assignments(self) -> bool:
        def _rows_present(_):
            return len(self.driver.find_elements(*self._table_rows)) > 0

        try:
            return bool(self.wait_for_condition(_rows_present, timeout=10))
        except Exception:
            return False

    def open_assign_position_modal(self):
        button = self._find_clickable(self._assign_button_candidates)
        self.scroll_into_view(button)
        self.safe_click(button)

    def wait_for_assignment(self, assignment_data: dict[str, str], timeout: int = 20):
        def _match(_):
            row = self._find_assignment_row(assignment_data)
            return row

        return self.wait_for_condition(_match, timeout=timeout)

    def row_contains_values(self, row, assignment_data: dict[str, str]) -> bool:
        text = self._normalize(row.text)
        for key in ("employee", "entity", "position", "status"):
            value = assignment_data.get(key, "")
            if not value:
                continue
            if self._normalize(value) not in text:
                return False
        return True

    def get_success_message(self) -> str:
        toast = self.wait_for_locator(self._notification, "visible", timeout=10)
        return toast.text.strip()

    def filter_by_employee_name(self, nombre: str):
        start = time.time()
        try:
            campo = self._find_filter_input()
            campo.clear()
            campo.send_keys(nombre)
            try:
                boton = self._find_clickable(self._filter_search_candidates, timeout=2)
                self.safe_click(boton)
            except TimeoutException:
                campo.send_keys(Keys.ENTER)
            self.wait_for_page_ready(timeout=8)
        except TimeoutException:
            if time.time() - start > 2:
                raise
            return

    def _find_clickable(self, locator_candidates, timeout: int = 10):
        def _first_clickable(driver):
            for locator in locator_candidates:
                elements = driver.find_elements(*locator)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            return element
                    except StaleElementReferenceException:
                        continue
            return False

        element = _first_clickable(self.driver)
        if element:
            return element
        return self.wait_for_condition(_first_clickable, timeout=timeout, poll_frequency=0.15)

    def _find_assignment_row(self, assignment_data: dict[str, str]):
        rows = self.driver.find_elements(*self._table_rows)
        for row in rows:
            normalized_text = self._normalize(row.text)
            if all(
                self._normalize(assignment_data.get(key, "")) in normalized_text
                for key in ("employee", "entity", "position", "status")
            ):
                return row
        return None

    def _find_filter_input(self):
        def _first_visible(driver):
            for locator in self._filter_name_candidates:
                elements = driver.find_elements(*locator)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            return element
                    except StaleElementReferenceException:
                        continue
            return False

        field = _first_visible(self.driver)
        if field:
            return field
        return self.wait_for_condition(_first_visible, timeout=1.5, poll_frequency=0.15)

    @staticmethod
    def _normalize(value: str) -> str:
        replacements = str.maketrans("??????????????", "AEIOUUNaeiouun")
        return value.strip().lower().translate(replacements)
