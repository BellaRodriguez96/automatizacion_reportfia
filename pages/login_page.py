import time

from selenium.common.exceptions import NoSuchElementException, TimeoutException, InvalidSessionIdException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from helpers import config
from pages.base import Base
from pages.two_factor_page import TwoFactorPage


class LoginPage(Base):
    # Selectores de la página de Inicio.
    ues_logo_str = "h-36"
    user_input_str = "carnet"
    password_input_str = "password"
    checkbox_str = "remember_me"
    forgot_password_str = "Olvidaste tu contraseña"
    login_button_str = "//*[@type = \"submit\"]"
    back_button_str = "h-4"
    notification_selector = (By.CSS_SELECTOR, "div.notyf__message")

    def __init__(self, driver):
        super().__init__(driver)

    # Métodos get que retornan los elementos WebElement.
    def get_logo(self):
        return self.driver.find_element(By.CLASS_NAME, self.ues_logo_str)

    def get_user_input(self):
        return self.driver.find_element(By.ID, self.user_input_str)

    def get_password_input(self):
        return self.driver.find_element(By.ID, self.password_input_str)

    def get_checkbox(self):
        return self.driver.find_element(By.ID, self.checkbox_str)

    def get_forgot_password(self):
        return self.driver.find_element(By.PARTIAL_LINK_TEXT, self.forgot_password_str)

    def get_login_button(self):
        return self.driver.find_element(By.XPATH, self.login_button_str)

    def get_back_button(self):
        return self.driver.find_element(By.CLASS_NAME, self.back_button_str)

    # Métodos de flujo
    def go_to_login(self):
        self.open_page(url=config.LOGIN_URL)

    def is_on_login_page(self) -> bool:
        return config.LOGIN_URL in self.driver.current_url

    def is_logged_in(self) -> bool:
        return config.HOME_URL in self.driver.current_url

    def login(self, username: str, password: str):
        self.enter_text(self.get_user_input(), username)
        self.enter_text(self.get_password_input(), password or "")
        self.clickElement(self.get_login_button())
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
            try:
                notif = _driver.find_element(*self.notification_selector)
                if notif.is_displayed():
                    return True
            except NoSuchElementException:
                pass
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
        return "two-factor" in self.driver.current_url

    def ensure_logged_in(self, username: str, password: str, *, auto_two_factor: bool = True):
        if self.is_logged_in():
            return
        if not self.is_on_login_page() and not self.requires_two_factor():
            self.go_to_login()
        if self.requires_two_factor() and auto_two_factor:
            TwoFactorPage(self.driver).complete_two_factor_flow(username)
            self.wait_for_url_contains("/inicio")
            return

        self.login(username, password)

        if self.is_logged_in():
            return

        if self.requires_two_factor():
            if not auto_two_factor:
                raise RuntimeError("Se requiere completar el 2FA para continuar.")
            TwoFactorPage(self.driver).complete_two_factor_flow(username)
            self.wait_for_url_contains("/inicio")
            return

        mensaje = self.get_error_notification()
        raise RuntimeError(f"No se pudo iniciar sesión: {mensaje or 'motivo desconocido'}")

    def get_error_notification(self, timeout: int = 5) -> str:
        try:
            return self.wait_for_locator(self.notification_selector, "visible", timeout=timeout).text.strip()
        except (TimeoutException, InvalidSessionIdException):
            return "Sesion no válida o mensaje no disponible"

    def has_security_lockdown(self) -> bool:
        html = self.driver.page_source.lower()
        palabras = [
            "intentos",
            "bloqueado",
            "demasiados intentos",
            "intentos excedidos",
            "captcha",
            "espera",
            "seguridad",
            "recaptcha",
        ]
        return any(p in html for p in palabras)
