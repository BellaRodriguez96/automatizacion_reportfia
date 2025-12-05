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
        self.wait_for_page_ready(min(timeout, 10))
        self.wait_for_url_contains(path, timeout=timeout)
        if verify_locator:
            try:
                self.wait_for_locator(verify_locator, "visible", timeout=timeout)
            except TimeoutException:
                pass

    def _ensure_authenticated(self, target_url: str):
        current = self.driver.current_url
        stored_user = getattr(self.driver, "reportfia_user", config.DEFAULT_USER)
        stored_password = getattr(self.driver, "reportfia_password", config.DEFAULT_PASSWORD)
        if "two-factor" in current:
            two_factor = TwoFactorPage(self.driver)
            two_factor.complete_two_factor_flow(stored_user)
            self.driver.get(target_url)
            return
        if "iniciar-sesion" in current or "login" in current:
            login_page = LoginPage(self.driver)
            login_page.ensure_logged_in(stored_user, stored_password)
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
    def go_to_maintenance_units(self):
        self._visit(
            "/mantenimientos/unidades-medida",
            verify_locator=(By.CSS_SELECTOR, "button[data-modal-target='static-modal']"),
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

    def go_to_reports_assignments(self):
        self._visit(
            "/reportes/mis-asignaciones",
            verify_locator=(By.CSS_SELECTOR, "a[href*='/reportes/detalle/']"),
            timeout=20,
        )

    def go_to_maintenance_funds(self):
        self._visit("/mantenimientos/fondos", verify_locator=(By.CSS_SELECTOR, "table"), timeout=15)

    def go_to_maintenance_incident_types(self):
        self._visit("/mantenimientos/tipos-incidencias", verify_locator=(By.CSS_SELECTOR, "table"), timeout=15)

    def go_to_maintenance_assets(self):
        self._visit("/mantenimientos/bienes", verify_locator=(By.CSS_SELECTOR, "table"), timeout=15)

    def go_to_bitacora(self):
        self._visit("/bitacora", verify_locator=(By.CSS_SELECTOR, "table"), timeout=15)

    def go_to_hr_entities(self):
        self._visit(
            "/recursos-humanos/entidades",
            verify_locator=(By.CSS_SELECTOR, "table"),
            timeout=15,
        )
