import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from pages.base import Base


class ReportsAssignmentsPage(Base):
    _assignment_links = (By.CSS_SELECTOR, "a[href*='/reportes/detalle/']")
    _actions_button = (By.CSS_SELECTOR, "button[aria-label*='acciones'], button[data-dropdown-toggle*='acciones']")
    _change_status_option = (By.XPATH, "//button[contains(., 'Cambiar estado')]|//a[contains(., 'Cambiar estado')]")
    _assignments_table = (By.CSS_SELECTOR, "table, .overflow-x-auto")

    def open_first_assignment(self) -> str:
        """Abre la primera asignación disponible sin depender de un único intento."""
        self.wait_for_locator(self._assignments_table, "visible", timeout=20)
        deadline = time.time() + 20
        while time.time() < deadline:
            links = self.driver.find_elements(*self._assignment_links)
            for link in links:
                if not link.is_displayed() or not link.is_enabled():
                    continue
                self.scroll_into_view(link)
                self.safe_click(link)
                try:
                    self.wait_for_url_contains("/reportes/detalle", timeout=15)
                except TimeoutException:
                    self.driver.back()
                    self.wait_for_locator(self._assignments_table, "visible", timeout=10)
                    continue
                self.wait_for_page_ready(timeout=10)
                if self.detect_http_500():
                    try:
                        self.driver.back()
                        self.wait_for_locator(self._assignments_table, "visible", timeout=10)
                    except Exception:
                        pass
                    raise RuntimeError("El detalle del reporte mostró un error 500.")
                return self.driver.current_url
            time.sleep(0.3)
        raise TimeoutException("No se encontraron asignaciones disponibles para abrir durante el tiempo de espera.")

    def has_change_status_action(self) -> bool:
        try:
            acciones = self.wait_for_locator(self._actions_button, "clickable", timeout=5)
            self.safe_click(acciones)
            self.wait_for_locator(self._change_status_option, "visible", timeout=5)
            return True
        except TimeoutException:
            return False
