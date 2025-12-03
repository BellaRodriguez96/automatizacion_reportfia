import time

from selenium.common.exceptions import InvalidSessionIdException, NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from helpers import config
from pages.base import Base
from pages.two_factor_page import TwoFactorPage


class LoginPage(Base):
    user_input_str = "carnet"
    password_input_str = "password"
    login_button_str = "//*[@type = \"submit\"]"
    notification_selector = (By.CSS_SELECTOR, "div.notyf__message")

    PERSISTENT_USERS = {config.DEFAULT_USER.lower(), config.MAINTENANCE_USER.lower()}
    FORCE_REFRESH_USERS = {config.ASSIGNEE_USER.lower(), config.FUNDS_USER.lower()}

    def go_to_login(self, *, force: bool = False):
        self.open_page(url=config.LOGIN_URL, force_reload=force)

    def is_on_login_page(self) -> bool:
        try:
            return config.LOGIN_URL in (self.driver.current_url or "")
        except (InvalidSessionIdException, WebDriverException):
            return False

    def is_logged_in(self) -> bool:
        try:
            return config.HOME_URL in (self.driver.current_url or "")
        except (InvalidSessionIdException, WebDriverException):
            return False

    def login(self, username: str, password: str):
        self._ensure_driver()
        self._wait_until_form_ready()
        self.enter_text(self.get_user_input(), username)
        self.enter_text(self.get_password_input(), password or "")
        submit_button = self.wait_for_locator((By.XPATH, self.login_button_str), "clickable", timeout=15)
        self.safe_click(submit_button)
        if not username.strip() or not password.strip():
            time.sleep(0.5)
            return
        self.wait_for_login_transition()

    def wait_for_login_transition(self, timeout: int | None = None):
        wait = WebDriverWait(self.driver, timeout or self.default_timeout)

        def _check(_driver):
            if self.is_logged_in():
                return True
            if self.requires_two_factor():
                return True
            for element in _driver.find_elements(*self.notification_selector):
                if element.is_displayed():
                    return True
            return False

        try:
            wait.until(_check)
        except TimeoutException:
            pass

    def wait_for_auth_state(self, timeout: int | None = None):
        wait = WebDriverWait(self.driver, timeout or self.default_timeout)

        def _check(_driver):
            if self.is_logged_in():
                return ("home", None)
            if self.requires_two_factor():
                return ("two_factor", None)
            for element in _driver.find_elements(*self.notification_selector):
                if element.is_displayed():
                    texto = element.text.strip()
                    lower_text = texto.lower()
                    if "codigo" in lower_text or "correo" in lower_text:
                        return ("two_factor", texto)
                    return ("error", texto)
            return False

        return wait.until(_check)

    def requires_two_factor(self) -> bool:
        try:
            current = (self.driver.current_url or "").lower()
        except (InvalidSessionIdException, WebDriverException):
            return False
        return "two-factor" in current or "/twofactor" in current

    def ensure_logged_in(self, username: str, password: str, *, auto_two_factor: bool = True):
        if not self.driver:
            raise RuntimeError("No hay WebDriver disponible para realizar login.")
        normalized_user = (username or "").strip().lower()
        if not normalized_user:
            raise ValueError("El usuario proporcionado para ensure_logged_in es invalido.")

        self._remember_credentials(normalized_user, password)
        if self._should_reset_session(normalized_user):
            self._clear_persistence()

        if self._has_active_session(normalized_user):
            return

        if not self.requires_two_factor() and not self.is_on_login_page():
            self.go_to_login()

        if self.requires_two_factor():
            if not auto_two_factor:
                raise RuntimeError("Se requiere completar 2FA manualmente antes de continuar.")
            if self._complete_two_factor(normalized_user):
                return
            # Si el flujo 2FA fallo, regresamos a login limpio.
            self.go_to_login(force=True)

        self.login(username, password)

        if self.requires_two_factor():
            if not auto_two_factor:
                raise RuntimeError("Se requiere completar 2FA manualmente antes de continuar.")
            if not self._complete_two_factor(normalized_user):
                raise TimeoutException("No fue posible completar el flujo de 2FA.")

        if self.is_logged_in():
            self._mark_session_active(normalized_user, password)
            return

        mensaje = self.get_error_notification()
        raise RuntimeError(f"No se pudo iniciar sesion: {mensaje or 'motivo desconocido'}")

    # ------------------------------------------------------------------ #
    #   UTILIDADES PRIVADAS
    # ------------------------------------------------------------------ #
    def _wait_until_form_ready(self, timeout: int | None = None):
        for locator in ((By.ID, self.user_input_str), (By.ID, self.password_input_str)):
            try:
                self.wait_for_locator(locator, "visible", timeout=timeout)
            except AttributeError:
                self.wait_for_locator(locator, "presence", timeout=timeout)

    def _complete_two_factor(self, normalized_user: str) -> bool:
        try:
            two_factor = TwoFactorPage(self.driver)
            two_factor.complete_two_factor_flow(normalized_user)
            self.wait_for_url_contains("/inicio", timeout=60)
            if self.is_logged_in():
                self._mark_session_active(normalized_user, getattr(self.driver, "reportfia_password", ""))
                return True
        except TimeoutException:
            pass
        return False

    def _remember_credentials(self, username: str, password: str):
        setattr(self.driver, "reportfia_user", username.lower())
        setattr(self.driver, "reportfia_password", password)

    def _mark_session_active(self, username: str, password: str):
        setattr(self.driver, "reportfia_user", username.lower())
        setattr(self.driver, "reportfia_password", password)
        setattr(self.driver, "reportfia_session_ts", time.time())

    def _has_active_session(self, normalized_user: str) -> bool:
        current_user = getattr(self.driver, "reportfia_user", None)
        if current_user != normalized_user:
            return False
        try:
            if self.is_logged_in():
                return True
            self.driver.get(config.HOME_URL)
            if self.is_logged_in():
                self._mark_session_active(normalized_user, getattr(self.driver, "reportfia_password", ""))
                return True
        except InvalidSessionIdException:
            return False
        except Exception:
            return False
        return False

    def _should_reset_session(self, normalized_user: str) -> bool:
        current_user = getattr(self.driver, "reportfia_user", None)
        if normalized_user in self.FORCE_REFRESH_USERS:
            return True
        if normalized_user in self.PERSISTENT_USERS:
            return current_user not in (None, normalized_user)
        return True

    def _clear_persistence(self):
        try:
            self.clear_storage()
        except Exception:
            pass
        setattr(self.driver, "reportfia_user", None)
        setattr(self.driver, "reportfia_password", None)
        setattr(self.driver, "reportfia_session_ts", None)

    def logout_and_clear(self):
        if not self.driver:
            return
        try:
            self.driver.get(f"{config.BASE_URL}/logout")
            self.wait_for_page_ready(timeout=5)
        except Exception:
            pass
        self._clear_persistence()

    def remember_login_success(self, username: str, password: str):
        """Permite a pruebas especiales registrar manualmente una sesion activa."""
        if not username:
            return
        self._mark_session_active(username.strip().lower(), password or "")

    def get_user_input(self):
        return self.driver.find_element(By.ID, self.user_input_str)

    def get_password_input(self):
        return self.driver.find_element(By.ID, self.password_input_str)

    def get_error_notification(self, timeout: int = 5) -> str:
        try:
            return self.wait_for_locator(self.notification_selector, "visible", timeout=timeout).text.strip()
        except (TimeoutException, InvalidSessionIdException):
            return "Sesion no valida o mensaje no disponible"

    def has_security_lockdown(self) -> bool:
        try:
            html = (self.driver.page_source or "").lower()
        except Exception:
            return False
        palabras = [
            "intentos",
            "bloqueado",
            "demasiados intentos",
            "captcha",
            "recaptcha",
        ]
        return any(p in html for p in palabras)
