import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from pages.base import Base


class MaintenanceAssetsPage(Base):
    _table = (By.CSS_SELECTOR, "table")
    _name_filter = (By.ID, "nombre-filter")
    _code_filter = (By.ID, "codigo-filter")
    _status_filter = (By.ID, "estado-bien-filter")
    _apply_button = (By.CSS_SELECTOR, "button[data-tooltip-target='tooltip-aplicar-filtros'], form button[type='submit']")
    _reset_button = (By.CSS_SELECTOR, "button[type='reset']")

    def wait_until_ready(self):
        self.wait_for_locator(self._table, "visible")

    def _set_input(self, locator, value: str):
        campo = self.wait_for_locator(locator, "visible")
        campo.clear()
        campo.send_keys(value)
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", campo
        )

    def filter_by_name(self, name: str):
        self._set_input(self._name_filter, name)

    def filter_by_code(self, code: str):
        self._set_input(self._code_filter, code)

    def filter_by_status(self, status_value: str):
        select = self.wait_for_locator(self._status_filter, "visible")
        self.driver.execute_script(
            "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
            select,
            status_value,
        )

    def apply_filters(self):
        if not self._click_with_retry(self._apply_button):
            try:
                campo = self.wait_for_locator(self._name_filter, "visible", timeout=3)
                campo.send_keys("\n")
            except Exception:
                pass
        self.wait_for_page_ready(timeout=8)
        self.wait_for_locator(self._table, "visible", timeout=8)

    def reset_filters(self):
        if not self._click_with_retry(self._reset_button):
            self.driver.get(f"{self.driver.current_url.split('?')[0]}")
        self.wait_for_page_ready(timeout=8)
        self.wait_for_locator(self._table, "visible", timeout=8)

    def table_contains_text(self, texto: str) -> bool:
        locator = (
            By.XPATH,
            f"//table//td[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{texto.lower()}')]",
        )
        try:
            self.wait_for_locator(locator, "presence", timeout=10)
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
