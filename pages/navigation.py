from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from helpers import config
from pages.base import Base
from pages.login_page import LoginPage
from pages.two_factor_page import TwoFactorPage


class NavigationMenu(Base):
    """Modela la navegación principal del sitio."""

    def _visit(self, path: str, verify_locator: tuple[str, str] | None = None, timeout: int = 30):
        base_url = config.BASE_URL.rstrip("/")
        path = path.lstrip("/")
        target = f"{base_url}/{path}"
        self.open_page(url=target)
        self._ensure_authenticated(target)
        self.wait_for_page_ready(timeout)
        self.wait_for_url_contains(path)
        if verify_locator:
            try:
                self.wait_for_locator(verify_locator, "visible", timeout=timeout)
            except TimeoutException:
                pass

    def _ensure_authenticated(self, target_url: str):
        current = self.driver.current_url
        if "two-factor" in current:
            two_factor = TwoFactorPage(self.driver)
            two_factor.complete_two_factor_flow(config.DEFAULT_USER)
            self.driver.get(target_url)
            return
        if "iniciar-sesion" in current or "login" in current:
            login_page = LoginPage(self.driver)
            login_page.ensure_logged_in(config.DEFAULT_USER, config.DEFAULT_PASSWORD)
            self.driver.get(target_url)

    def go_to_security_users(self):
        self._visit("/seguridad/usuarios", verify_locator=(By.ID, "add-button"))

    def go_to_maintenance_schools(self):
        self._visit(
            "/mantenimientos/escuela",
            verify_locator=(By.CSS_SELECTOR, "button[data-modal-toggle='static-modal']"),
            timeout=15,
        )

    def go_to_maintenance_resources(self):
        self._visit(
            "/mantenimientos/recursos",
            verify_locator=(By.CSS_SELECTOR, "button[data-modal-toggle='static-modal']"),
            timeout=15,
        )

    def go_to_reports_list(self):
        self._visit(
            "/reportes/listado-general",
            verify_locator=(By.ID, "dropdownRadioButton"),
            timeout=15,
        )

    def open_report_registration(self):
        self._visit("/reportes/registrar", verify_locator=(By.ID, "descripcion"))
