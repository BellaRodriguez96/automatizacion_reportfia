import time

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from pages.base import Base


class BitacoraPage(Base):
    _table = (By.CSS_SELECTOR, "table")
    _empty_state = (By.CSS_SELECTOR, ".empty-state, [data-empty], .text-gray-500")
    _model_select = (By.ID, "model")
    _event_select = (By.ID, "event")
    _name_input = (By.ID, "nombre")
    _start_date = (By.ID, "start_date")
    _end_date = (By.ID, "end_date")
    _apply_button = (By.CSS_SELECTOR, "button[data-tooltip-target='tooltip-aplicar-filtros'], form button[type='submit']")
    _reset_button = (By.CSS_SELECTOR, "button[type='reset']")

    def wait_until_loaded(self):
        if self._wait_table_or_empty(timeout=12):
            return
        # Si no cargó a la primera, refresca una vez y vuelve a intentarlo rápidamente.
        self.driver.refresh()
        self.wait_for_page_ready(timeout=8)
        if not self._wait_table_or_empty(timeout=12):
            raise TimeoutException("La bitácora no mostró resultados ni estado vacío tras recargar.")

    def _select_by_text(self, locator, text: str, fallback_value: str | None = None):
        element = self.wait_for_locator(locator, "visible")
        try:
            Select(element).select_by_visible_text(text)
        except (NoSuchElementException, TimeoutException):
            value = fallback_value or text
            self.driver.execute_script(
                "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                element,
                value,
            )

    def set_model(self, texto: str):
        self._select_by_text(self._model_select, texto, fallback_value="App\\\\Models\\\\Mantenimientos\\\\Escuela")

    def set_event(self, texto: str):
        self._select_by_text(self._event_select, texto)

    def set_name(self, nombre: str):
        campo = self.wait_for_locator(self._name_input, "visible")
        campo.clear()
        if nombre:
            campo.send_keys(nombre)
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', {bubbles: true})); arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            campo,
        )

    def set_date_range(self, inicio: str, fin: str):
        start = self.wait_for_locator(self._start_date, "visible")
        end = self.wait_for_locator(self._end_date, "visible")
        for element, value in ((start, inicio), (end, fin)):
            self.driver.execute_script(
                "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true})); arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                element,
                value,
            )

    def apply_filters(self):
        if not self._click_with_retry(self._apply_button):
            campo = self.wait_for_locator(self._name_input, "visible", timeout=3)
            campo.send_keys("\n")
        self.wait_for_page_ready(timeout=8)
        self.wait_until_loaded()

    def reset_filters(self):
        if not self._click_with_retry(self._reset_button):
            self.driver.get(f"{self.driver.current_url.split('?')[0]}")
        self.wait_for_page_ready(timeout=8)
        self.wait_until_loaded()

    def table_contains(self, texto: str) -> bool:
        locator = (
            By.XPATH,
            f"//table//tr[td[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{texto.lower()}')]]",
        )
        try:
            self.wait_for_locator(locator, "presence", timeout=10)
            return True
        except TimeoutException:
            return False

    def _wait_table_or_empty(self, timeout: int) -> bool:
        try:
            self.wait_for_locator(self._table, "visible", timeout=timeout)
            return True
        except TimeoutException:
            try:
                self.wait_for_locator(self._empty_state, "visible", timeout=3)
                return True
            except TimeoutException:
                return False

    def _click_with_retry(self, locator, *, wait_timeout: int = 2, total_timeout: int = 6) -> bool:
        deadline = time.time() + total_timeout
        while time.time() < deadline:
            try:
                boton = self.wait_for_locator(locator, "clickable", timeout=wait_timeout)
                self.scroll_into_view(boton)
                self.safe_click(boton)
                return True
            except TimeoutException:
                continue
        return False
