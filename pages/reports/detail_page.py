from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from pages.base import Base


class ReportDetailPage(Base):
    _general_info_header = (
        By.XPATH,
        "//h3[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'informaci')]",
    )
    _assignment_header = (
        By.XPATH,
        "//p[contains(translate(normalize-space(.), 'ÍÓÚÁÉáéíóú', 'iouaeaeiou'), 'asignacion')]",
    )
    _history_table = (
        By.XPATH,
        "//table[.//th[contains(translate(normalize-space(.), 'ÍÓÚÁÉáéíóú', 'iouaeaeiou'), 'acciones')]]",
    )
    _evidence_block = (
        By.XPATH,
        "//div[contains(@id,'evidencia') or contains(@class,'carousel')]//img | "
        "//img[contains(@src, '/storage/reportes/')]",
    )
    _evidence_placeholder = (
        By.XPATH,
        "//div[contains(@id,'evidencia') or contains(@class,'carousel')] | "
        "//p[contains(translate(normalize-space(.), 'ÁÉÍÓÚáéíóú', 'AEIOUaeiou'), 'EVIDENCIA')]",
    )

    def wait_until_loaded(self):
        self.wait_for_url_contains("/reportes/detalle", timeout=30)
        self.wait_for_page_ready(timeout=15)

    def has_state_information(self) -> bool:
        return self._page_contains("estado")

    def has_assignment_information(self) -> bool:
        if self._is_present(self._assignment_header):
            return True
        return self._page_contains("asignación") or self._page_contains("asignacion")

    def has_general_information(self) -> bool:
        return self._is_present(self._general_info_header)

    def has_history_information(self) -> bool:
        if self._is_present(self._history_table):
            return True
        return self._page_contains("acciones")

    def has_evidence_section(self) -> bool:
        try:
            html = (self.driver.page_source or "").lower()
        except Exception:
            html = ""
        keywords = ("storage/reportes", "evidencia", "gallery", "carrusel")
        if any(keyword in html for keyword in keywords):
            return True
        try:
            elements = self.driver.find_elements(*self._evidence_block)
        except Exception:
            elements = []
        return any(el.is_displayed() for el in elements) or self._is_present(self._evidence_placeholder)

    def _is_present(self, locator) -> bool:
        try:
            element = self.wait_for_locator(locator, "visible", timeout=5)
            return element is not None
        except TimeoutException:
            return False

    def _page_contains(self, keyword: str) -> bool:
        try:
            html = (self.driver.page_source or "").lower()
        except Exception:
            return False
        return keyword.lower() in html
